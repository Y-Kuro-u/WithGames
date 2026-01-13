"""
Notification Manager Cog for WithGames Discord Bot.
Handles automatic reminders and notifications for events.
"""
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
from typing import List

from src.services.event_service import event_service
from src.services.participant_service import participant_service
from src.ui.embeds import EventEmbeds
from src.models.event import EventStatus
from src.utils.datetime_utils import DateTimeUtils
from src.config import config

logger = logging.getLogger(__name__)


class NotificationManager(commands.Cog):
    """Cog for managing notifications and reminders."""

    def __init__(self, bot: commands.Bot):
        """Initialize notification manager cog.

        Args:
            bot: Bot instance
        """
        self.bot = bot
        self.event_service = event_service
        self.participant_service = participant_service
        self.reminder_minutes = config.reminder_minutes

        # Start background tasks
        self.check_reminders.start()
        self.check_completed_events.start()

        logger.info("Notification manager initialized")

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.check_reminders.cancel()
        self.check_completed_events.cancel()
        logger.info("Notification manager unloaded")

    @tasks.loop(minutes=5)
    async def check_reminders(self):
        """Check for events that need reminders sent.

        Runs every 5 minutes to check for upcoming events.
        """
        try:
            logger.debug("Checking for events needing reminders...")

            # Get all guilds the bot is in
            for guild in self.bot.guilds:
                # Get all active/full/closed events for this guild
                events = await self.event_service.get_all_events(str(guild.id))

                for event in events:
                    # Skip if reminder already sent
                    if event.reminder_sent:
                        continue

                    # Skip if event is not active, full, or closed
                    if event.status not in [EventStatus.ACTIVE, EventStatus.FULL, EventStatus.CLOSED]:
                        continue

                    # Check if reminder should be sent
                    if DateTimeUtils.should_send_reminder(
                        event.start_time,
                        event.reminder_sent,
                        self.reminder_minutes
                    ):
                        await self._send_reminder(event)

            logger.debug("Reminder check completed")

        except Exception as e:
            logger.error(f"Error checking reminders: {e}", exc_info=True)

    @tasks.loop(minutes=10)
    async def check_completed_events(self):
        """Check for events that should be marked as completed.

        Runs every 10 minutes to mark past events as completed.
        """
        try:
            logger.debug("Checking for completed events...")

            # Get all guilds the bot is in
            for guild in self.bot.guilds:
                # Get all events for this guild
                events = await self.event_service.get_all_events(str(guild.id))

                for event in events:
                    # Skip if already completed or cancelled
                    if event.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
                        continue

                    # Check if event has passed
                    if event.start_time < datetime.utcnow():
                        event.status = EventStatus.COMPLETED
                        await self.event_service.update_event(event)
                        logger.info(f"Marked event {event.id} as completed")

            logger.debug("Completed events check finished")

        except Exception as e:
            logger.error(f"Error checking completed events: {e}", exc_info=True)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        """Wait until bot is ready before starting reminder checks."""
        await self.bot.wait_until_ready()
        logger.info("Reminder check task started")

    @check_completed_events.before_loop
    async def before_check_completed_events(self):
        """Wait until bot is ready before starting completed event checks."""
        await self.bot.wait_until_ready()
        logger.info("Completed events check task started")

    async def _send_reminder(self, event):
        """Send reminder notification to all participants.

        Args:
            event: Event to send reminder for
        """
        try:
            logger.info(f"Sending reminder for event {event.id} - {event.title}")

            # Get all participants (not waitlist)
            participants = await self.participant_service.get_participants(event.id)

            if not participants:
                logger.warning(f"No participants found for event {event.id}")
                # Mark as sent anyway to avoid repeated checks
                event.reminder_sent = True
                await self.event_service.update_event(event)
                return

            # Create reminder embed
            reminder_embed = EventEmbeds.create_reminder_embed(event)

            # Send DM to each participant
            sent_count = 0
            failed_count = 0

            for participant in participants:
                try:
                    user = await self.bot.fetch_user(int(participant.user_id))
                    if user:
                        await user.send(embed=reminder_embed)
                        sent_count += 1
                        logger.debug(f"Sent reminder to user {participant.user_id}")
                except discord.Forbidden:
                    logger.warning(f"Cannot send DM to user {participant.user_id} (DMs disabled)")
                    failed_count += 1
                except discord.HTTPException as e:
                    logger.error(f"Failed to send DM to user {participant.user_id}: {e}")
                    failed_count += 1
                except Exception as e:
                    logger.error(f"Unexpected error sending DM to {participant.user_id}: {e}")
                    failed_count += 1

            # Also send reminder in the channel
            try:
                channel = self.bot.get_channel(int(event.channel_id))
                if channel:
                    # Mention all participants
                    mentions = " ".join([f"<@{p.user_id}>" for p in participants[:20]])
                    if len(participants) > 20:
                        mentions += f" (+{len(participants) - 20}名)"

                    channel_reminder = discord.Embed(
                        title="⏰ イベント開始のお知らせ",
                        description=f"イベント「**{event.title}**」が{self.reminder_minutes}分後に開始します！",
                        color=0x3498db,
                    )
                    channel_reminder.add_field(
                        name="📅 開始日時",
                        value=DateTimeUtils.format_full_datetime(event.start_time),
                        inline=False,
                    )
                    channel_reminder.add_field(
                        name="👥 参加者",
                        value=f"{event.current_participants}/{event.max_participants}名",
                        inline=True,
                    )

                    await channel.send(content=mentions, embed=channel_reminder)
                    logger.info(f"Sent channel reminder for event {event.id}")
            except Exception as e:
                logger.error(f"Failed to send channel reminder: {e}")

            # Mark reminder as sent
            event.reminder_sent = True
            await self.event_service.update_event(event)

            logger.info(
                f"Reminder sent for event {event.id}: {sent_count} successful, {failed_count} failed"
            )

        except Exception as e:
            logger.error(f"Error sending reminder for event {event.id}: {e}", exc_info=True)


async def setup(bot: commands.Bot):
    """Setup function to add cog to bot.

    Args:
        bot: Bot instance
    """
    await bot.add_cog(NotificationManager(bot))
    logger.info("NotificationManager cog loaded")
