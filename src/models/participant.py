"""
Participant model for WithGames Discord Bot.
Represents a user participating in an event.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ParticipantStatus(str, Enum):
    """Participant status enumeration."""

    JOINED = "joined"
    WAITLIST = "waitlist"


@dataclass
class Participant:
    """Participant model representing a user in an event."""

    event_id: str
    user_id: str
    user_name: str
    status: ParticipantStatus = ParticipantStatus.JOINED
    position: int = 0
    joined_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert Participant to dictionary for Firestore.

        Returns:
            Dictionary representation of the participant
        """
        data = asdict(self)

        # Convert datetime to Firestore timestamp
        data["joined_at"] = self.joined_at

        # Convert enum to string
        data["status"] = self.status.value

        # Remove id field (Firestore manages this separately)
        if "id" in data:
            del data["id"]

        return data

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], doc_id: Optional[str] = None
    ) -> "Participant":
        """Create Participant from Firestore document.

        Args:
            data: Dictionary from Firestore document
            doc_id: Firestore document ID

        Returns:
            Participant instance
        """
        # Convert status string to enum
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ParticipantStatus(data["status"])

        # Handle timestamp
        if "joined_at" in data:
            if hasattr(data["joined_at"], "timestamp"):
                # Firestore Timestamp
                data["joined_at"] = datetime.fromtimestamp(
                    data["joined_at"].timestamp()
                )
            elif isinstance(data["joined_at"], str):
                data["joined_at"] = datetime.fromisoformat(data["joined_at"])

        participant = cls(**data)
        participant.id = doc_id
        return participant

    def is_on_waitlist(self) -> bool:
        """Check if participant is on waitlist.

        Returns:
            True if on waitlist, False otherwise
        """
        return self.status == ParticipantStatus.WAITLIST

    def promote_from_waitlist(self):
        """Promote participant from waitlist to joined status."""
        if self.is_on_waitlist():
            self.status = ParticipantStatus.JOINED
            self.position = 0

    def __str__(self) -> str:
        """String representation of the participant."""
        return f"Participant(user='{self.user_name}', event_id='{self.event_id}', status={self.status.value})"
