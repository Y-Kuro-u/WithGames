"""
Select menu components for WithGames Discord Bot.
"""
import discord
from discord.ui import Select, View
from typing import List, Optional
from src.utils.game_data import GameData, CUSTOM_GAME


class GameSelectMenu(Select):
    """Select menu for choosing a game."""

    def __init__(self, popular_count: int = 10):
        """Initialize game select menu.

        Args:
            popular_count: Number of popular games to show
        """
        # Get popular games
        popular_games = GameData.get_popular_games(popular_count)

        # Create options
        options = []
        for game in popular_games:
            options.append(
                discord.SelectOption(
                    label=game.name,
                    value=game.name,
                    emoji=game.emoji,
                    description=game.category,
                )
            )

        # Add custom option at the end
        options.append(
            discord.SelectOption(
                label=CUSTOM_GAME.name,
                value="custom",
                emoji=CUSTOM_GAME.emoji,
                description="手動でゲーム名を入力",
            )
        )

        super().__init__(
            placeholder="ゲームを選択してください 🎮",
            min_values=1,
            max_values=1,
            options=options,
        )


class GameSelectView(View):
    """View containing game select menu."""

    def __init__(self, popular_count: int = 10):
        """Initialize game select view.

        Args:
            popular_count: Number of popular games to show
        """
        super().__init__(timeout=300)  # 5 minute timeout

        self.selected_game: Optional[str] = None
        self.selected_emoji: Optional[str] = None

        # Create and add select menu
        self.game_select = GameSelectMenu(popular_count)
        self.game_select.callback = self.select_callback
        self.add_item(self.game_select)

    async def select_callback(self, interaction: discord.Interaction):
        """Handle game selection.

        Args:
            interaction: Discord interaction from the select menu
        """
        selected_value = self.game_select.values[0]

        if selected_value == "custom":
            # Custom game - will be handled by a button that opens modal
            self.selected_game = "custom"
            self.selected_emoji = CUSTOM_GAME.emoji
        else:
            # Pre-defined game
            self.selected_game = selected_value
            game_info = GameData.get_game_by_name(selected_value)
            self.selected_emoji = game_info.emoji if game_info else "🎮"

        # This is the select menu interaction, not the original command interaction
        # We need to acknowledge it, but we'll update the original message via edit
        await interaction.response.edit_message(
            content=f"選択しました: {self.selected_emoji} **{self.selected_game if self.selected_game != 'custom' else 'カスタムゲーム'}**",
            view=None  # Remove the select menu
        )

        # Stop the view
        self.stop()


class EventSelectMenu(Select):
    """Select menu for choosing an event from a list."""

    def __init__(self, events: List[dict], max_options: int = 25):
        """Initialize event select menu.

        Args:
            events: List of event dictionaries with 'id', 'title', 'game_emoji'
            max_options: Maximum number of options (Discord limit is 25)
        """
        options = []
        for event in events[:max_options]:
            options.append(
                discord.SelectOption(
                    label=event.get("title", "Unknown Event"),
                    value=event.get("id", ""),
                    emoji=event.get("game_emoji", "🎮"),
                    description=f"{event.get('current_participants', 0)}/{event.get('max_participants', 0)} 参加者",
                )
            )

        super().__init__(
            placeholder="イベントを選択してください",
            min_values=1,
            max_values=1,
            options=options if options else [
                discord.SelectOption(
                    label="イベントなし",
                    value="none",
                    description="現在イベントがありません"
                )
            ],
        )


class EventSelectView(View):
    """View containing event select menu."""

    def __init__(self, events: List[dict], max_options: int = 25):
        """Initialize event select view.

        Args:
            events: List of event dictionaries
            max_options: Maximum number of options
        """
        super().__init__(timeout=180)  # 3 minute timeout

        self.selected_event_id: Optional[str] = None

        # Create and add select menu
        self.event_select = EventSelectMenu(events, max_options)
        self.event_select.callback = self.select_callback
        self.add_item(self.event_select)

    async def select_callback(self, interaction: discord.Interaction):
        """Handle event selection."""
        self.selected_event_id = self.event_select.values[0]
        self.stop()
        await interaction.response.defer()
