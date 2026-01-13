"""
Text formatting utilities for WithGames Discord Bot.
"""
from typing import List


class Formatters:
    """Text formatting utilities."""

    @staticmethod
    def create_progress_bar(
        current: int, maximum: int, length: int = 10, filled_char: str = "█", empty_char: str = "░"
    ) -> str:
        """Create a visual progress bar.

        Args:
            current: Current value
            maximum: Maximum value
            length: Length of the progress bar
            filled_char: Character for filled portion
            empty_char: Character for empty portion

        Returns:
            Progress bar string (e.g., "████████░░")
        """
        if maximum == 0:
            filled_length = 0
        else:
            filled_length = int((current / maximum) * length)

        filled_length = min(filled_length, length)  # Ensure within bounds

        filled = filled_char * filled_length
        empty = empty_char * (length - filled_length)

        return f"{filled}{empty}"

    @staticmethod
    def format_participation_status(current: int, maximum: int) -> str:
        """Format participation status with progress bar and emoji.

        Args:
            current: Current participants
            maximum: Maximum participants

        Returns:
            Formatted status string with progress bar
        """
        percentage = int((current / maximum) * 100) if maximum > 0 else 0
        progress_bar = Formatters.create_progress_bar(current, maximum)

        # Add emoji based on status
        emoji = ""
        if current >= maximum:
            emoji = " 🔥"
        elif percentage >= 75:
            emoji = " 🔥"
        elif percentage >= 50:
            emoji = ""
        else:
            emoji = ""

        return f"{progress_bar} {current}/{maximum} 名 ({percentage}%){emoji}"

    @staticmethod
    def format_waitlist_status(waitlist_count: int) -> str:
        """Format waitlist status.

        Args:
            waitlist_count: Number of people on waitlist

        Returns:
            Formatted waitlist string
        """
        if waitlist_count == 0:
            return ""

        return f"キャンセル待ち: {waitlist_count}名 ⏳"

    @staticmethod
    def format_participant_list(
        participants: List, max_display: int = 10, show_position: bool = False
    ) -> str:
        """Format list of participants for display.

        Args:
            participants: List of Participant objects
            max_display: Maximum number to display
            show_position: Whether to show position numbers

        Returns:
            Formatted participant list string with Discord mentions
        """
        if not participants:
            return "まだ参加者がいません"

        displayed = participants[:max_display]
        remaining = len(participants) - max_display

        lines = []
        for i, participant in enumerate(displayed, start=1):
            # Use Discord mention format
            mention = f"<@{participant.user_id}>"
            if show_position:
                lines.append(f"{i}. {mention}")
            else:
                lines.append(f"✅ {mention}")

        result = "\n".join(lines)

        if remaining > 0:
            result += f"\n\n[他 +{remaining}名が参加中]"

        return result

    @staticmethod
    def format_waitlist(waitlist: List, max_display: int = 5) -> str:
        """Format waitlist for display.

        Args:
            waitlist: List of Participant objects on waitlist
            max_display: Maximum number to display

        Returns:
            Formatted waitlist string with Discord mentions
        """
        if not waitlist:
            return ""

        displayed = waitlist[:max_display]
        remaining = len(waitlist) - max_display

        lines = []
        for i, participant in enumerate(displayed, start=1):
            mention = f"<@{participant.user_id}>"
            lines.append(f"⏳ {i}. {mention}")

        result = "\n".join(lines)

        if remaining > 0:
            result += f"\n[他 +{remaining}名が待機中]"

        return result

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def format_user_mention(user_id: str) -> str:
        """Format user mention.

        Args:
            user_id: Discord user ID

        Returns:
            Mention string
        """
        return f"<@{user_id}>"

    @staticmethod
    def format_channel_mention(channel_id: str) -> str:
        """Format channel mention.

        Args:
            channel_id: Discord channel ID

        Returns:
            Channel mention string
        """
        return f"<#{channel_id}>"

    @staticmethod
    def format_event_id_short(event_id: str) -> str:
        """Format event ID for display (shortened).

        Args:
            event_id: Full event ID

        Returns:
            Shortened event ID (first 8 characters)
        """
        return event_id[:8] if event_id else "N/A"
