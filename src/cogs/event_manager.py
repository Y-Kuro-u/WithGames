"""
Event Manager Cog for WithGames Discord Bot.
Handles event creation, listing, editing, and deletion commands.
"""
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View
import logging
from datetime import datetime
from typing import Optional

from src.services.event_service import event_service
from src.services.participant_service import participant_service
from src.ui.embeds import EventEmbeds
from src.ui.selects import GameSelectView
from src.ui.modals import EventCreationModal, CustomGameModal, EventEditModal
from src.ui.buttons import EventParticipationView
from src.utils.validators import Validators
from src.utils.game_data import GameData
from src.utils.permissions import PermissionChecker
from src.utils.datetime_utils import DateTimeUtils
from src.models.event import Event, EventStatus

logger = logging.getLogger(__name__)


class EventManager(commands.Cog):
    """Cog for managing events."""

    def __init__(self, bot: commands.Bot):
        """Initialize event manager cog.

        Args:
            bot: Bot instance
        """
        self.bot = bot
        self.event_service = event_service

    @app_commands.command(name="create_event", description="新しいゲームイベントを作成します")
    async def create_event(self, interaction: discord.Interaction):
        """Create a new event.

        Args:
            interaction: Discord interaction
        """
        try:
            # Step 1: Show game selection menu
            game_view = GameSelectView(popular_count=10)
            await interaction.response.send_message(
                "ゲームを選択してください:",
                view=game_view,
                ephemeral=True,
            )

            # Wait for game selection
            await game_view.wait()

            if not game_view.selected_game:
                await interaction.followup.send(
                    "タイムアウトしました。もう一度お試しください。",
                    ephemeral=True,
                )
                return

            game_type = game_view.selected_game
            game_emoji = game_view.selected_emoji

            # Step 2: Handle custom game or show event creation button
            from src.ui.buttons import EventCreationButton, CustomGameButton

            if game_type == "custom":
                # For custom games, first ask for the game name
                button_view = View(timeout=300)
                custom_button = CustomGameButton(self.event_service, self.bot)
                button_view.add_item(custom_button)

                await interaction.followup.send(
                    f"{game_emoji} カスタムゲームを選択しました。\n下のボタンをクリックしてゲーム名を入力してください:",
                    view=button_view,
                    ephemeral=True,
                )
            else:
                # For pre-defined games, show event creation button directly
                button_view = View(timeout=300)
                create_button = EventCreationButton(game_type, game_emoji, self.event_service, self.bot)
                button_view.add_item(create_button)

                await interaction.followup.send(
                    f"ゲーム: {game_emoji} **{game_type}**\n下のボタンをクリックしてイベントの詳細を入力してください:",
                    view=button_view,
                    ephemeral=True,
                )

        except Exception as e:
            logger.exception(f"Error creating event: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー",
                "イベントの作成中にエラーが発生しました。",
                [str(e)],
            )
            # Check if interaction has been responded to
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except discord.HTTPException:
                # If sending the error message fails, just log it
                logger.error("Failed to send error message to user")

    @app_commands.command(name="list_events", description="募集中のイベント一覧を表示します")
    async def list_events(self, interaction: discord.Interaction):
        """List all active events.

        Args:
            interaction: Discord interaction
        """
        try:
            await interaction.response.defer(ephemeral=True)

            # Get active events for this guild
            events = await self.event_service.get_active_events(
                str(interaction.guild_id), limit=25
            )

            if not events:
                embed = EventEmbeds.create_info_embed(
                    "イベント一覧",
                    "現在募集中のイベントはありません。\n\n`/create_event` コマンドで新しいイベントを作成できます。",
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Create event list embed
            event_list_embed = EventEmbeds.create_event_list_embed(events, page=1, total_pages=1)

            await interaction.followup.send(embed=event_list_embed, ephemeral=True)

            logger.info(
                f"User {interaction.user.id} listed {len(events)} events in guild {interaction.guild_id}"
            )

        except Exception as e:
            logger.exception(f"Error listing events: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー",
                "イベント一覧の取得中にエラーが発生しました。",
                [str(e)],
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="edit_event", description="イベントを編集します（作成者・管理者のみ）")
    @app_commands.describe(event_id="編集するイベントのID")
    async def edit_event(self, interaction: discord.Interaction, event_id: str):
        """Edit an existing event.

        Args:
            interaction: Discord interaction
            event_id: Event ID to edit
        """
        try:
            # Get the event
            event = await self.event_service.get_event(event_id)
            
            if not event:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "指定されたイベントが見つかりません。",
                    []
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Check permissions
            can_manage, reason = PermissionChecker.can_manage_event(
                interaction.user, event, interaction.guild
            )
            
            if not can_manage:
                error_embed = EventEmbeds.create_error_embed(
                    "権限エラー",
                    reason,
                    []
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Format current start time for display
            current_start_time_str = DateTimeUtils.format_edit_datetime(event.start_time)

            # Show edit modal with current values
            edit_modal = EventEditModal(
                current_title=event.title,
                current_description=event.description or "",
                current_start_time=current_start_time_str,
                current_max_participants=event.max_participants,
            )

            # Check if interaction has already been responded to
            if interaction.response.is_done():
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "インタラクションが既に処理されています。もう一度お試しください。",
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            await interaction.response.send_modal(edit_modal)
            await edit_modal.wait()

            # Validate the new input
            is_valid, validated_data, errors = Validators.validate_event_data(
                title=edit_modal.title_input.value,
                description=edit_modal.description_input.value,
                datetime_str=edit_modal.start_time_input.value,
                max_participants_str=edit_modal.max_participants_input.value,
                game_type=event.game_type,
            )

            if not is_valid:
                error_embed = EventEmbeds.create_error_embed(
                    "入力エラー",
                    "入力内容にエラーがあります。",
                    errors,
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Store old max_participants for comparison
            old_max_participants = event.max_participants

            # Update event fields
            event.title = validated_data["title"]
            event.description = validated_data["description"]
            event.start_time = validated_data["start_time"]
            event.max_participants = validated_data["max_participants"]
            event.updated_at = datetime.utcnow()

            # Handle capacity changes
            if old_max_participants != event.max_participants:
                await self._handle_capacity_change(event, old_max_participants)

            # Update event status based on new values
            event.update_status()

            # Save to Firestore
            success = await self.event_service.update_event(event)
            
            if not success:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "イベントの更新に失敗しました。",
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Update the event message if it exists
            if event.message_id:
                try:
                    channel = interaction.channel
                    message = await channel.fetch_message(int(event.message_id))
                    
                    # Get updated participant lists
                    participants = await participant_service.get_participants(event.id)
                    waitlist = await participant_service.get_waitlist(event.id)
                    
                    participant_names = [p.user_name for p in participants]
                    waitlist_names = [p.user_name for p in waitlist]
                    
                    # Update embed
                    updated_embed = EventEmbeds.create_event_embed(
                        event, participants=participant_names, waitlist=waitlist_names
                    )
                    participation_view = EventParticipationView(event.id)
                    
                    await message.edit(embed=updated_embed, view=participation_view)
                except Exception as e:
                    logger.warning(f"Failed to update event message: {e}")

            # Send confirmation
            success_embed = EventEmbeds.create_success_embed(
                "イベント編集完了",
                f"イベント「{event.title}」を更新しました。",
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)

            logger.info(
                f"User {interaction.user.id} edited event {event_id} in guild {interaction.guild_id}"
            )

        except Exception as e:
            logger.exception(f"Error editing event: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー",
                "イベントの編集中にエラーが発生しました。",
                [str(e)],
            )
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except discord.HTTPException:
                logger.error("Failed to send error message to user")

    @app_commands.command(name="delete_event", description="イベントを削除します（作成者・管理者のみ）")
    @app_commands.describe(event_id="削除するイベントのID")
    async def delete_event(self, interaction: discord.Interaction, event_id: str):
        """Delete an existing event.

        Args:
            interaction: Discord interaction
            event_id: Event ID to delete
        """
        try:
            await interaction.response.defer(ephemeral=True)

            # Get the event
            event = await self.event_service.get_event(event_id)
            
            if not event:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "指定されたイベントが見つかりません。",
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Check permissions
            can_delete, reason = PermissionChecker.can_delete_event(
                interaction.user, event, interaction.guild
            )
            
            if not can_delete:
                error_embed = EventEmbeds.create_error_embed(
                    "権限エラー",
                    reason,
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Delete all participants
            await participant_service.delete_all_participants(event_id)

            # Delete the event message if it exists
            if event.message_id:
                try:
                    channel = interaction.channel
                    message = await channel.fetch_message(int(event.message_id))
                    await message.delete()
                except Exception as e:
                    logger.warning(f"Failed to delete event message: {e}")

            # Delete the event from Firestore
            success = await self.event_service.delete_event(event_id)
            
            if not success:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "イベントの削除に失敗しました。",
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Send confirmation
            success_embed = EventEmbeds.create_success_embed(
                "イベント削除完了",
                f"イベント「{event.title}」を削除しました。",
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)

            logger.info(
                f"User {interaction.user.id} deleted event {event_id} in guild {interaction.guild_id}"
            )

        except Exception as e:
            logger.exception(f"Error deleting event: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー",
                "イベントの削除中にエラーが発生しました。",
                [str(e)],
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    async def _handle_capacity_change(self, event: Event, old_max_participants: int):
        """Handle capacity changes for an event.

        Args:
            event: Event with new capacity
            old_max_participants: Previous max participants value
        """
        try:
            new_max = event.max_participants
            
            # Get current participants and waitlist
            participants = await participant_service.get_participants(event.id)
            waitlist = await participant_service.get_waitlist(event.id)
            
            current_count = len(participants)

            # Case 1: Capacity increased
            if new_max > old_max_participants:
                # Move people from waitlist to participants if there's room
                available_spots = new_max - current_count
                
                if available_spots > 0 and waitlist:
                    # Promote waitlist members to participants
                    to_promote = min(available_spots, len(waitlist))
                    for i in range(to_promote):
                        await participant_service.promote_from_waitlist(
                            event.id, waitlist[i].user_id
                        )
                    
                    logger.info(
                        f"Promoted {to_promote} users from waitlist for event {event.id}"
                    )

            # Case 2: Capacity decreased
            elif new_max < old_max_participants:
                # Check if we need to move participants to waitlist
                if current_count > new_max:
                    # Move excess participants to waitlist
                    excess_count = current_count - new_max
                    # Get the last joined participants
                    participants_sorted = sorted(
                        participants, key=lambda p: p.joined_at, reverse=True
                    )
                    
                    for i in range(excess_count):
                        if i < len(participants_sorted):
                            await participant_service.demote_to_waitlist(
                                event.id, participants_sorted[i].user_id
                            )
                    
                    logger.info(
                        f"Moved {excess_count} users to waitlist for event {event.id}"
                    )

            # Update event participant count
            updated_participants = await participant_service.get_participants(event.id)
            event.current_participants = len(updated_participants)

        except Exception as e:
            logger.error(f"Error handling capacity change for event {event.id}: {e}")
            raise

    @app_commands.command(name="close_event", description="イベントの募集を終了します（作成者・管理者のみ）")
    @app_commands.describe(event_id="募集を終了するイベントのID")
    async def close_event(self, interaction: discord.Interaction, event_id: str):
        """Close recruitment for an event.

        Args:
            interaction: Discord interaction
            event_id: Event ID to close
        """
        try:
            await interaction.response.defer(ephemeral=True)

            # Get the event
            event = await self.event_service.get_event(event_id)
            
            if not event:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "指定されたイベントが見つかりません。",
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Check permissions
            can_manage, reason = PermissionChecker.can_manage_event(
                interaction.user, event, interaction.guild
            )
            
            if not can_manage:
                error_embed = EventEmbeds.create_error_embed(
                    "権限エラー",
                    reason,
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Check if already closed or completed
            if event.status == EventStatus.CLOSED:
                error_embed = EventEmbeds.create_info_embed(
                    "募集終了済み",
                    "このイベントは既に募集が終了しています。"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            if event.status in [EventStatus.CANCELLED, EventStatus.COMPLETED]:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    f"このイベントは既に{event.status.value}状態です。",
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Close the event
            event.status = EventStatus.CLOSED
            event.updated_at = datetime.utcnow()

            # Save to Firestore
            success = await self.event_service.update_event(event)
            
            if not success:
                error_embed = EventEmbeds.create_error_embed(
                    "エラー",
                    "募集終了処理に失敗しました。",
                    []
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Update the event message if it exists
            if event.message_id:
                try:
                    channel = interaction.channel
                    message = await channel.fetch_message(int(event.message_id))
                    
                    # Get participant lists
                    participants = await participant_service.get_participants(event.id)
                    waitlist = await participant_service.get_waitlist(event.id)
                    
                    participant_names = [p.user_name for p in participants]
                    waitlist_names = [p.user_name for p in waitlist]
                    
                    # Update embed
                    updated_embed = EventEmbeds.create_event_embed(
                        event, participants=participant_names, waitlist=waitlist_names
                    )
                    
                    # Remove buttons since recruitment is closed
                    await message.edit(embed=updated_embed, view=None)
                    
                    # Add a notice that recruitment is closed
                    notice_embed = discord.Embed(
                        title="🔒 募集終了",
                        description="このイベントの募集は終了しました。",
                        color=0x9B59B6,
                    )
                    await channel.send(embed=notice_embed, reference=message)
                    
                except Exception as e:
                    logger.warning(f"Failed to update event message: {e}")

            # Send confirmation
            success_embed = EventEmbeds.create_success_embed(
                "募集終了完了",
                f"イベント「{event.title}」の募集を終了しました。\n参加者は確定し、新規参加はできなくなります。",
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)

            logger.info(
                f"User {interaction.user.id} closed event {event_id} in guild {interaction.guild_id}"
            )

        except Exception as e:
            logger.exception(f"Error closing event: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー",
                "募集終了処理中にエラーが発生しました。",
                [str(e)],
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function to add cog to bot.

    Args:
        bot: Bot instance
    """
    await bot.add_cog(EventManager(bot))
    logger.info("EventManager cog loaded")
