"""
Event model for WithGames Discord Bot.
Represents a game event with participants and recruitment details.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EventStatus(str, Enum):
    """Event status enumeration."""

    ACTIVE = "active"
    FULL = "full"
    CLOSED = "closed"  # Recruitment closed but event not started
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class Event:
    """Event model representing a game recruitment event."""

    title: str
    description: str
    game_type: str
    start_time: datetime
    max_participants: int
    creator_id: str
    creator_name: str
    guild_id: str
    channel_id: str
    game_emoji: str = "🎮"
    game_icon_url: Optional[str] = None
    message_id: Optional[str] = None
    current_participants: int = 0
    status: EventStatus = EventStatus.ACTIVE
    reminder_sent: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert Event to dictionary for Firestore.

        Returns:
            Dictionary representation of the event
        """
        data = asdict(self)

        # Convert datetime objects to Firestore timestamps
        data["start_time"] = self.start_time
        data["created_at"] = self.created_at
        data["updated_at"] = self.updated_at

        # Convert enum to string
        data["status"] = self.status.value

        # Remove id field (Firestore manages this separately)
        if "id" in data:
            del data["id"]

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: Optional[str] = None) -> "Event":
        """Create Event from Firestore document.

        Args:
            data: Dictionary from Firestore document
            doc_id: Firestore document ID

        Returns:
            Event instance
        """
        # Convert status string to enum
        if "status" in data and isinstance(data["status"], str):
            data["status"] = EventStatus(data["status"])

        # Handle timestamps
        if "start_time" in data:
            if hasattr(data["start_time"], "timestamp"):
                # Firestore Timestamp
                data["start_time"] = datetime.fromtimestamp(
                    data["start_time"].timestamp()
                )
            elif isinstance(data["start_time"], str):
                data["start_time"] = datetime.fromisoformat(data["start_time"])

        if "created_at" in data:
            if hasattr(data["created_at"], "timestamp"):
                data["created_at"] = datetime.fromtimestamp(
                    data["created_at"].timestamp()
                )
            elif isinstance(data["created_at"], str):
                data["created_at"] = datetime.fromisoformat(data["created_at"])

        if "updated_at" in data:
            if hasattr(data["updated_at"], "timestamp"):
                data["updated_at"] = datetime.fromtimestamp(
                    data["updated_at"].timestamp()
                )
            elif isinstance(data["updated_at"], str):
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        event = cls(**data)
        event.id = doc_id
        return event

    def is_full(self) -> bool:
        """Check if event is at max capacity.

        Returns:
            True if event is full, False otherwise
        """
        return self.current_participants >= self.max_participants

    def can_accept_participants(self) -> bool:
        """Check if event can accept more participants.

        Returns:
            True if event can accept participants, False otherwise
        """
        return (
            self.status == EventStatus.ACTIVE
            and not self.is_full()
            and self.start_time > datetime.utcnow()
        )

    def update_status(self):
        """Update event status based on current state."""
        if self.is_full() and self.status == EventStatus.ACTIVE:
            self.status = EventStatus.FULL
        elif not self.is_full() and self.status == EventStatus.FULL:
            self.status = EventStatus.ACTIVE

        if self.start_time < datetime.utcnow() and self.status in [
            EventStatus.ACTIVE,
            EventStatus.FULL,
        ]:
            self.status = EventStatus.COMPLETED

        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation of the event."""
        return f"Event(title='{self.title}', game='{self.game_type}', status={self.status.value})"
