#!/usr/bin/env python3
"""
Discord コマンド同期スクリプト

このスクリプトは Discord Bot のスラッシュコマンドを同期します。
開発中は --guild-id を指定してギルド固有の同期を行うことで、即座に反映されます。
本番環境では --global でグローバル同期を行いますが、反映まで最大1時間かかります。

使用例:
    # 特定のギルドに同期（即座に反映、開発推奨）
    uv run python scripts/sync_commands.py --guild-id 123456789012345678

    # グローバル同期（反映まで最大1時間）
    uv run python scripts/sync_commands.py --global

    # 既存のコマンドを削除してから同期
    uv run python scripts/sync_commands.py --guild-id 123456789012345678 --clear

    # 全てのギルドからコマンドを削除
    uv run python scripts/sync_commands.py --guild-id 123456789012345678 --clear-only
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands

# src モジュールをインポート可能にする
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config


class CommandSyncBot(commands.Bot):
    """コマンド同期専用の Bot クラス"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sync_mode = None
        self.guild_id = None
        self.clear_commands = False
        self.clear_only = False

    async def setup_hook(self):
        """Bot起動時の処理（Cogの読み込み）"""
        # Cogsを読み込む（コマンドを登録するため）
        await self.load_extension("src.cogs.event_manager")
        await self.load_extension("src.cogs.participant_manager")
        # notification_manager はコマンド同期には不要（バックグラウンドタスクのみ）
        print("✓ Cogs loaded successfully")

    async def on_ready(self):
        """Bot準備完了時の処理（コマンド同期）"""
        print(f"✓ Logged in as {self.user} (ID: {self.user.id})")
        print(f"✓ Connected to {len(self.guilds)} guild(s)")
        print("-" * 50)

        try:
            if self.sync_mode == "guild":
                await self._sync_guild_commands()
            elif self.sync_mode == "global":
                await self._sync_global_commands()
            else:
                print("❌ No sync mode specified")
                await self.close()
                return

            print("-" * 50)
            print("✓ Command sync completed successfully!")

        except Exception as e:
            print(f"❌ Error during command sync: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close()

    async def _sync_guild_commands(self):
        """ギルド固有のコマンド同期"""
        guild = discord.Object(id=self.guild_id)
        
        if self.clear_only:
            # コマンドを削除するのみ
            print(f"Clearing all commands from guild {self.guild_id}...")
            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✓ Cleared all commands from guild {self.guild_id}")
            return

        if self.clear_commands:
            # 既存のコマンドをクリア
            print(f"Clearing existing commands from guild {self.guild_id}...")
            self.tree.clear_commands(guild=guild)

        # ギルドにコマンドをコピー
        print(f"Syncing commands to guild {self.guild_id}...")
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        
        print(f"✓ Synced {len(synced)} command(s) to guild {self.guild_id}")
        print("\nSynced commands:")
        for cmd in synced:
            print(f"  - /{cmd.name}: {cmd.description}")

    async def _sync_global_commands(self):
        """グローバルコマンド同期"""
        if self.clear_only:
            # グローバルコマンドを削除
            print("Clearing all global commands...")
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            print("✓ Cleared all global commands")
            return

        if self.clear_commands:
            # 既存のグローバルコマンドをクリア
            print("Clearing existing global commands...")
            self.tree.clear_commands(guild=None)

        # グローバルにコマンドを同期
        print("Syncing commands globally...")
        print("⚠️  Warning: Global sync may take up to 1 hour to propagate!")
        synced = await self.tree.sync()
        
        print(f"✓ Synced {len(synced)} command(s) globally")
        print("\nSynced commands:")
        for cmd in synced:
            print(f"  - /{cmd.name}: {cmd.description}")


async def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="Discord Bot のスラッシュコマンドを同期します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 開発用: 特定のギルドに即座に同期
  %(prog)s --guild-id 123456789012345678
  
  # 本番用: グローバルに同期（最大1時間かかる）
  %(prog)s --global
  
  # 既存のコマンドをクリアしてから同期
  %(prog)s --guild-id 123456789012345678 --clear
  
  # コマンドのみ削除（同期しない）
  %(prog)s --guild-id 123456789012345678 --clear-only
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--guild-id",
        type=int,
        help="コマンドを同期するギルドID（即座に反映、開発推奨）"
    )
    group.add_argument(
        "--global",
        action="store_true",
        dest="global_sync",
        help="グローバルに同期（反映まで最大1時間）"
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="既存のコマンドを削除してから同期"
    )
    parser.add_argument(
        "--clear-only",
        action="store_true",
        help="コマンドを削除するのみ（同期しない）"
    )

    args = parser.parse_args()

    # 設定を読み込み
    try:
        from src.config import config
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure the following environment variables are set:")
        print("  - DISCORD_TOKEN")
        print("  - DISCORD_APPLICATION_ID (optional but recommended)")
        print("\nYou can set them in a .env file or export them:")
        print('  export DISCORD_TOKEN="your-token-here"')
        sys.exit(1)

    # Intents設定（最小限）
    intents = discord.Intents.default()
    intents.message_content = False  # コマンド同期には不要

    # Application IDを整数に変換（設定されている場合のみ）
    app_id = None
    if config.discord_application_id:
        try:
            app_id = int(config.discord_application_id)
        except ValueError:
            print(f"⚠️  Warning: Invalid DISCORD_APPLICATION_ID: {config.discord_application_id}")
            print("    Continuing without application_id (may be slower)")

    # Bot作成
    bot = CommandSyncBot(
        command_prefix="!",  # スラッシュコマンドのみなので使用しない
        intents=intents,
        application_id=app_id,
    )

    # 同期モードを設定
    if args.guild_id:
        bot.sync_mode = "guild"
        bot.guild_id = args.guild_id
        print(f"Mode: Guild-specific sync (Guild ID: {args.guild_id})")
    else:
        bot.sync_mode = "global"
        print("Mode: Global sync (may take up to 1 hour)")

    bot.clear_commands = args.clear
    bot.clear_only = args.clear_only

    if args.clear:
        print("Option: Clear existing commands before sync")
    if args.clear_only:
        print("Option: Clear commands only (no sync)")

    print("-" * 50)

    # Botを起動
    try:
        async with bot:
            await bot.start(config.discord_token)
    except discord.LoginFailure:
        print("❌ Failed to login. Please check your DISCORD_TOKEN")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
