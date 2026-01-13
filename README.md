# WithGames Discord Bot

A feature-rich Discord bot for managing game event recruitment with rich UI components, participant management, and automated notifications.

## Features

- **Event Creation**: Create game recruitment events with title, description, date/time, and capacity
- **Participant Management**: Join/cancel with buttons, automatic waitlist management
- **Rich UI**: Beautiful embeds with progress bars, status colors, and game icons
- **Notifications**: Automatic reminders before events start
- **Multi-game Support**: Support for various game types with custom emojis and icons

## Tech Stack

- **Bot Framework**: discord.py 2.4+
- **Database**: Google Cloud Firestore
- **Deployment**: Google Cloud Run
- **Language**: Python 3.11+

## Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- Google Cloud Project with Firestore enabled (for production)
- Docker and Docker Compose (optional, for containerized development)

### Quick Start

For detailed setup instructions, see the documentation:

- **[📖 Local Development Setup](docs/SETUP.md)** - Discord bot configuration, Firestore emulator, command sync
- **[☁️ GCP Setup Guide](docs/GCP_SETUP.md)** - Google Cloud Platform environment setup
- **[🚀 Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to Cloud Run
- **[🔄 CI/CD Guide](docs/CICD.md)** - GitHub Actions automated deployment
- **[🔧 Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Basic Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd WithGames
   ```

2. **Install uv and dependencies**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your DISCORD_TOKEN
   ```

4. **Start the bot**
   ```bash
   # Using helper script (recommended)
   ./scripts/start_local.sh --emulator
   
   # Or manually with Docker
   docker-compose up
   ```

5. **Sync Discord commands**
   ```bash
   uv run python scripts/sync_commands.py --guild-id YOUR_GUILD_ID
   ```

For more details, see [docs/SETUP.md](docs/SETUP.md)

## Project Structure

```
WithGames/
├── src/
│   ├── main.py                 # Entry point
│   ├── bot.py                  # Bot initialization
│   ├── config.py               # Configuration management
│   ├── cogs/                   # Command modules (Phase 2+)
│   ├── services/               # Business logic services
│   ├── models/                 # Data models
│   ├── ui/                     # UI components
│   └── utils/                  # Utility functions
├── scripts/                    # Setup and deployment scripts
│   ├── sync_commands.py        # Discord command sync utility
│   ├── start_local.sh          # Local development startup
│   ├── setup_gcp.sh            # GCP initial setup automation
│   └── deploy.sh               # Cloud Run deployment
├── docs/                       # Documentation
│   ├── SETUP.md                # Local development guide
│   ├── GCP_SETUP.md            # GCP setup instructions
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── CICD.md                 # CI/CD configuration
├── .github/workflows/          # GitHub Actions workflows
│   ├── ci.yml                  # Test and lint
│   └── deploy.yml              # Automated deployment
├── tests/                      # Unit tests
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Local development setup
└── pyproject.toml              # Python project configuration (uv)
```

## Development Status

### ✅ Phase 1: Foundation (Completed)
- Bot initialization and Firestore connection
- Basic models and configuration
- Docker setup

### ✅ Phase 2: Event Creation (Completed)
- `/create_event` command
- Rich embed UI with game selection
- Event storage in Firestore

### ✅ Phase 3: Participant Management (Completed)
- `/join_event` and `/cancel_event` commands
- Automatic waitlist management
- Participant tracking

### ✅ Phase 4: Event Management (Completed)
- `/edit_event` command with capacity handling
- `/delete_event` command with cascade deletion
- `/close_event` for manual recruitment closure

### ✅ Phase 5: Notifications (Completed)
- Reminder system (configurable minutes before event)
- Automatic event completion detection
- DM and channel notifications

### ✅ Phase 6: Deployment & CI/CD (Completed)
- GCP Cloud Run deployment configuration
- GitHub Actions CI/CD pipelines
- Automated testing and deployment
- Setup scripts and comprehensive documentation

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DISCORD_TOKEN` | Discord bot token | Yes | - |
| `DISCORD_APPLICATION_ID` | Discord application ID | No | - |
| `GCP_PROJECT_ID` | Google Cloud project ID | Yes | - |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | No | - |
| `ENVIRONMENT` | Environment (dev/staging/production) | No | dev |
| `REMINDER_MINUTES` | Minutes before event to send reminder | No | 30 |
| `FIRESTORE_EMULATOR_HOST` | Firestore emulator host (for local dev) | No | - |

## Testing

```bash
# Run tests
uv run pytest tests/

# With coverage
uv run pytest tests/ --cov=src

# Run linter
uv run ruff check src/

# Format code
uv run ruff format src/
```

## Useful Commands

```bash
# Local Development
./scripts/start_local.sh --emulator     # Start with Firestore emulator
./scripts/start_local.sh --production   # Start with production Firestore
./scripts/start_local.sh --docker       # Start with Docker Compose

# Discord Command Sync
uv run python scripts/sync_commands.py --guild-id YOUR_GUILD_ID  # Sync to specific server
uv run python scripts/sync_commands.py --global                  # Sync globally (takes up to 1 hour)

# GCP Deployment
./scripts/setup_gcp.sh --project-id PROJECT_ID --discord-token "TOKEN"  # Initial GCP setup
./scripts/deploy.sh --project-id PROJECT_ID                              # Deploy to Cloud Run

# Testing and Linting
uv run pytest tests/                    # Run tests
uv run pytest tests/ --cov=src          # With coverage
uv run ruff check .                     # Run linter
uv run ruff format .                    # Format code
uv run pyright                          # Type checking

# Dependency Management
uv add <package-name>                   # Add a new dependency
uv add --dev <package-name>             # Add a dev dependency
uv sync --upgrade                       # Update all dependencies
uv pip list                             # Show installed packages
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.
