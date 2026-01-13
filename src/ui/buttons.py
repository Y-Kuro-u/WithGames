"""
Button views and components for WithGames Discord Bot.
Handles interactive buttons for event participation and management.
"""
import discord
from discord.ui import View, Button
import logging
from typing import Optional

from src.ui.modals import EventCreationModal, CustomGameModal
from src.ui.embeds import EventEmbeds
from src.utils.validators import Validators
from src.utils.datetime_utils import DateTimeUtils
from src.utils.game_data import GameData
from src.models.event import Event, EventStatus
from datetime import datetime

logger = logging.getLogger(__name__)


class EventParticipationView(View):
    """Persistent view with buttons for event participation."""

    def __init__(self, event_id: str):
        """Initialize event participation view.

        Args:
            event_id: Event ID for button callbacks
        """
        # Persistent views should have timeout=None
        super().__init__(timeout=None)
        self.event_id = event_id

        # Join button (green)
        join_button = Button(
            label="参加する",
            style=discord.ButtonStyle.success,
            emoji="✅",
            custom_id=f"event_join_{event_id}",
        )
        self.add_item(join_button)

        # Cancel button (red) - renamed to be clearer
        cancel_button = Button(
            label="参加をやめる",
            style=discord.ButtonStyle.danger,
            emoji="❌",
            custom_id=f"event_cancel_{event_id}",
        )
        self.add_item(cancel_button)

        # Details button (gray)
        details_button = Button(
            label="詳細",
            style=discord.ButtonStyle.secondary,
            emoji="📋",
            custom_id=f"event_details_{event_id}",
        )
        self.add_item(details_button)

        # Share button (blurple)
        share_button = Button(
            label="共有",
            style=discord.ButtonStyle.primary,
            emoji="📤",
            custom_id=f"event_share_{event_id}",
        )
        self.add_item(share_button)


