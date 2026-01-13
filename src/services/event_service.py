"""
Event service for WithGames Discord Bot.
Handles event business logic and Firestore operations.
"""
import logging
from datetime import datetime
from typing import List, Optional
from src.models.event import Event, EventStatus
from src.services.firestore_service import firestore_service
from src.utils.game_data import GameData

logger = logging.getLogger(__name__)


class EventService:
    """Service for event operations."""

    def __init__(self):
        """Initialize event service."""
        self.firestore = firestore_service
        self.collection_name = "events"

    async def create_event(
        self,
        title: str,
        description: str,
        game_type: str,
        start_time: datetime,
        max_participants: int,
        creator_id: str,
        creator_name: str,
        guild_id: str,
        channel_id: str,
    ) -> Event:
        """Create a new event.

        Args:
            title: Event title
            description: Event description
            game_type: Game type
            start_time: Event start time
            max_participants: Maximum participants
            creator_id: Creator's Discord ID
            creator_name: Creator's display name
            guild_id: Guild ID
            channel_id: Channel ID

        Returns:
            Created event

        Raises:
            Exception: If event creation fails
        """
        try:
            # Get game emoji and icon URL
            game_emoji = GameData.get_game_emoji(game_type)
            game_icon_url = GameData.get_game_icon_url(game_type)

            # Create event object
            event = Event(
                title=title,
                description=description,
                game_type=game_type,
                game_emoji=game_emoji,
                game_icon_url=game_icon_url,
                start_time=start_time,
                max_participants=max_participants,
                creator_id=creator_id,
                creator_name=creator_name,
                guild_id=guild_id,
                channel_id=channel_id,
                status=EventStatus.ACTIVE,
            )

            # Save to Firestore
            event_data = event.to_dict()
            event_id = self.firestore.create_document(
                self.collection_name, event_data
            )

            event.id = event_id
            logger.info(f"Created event: {event_id}")

            return event

        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise

    async def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event if found, None otherwise
        """
        try:
            event_data = self.firestore.get_document(
                self.collection_name, event_id
            )

            if event_data:
                return Event.from_dict(event_data, doc_id=event_id)

            return None

        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            return None

    async def update_event(self, event: Event) -> bool:
        """Update an event.

        Args:
            event: Event to update

        Returns:
            True if successful, False otherwise
        """
        try:
            event.updated_at = datetime.utcnow()
            event_data = event.to_dict()

            self.firestore.update_document(
                self.collection_name, event.id, event_data
            )

            logger.info(f"Updated event: {event.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update event {event.id}: {e}")
            return False

    async def update_event_message_id(
        self, event_id: str, message_id: str
    ) -> bool:
        """Update event's message ID.

        Args:
            event_id: Event ID
            message_id: Discord message ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.firestore.update_document(
                self.collection_name,
                event_id,
                {"message_id": message_id, "updated_at": datetime.utcnow()},
            )

            logger.info(f"Updated message_id for event {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update message_id for event {event_id}: {e}")
            return False

    async def delete_event(self, event_id: str) -> bool:
        """Delete an event.

        Args:
            event_id: Event ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.firestore.delete_document(self.collection_name, event_id)
            logger.info(f"Deleted event: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            return False

    async def get_active_events(
        self, guild_id: str, limit: Optional[int] = None
    ) -> List[Event]:
        """Get all active events for a guild.

        Args:
            guild_id: Guild ID
            limit: Optional limit on number of results

        Returns:
            List of active events
        """
        try:
            filters = [
                ("guild_id", "==", guild_id),
                ("status", "==", EventStatus.ACTIVE.value),
            ]

            event_data_list = self.firestore.query_documents(
                self.collection_name,
                filters=filters,
                order_by="start_time",
                limit=limit,
            )

            events = [
                Event.from_dict(data, doc_id=data.get("id"))
                for data in event_data_list
            ]

            return events

        except Exception as e:
            logger.error(f"Failed to get active events for guild {guild_id}: {e}")
            return []

    async def get_all_events(
        self, guild_id: str, limit: Optional[int] = None
    ) -> List[Event]:
        """Get all events for a guild.

        Args:
            guild_id: Guild ID
            limit: Optional limit on number of results

        Returns:
            List of all events
        """
        try:
            filters = [("guild_id", "==", guild_id)]

            event_data_list = self.firestore.query_documents(
                self.collection_name,
                filters=filters,
                order_by="created_at",
                limit=limit,
            )

            events = [
                Event.from_dict(data, doc_id=data.get("id"))
                for data in event_data_list
            ]

            return events

        except Exception as e:
            logger.error(f"Failed to get all events for guild {guild_id}: {e}")
            return []

    async def increment_participant_count(self, event_id: str) -> bool:
        """Increment event's participant count.

        Args:
            event_id: Event ID

        Returns:
            True if successful, False otherwise
        """
        try:
            event = await self.get_event(event_id)
            if not event:
                return False

            event.current_participants += 1
            event.update_status()

            return await self.update_event(event)

        except Exception as e:
            logger.error(f"Failed to increment participant count for {event_id}: {e}")
            return False

    async def decrement_participant_count(self, event_id: str) -> bool:
        """Decrement event's participant count.

        Args:
            event_id: Event ID

        Returns:
            True if successful, False otherwise
        """
        try:
            event = await self.get_event(event_id)
            if not event:
                return False

            event.current_participants = max(0, event.current_participants - 1)
            event.update_status()

            return await self.update_event(event)

        except Exception as e:
            logger.error(f"Failed to decrement participant count for {event_id}: {e}")
            return False

    async def can_user_join(self, event_id: str) -> tuple[bool, str]:
        """Check if a user can join an event.

        Args:
            event_id: Event ID

        Returns:
            Tuple of (can_join, reason)
        """
        event = await self.get_event(event_id)

        if not event:
            return False, "イベントが見つかりません"

        if event.status == EventStatus.CLOSED:
            return False, "このイベントの募集は終了しました"

        if event.status == EventStatus.CANCELLED:
            return False, "このイベントはキャンセルされました"

        if event.status == EventStatus.COMPLETED:
            return False, "このイベントは既に終了しました"

        return True, ""


# Global service instance
event_service = EventService()
