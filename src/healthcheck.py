"""
Cloud Run用のヘルスチェックHTTPサーバー

Cloud Runはコンテナがポートをリッスンすることを期待しているため、
Discord Botと並行して簡易的なHTTPサーバーを起動します。
"""

import asyncio
import os
from aiohttp import web
import logging

logger = logging.getLogger(__name__)


async def health_check(request):
    """ヘルスチェックエンドポイント"""
    return web.Response(text="OK", status=200)


async def root(request):
    """ルートエンドポイント"""
    return web.Response(
        text="WithGames Discord Bot is running",
        status=200,
        content_type="text/plain"
    )


def create_app():
    """アプリケーション作成"""
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/health", health_check)
    app.router.add_get("/healthz", health_check)
    return app


async def run_healthcheck_server():
    """ヘルスチェックサーバーを起動（非同期）"""
    port = int(os.environ.get("PORT", 8080))
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server listening on 0.0.0.0:{port}")
    
    # サーバーを永続的に実行
    while True:
        await asyncio.sleep(3600)  # 1時間ごとにチェック
