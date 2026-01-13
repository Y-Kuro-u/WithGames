"""
Configuration management for WithGames Discord Bot.
Handles environment variables, GCP authentication, and application settings.
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration class."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self._validate_required_variables()

    @property
    def discord_token(self) -> str:
        """Discord bot token."""
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        return token

    @property
    def discord_application_id(self) -> Optional[str]:
        """Discord application ID."""
        return os.getenv("DISCORD_APPLICATION_ID")

    @property
    def gcp_project_id(self) -> str:
        """Google Cloud Platform project ID."""
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        return project_id

    @property
    def google_application_credentials(self) -> Optional[str]:
        """Path to Google Application Credentials JSON file."""
        return os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    @property
    def environment(self) -> str:
        """Application environment (dev, staging, production)."""
        return os.getenv("ENVIRONMENT", "dev")

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "dev"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def reminder_minutes(self) -> int:
        """Minutes before event start to send reminder."""
        return int(os.getenv("REMINDER_MINUTES", "30"))

    @property
    def firestore_emulator_host(self) -> Optional[str]:
        """Firestore Emulator host (for local development)."""
        return os.getenv("FIRESTORE_EMULATOR_HOST")

    @property
    def use_firestore_emulator(self) -> bool:
        """Check if using Firestore Emulator."""
        return self.firestore_emulator_host is not None

    @property
    def guild_id(self) -> Optional[str]:
        """Discord Guild ID for guild-specific command sync (optional)."""
        return os.getenv("GUILD_ID")

    def _validate_required_variables(self):
        """Validate that all required environment variables are set."""
        required_vars = ["DISCORD_TOKEN", "GCP_PROJECT_ID"]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        logger.info(f"Configuration loaded for environment: {self.environment}")

        if self.use_firestore_emulator:
            logger.info(
                f"Using Firestore Emulator at {self.firestore_emulator_host}"
            )

    def setup_logging(self, level: int = logging.INFO):
        """Setup application logging.

        Args:
            level: Logging level (default: INFO)
        """
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if self.is_development:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled for development environment")


# Global configuration instance
config = Config()
