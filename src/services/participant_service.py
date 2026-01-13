"""
Participant service for WithGames Discord Bot.
Handles participant business logic and Firestore operations.
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from src.models.participant import Participant, ParticipantStatus
from src.services.firestore_service import firestore_service
from src.services.event_service import event_service

logger = logging.getLogger(__name__)


class ParticipantService:
    """Service for participant operations."""

    def __init__(self):
        """Initialize participant service."""
        self.firestore = firestore_service
        self.collection_name = "participants"
        self.event_service = event_service

    async def join_event(
        self, event_id: str, user_id: str, user_name: str
    ) -> Tuple[bool, str, Optional[Participant]]:
        """Add a user to an event.

        Args:
            event_id: Event ID
            user_id: User's Discord ID
            user_name: User's display name

        Returns:
            Tuple of (success, message, participant)
            - success: True if joined/waitlisted successfully
            - message: Status message for user
            - participant: Created participant object
        """
        try:
            # Check if event exists and can be joined
            event = await self.event_service.get_event(event_id)
            if not event:
                return False, "イベントが見つかりません", None

            can_join, reason = await self.event_service.can_user_join(event_id)
            if not can_join:
                return False, reason, None

            # Check if user is already participating
            existing = await self.is_user_participating(event_id, user_id)
            if existing:
                return False, "既にこのイベントに参加しています。\n参加をやめる場合は「❌ 参加をやめる」ボタンを押してください。", None

            # Determine if user joins directly or goes to waitlist
            participants = await self.get_participants(event_id)
            current_count = len(participants)

            if current_count < event.max_participants:
                # Join directly
                status = ParticipantStatus.JOINED
                position = 0
                message = f"✅ イベント「{event.title}」に参加しました！"
            else:
                # Add to waitlist
                waitlist = await self.get_waitlist(event_id)
                status = ParticipantStatus.WAITLIST
                position = len(waitlist) + 1
                message = f"⏳ 定員に達しているため、キャンセル待ちリスト（{position}番目）に追加しました"

            # Create participant
            participant = Participant(
                event_id=event_id,
                user_id=user_id,
                user_name=user_name,
                status=status,
                position=position,
            )

            # Save to Firestore
            participant_data = participant.to_dict()
            logger.info(f"Saving participant to Firestore: {participant_data}")
            participant_id = self.firestore.create_document(
                self.collection_name, participant_data
            )
            participant.id = participant_id
            logger.info(f"Participant saved with ID: {participant_id}")

            # Update event participant count if joined directly
            if status == ParticipantStatus.JOINED:
                await self.event_service.increment_participant_count(event_id)

            logger.info(
                f"User {user_id} joined event {event_id} with status {status.value}"
            )

            return True, message, participant

        except Exception as e:
            logger.error(f"Failed to join event {event_id}: {e}")
            return False, "参加処理中にエラーが発生しました", None

    async def leave_event(
        self, event_id: str, user_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Remove a user from an event.

        Args:
            event_id: Event ID
            user_id: User's Discord ID

        Returns:
            Tuple of (success, message, promoted_user_id)
            - success: True if left successfully
            - message: Status message for user
            - promoted_user_id: ID of user promoted from waitlist (if any)
        """
        try:
            # Get participant record
            participant = await self.get_participant_by_user(event_id, user_id)
            if not participant:
                return False, "このイベントに参加していません", None

            # Delete participant
            self.firestore.delete_document(self.collection_name, participant.id)

            # If was in main list, decrement count and promote from waitlist
            promoted_user_id = None
            if participant.status == ParticipantStatus.JOINED:
                await self.event_service.decrement_participant_count(event_id)
                promoted_user_id = await self._promote_from_waitlist(event_id)

            # If was in waitlist, update positions
            elif participant.status == ParticipantStatus.WAITLIST:
                await self._update_waitlist_positions(event_id)

            event = await self.event_service.get_event(event_id)
            event_title = event.title if event else "イベント"

            logger.info(f"User {user_id} left event {event_id}")

            return True, f"❌ 「{event_title}」への参加をキャンセルしました", promoted_user_id

        except Exception as e:
            logger.error(f"Failed to leave event {event_id}: {e}")
            return False, "キャンセル処理中にエラーが発生しました", None

    async def get_participants(
        self, event_id: str, limit: Optional[int] = None
    ) -> List[Participant]:
        """Get all participants for an event (excluding waitlist).

        Args:
            event_id: Event ID
            limit: Optional limit on results

        Returns:
            List of participants
        """
        try:
            filters = [
                ("event_id", "==", event_id),
                ("status", "==", ParticipantStatus.JOINED.value),
            ]

            logger.info(f"Querying participants for event {event_id} with filters: {filters}")
            # Remove order_by to avoid needing a composite index
            participant_data_list = self.firestore.query_documents(
                self.collection_name,
                filters=filters,
                limit=limit,
            )
            logger.info(f"Found {len(participant_data_list)} participants for event {event_id}")

            participants = [
                Participant.from_dict(data, doc_id=data.get("id"))
                for data in participant_data_list
            ]
            
            # Sort by joined_at in Python instead of Firestore
            participants.sort(key=lambda p: p.joined_at)

            return participants

        except Exception as e:
            logger.error(f"Failed to get participants for event {event_id}: {e}")
            return []

    async def get_waitlist(
        self, event_id: str, limit: Optional[int] = None
    ) -> List[Participant]:
        """Get waitlist for an event.

        Args:
            event_id: Event ID
            limit: Optional limit on results

        Returns:
            List of waitlisted participants
        """
        try:
            filters = [
                ("event_id", "==", event_id),
                ("status", "==", ParticipantStatus.WAITLIST.value),
            ]

            # Remove order_by to avoid needing a composite index
            participant_data_list = self.firestore.query_documents(
                self.collection_name,
                filters=filters,
                limit=limit,
            )

            waitlist = [
                Participant.from_dict(data, doc_id=data.get("id"))
                for data in participant_data_list
            ]
            
            # Sort by position in Python instead of Firestore
            waitlist.sort(key=lambda p: p.position)

            return waitlist

        except Exception as e:
            logger.error(f"Failed to get waitlist for event {event_id}: {e}")
            return []

    async def get_participant_by_user(
        self, event_id: str, user_id: str
    ) -> Optional[Participant]:
        """Get a participant by event and user ID.

        Args:
            event_id: Event ID
            user_id: User's Discord ID

        Returns:
            Participant if found, None otherwise
        """
        try:
            filters = [
                ("event_id", "==", event_id),
                ("user_id", "==", user_id),
            ]

            participant_data_list = self.firestore.query_documents(
                self.collection_name, filters=filters, limit=1
            )

            if participant_data_list:
                return Participant.from_dict(
                    participant_data_list[0], doc_id=participant_data_list[0].get("id")
                )

            return None

        except Exception as e:
            logger.error(
                f"Failed to get participant for event {event_id}, user {user_id}: {e}"
            )
            return None

    async def is_user_participating(self, event_id: str, user_id: str) -> bool:
        """Check if a user is participating in an event (including waitlist).

        Args:
            event_id: Event ID
            user_id: User's Discord ID

        Returns:
            True if user is participating or on waitlist
        """
        participant = await self.get_participant_by_user(event_id, user_id)
        return participant is not None

    async def get_user_events(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Participant]:
        """Get all events a user is participating in.

        Args:
            user_id: User's Discord ID
            limit: Optional limit on results

        Returns:
            List of participant records
        """
        try:
            filters = [
                ("user_id", "==", user_id),
            ]

            participant_data_list = self.firestore.query_documents(
                self.collection_name,
                filters=filters,
                order_by="joined_at",
                limit=limit,
            )

            participants = [
                Participant.from_dict(data, doc_id=data.get("id"))
                for data in participant_data_list
            ]

            return participants

        except Exception as e:
            logger.error(f"Failed to get events for user {user_id}: {e}")
            return []

    async def _promote_from_waitlist(self, event_id: str) -> Optional[str]:
        """Promote the first person from waitlist to participant.

        Args:
            event_id: Event ID

        Returns:
            User ID of promoted user, or None
        """
        try:
            waitlist = await self.get_waitlist(event_id, limit=1)
            if not waitlist:
                return None

            first_in_line = waitlist[0]

            # Update status to JOINED
            first_in_line.status = ParticipantStatus.JOINED
            first_in_line.position = 0
            first_in_line.updated_at = datetime.utcnow()

            participant_data = first_in_line.to_dict()
            self.firestore.update_document(
                self.collection_name, first_in_line.id, participant_data
            )

            # Increment participant count
            await self.event_service.increment_participant_count(event_id)

            # Update remaining waitlist positions
            await self._update_waitlist_positions(event_id)

            logger.info(
                f"Promoted user {first_in_line.user_id} from waitlist for event {event_id}"
            )

            return first_in_line.user_id

        except Exception as e:
            logger.error(f"Failed to promote from waitlist for event {event_id}: {e}")
            return None

    async def _update_waitlist_positions(self, event_id: str) -> bool:
        """Update position numbers for waitlist after a change.

        Args:
            event_id: Event ID

        Returns:
            True if successful
        """
        try:
            waitlist = await self.get_waitlist(event_id)

            for index, participant in enumerate(waitlist, start=1):
                if participant.position != index:
                    participant.position = index
                    participant.updated_at = datetime.utcnow()

                    participant_data = participant.to_dict()
                    self.firestore.update_document(
                        self.collection_name, participant.id, participant_data
                    )

            logger.info(f"Updated waitlist positions for event {event_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to update waitlist positions for event {event_id}: {e}"
            )
            return False

    async def promote_from_waitlist(self, event_id: str, user_id: str) -> bool:
        """Promote a specific user from waitlist to participant.

        Args:
            event_id: Event ID
            user_id: User ID to promote

        Returns:
            True if successful, False otherwise
        """
        try:
            participant = await self.get_participant_by_user(event_id, user_id)
            
            if not participant or participant.status != ParticipantStatus.WAITLIST:
                return False

            # Update status to JOINED
            participant.status = ParticipantStatus.JOINED
            participant.position = 0
            participant.updated_at = datetime.utcnow()

            participant_data = participant.to_dict()
            self.firestore.update_document(
                self.collection_name, participant.id, participant_data
            )

            # Increment participant count
            await self.event_service.increment_participant_count(event_id)

            # Update remaining waitlist positions
            await self._update_waitlist_positions(event_id)

            logger.info(f"Promoted user {user_id} from waitlist for event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to promote user {user_id} from waitlist: {e}")
            return False

    async def demote_to_waitlist(self, event_id: str, user_id: str) -> bool:
        """Demote a participant to waitlist.

        Args:
            event_id: Event ID
            user_id: User ID to demote

        Returns:
            True if successful, False otherwise
        """
        try:
            participant = await self.get_participant_by_user(event_id, user_id)
            
            if not participant or participant.status != ParticipantStatus.JOINED:
                return False

            # Get current waitlist to determine position
            waitlist = await self.get_waitlist(event_id)
            new_position = len(waitlist) + 1

            # Update status to WAITLIST
            participant.status = ParticipantStatus.WAITLIST
            participant.position = new_position
            participant.updated_at = datetime.utcnow()

            participant_data = participant.to_dict()
            self.firestore.update_document(
                self.collection_name, participant.id, participant_data
            )

            # Decrement participant count
            await self.event_service.decrement_participant_count(event_id)

            logger.info(f"Demoted user {user_id} to waitlist for event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to demote user {user_id} to waitlist: {e}")
            return False

    async def delete_all_participants(self, event_id: str) -> bool:
        """Delete all participants for an event.

        Args:
            event_id: Event ID

        Returns:
            True if successful, False otherwise
        """
        try:
            filters = [("event_id", "==", event_id)]
            
            participant_data_list = self.firestore.query_documents(
                self.collection_name, filters=filters
            )

            for participant_data in participant_data_list:
                participant_id = participant_data.get("id")
                if participant_id:
                    self.firestore.delete_document(self.collection_name, participant_id)

            logger.info(f"Deleted all participants for event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete participants for event {event_id}: {e}")
            return False


# Global service instance
participant_service = ParticipantService()
