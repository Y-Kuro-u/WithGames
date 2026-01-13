"""
Modal dialogs for WithGames Discord Bot.
"""
import discord
from discord.ui import Modal, TextInput
from typing import Optional


class EventCreationModal(Modal):
    """Modal for creating a new event."""

    def __init__(self, game_type: str, game_emoji: str = "🎮"):
        """Initialize event creation modal.

        Args:
            game_type: Selected game type
            game_emoji: Emoji for the game
        """
        super().__init__(title=f"イベント作成 - {game_type}")

        self.game_type = game_type
        self.game_emoji = game_emoji

        # Event title input
        self.title_input = TextInput(
            label="イベントタイトル",
            placeholder="例: ランク5人パーティー募集",
            max_length=100,
            required=True,
        )
        self.add_item(self.title_input)

        # Description input
        self.description_input = TextInput(
            label="説明",
            placeholder="イベントの詳細を入力してください",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=False,
        )
        self.add_item(self.description_input)

        # Start time input
        self.start_time_input = TextInput(
            label="開始日時",
            placeholder="例: 2026-01-15 20:00",
            max_length=50,
            required=True,
        )
        self.add_item(self.start_time_input)

        # Max participants input
        self.max_participants_input = TextInput(
            label="定員",
            placeholder="例: 5",
            max_length=3,
            required=True,
        )
        self.add_item(self.max_participants_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission.

        This method should be overridden or handled by the command.
        """
        # Store the interaction for later use
        self.interaction = interaction
        # Defer the response - actual handling will be done by the command
        await interaction.response.defer(ephemeral=True)


class EventEditModal(Modal):
    """Modal for editing an existing event."""

    def __init__(
        self,
        current_title: str,
        current_description: str,
        current_start_time: str,
        current_max_participants: int,
    ):
        """Initialize event edit modal.

        Args:
            current_title: Current event title
            current_description: Current description
            current_start_time: Current start time
            current_max_participants: Current max participants
        """
        super().__init__(title="イベント編集")

        # Title input with current value
        self.title_input = TextInput(
            label="イベントタイトル",
            default=current_title,
            max_length=100,
            required=True,
        )
        self.add_item(self.title_input)

        # Description input with current value
        self.description_input = TextInput(
            label="説明",
            default=current_description,
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=False,
        )
        self.add_item(self.description_input)

        # Start time input with current value
        self.start_time_input = TextInput(
            label="開始日時",
            default=current_start_time,
            max_length=50,
            required=True,
        )
        self.add_item(self.start_time_input)

        # Max participants input with current value
        self.max_participants_input = TextInput(
            label="定員",
            default=str(current_max_participants),
            max_length=3,
            required=True,
        )
        self.add_item(self.max_participants_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        self.interaction = interaction
        await interaction.response.defer(ephemeral=True)


class CustomGameModal(Modal):
    """Modal for entering custom game name."""

    def __init__(self):
        """Initialize custom game modal."""
        super().__init__(title="カスタムゲーム入力")

        self.game_name_input = TextInput(
            label="ゲーム名",
            placeholder="プレイするゲームの名前を入力してください",
            max_length=50,
            required=True,
        )
        self.add_item(self.game_name_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        self.interaction = interaction
        await interaction.response.defer(ephemeral=True)
