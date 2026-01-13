# GCPセットアップガイド

このドキュメントでは、Google Cloud Platform (GCP) で WithGames Discord Bot を本番運用するための初期セットアップ手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [GCPプロジェクトの作成](#gcpプロジェクトの作成)
3. [必要なAPIの有効化](#必要なapiの有効化)
4. [Firestoreのセットアップ](#firestoreのセットアップ)
5. [サービスアカウントの作成](#サービスアカウントの作成)
6. [Cloud Runのセットアップ](#cloud-runのセットアップ)
7. [環境変数とシークレットの設定](#環境変数とシークレットの設定)
8. [自動セットアップスクリプト](#自動セットアップスクリプト)

## 前提条件

- GCPアカウント（[無料トライアル](https://cloud.google.com/free)あり）
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) がインストール済み
- 請求先アカウントの設定済み
- プロジェクト作成権限

### gcloud CLIの初期化

```bash
# gcloud CLIをインストール後、初期化
gcloud init

# 認証
gcloud auth login

# アカウント確認
gcloud auth list
```

## GCPプロジェクトの作成

### オプション1: GCPコンソールから作成

1. [GCPコンソール](https://console.cloud.google.com/) にアクセス
2. プロジェクトセレクタをクリック
3. 「新しいプロジェクト」をクリック
4. プロジェクト名を入力（例: `withgames-bot-prod`）
5. プロジェクトIDをメモ（例: `withgames-bot-prod-12345`）
6. 「作成」をクリック

### オプション2: gcloud CLIから作成

```bash
# プロジェクトIDを設定（一意である必要があります）
export PROJECT_ID="withgames-bot-prod"

# プロジェクト作成
gcloud projects create $PROJECT_ID --name="WithGames Discord Bot Production"

# プロジェクトを選択
gcloud config set project $PROJECT_ID

# 請求先アカウントをリンク（BILLING_ACCOUNT_IDを実際のIDに置き換え）
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

請求先アカウントIDの確認:
```bash
gcloud billing accounts list
```

## 必要なAPIの有効化

```bash
# 必要なAPIを一括で有効化
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

有効化には数分かかる場合があります。

## Firestoreのセットアップ

### 1. Firestoreデータベースの作成

```bash
# Firestore Native モードでデータベースを作成
gcloud firestore databases create --location=asia-northeast1 --type=firestore-native
```

または、GCPコンソールから:
1. [Firestoreコンソール](https://console.cloud.google.com/firestore) にアクセス
2. 「データベースを作成」をクリック
3. 「ネイティブモード」を選択
4. ロケーション: `asia-northeast1` (東京)
5. 「作成」をクリック

### 2. セキュリティルールの設定

```bash
# セキュリティルールをデプロイ
gcloud firestore rules deploy firestore.rules
```

`firestore.rules` ファイルの内容:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // すべての読み書きを許可（サービスアカウント経由のアクセスのみ）
    match /{document=**} {
      allow read, write: if false;  // デフォルトで拒否
    }
  }
}
```

**注意**: Botはサービスアカウント経由でアクセスするため、これらのルールは適用されません。

## サービスアカウントの作成

### 1. サービスアカウントの作成

```bash
# サービスアカウント名
export SA_NAME="withgames-bot-sa"
export SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# サービスアカウント作成
gcloud iam service-accounts create $SA_NAME \
  --display-name="WithGames Discord Bot Service Account" \
  --description="Service account for WithGames Discord Bot"
```

### 2. 必要な権限の付与

```bash
# Firestore データストアユーザー
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/datastore.user"

# Secret Manager シークレットアクセサー
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

# ログ書き込み
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/logging.logWriter"

# メトリクス書き込み
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/monitoring.metricWriter"
```

### 3. サービスアカウントキーの作成（ローカル開発用）

```bash
# キーファイルを作成
gcloud iam service-accounts keys create ./service-account-key.json \
  --iam-account=$SA_EMAIL

# 権限を制限
chmod 600 ./service-account-key.json

# .gitignoreに追加されていることを確認
echo "service-account-key.json" >> .gitignore
```

**重要**: このキーファイルは絶対にGitにコミットしないこと！

## Cloud Runのセットアップ

### 1. Artifact Registryリポジトリの作成

```bash
# リポジトリ名
export REPO_NAME="withgames-bot"
export REGION="asia-northeast1"

# Docker リポジトリを作成
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="WithGames Discord Bot container images"
```

### 2. Cloud Runサービスの初期設定

```bash
# サービス名
export SERVICE_NAME="withgames-bot"

# 最初は何もデプロイせずに、設定だけ行います
# 実際のデプロイは CI/CD または手動デプロイで行います
```

## 環境変数とシークレットの設定

### 1. Discord Tokenをシークレットとして保存

```bash
# Discord Bot Token を Secret Manager に保存
echo -n "YOUR_DISCORD_BOT_TOKEN" | \
  gcloud secrets create discord-bot-token \
    --data-file=- \
    --replication-policy="automatic"

# サービスアカウントにアクセス権限を付与
gcloud secrets add-iam-policy-binding discord-bot-token \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

### 2. Discord Application IDをシークレットとして保存

```bash
# Discord Application ID を Secret Manager に保存
echo -n "YOUR_DISCORD_APP_ID" | \
  gcloud secrets create discord-app-id \
    --data-file=- \
    --replication-policy="automatic"

# サービスアカウントにアクセス権限を付与
gcloud secrets add-iam-policy-binding discord-app-id \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Event Webhook URLをシークレットとして保存（オプション）

イベント募集情報を特定のチャンネルに投稿したい場合は、Webhook URLをSecret Managerに保存します。

```bash
# Event Webhook URL を Secret Manager に保存
echo -n "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN" | \
  gcloud secrets create event-webhook-url \
    --data-file=- \
    --replication-policy="automatic"

# サービスアカウントにアクセス権限を付与
gcloud secrets add-iam-policy-binding event-webhook-url \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

**Webhook URLの取得方法:**
1. Discordサーバーの設定を開く
2. 「連携サービス」→「ウェブフック」を選択
3. 「新しいウェブフック」をクリック
4. ウェブフック名を設定（例: WithGames Events）
5. イベントを投稿したいチャンネルを選択
6. 「ウェブフックURLをコピー」をクリック

**注意**: Webhook URLを設定しない場合、イベントはコマンドを実行したチャンネルに投稿されます。

### 4. その他の環境変数

Cloud Run サービス作成時に以下の環境変数を設定します:

```bash
# 環境変数リスト
ENVIRONMENT=production
GCP_PROJECT_ID=${PROJECT_ID}
DISCORD_APPLICATION_ID=YOUR_DISCORD_APP_ID
REMINDER_MINUTES=30
```

## 自動セットアップスクリプト

すべての手順を自動化するスクリプトを用意しています:

```bash
# スクリプトに実行権限を付与
chmod +x scripts/setup_gcp.sh

# 対話的セットアップ
./scripts/setup_gcp.sh

# または引数で指定
./scripts/setup_gcp.sh \
  --project-id your-project-id \
  --discord-token "your-discord-token" \
  --discord-app-id "your-app-id" \
  --webhook-url "https://discord.com/api/webhooks/..." \
  --region asia-northeast1
```

## セットアップの確認

### 1. プロジェクト情報の確認

```bash
# プロジェクト情報
gcloud config get-value project

# 有効なAPI
gcloud services list --enabled

# サービスアカウント
gcloud iam service-accounts list

# Firestore
gcloud firestore databases list
```

### 2. 接続テスト

```bash
# ローカルからFirestoreに接続してテスト
export GOOGLE_APPLICATION_CREDENTIALS="./service-account-key.json"
uv run python -c "from src.services.firestore_service import firestore_service; print(firestore_service.test_connection())"
```

成功すると `True` が表示されます。

## コスト管理

### 予算アラートの設定

```bash
# 予算を作成（月額 $10 の例）
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="WithGames Bot Budget" \
  --budget-amount=10USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### コスト最適化のヒント

1. **Cloud Run**
   - 最小インスタンス数: 0（アイドル時は課金なし）
   - 最大インスタンス数: 1-2（小規模運用の場合）
   - CPU: 常時割り当て（バックグラウンドタスク用）

2. **Firestore**
   - 読み取り/書き込み回数を最小化
   - インデックスを最適化
   - 不要なデータは定期的に削除

3. **Secret Manager**
   - シークレットのバージョン数を制限
   - 古いバージョンを定期的に削除

## トラブルシューティング

### APIが有効にならない

```bash
# APIの状態を確認
gcloud services list --enabled | grep firestore

# 手動で有効化
gcloud services enable firestore.googleapis.com
```

### 権限エラー

```bash
# サービスアカウントの権限を確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:serviceAccount:${SA_EMAIL}"
```

### Firestore接続エラー

```bash
# プロジェクトIDを確認
gcloud config get-value project

# Firestoreデータベースが作成されているか確認
gcloud firestore databases list

# サービスアカウントキーのパスを確認
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS
```

## 次のステップ

- [デプロイガイド](./DEPLOYMENT.md) - アプリケーションのデプロイ方法
- [CI/CDセットアップ](./CICD.md) - GitHub Actionsの設定
- [モニタリング設定](./MONITORING.md) - ログとメトリクスの監視

## セキュリティのベストプラクティス

1. **サービスアカウントキー**
   - キーファイルは安全に保管
   - 定期的にローテーション
   - Gitにコミットしない

2. **Secret Manager**
   - 機密情報は必ずSecret Managerに保存
   - 環境変数に直接設定しない

3. **IAM権限**
   - 最小権限の原則に従う
   - 定期的に権限を見直す

4. **ネットワーク**
   - Cloud Runサービスは認証必須に設定
   - VPCコネクタを使用して内部通信を保護（オプション）

## 参考リンク

- [GCP プロジェクトの管理](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- [Firestore ドキュメント](https://cloud.google.com/firestore/docs)
- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Secret Manager ドキュメント](https://cloud.google.com/secret-manager/docs)