class EventCreationButton(Button):
    """Button to trigger event creation modal."""

    def __init__(self, game_type: str, game_emoji: str, event_service, bot):
        """Initialize event creation button.

        Args:
            game_type: Selected game type
            game_emoji: Emoji for the game
            event_service: Event service instance
            bot: Bot instance
        """
        super().__init__(
            label="イベント詳細を入力",
            style=discord.ButtonStyle.primary,
            emoji="📝",
        )
        self.game_type = game_type
        self.game_emoji = game_emoji
        self.event_service = event_service
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        """Handle button click.

        Args:
            interaction: Discord interaction
        """
        try:
            # Show modal for event details
            modal = EventCreationModal(self.game_type, self.game_emoji)
            await interaction.response.send_modal(modal)
            await modal.wait()

            if not hasattr(modal, "interaction"):
                return

            # Validate input
            is_valid, validated_data, errors = Validators.validate_event_data(
                title=modal.title_input.value,
                description=modal.description_input.value,
                datetime_str=modal.start_time_input.value,
                max_participants_str=modal.max_participants_input.value,
                game_type=self.game_type,
            )

            if not is_valid:
                error_embed = EventEmbeds.create_error_embed(
                    "入力エラー",
                    "入力内容にエラーがあります。",
                    errors,
                )
                await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Get game icon URL if available
            game_icon_url = GameData.get_game_icon_url(self.game_type)

            # Create event object
            # Save event to Firestore
            # Use modal.interaction instead of button interaction
            event = await self.event_service.create_event(
                title=validated_data["title"],
                description=validated_data["description"],
                game_type=self.game_type,
                start_time=validated_data["start_time"],
                max_participants=validated_data["max_participants"],
                creator_id=str(modal.interaction.user.id),
                creator_name=modal.interaction.user.display_name,
                guild_id=str(modal.interaction.guild_id),
                channel_id=str(modal.interaction.channel_id),
            )

            if not event:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "イベントの保存に失敗しました。",
                    []
                )
                await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Create event embed with participation buttons
            event_embed = EventEmbeds.create_event_embed(
                event, participants=[], waitlist=[]
            )
            participation_view = EventParticipationView(event.id)

            # Post event message to the channel
            # Get channel via bot to ensure proper context
            guild = self.bot.get_guild(int(event.guild_id))
            if not guild:
                logger.error(f"Guild {event.guild_id} not found")
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "サーバー情報の取得に失敗しました。",
                    []
                )
                await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            channel = guild.get_channel(int(event.channel_id))
            if not channel:
                logger.error(f"Channel {event.channel_id} not found in guild {event.guild_id}")
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "チャンネル情報の取得に失敗しました。",
                    []
                )
                await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            # Check bot permissions in this channel
            bot_member = guild.me
            if not bot_member:
                logger.error(f"Bot member not found in guild {event.guild_id}")
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "ボット情報の取得に失敗しました。",
                    []
                )
                await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            permissions = channel.permissions_for(bot_member)
            logger.info(f"Bot permissions in channel {channel.id}: send_messages={permissions.send_messages}, embed_links={permissions.embed_links}, view_channel={permissions.view_channel}")
            
            if not permissions.send_messages or not permissions.embed_links:
                logger.error(f"Bot lacks required permissions in channel {channel.id}")
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "このチャンネルにメッセージを送信する権限がありません。",
                    [
                        f"チャンネル: {channel.name}",
                        "必要な権限: メッセージを送信、埋め込みリンク",
                        "サーバー設定 → ロール → ボットのロールで権限を確認してください。",
                        "または、チャンネル設定 → 権限 でボットの権限を個別に設定してください。"
                    ]
                )
                await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                return
            
            logger.info(f"Sending event message to channel {channel.id} ({channel.name})")
            event_message = await channel.send(
                embed=event_embed,
                view=participation_view,
            )

            # Update event with message ID
            event.message_id = str(event_message.id)
            await self.event_service.update_event(event)

            # Send confirmation to user
            confirmation_embed = EventEmbeds.create_event_created_embed(
                event, str(channel.id)
            )
            await modal.interaction.followup.send(
                embed=confirmation_embed,
                ephemeral=True,
            )

            logger.info(
                f"User {interaction.user.id} created event {event.id} in guild {interaction.guild_id}"
            )

        except Exception as e:
            logger.exception(f"Error in event creation button callback: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー",
                "イベント作成中にエラーが発生しました。",
                [str(e)],
            )
            try:
                if hasattr(modal, "interaction"):
                    await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except Exception:
                logger.error("Failed to send error message")


class CustomGameButton(Button):
    """Button to trigger custom game name input."""

    def __init__(self, event_service, bot):
        """Initialize custom game button.

        Args:
            event_service: Event service instance
            bot: Bot instance
        """
        super().__init__(
            label="ゲーム名を入力",
            style=discord.ButtonStyle.primary,
            emoji="✏️",
        )
        self.event_service = event_service
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        """Handle button click.

        Args:
            interaction: Discord interaction
        """
        try:
            # Show modal for custom game name
            modal = CustomGameModal()
            await interaction.response.send_modal(modal)
            await modal.wait()

            if not hasattr(modal, "interaction"):
                return

            game_name = modal.game_name_input.value
            game_emoji = "🎮"  # Default emoji for custom games

            # Now show the event creation button with the custom game
            from discord.ui import View
            button_view = View(timeout=300)
            create_button = EventCreationButton(
                game_name, game_emoji, self.event_service, self.bot
            )
            button_view.add_item(create_button)

            await modal.interaction.followup.send(
                f"ゲーム: {game_emoji} **{game_name}**\n下のボタンをクリックしてイベントの詳細を入力してください:",
                view=button_view,
                ephemeral=True,
            )

        except Exception as e:
            logger.exception(f"Error in custom game button callback: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー",
                "カスタムゲーム入力中にエラーが発生しました。",
                [str(e)],
            )
            try:
                if hasattr(modal, "interaction"):
                    await modal.interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except Exception:
                logger.error("Failed to send error message")
