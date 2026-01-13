"""
Color constants for WithGames Discord Bot.
Defines colors for different event statuses and UI elements.
"""


class Colors:
    """Color constants for embeds and UI elements."""

    # Event status colors
    ACTIVE = 0x2ECC71  # Green - Event is accepting participants
    FULL = 0xE67E22  # Orange - Event is at capacity
    CLOSED = 0x9B59B6  # Purple - Recruitment closed
    CANCELLED = 0xE74C3C  # Red - Event is cancelled
    COMPLETED = 0x95A5A6  # Gray - Event is completed

    # UI element colors
    INFO = 0x3498DB  # Blue - Information messages
    SUCCESS = 0x2ECC71  # Green - Success messages
    WARNING = 0xF39C12  # Yellow - Warning messages
    ERROR = 0xE74C3C  # Red - Error messages

    # Brand colors
    PRIMARY = 0x5865F2  # Discord Blurple
    SECONDARY = 0x57F287  # Discord Green

    @staticmethod
    def from_status(status: str) -> int:
        """Get color based on event status.

        Args:
            status: Event status string

        Returns:
            Color hex value
        """
        status_colors = {
            "active": Colors.ACTIVE,
            "full": Colors.FULL,
            "closed": Colors.CLOSED,
            "cancelled": Colors.CANCELLED,
            "completed": Colors.COMPLETED,
        }
        return status_colors.get(status.lower(), Colors.INFO)
