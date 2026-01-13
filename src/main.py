"""
Main entry point for WithGames Discord Bot.
"""
import asyncio
import logging
import os
import signal
import sys
from src.config import config
from src.bot import create_bot

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot."""
    # Setup logging
    config.setup_logging()

    logger.info("=" * 50)
    logger.info("WithGames Discord Bot Starting...")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"GCP Project: {config.gcp_project_id}")
    logger.info("=" * 50)

    # Cloud Run環境の場合、ヘルスチェックサーバーを起動
    healthcheck_task = None
    if os.environ.get("PORT"):
        from src.healthcheck import run_healthcheck_server
        logger.info("Starting health check server...")
        healthcheck_task = asyncio.create_task(run_healthcheck_server())
        # サーバーが起動するまで少し待つ
        await asyncio.sleep(1)

    # Create bot instance
    bot = create_bot()

    # Setup graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(bot.close())
        if healthcheck_task:
            healthcheck_task.cancel()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the bot
    try:
        logger.info("Starting bot...")
        async with bot:
            await bot.start(config.discord_token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if healthcheck_task:
            healthcheck_task.cancel()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown complete")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)
