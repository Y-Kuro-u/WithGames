"""
Datetime utilities for WithGames Discord Bot.
"""
from datetime import datetime, timedelta
from typing import Optional
import pytz


class DateTimeUtils:
    """Datetime utility functions."""

    @staticmethod
    def to_discord_timestamp(dt: datetime, style: str = "F") -> str:
        """Convert datetime to Discord timestamp format.

        Discord automatically displays timestamps in the user's local timezone.

        Args:
            dt: Datetime object
            style: Discord timestamp style
                - "t": Short time (e.g., "16:20")
                - "T": Long time (e.g., "16:20:30")
                - "d": Short date (e.g., "20/04/2021")
                - "D": Long date (e.g., "20 April 2021")
                - "f": Short date/time (e.g., "20 April 2021 16:20") [DEFAULT]
                - "F": Long date/time (e.g., "Tuesday, 20 April 2021 16:20")
                - "R": Relative time (e.g., "2 months ago")

        Returns:
            Discord timestamp string
        """
        timestamp = int(dt.timestamp())
        return f"<t:{timestamp}:{style}>"

    @staticmethod
    def format_relative_time(dt: datetime) -> str:
        """Format datetime as relative time (Discord format).

        Args:
            dt: Datetime object

        Returns:
            Discord relative timestamp string
        """
        return DateTimeUtils.to_discord_timestamp(dt, style="R")

    @staticmethod
    def format_full_datetime(dt: datetime) -> str:
        """Format datetime in full format (Discord format).

        Args:
            dt: Datetime object

        Returns:
            Discord full datetime string
        """
        return DateTimeUtils.to_discord_timestamp(dt, style="F")

    @staticmethod
    def format_edit_datetime(dt: datetime) -> str:
        """Format datetime for editing (YYYY-MM-DD HH:MM format).

        Args:
            dt: Datetime object

        Returns:
            Formatted datetime string for editing
        """
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def is_past(dt: datetime) -> bool:
        """Check if datetime is in the past.

        Args:
            dt: Datetime object

        Returns:
            True if datetime is in the past, False otherwise
        """
        return dt < datetime.now()

    @staticmethod
    def is_future(dt: datetime) -> bool:
        """Check if datetime is in the future.

        Args:
            dt: Datetime object

        Returns:
            True if datetime is in the future, False otherwise
        """
        return dt > datetime.now()

    @staticmethod
    def get_time_until(dt: datetime) -> timedelta:
        """Get time until a datetime.

        Args:
            dt: Datetime object

        Returns:
            Timedelta until the datetime
        """
        return dt - datetime.now()

    @staticmethod
    def get_time_since(dt: datetime) -> timedelta:
        """Get time since a datetime.

        Args:
            dt: Datetime object

        Returns:
            Timedelta since the datetime
        """
        return datetime.now() - dt

    @staticmethod
    def format_duration(td: timedelta) -> str:
        """Format timedelta as human-readable string.

        Args:
            td: Timedelta object

        Returns:
            Formatted duration string (e.g., "2時間30分")
        """
        total_seconds = int(td.total_seconds())

        if total_seconds < 0:
            return "過去"

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        parts = []
        if days > 0:
            parts.append(f"{days}日")
        if hours > 0:
            parts.append(f"{hours}時間")
        if minutes > 0:
            parts.append(f"{minutes}分")

        if not parts:
            return "1分未満"

        return "".join(parts)

    @staticmethod
    def get_reminder_time(event_time: datetime, minutes_before: int = 30) -> datetime:
        """Get reminder time for an event.

        Args:
            event_time: Event start time
            minutes_before: Minutes before event to send reminder

        Returns:
            Reminder datetime
        """
        return event_time - timedelta(minutes=minutes_before)

    @staticmethod
    def should_send_reminder(
        event_time: datetime, reminder_sent: bool, minutes_before: int = 30
    ) -> bool:
        """Check if reminder should be sent.

        Args:
            event_time: Event start time
            reminder_sent: Whether reminder has been sent
            minutes_before: Minutes before event to send reminder

        Returns:
            True if reminder should be sent, False otherwise
        """
        if reminder_sent:
            return False

        reminder_time = DateTimeUtils.get_reminder_time(event_time, minutes_before)
        now = datetime.now()

        return now >= reminder_time and now < event_time

    @staticmethod
    def to_utc(dt: datetime) -> datetime:
        """Convert datetime to UTC.

        Args:
            dt: Datetime object

        Returns:
            UTC datetime
        """
        if dt.tzinfo is None:
            # Assume local timezone if naive
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(pytz.UTC)

    @staticmethod
    def from_utc(dt: datetime, timezone: str = "Asia/Tokyo") -> datetime:
        """Convert UTC datetime to specific timezone.

        Args:
            dt: UTC datetime
            timezone: Target timezone string

        Returns:
            Localized datetime
        """
        tz = pytz.timezone(timezone)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(tz)
