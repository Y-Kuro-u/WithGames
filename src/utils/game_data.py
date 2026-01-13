"""
Game data and information for WithGames Discord Bot.
Contains popular games with emojis and icon URLs.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GameInfo:
    """Game information."""

    name: str
    emoji: str
    category: str
    icon_url: Optional[str] = None


class GameData:
    """Game data repository."""

    GAMES: List[GameInfo] = [
        # FPS Games
        GameInfo(
            name="Valorant",
            emoji="🔫",
            category="FPS",
            icon_url="https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/1172470/1fbe3bb93f3c2a9dad26d493f62e8bb79a4e39d3.jpg",
        ),
        GameInfo(
            name="Apex Legends",
            emoji="🎯",
            category="FPS",
            icon_url="https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/1172470/1fbe3bb93f3c2a9dad26d493f62e8bb79a4e39d3.jpg",
        ),
        GameInfo(
            name="Overwatch 2",
            emoji="⚡",
            category="FPS",
        ),
        GameInfo(
            name="Counter-Strike 2",
            emoji="💥",
            category="FPS",
        ),
        GameInfo(
            name="Call of Duty",
            emoji="🎖️",
            category="FPS",
        ),
        # MOBA
        GameInfo(
            name="League of Legends",
            emoji="⚔️",
            category="MOBA",
        ),
        GameInfo(
            name="Dota 2",
            emoji="🛡️",
            category="MOBA",
        ),
        # Battle Royale
        GameInfo(
            name="Fortnite",
            emoji="🏰",
            category="Battle Royale",
        ),
        GameInfo(
            name="PUBG",
            emoji="🎮",
            category="Battle Royale",
        ),
        # Casual/Party
        GameInfo(
            name="Among Us",
            emoji="🎪",
            category="Party",
        ),
        GameInfo(
            name="Fall Guys",
            emoji="👾",
            category="Party",
        ),
        # Sandbox/Creative
        GameInfo(
            name="Minecraft",
            emoji="⛏️",
            category="Sandbox",
        ),
        GameInfo(
            name="Terraria",
            emoji="🌍",
            category="Sandbox",
        ),
        # RPG/Action
        GameInfo(
            name="モンスターハンター",
            emoji="🐉",
            category="Action RPG",
        ),
        GameInfo(
            name="Elden Ring",
            emoji="⚔️",
            category="Action RPG",
        ),
        GameInfo(
            name="Destiny 2",
            emoji="🌌",
            category="Action RPG",
        ),
        # Nintendo
        GameInfo(
            name="スプラトゥーン3",
            emoji="🦑",
            category="TPS",
        ),
        GameInfo(
            name="マリオカート",
            emoji="🏎️",
            category="Racing",
        ),
        GameInfo(
            name="スマッシュブラザーズ",
            emoji="🥊",
            category="Fighting",
        ),
        # MMO
        GameInfo(
            name="Final Fantasy XIV",
            emoji="⚜️",
            category="MMORPG",
        ),
        GameInfo(
            name="World of Warcraft",
            emoji="🐲",
            category="MMORPG",
        ),
        # Card Games
        GameInfo(
            name="Hearthstone",
            emoji="🃏",
            category="Card Game",
        ),
        # Mobile
        GameInfo(
            name="ブロスタ",
            emoji="💎",
            category="Mobile",
        ),
    ]

    @classmethod
    def get_all_games(cls) -> List[GameInfo]:
        """Get all available games.

        Returns:
            List of all games
        """
        return cls.GAMES

    @classmethod
    def get_game_names(cls) -> List[str]:
        """Get list of all game names.

        Returns:
            List of game names
        """
        return [game.name for game in cls.GAMES]

    @classmethod
    def get_game_by_name(cls, name: str) -> Optional[GameInfo]:
        """Get game info by name.

        Args:
            name: Game name

        Returns:
            GameInfo if found, None otherwise
        """
        for game in cls.GAMES:
            if game.name.lower() == name.lower():
                return game
        return None

    @classmethod
    def search_games(cls, query: str, limit: int = 25) -> List[GameInfo]:
        """Search games by query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching games
        """
        query_lower = query.lower()
        results = [
            game
            for game in cls.GAMES
            if query_lower in game.name.lower() or query_lower in game.category.lower()
        ]
        return results[:limit]

    @classmethod
    def get_popular_games(cls, count: int = 10) -> List[GameInfo]:
        """Get most popular games.

        Args:
            count: Number of games to return

        Returns:
            List of popular games
        """
        return cls.GAMES[:count]

    @classmethod
    def get_game_emoji(cls, game_name: str) -> str:
        """Get emoji for a game.

        Args:
            game_name: Game name

        Returns:
            Emoji for the game, default 🎮 if not found
        """
        game = cls.get_game_by_name(game_name)
        return game.emoji if game else "🎮"

    @classmethod
    def get_game_icon_url(cls, game_name: str) -> Optional[str]:
        """Get icon URL for a game.

        Args:
            game_name: Game name

        Returns:
            Icon URL if available, None otherwise
        """
        game = cls.get_game_by_name(game_name)
        return game.icon_url if game else None


# Custom game placeholder
CUSTOM_GAME = GameInfo(
    name="その他（手動入力）",
    emoji="📝",
    category="Custom",
)
