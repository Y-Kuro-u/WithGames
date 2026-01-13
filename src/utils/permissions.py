"""
Permission checking utilities for WithGames Discord Bot.
"""
import discord
from typing import Optional
from src.models.event import Event


class PermissionChecker:
    """Helper class for checking user permissions."""

    @staticmethod
    def can_manage_event(
        user: discord.User, event: Event, guild: Optional[discord.Guild] = None
    ) -> tuple[bool, str]:
        """Check if a user can manage (edit/delete) an event.

        Args:
            user: Discord user
            event: Event to check permissions for
            guild: Discord guild (optional, for admin check)

        Returns:
            Tuple of (can_manage, reason)
            - can_manage: True if user can manage the event
            - reason: Reason if user cannot manage
        """
        # Check if user is the creator
        if str(user.id) == event.creator_id:
            return True, ""

        # Check if user is a server administrator
        if guild:
            member = guild.get_member(user.id)
            if member and member.guild_permissions.administrator:
                return True, ""

        return False, "このイベントを編集する権限がありません（作成者または管理者のみ）"

    @staticmethod
    def can_delete_event(
        user: discord.User, event: Event, guild: Optional[discord.Guild] = None
    ) -> tuple[bool, str]:
        """Check if a user can delete an event.

        Args:
            user: Discord user
            event: Event to check permissions for
            guild: Discord guild (optional, for admin check)

        Returns:
            Tuple of (can_delete, reason)
            - can_delete: True if user can delete the event
            - reason: Reason if user cannot delete
        """
        # Same permissions as manage_event
        return PermissionChecker.can_manage_event(user, event, guild)

    @staticmethod
    def is_event_creator(user: discord.User, event: Event) -> bool:
        """Check if a user is the creator of an event.

        Args:
            user: Discord user
            event: Event to check

        Returns:
            True if user is the creator
        """
        return str(user.id) == event.creator_id

    @staticmethod
    def is_guild_admin(user: discord.User, guild: discord.Guild) -> bool:
        """Check if a user is a guild administrator.

        Args:
            user: Discord user
            guild: Discord guild

        Returns:
            True if user is an administrator
        """
        member = guild.get_member(user.id)
        if member:
            return member.guild_permissions.administrator
        return False
