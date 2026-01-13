"""
Input validation utilities for WithGames Discord Bot.
"""
from datetime import datetime
from typing import Tuple, Optional
from dateutil import parser as date_parser


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class Validators:
    """Input validation utilities."""

    # Constants
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 100
    MIN_DESCRIPTION_LENGTH = 0
    MAX_DESCRIPTION_LENGTH = 1000
    MIN_PARTICIPANTS = 2
    MAX_PARTICIPANTS = 50

    @staticmethod
    def validate_title(title: str) -> Tuple[bool, Optional[str]]:
        """Validate event title.

        Args:
            title: Event title

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not title or not title.strip():
            return False, "タイトルを入力してください"

        if len(title) < Validators.MIN_TITLE_LENGTH:
            return False, f"タイトルは{Validators.MIN_TITLE_LENGTH}文字以上にしてください"

        if len(title) > Validators.MAX_TITLE_LENGTH:
            return False, f"タイトルは{Validators.MAX_TITLE_LENGTH}文字以内にしてください"

        return True, None

    @staticmethod
    def validate_description(description: str) -> Tuple[bool, Optional[str]]:
        """Validate event description.

        Args:
            description: Event description

        Returns:
            Tuple of (is_valid, error_message)
        """
        if description and len(description) > Validators.MAX_DESCRIPTION_LENGTH:
            return (
                False,
                f"説明は{Validators.MAX_DESCRIPTION_LENGTH}文字以内にしてください",
            )

        return True, None

    @staticmethod
    def validate_datetime(datetime_str: str) -> Tuple[bool, Optional[datetime], Optional[str]]:
        """Validate and parse datetime string.

        Args:
            datetime_str: Datetime string (e.g., "2026-01-15 20:00")

        Returns:
            Tuple of (is_valid, parsed_datetime, error_message)
        """
        if not datetime_str or not datetime_str.strip():
            return False, None, "開始日時を入力してください"

        try:
            # Try to parse the datetime
            parsed_dt = date_parser.parse(datetime_str, dayfirst=False)

            # Check if datetime is in the past
            if parsed_dt < datetime.now():
                return False, None, "開始日時が過去の日時です。未来の日時を指定してください"

            # Check if datetime is too far in the future (e.g., more than 1 year)
            max_future = datetime.now().replace(year=datetime.now().year + 1)
            if parsed_dt > max_future:
                return False, None, "開始日時が遠すぎます（1年以内にしてください）"

            return True, parsed_dt, None

        except (ValueError, OverflowError) as e:
            return (
                False,
                None,
                f"日時の形式が正しくありません。例: 2026-01-15 20:00 または 2026/01/15 20:00",
            )

    @staticmethod
    def validate_max_participants(max_participants_str: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Validate maximum participants.

        Args:
            max_participants_str: Maximum participants as string

        Returns:
            Tuple of (is_valid, parsed_value, error_message)
        """
        if not max_participants_str or not max_participants_str.strip():
            return False, None, "定員を入力してください"

        try:
            max_participants = int(max_participants_str)

            if max_participants < Validators.MIN_PARTICIPANTS:
                return (
                    False,
                    None,
                    f"定員は{Validators.MIN_PARTICIPANTS}人以上にしてください",
                )

            if max_participants > Validators.MAX_PARTICIPANTS:
                return (
                    False,
                    None,
                    f"定員は{Validators.MAX_PARTICIPANTS}人以下にしてください",
                )

            return True, max_participants, None

        except ValueError:
            return False, None, "定員は数字で入力してください"

    @staticmethod
    def validate_game_type(game_type: str) -> Tuple[bool, Optional[str]]:
        """Validate game type.

        Args:
            game_type: Game type string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not game_type or not game_type.strip():
            return False, "ゲーム種類を選択してください"

        if len(game_type) > 50:
            return False, "ゲーム名は50文字以内にしてください"

        return True, None

    @staticmethod
    def validate_event_data(
        title: str,
        description: str,
        datetime_str: str,
        max_participants_str: str,
        game_type: str,
    ) -> Tuple[bool, dict, list]:
        """Validate all event data at once.

        Args:
            title: Event title
            description: Event description
            datetime_str: Datetime string
            max_participants_str: Max participants string
            game_type: Game type

        Returns:
            Tuple of (is_valid, validated_data, error_messages)
        """
        errors = []
        validated_data = {}

        # Validate title
        is_valid, error = Validators.validate_title(title)
        if not is_valid:
            errors.append(error)
        else:
            validated_data["title"] = title.strip()

        # Validate description
        is_valid, error = Validators.validate_description(description)
        if not is_valid:
            errors.append(error)
        else:
            validated_data["description"] = description.strip() if description else ""

        # Validate datetime
        is_valid, parsed_dt, error = Validators.validate_datetime(datetime_str)
        if not is_valid:
            errors.append(error)
        else:
            validated_data["start_time"] = parsed_dt

        # Validate max participants
        is_valid, max_p, error = Validators.validate_max_participants(
            max_participants_str
        )
        if not is_valid:
            errors.append(error)
        else:
            validated_data["max_participants"] = max_p

        # Validate game type
        is_valid, error = Validators.validate_game_type(game_type)
        if not is_valid:
            errors.append(error)
        else:
            validated_data["game_type"] = game_type.strip()

        return len(errors) == 0, validated_data, errors
