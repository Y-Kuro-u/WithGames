"""
Participant Manager Cog for WithGames Discord Bot.
Handles participant management, button interactions, and user events listing.
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from src.services.participant_service import participant_service
from src.services.event_service import event_service
from src.ui.embeds import EventEmbeds
from src.ui.buttons import EventParticipationView

logger = logging.getLogger(__name__)


class ParticipantManager(commands.Cog):
    """Cog for managing event participants."""

    def __init__(self, bot: commands.Bot):
        """Initialize participant manager cog.

        Args:
            bot: Bot instance
        """
        self.bot = bot
        self.participant_service = participant_service
        self.event_service = event_service

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions for persistent views.

        Args:
            interaction: Discord interaction
        """
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        logger.info(f"Button interaction received: custom_id={custom_id}, user={interaction.user.id}")

        # Join button
        if custom_id.startswith("event_join_"):
            await self.handle_join_button(interaction)

        # Cancel button
        elif custom_id.startswith("event_cancel_"):
            await self.handle_cancel_button(interaction)

        # Details button
        elif custom_id.startswith("event_details_"):
            await self.handle_details_button(interaction)

        # Share button
        elif custom_id.startswith("event_share_"):
            await self.handle_share_button(interaction)
        else:
            logger.warning(f"Unknown button interaction: {custom_id}")

    async def handle_join_button(self, interaction: discord.Interaction):
        """Handle event join button click.

        Args:
            interaction: Discord interaction
        """
        try:
            # Defer the interaction immediately to avoid timeout
            await interaction.response.defer(ephemeral=True)
            
            # Extract event ID from custom_id
            custom_id = interaction.data.get("custom_id", "")
            event_id = custom_id.replace("event_join_", "")

            # Join event
            success, message, participant = await self.participant_service.join_event(
                event_id=event_id,
                user_id=str(interaction.user.id),
                user_name=interaction.user.display_name,
            )

            # Send response to user (ephemeral)
            if success:
                embed = EventEmbeds.create_success_embed("参加登録完了", message)
            else:
                embed = EventEmbeds.create_error_embed("参加エラー", message, [])

            await interaction.followup.send(embed=embed, ephemeral=True)

            # Update event embed if successful
            if success:
                await self._update_event_message(event_id, interaction.message)

                # Notify creator (if not the creator themselves)
                event = await self.event_service.get_event(event_id)
                if event and str(interaction.user.id) != event.creator_id:
                    await self._notify_creator_join(event, interaction.user)

        except Exception as e:
            logger.exception(f"Error handling join button: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー", "参加処理中にエラーが発生しました。", [str(e)]
            )
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except discord.HTTPException:
                logger.error("Failed to send error message to user")

    async def handle_cancel_button(self, interaction: discord.Interaction):
        """Handle event cancel button click.

        Args:
            interaction: Discord interaction
        """
        try:
            # Defer the interaction immediately to avoid timeout
            await interaction.response.defer(ephemeral=True)
            
            # Extract event ID from custom_id
            custom_id = interaction.data.get("custom_id", "")
            event_id = custom_id.replace("event_cancel_", "")

            # Leave event
            (
                success,
                message,
                promoted_user_id,
            ) = await self.participant_service.leave_event(
                event_id=event_id, user_id=str(interaction.user.id)
            )

            # Send response to user (ephemeral)
            if success:
                embed = EventEmbeds.create_info_embed("キャンセル完了", message)
            else:
                embed = EventEmbeds.create_error_embed("キャンセルエラー", message, [])

            await interaction.followup.send(embed=embed, ephemeral=True)

            # Update event embed if successful
            if success:
                await self._update_event_message(event_id, interaction.message)

                # Notify promoted user if any
                if promoted_user_id:
                    await self._notify_promotion(event_id, promoted_user_id)

                # Notify creator
                event = await self.event_service.get_event(event_id)
                if event and str(interaction.user.id) != event.creator_id:
                    await self._notify_creator_cancel(event, interaction.user)

        except Exception as e:
            logger.exception(f"Error handling cancel button: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー", "キャンセル処理中にエラーが発生しました。", [str(e)]
            )
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except discord.HTTPException:
                logger.error("Failed to send error message to user")

    async def handle_details_button(self, interaction: discord.Interaction):
        """Handle event details button click.

        Args:
            interaction: Discord interaction
        """
        try:
            # Defer the interaction immediately to avoid timeout
            await interaction.response.defer(ephemeral=True)
            
            # Extract event ID from custom_id
            custom_id = interaction.data.get("custom_id", "")
            event_id = custom_id.replace("event_details_", "")

            # Get event and participants
            event = await self.event_service.get_event(event_id)
            if not event:
                embed = EventEmbeds.create_error_embed(
                    "エラー", "イベントが見つかりません", []
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            participants = await self.participant_service.get_participants(event_id)
            waitlist = await self.participant_service.get_waitlist(event_id)

            # Create detailed embed
            embed = EventEmbeds.create_participant_details_embed(
                event, participants, waitlist
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception(f"Error handling details button: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー", "詳細取得中にエラーが発生しました。", [str(e)]
            )
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except discord.HTTPException:
                logger.error("Failed to send error message to user")

    async def handle_share_button(self, interaction: discord.Interaction):
        """Handle event share button click.

        Args:
            interaction: Discord interaction
        """
        try:
            # Get message URL
            message_url = interaction.message.jump_url

            # Create shareable message
            embed = discord.Embed(
                title="🔗 イベントを共有",
                description=f"以下のリンクを共有してください:\n{message_url}",
                color=0x3498db,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception(f"Error handling share button: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー", "共有リンク生成中にエラーが発生しました。", [str(e)]
            )
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except discord.HTTPException:
                logger.error("Failed to send error message to user")

    async def _update_event_message(
        self, event_id: str, message: Optional[discord.Message] = None
    ):
        """Update the event message embed with current participant data.

        Args:
            event_id: Event ID
            message: Discord message to update (if None, will fetch from event)
        """
        try:
            # Get event
            event = await self.event_service.get_event(event_id)
            if not event:
                return

            # Get participants and waitlist
            participants = await self.participant_service.get_participants(event_id)
            waitlist = await self.participant_service.get_waitlist(event_id)

            # Create updated embed
            embed = EventEmbeds.create_event_embed(event, participants, waitlist)
            view = EventParticipationView(event_id)

            # Update message
            if message:
                await message.edit(embed=embed, view=view)
            elif event.message_id and event.channel_id:
                # Fetch message from channel
                channel = self.bot.get_channel(int(event.channel_id))
                if channel:
                    try:
                        message = await channel.fetch_message(int(event.message_id))
                        await message.edit(embed=embed, view=view)
                    except discord.NotFound:
                        logger.warning(
                            f"Message {event.message_id} not found for event {event_id}"
                        )

        except Exception as e:
            logger.error(f"Failed to update event message for {event_id}: {e}")

    async def _notify_creator_join(self, event, user: discord.User):
        """Notify event creator when someone joins.

        Args:
            event: Event object
            user: User who joined
        """
        try:
            creator = await self.bot.fetch_user(int(event.creator_id))
            if creator:
                embed = discord.Embed(
                    title="✅ 新しい参加者",
                    description=f"{user.mention} があなたのイベントに参加しました！",
                    color=0x2ecc71,
                )
                embed.add_field(name="イベント", value=event.title, inline=False)
                embed.add_field(
                    name="現在の参加者",
                    value=f"{event.current_participants}/{event.max_participants}名",
                    inline=False,
                )

                await creator.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to notify creator of join: {e}")

    async def _notify_creator_cancel(self, event, user: discord.User):
        """Notify event creator when someone cancels.

        Args:
            event: Event object
            user: User who canceled
        """
        try:
            creator = await self.bot.fetch_user(int(event.creator_id))
            if creator:
                embed = discord.Embed(
                    title="❌ 参加キャンセル",
                    description=f"{user.mention} がイベントへの参加をキャンセルしました",
                    color=0xe67e22,
                )
                embed.add_field(name="イベント", value=event.title, inline=False)
                embed.add_field(
                    name="現在の参加者",
                    value=f"{event.current_participants}/{event.max_participants}名",
                    inline=False,
                )

                await creator.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to notify creator of cancel: {e}")

    async def _notify_promotion(self, event_id: str, user_id: str):
        """Notify user when promoted from waitlist.

        Args:
            event_id: Event ID
            user_id: User ID who was promoted
        """
        try:
            event = await self.event_service.get_event(event_id)
            if not event:
                return

            user = await self.bot.fetch_user(int(user_id))
            if user:
                # Create message URL
                message_url = f"https://discord.com/channels/{event.guild_id}/{event.channel_id}/{event.message_id}"

                embed = discord.Embed(
                    title="🎉 キャンセル待ちから昇格しました！",
                    description=f"イベント「{event.title}」に参加できるようになりました！",
                    color=0x2ecc71,
                )
                embed.add_field(
                    name="📅 開始日時",
                    value=f"<t:{int(event.start_time.timestamp())}:F>",
                    inline=False,
                )
                embed.add_field(
                    name="📍 チャンネル", value=f"<#{event.channel_id}>", inline=False
                )
                embed.add_field(name="🔗 リンク", value=message_url, inline=False)

                await user.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to notify promotion: {e}")

    @app_commands.command(
        name="my_events", description="自分が参加しているイベント一覧を表示します"
    )
    async def my_events(self, interaction: discord.Interaction):
        """List events the user is participating in.

        Args:
            interaction: Discord interaction
        """
        try:
            await interaction.response.defer(ephemeral=True)

            # Get user's participant records
            participants = await self.participant_service.get_user_events(
                str(interaction.user.id), limit=25
            )

            if not participants:
                embed = EventEmbeds.create_info_embed(
                    "マイイベント",
                    "現在参加しているイベントはありません。\n\n`/create_event` でイベントを作成するか、\n募集中のイベントに参加してください。",
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Get events for each participant
            event_list = []
            for participant in participants:
                event = await self.event_service.get_event(participant.event_id)
                if event:
                    event_list.append(
                        {
                            "event": event,
                            "participant": participant,
                        }
                    )

            # Create embed
            embed = EventEmbeds.create_my_events_embed(event_list)

            await interaction.followup.send(embed=embed, ephemeral=True)

            logger.info(
                f"User {interaction.user.id} listed {len(event_list)} personal events"
            )

        except Exception as e:
            logger.exception(f"Error listing user events: {e}")
            error_embed = EventEmbeds.create_error_embed(
                "エラー", "イベント一覧の取得中にエラーが発生しました。", [str(e)]
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function to add cog to bot.

    Args:
        bot: Bot instance
    """
    await bot.add_cog(ParticipantManager(bot))
    logger.info("ParticipantManager cog loaded")
