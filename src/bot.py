"""
Discord Bot initialization and setup for WithGames.
"""
import logging
import discord
from discord.ext import commands
from src.config import config
from src.services.firestore_service import firestore_service

logger = logging.getLogger(__name__)


class WithGamesBot(commands.Bot):
    """Custom Discord Bot class for WithGames."""

    def __init__(self):
        """Initialize the bot with required intents and configuration."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",  # Fallback prefix, mainly using slash commands
            intents=intents,
            help_command=None,
        )

        self.config = config
        self.firestore = firestore_service

    async def setup_hook(self):
        """Setup hook called when bot is ready."""
        logger.info("Running setup hook...")

        # Test Firestore connection (warning only, don't block startup)
        try:
            if self.firestore.test_connection():
                logger.info("✓ Firestore connection established")
            else:
                logger.warning("⚠ Firestore connection test failed - bot will continue but database operations may fail")
        except Exception as e:
            logger.warning(f"⚠ Firestore connection error: {e} - bot will continue but database operations may fail")

        # Load cogs
        await self.load_cogs()

        # Sync slash commands
        try:
            logger.info("Syncing slash commands...")
            
            # Check if GUILD_ID is set for guild-specific sync (faster)
            guild_id = self.config.guild_id
            if guild_id:
                guild = discord.Object(id=int(guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Slash commands synced to guild {guild_id}")
            else:
                # Global sync (slower, up to 1 hour to propagate)
                await self.tree.sync()
                logger.info("Slash commands synced globally")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def load_cogs(self):
        """Load all cogs."""
        cogs = [
            "src.cogs.event_manager",
            "src.cogs.participant_manager",
            "src.cogs.notification_manager",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

    async def on_ready(self):
        """Event handler for when the bot is ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /create_event"
            )
        )

        logger.info("Bot is ready!")

    async def on_error(self, event_method: str, *args, **kwargs):
        """Global error handler."""
        logger.exception(f"Error in {event_method}")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """Command error handler."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors

        logger.error(f"Command error in {ctx.command}: {error}")

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")
        else:
            await ctx.send("An error occurred while executing the command.")


def create_bot() -> WithGamesBot:
    """Create and return a configured bot instance.

    Returns:
        Configured WithGamesBot instance
    """
    logger.info("Creating bot instance...")
    bot = WithGamesBot()
    logger.info("Bot instance created")
    return bot
