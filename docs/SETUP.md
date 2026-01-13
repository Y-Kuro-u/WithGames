# セットアップガイド

このドキュメントでは、WithGames Discord Botのローカル開発環境のセットアップ手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [Discord Botの作成](#discord-botの作成)
3. [ローカル環境のセットアップ](#ローカル環境のセットアップ)
4. [Botの起動](#botの起動)
5. [コマンドの同期](#コマンドの同期)

## 前提条件

- Python 3.11以上
- [uv](https://docs.astral.sh/uv/) がインストールされていること
- Discord Developer Portal へのアクセス
- Google Cloud SDK (gcloud) - Firestore Emulator用

### uvのインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Google Cloud SDKのインストール

```bash
# macOS
brew install google-cloud-sdk

# Linux
# https://cloud.google.com/sdk/docs/install を参照

# Firestoreエミュレータコンポーネントのインストール
gcloud components install beta
gcloud components install cloud-firestore-emulator
```

## Discord Botの作成

### 1. Discord Developer Portalでアプリケーションを作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリック
3. アプリケーション名を入力（例: WithGames）
4. 利用規約に同意して「Create」

### 2. Botユーザーを作成

1. 左メニューから「Bot」を選択
2. 「Add Bot」をクリック
3. Bot設定:
   - **Public Bot**: オフ（推奨）
   - **Requires OAuth2 Code Grant**: オフ
   - **Presence Intent**: オン
   - **Server Members Intent**: オン
   - **Message Content Intent**: オン

### 3. Botトークンを取得

1. Bot設定ページで「Reset Token」をクリック
2. トークンをコピーして安全な場所に保存
3. **注意**: このトークンは絶対に公開しないこと

### 4. Application IDを取得

1. 左メニューから「General Information」を選択
2. 「Application ID」をコピー

### 5. Botをサーバーに招待

1. 左メニューから「OAuth2」→「URL Generator」を選択
2. **Scopes**で以下を選択:
   - `bot`
   - `applications.commands`
3. **Bot Permissions**で以下を選択:
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions
   - Use Slash Commands
4. 生成されたURLをコピーしてブラウザで開く
5. Botを追加するサーバーを選択

## ローカル環境のセットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd WithGames
```

### 2. 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集
nano .env  # または vim, code など好きなエディタで
```

`.env`ファイルに以下の情報を設定:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token_here
DISCORD_APPLICATION_ID=your_application_id_here

# Google Cloud Platform
GCP_PROJECT_ID=your_gcp_project_id

# Environment
ENVIRONMENT=dev

# Bot Settings
REMINDER_MINUTES=30

# Firestore Emulator (for local development)
FIRESTORE_EMULATOR_HOST=localhost:8080
```

### 3. 依存関係のインストール

```bash
# 本番用依存関係のみインストール
uv sync

# 開発用依存関係も含めてインストール
uv sync --all-extras
```

## Botの起動

### オプション1: Firestore Emulatorを使用（推奨）

Firestore Emulatorを使用すると、実際のFirestoreインスタンスを使わずにローカルで開発できます。

**ターミナル1: Firestore Emulatorの起動**
```bash
gcloud beta emulators firestore start --host-port=localhost:8080
```

**ターミナル2: Botの起動**
```bash
# .envにFIRESTORE_EMULATOR_HOST=localhost:8080が設定されていることを確認
uv run python -m src.main
```

または起動スクリプトを使用:
```bash
./scripts/start_local.sh
```

### オプション2: Dockerを使用

```bash
# ビルドして起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up -d

# ログを確認
docker-compose logs -f bot

# 停止
docker-compose down
```

### オプション3: 実際のFirestoreを使用

```bash
# FIRESTORE_EMULATOR_HOSTをコメントアウトまたは削除
# .envファイルを編集
ENVIRONMENT=dev
GCP_PROJECT_ID=your_actual_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Botを起動
uv run python -m src.main
```

## コマンドの同期

Bot起動時、スラッシュコマンドは自動的にグローバルに同期されます。

### サーバー固有のコマンド同期（開発用）

特定のサーバーのみにコマンドを同期することで、即座に反映されます（グローバル同期は最大1時間かかる場合があります）。

```bash
# サーバーIDを指定してコマンドを同期
uv run python scripts/sync_commands.py --guild-id YOUR_GUILD_ID

# または環境変数で指定
DISCORD_GUILD_ID=YOUR_GUILD_ID uv run python scripts/sync_commands.py
```

### グローバルコマンド同期

```bash
# すべてのサーバーに同期（最大1時間で反映）
uv run python scripts/sync_commands.py --global
```

## トラブルシューティング

### Botが起動しない

1. **トークンが正しいか確認**
   ```bash
   # .envファイルの確認
   cat .env | grep DISCORD_TOKEN
   ```

2. **依存関係を再インストール**
   ```bash
   rm -rf .venv uv.lock
   uv sync
   ```

3. **Python バージョンを確認**
   ```bash
   uv run python --version
   # Python 3.11.x が表示されるはず
   ```

### コマンドが表示されない

1. **Botの権限を確認**
   - Bot設定で必要な Intents が有効になっているか
   - サーバーでの権限が適切か

2. **コマンドを再同期**
   ```bash
   uv run python scripts/sync_commands.py --guild-id YOUR_GUILD_ID
   ```

3. **Discordクライアントを再起動**
   - Discordアプリを完全に終了して再起動

### Firestore接続エラー

1. **エミュレータが起動しているか確認**
   ```bash
   # 別のターミナルで実行
   gcloud beta emulators firestore start --host-port=localhost:8080
   ```

2. **環境変数を確認**
   ```bash
   echo $FIRESTORE_EMULATOR_HOST
   # localhost:8080 が表示されるはず
   ```

## 開発ワークフロー

### 1. コードの変更

```bash
# ブランチを作成
git checkout -b feature/new-feature

# コードを編集
# ...

# フォーマットとリント
uv run ruff format src/
uv run ruff check src/

# テスト実行
uv run pytest tests/
```

### 2. Botを再起動

コード変更後、Botを再起動して変更を反映:

```bash
# Ctrl+C でBotを停止
# 再度起動
uv run python -m src.main
```

### 3. デバッグ

```bash
# デバッグログを有効化
# src/config.py の setup_logging で level=logging.DEBUG に設定

# またはログレベルを環境変数で設定
LOG_LEVEL=DEBUG uv run python -m src.main
```

## 次のステップ

- [GCPセットアップガイド](./GCP_SETUP.md) - 本番環境の構築
- [デプロイガイド](./DEPLOYMENT.md) - GCP Cloud Runへのデプロイ
- [開発ガイド](./DEVELOPMENT.md) - コーディング規約とベストプラクティス

## サポート

問題が解決しない場合は、以下を確認してください:

1. [GitHub Issues](https://github.com/your-repo/issues) で既知の問題を検索
2. Discord サーバーでサポートを求める
3. 新しいIssueを作成して問題を報告
