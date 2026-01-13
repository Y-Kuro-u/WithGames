"""
Embed generation utilities for WithGames Discord Bot.
Creates rich, user-friendly embeds for events and messages.
"""
import discord
from datetime import datetime
from typing import List, Optional
from src.models.event import Event
from src.ui.colors import Colors
from src.utils.datetime_utils import DateTimeUtils
from src.utils.formatters import Formatters
from src.utils.game_data import GameData


class EventEmbeds:
    """Event-related embed generators."""

    @staticmethod
    def create_event_embed(
        event: Event,
        participants: Optional[List[str]] = None,
        waitlist: Optional[List[str]] = None,
    ) -> discord.Embed:
        """Create rich embed for event display.

        Args:
            event: Event object
            participants: List of participant names
            waitlist: List of waitlist participant names

        Returns:
            Discord Embed object
        """
        # Get color based on status
        color = Colors.from_status(event.status.value)

        # Create embed with title including game emoji
        title = f"{event.game_emoji} {event.title}"
        embed = discord.Embed(
            title=title,
            description=event.description or "詳細な説明はありません",
            color=color,
        )

        # Add game icon as thumbnail if available
        if event.game_icon_url:
            embed.set_thumbnail(url=event.game_icon_url)

        # Add start time field with both full and relative time
        start_time_str = DateTimeUtils.format_full_datetime(event.start_time)
        relative_time_str = DateTimeUtils.format_relative_time(event.start_time)
        embed.add_field(
            name="📅 開始日時",
            value=f"{start_time_str}\n{relative_time_str}",
            inline=False,
        )

        # Add game type field
        embed.add_field(
            name="🎮 ゲーム",
            value=event.game_type,
            inline=True,
        )

        # Add participation status with progress bar
        participation_status = Formatters.format_participation_status(
            event.current_participants, event.max_participants
        )
        embed.add_field(
            name="👥 参加状況",
            value=participation_status,
            inline=True,
        )

        # Add creator field
        creator_mention = Formatters.format_user_mention(event.creator_id)
        embed.add_field(
            name="👤 作成者",
            value=creator_mention,
            inline=True,
        )

        # Add participants list if provided
        if participants is not None:
            participant_list = Formatters.format_participant_list(
                participants, max_display=10
            )
            embed.add_field(
                name="✅ 参加者",
                value=participant_list,
                inline=False,
            )

        # Add waitlist if exists
        if waitlist and len(waitlist) > 0:
            waitlist_str = Formatters.format_waitlist(waitlist, max_display=5)
            if waitlist_str:
                embed.add_field(
                    name="⏳ キャンセル待ち",
                    value=waitlist_str,
                    inline=False,
                )

        # Add footer with event ID and last update time
        event_id_short = Formatters.format_event_id_short(event.id)
        updated_time = DateTimeUtils.format_relative_time(event.updated_at)
        embed.set_footer(
            text=f"イベントID: {event_id_short} | 最終更新: {updated_time}"
        )

        return embed

    @staticmethod
    def create_success_embed(
        title: str, description: str, additional_fields: Optional[List[tuple]] = None
    ) -> discord.Embed:
        """Create success message embed.

        Args:
            title: Embed title
            description: Embed description
            additional_fields: Optional list of (name, value, inline) tuples

        Returns:
            Discord Embed object
        """
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=Colors.SUCCESS,
        )

        if additional_fields:
            for name, value, inline in additional_fields:
                embed.add_field(name=name, value=value, inline=inline)

        return embed

    @staticmethod
    def create_error_embed(
        title: str, description: str, errors: Optional[List[str]] = None
    ) -> discord.Embed:
        """Create error message embed.

        Args:
            title: Embed title
            description: Embed description
            errors: Optional list of error messages

        Returns:
            Discord Embed object
        """
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=Colors.ERROR,
        )

        if errors:
            error_text = "\n".join([f"• {error}" for error in errors])
            embed.add_field(
                name="原因",
                value=error_text,
                inline=False,
            )

            embed.add_field(
                name="💡 ヒント",
                value="コマンドを再実行して修正してください",
                inline=False,
            )

        return embed

    @staticmethod
    def create_event_created_embed(event: Event, channel_id: str) -> discord.Embed:
        """Create embed for event creation confirmation.

        Args:
            event: Created event
            channel_id: Channel ID where event was posted

        Returns:
            Discord Embed object
        """
        channel_mention = Formatters.format_channel_mention(channel_id)
        start_time = DateTimeUtils.format_full_datetime(event.start_time)

        description = (
            f"イベント「**{event.title}**」を作成しました！\n"
            f"📍 {channel_mention} に投稿されました"
        )

        fields = [
            ("🎮 ゲーム", event.game_type, True),
            ("📅 開始日時", start_time, True),
            ("👥 定員", f"{event.max_participants}名", True),
        ]

        return EventEmbeds.create_success_embed(
            "イベント作成完了",
            description,
            fields,
        )

    @staticmethod
    def create_join_success_embed(event: Event) -> discord.Embed:
        """Create embed for successful event join.

        Args:
            event: Event that was joined

        Returns:
            Discord Embed object
        """
        start_time = DateTimeUtils.format_full_datetime(event.start_time)

        description = (
            f"イベント「**{event.title}**」に参加しました！\n"
            f"📅 開始日時: {start_time}\n"
            f"⏰ 30分前にリマインダーを送信します"
        )

        return EventEmbeds.create_success_embed(
            "参加完了",
            description,
        )

    @staticmethod
    def create_waitlist_added_embed(event: Event, position: int) -> discord.Embed:
        """Create embed for waitlist addition.

        Args:
            event: Event
            position: Position in waitlist

        Returns:
            Discord Embed object
        """
        description = (
            f"定員に達しているため、キャンセル待ちリストに追加しました\n"
            f"📊 現在の順番: **{position}番目**\n"
            f"💡 誰かがキャンセルすると自動的に繰り上げられます"
        )

        embed = discord.Embed(
            title="⏳ キャンセル待ち",
            description=description,
            color=Colors.WARNING,
        )

        return embed

    @staticmethod
    def create_event_list_embed(
        events: List[Event], page: int = 1, total_pages: int = 1
    ) -> discord.Embed:
        """Create embed for event list.

        Args:
            events: List of events
            page: Current page number
            total_pages: Total number of pages

        Returns:
            Discord Embed object
        """
        embed = discord.Embed(
            title="📋 募集中のイベント一覧",
            description=f"全{len(events)}件のイベント (ページ {page}/{total_pages})",
            color=Colors.INFO,
        )

        if not events:
            embed.description = "現在募集中のイベントはありません"
            return embed

        # Add each event as a field (max 5 per page)
        for event in events[:5]:
            start_time = DateTimeUtils.format_relative_time(event.start_time)
            participation = f"{event.current_participants}/{event.max_participants}"

            field_name = f"{event.game_emoji} {event.title}"
            field_value = f"👥 {participation} | 📅 {start_time}"

            embed.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        return embed

    @staticmethod
    def create_confirmation_embed(
        title: str, description: str, warning: bool = True
    ) -> discord.Embed:
        """Create confirmation dialog embed.

        Args:
            title: Embed title
            description: Embed description
            warning: Whether to use warning color

        Returns:
            Discord Embed object
        """
        color = Colors.WARNING if warning else Colors.INFO

        embed = discord.Embed(
            title=f"⚠️ {title}" if warning else title,
            description=description,
            color=color,
        )

        return embed

    @staticmethod
    def create_info_embed(title: str, description: str) -> discord.Embed:
        """Create info message embed.

        Args:
            title: Embed title
            description: Embed description

        Returns:
            Discord Embed object
        """
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=Colors.INFO,
        )

        return embed

    @staticmethod
    def create_reminder_embed(event: Event) -> discord.Embed:
        """Create reminder notification embed.

        Args:
            event: Event to remind about

        Returns:
            Discord Embed object
        """
        start_time = DateTimeUtils.format_full_datetime(event.start_time)
        channel_mention = Formatters.format_channel_mention(event.channel_id)

        embed = discord.Embed(
            title="⏰ イベント開始のお知らせ",
            description="参加予定のイベントが30分後に開始します！",
            color=Colors.INFO,
        )

        if event.game_icon_url:
            embed.set_thumbnail(url=event.game_icon_url)

        embed.add_field(
            name="🎮 イベント",
            value=event.title,
            inline=False,
        )

        embed.add_field(
            name="📅 開始日時",
            value=start_time,
            inline=True,
        )

        embed.add_field(
            name="👥 参加者",
            value=f"{event.current_participants}/{event.max_participants}名",
            inline=True,
        )

        embed.add_field(
            name="📍 チャンネル",
            value=channel_mention,
            inline=False,
        )

        return embed

    @staticmethod
    def create_participant_details_embed(
        event: Event, participants: List, waitlist: List
    ) -> discord.Embed:
        """Create detailed participant list embed.

        Args:
            event: Event object
            participants: List of Participant objects
            waitlist: List of waitlisted Participant objects

        Returns:
            Discord Embed object
        """
        embed = discord.Embed(
            title=f"👥 参加者リスト - {event.title}",
            description=f"イベントの参加者情報です",
            color=Colors.INFO,
        )

        # Participants list
        if participants:
            # Format as Discord mentions with fallback to name
            participant_list = "\n".join(
                [f"✅ <@{p.user_id}>" for p in participants[:20]]
            )
            if len(participants) > 20:
                participant_list += f"\n...他{len(participants) - 20}名"

            embed.add_field(
                name=f"✅ 参加者 ({len(participants)}/{event.max_participants})",
                value=participant_list if participant_list else "なし",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"✅ 参加者 (0/{event.max_participants})",
                value="まだ参加者がいません",
                inline=False,
            )

        # Waitlist
        if waitlist:
            waitlist_list = "\n".join(
                [f"⏳ {i+1}. <@{p.user_id}>" for i, p in enumerate(waitlist[:10])]
            )
            if len(waitlist) > 10:
                waitlist_list += f"\n...他{len(waitlist) - 10}名"

            embed.add_field(
                name=f"⏳ キャンセル待ち ({len(waitlist)}名)",
                value=waitlist_list,
                inline=False,
            )

        return embed

    @staticmethod
    def create_my_events_embed(event_list: List[dict]) -> discord.Embed:
        """Create user's events list embed.

        Args:
            event_list: List of dicts with 'event' and 'participant' keys

        Returns:
            Discord Embed object
        """
        embed = discord.Embed(
            title="📋 マイイベント",
            description=f"参加中のイベント: {len(event_list)}件",
            color=Colors.INFO,
        )

        for item in event_list[:10]:
            event = item["event"]
            participant = item["participant"]

            start_time = DateTimeUtils.format_relative_time(event.start_time)
            status_emoji = "✅" if participant.status.value == "joined" else "⏳"
            status_text = (
                "参加中"
                if participant.status.value == "joined"
                else f"キャンセル待ち ({participant.position}番目)"
            )

            field_name = f"{status_emoji} {event.game_emoji} {event.title}"
            field_value = (
                f"📅 {start_time}\n"
                f"👥 {event.current_participants}/{event.max_participants} | {status_text}"
            )

            embed.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        if len(event_list) > 10:
            embed.set_footer(text=f"...他{len(event_list) - 10}件のイベント")

        return embed
