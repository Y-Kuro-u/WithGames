# デプロイガイド

このドキュメントでは、WithGames Discord Bot を GCP Cloud Run にデプロイする方法を説明します。

## 目次

1. [前提条件](#前提条件)
2. [初回デプロイ](#初回デプロイ)
3. [更新デプロイ](#更新デプロイ)
4. [ロールバック](#ロールバック)
5. [モニタリング](#モニタリング)
6. [CI/CDデプロイ](#cicdデプロイ)

## 前提条件

- [GCPセットアップ](./GCP_SETUP.md) が完了していること
- Docker がインストールされていること
- gcloud CLI が認証済みであること
- プロジェクトの選択:
  ```bash
  gcloud config set project YOUR_PROJECT_ID
  ```

## 初回デプロイ

### ステップ1: Dockerイメージのビルド

```bash
# プロジェクトIDとリージョンを設定
export PROJECT_ID=$(gcloud config get-value project)
export REGION="asia-northeast1"
export REPO_NAME="withgames-bot"
export SERVICE_NAME="withgames-bot"
export IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"

# Dockerイメージをビルド
docker build -t ${IMAGE_NAME}:latest .

# イメージをArtifact Registryにプッシュ
docker push ${IMAGE_NAME}:latest
```

### ステップ2: Cloud Runサービスのデプロイ

```bash
# Secret ManagerからシークレットとSecret Managerを取得するように設定
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME}:latest \
  --platform=managed \
  --region=${REGION} \
  --service-account=withgames-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},REMINDER_MINUTES=30" \
  --set-secrets="DISCORD_TOKEN=discord-bot-token:latest,DISCORD_APPLICATION_ID=discord-app-id:latest" \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=1 \
  --max-instances=2 \
  --cpu-boost \
  --no-allow-unauthenticated \
  --timeout=60s \
  --concurrency=80
```

**重要な設定の説明**:

- `--min-instances=1`: 常に1インスタンス稼働（コールドスタート回避、バックグラウンドタスク用）
- `--cpu-boost`: 起動時のCPUブースト（起動高速化）
- `--no-allow-unauthenticated`: 外部からの直接アクセスを禁止
- `--set-secrets`: Secret Managerから機密情報を注入
  - `DISCORD_TOKEN`: Discord Bot Token
  - `DISCORD_APPLICATION_ID`: Discord Application ID

### ステップ3: シークレットの設定（初回のみ）

シークレットがまだ作成されていない場合は、以下のコマンドで作成します:

```bash
# Discord Application IDをSecret Managerに保存
echo -n "YOUR_DISCORD_APP_ID" | \
  gcloud secrets create discord-app-id \
    --data-file=- \
    --replication-policy="automatic"

# サービスアカウントにアクセス権限を付与
gcloud secrets add-iam-policy-binding discord-app-id \
  --member="serviceAccount:withgames-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### ステップ4: デプロイの確認

```bash
# サービスの状態を確認
gcloud run services describe ${SERVICE_NAME} --region=${REGION}

# ログを確認
gcloud run logs read ${SERVICE_NAME} --region=${REGION} --limit=50

# リアルタイムでログを確認
gcloud run logs tail ${SERVICE_NAME} --region=${REGION}
```

成功すると、ログに以下のようなメッセージが表示されます:
```
Bot is ready!
Logged in as WithGames#1234
Connected to X guilds
```

## 更新デプロイ

### 方法1: 新しいイメージをビルドしてデプロイ

```bash
# 1. コードを更新
git pull origin main

# 2. 新しいイメージをビルド（タグにコミットハッシュを使用）
export GIT_HASH=$(git rev-parse --short HEAD)
docker build -t ${IMAGE_NAME}:${GIT_HASH} -t ${IMAGE_NAME}:latest .

# 3. イメージをプッシュ
docker push ${IMAGE_NAME}:${GIT_HASH}
docker push ${IMAGE_NAME}:latest

# 4. Cloud Runを更新
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME}:${GIT_HASH} \
  --region=${REGION}
```

### 方法2: デプロイスクリプトを使用

```bash
# デプロイスクリプトを実行
./scripts/deploy.sh

# または環境変数で指定
PROJECT_ID="your-project-id" ./scripts/deploy.sh
```

### 方法3: Cloud Buildを使用

```bash
# Cloud Buildを使用してビルドとデプロイ
gcloud builds submit --config cloudbuild.yaml
```

## ロールバック

問題が発生した場合、以前のリビジョンにロールバックできます。

### 1. 利用可能なリビジョンを確認

```bash
# リビジョン一覧
gcloud run revisions list \
  --service=${SERVICE_NAME} \
  --region=${REGION}
```

### 2. 特定のリビジョンにトラフィックを切り替え

```bash
# リビジョン名を取得（例: withgames-bot-00005-abc）
export REVISION_NAME="withgames-bot-00005-abc"

# トラフィックを100%そのリビジョンに切り替え
gcloud run services update-traffic ${SERVICE_NAME} \
  --to-revisions=${REVISION_NAME}=100 \
  --region=${REGION}
```

### 3. 以前のイメージに戻す

```bash
# 特定のイメージタグにロールバック
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME}:previous-tag \
  --region=${REGION}
```

## モニタリング

### ログの確認

```bash
# 最新のログを表示
gcloud run logs read ${SERVICE_NAME} --region=${REGION} --limit=100

# エラーログのみ表示
gcloud run logs read ${SERVICE_NAME} \
  --region=${REGION} \
  --log-filter="severity>=ERROR" \
  --limit=50

# 特定のタイムスタンプ以降のログ
gcloud run logs read ${SERVICE_NAME} \
  --region=${REGION} \
  --log-filter="timestamp>=\"2026-01-12T00:00:00Z\""
```

### メトリクスの確認

```bash
# Cloud Consoleでメトリクスを確認
echo "https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics?project=${PROJECT_ID}"
```

主要なメトリクス:
- **リクエスト数**: Botへのイベント数
- **レイテンシ**: 応答時間
- **エラー率**: エラーの発生率
- **CPU使用率**: CPU使用状況
- **メモリ使用率**: メモリ使用状況

### アラートの設定

```bash
# メモリ使用率が80%を超えたらアラート
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="WithGames Bot High Memory" \
  --condition-display-name="Memory > 80%" \
  --condition-threshold-value=0.8 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="${SERVICE_NAME}" AND metric.type="run.googleapis.com/container/memory/utilizations"'
```

## CI/CDデプロイ

GitHub Actions を使用した自動デプロイについては、[CI/CD設定](./CICD.md) を参照してください。

### GitHub Actions での自動デプロイフロー

1. `main` ブランチにプッシュ
2. GitHub Actions がトリガー
3. テスト実行
4. Dockerイメージビルド
5. Artifact Registry にプッシュ
6. Cloud Run にデプロイ
7. 通知（成功/失敗）

## デプロイメントのベストプラクティス

### 1. タグ付けとバージョニング

```bash
# セマンティックバージョニングを使用
git tag v1.0.0
git push origin v1.0.0

# イメージにもタグを付ける
docker build -t ${IMAGE_NAME}:v1.0.0 -t ${IMAGE_NAME}:latest .
```

### 2. カナリアデプロイ

```bash
# 新しいリビジョンに10%のトラフィックを送る
gcloud run services update-traffic ${SERVICE_NAME} \
  --to-revisions=${NEW_REVISION}=10,${OLD_REVISION}=90 \
  --region=${REGION}

# 問題なければ徐々に増やす
gcloud run services update-traffic ${SERVICE_NAME} \
  --to-revisions=${NEW_REVISION}=50,${OLD_REVISION}=50 \
  --region=${REGION}

# 最終的に100%に
gcloud run services update-traffic ${SERVICE_NAME} \
  --to-latest \
  --region=${REGION}
```

### 3. ヘルスチェック

現在のBotには専用のヘルスチェックエンドポイントはありませんが、ログで起動状態を確認できます。

### 4. 環境変数の管理

```bash
# 環境変数を更新
gcloud run services update ${SERVICE_NAME} \
  --update-env-vars="NEW_VAR=value,REMINDER_MINUTES=60" \
  --region=${REGION}

# 環境変数を削除
gcloud run services update ${SERVICE_NAME} \
  --remove-env-vars="OLD_VAR" \
  --region=${REGION}
```

## トラブルシューティング

### デプロイが失敗する

```bash
# ビルドログを確認
gcloud builds list --limit=5

# 最新のビルドの詳細
gcloud builds describe BUILD_ID

# Cloud Run サービスのイベントを確認
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format=yaml
```

### Bot が起動しない

1. **環境変数を確認**
   ```bash
   gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(spec.template.spec.containers[0].env)"
   ```

2. **シークレットを確認**
   ```bash
   gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(spec.template.spec.containers[0].env)"
   ```

3. **サービスアカウントの権限を確認**
   ```bash
   gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(spec.template.spec.serviceAccountName)"
   ```

### コールドスタート問題

```bash
# 最小インスタンス数を増やす（常に稼働）
gcloud run services update ${SERVICE_NAME} \
  --min-instances=1 \
  --region=${REGION}
```

### メモリ不足

```bash
# メモリを増やす
gcloud run services update ${SERVICE_NAME} \
  --memory=1Gi \
  --region=${REGION}
```

## コスト最適化

### リソースの最適化

```bash
# CPU とメモリを最適化
gcloud run services update ${SERVICE_NAME} \
  --cpu=1 \
  --memory=512Mi \
  --region=${REGION}

# 最小インスタンスを0に（アイドル時は課金なし）
# 注意: バックグラウンドタスクがある場合は1以上にする
gcloud run services update ${SERVICE_NAME} \
  --min-instances=0 \
  --region=${REGION}
```

### コスト見積もり

- **Cloud Run**: $0.00002400/vCPU秒、$0.00000250/GiB秒
- **最小インスタンス1の場合**: 月額約 $10-20
- **Firestore**: 読み取り・書き込みベース、月額約 $5-10
- **合計**: 月額約 $15-30（小規模運用の場合）

## 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Build ドキュメント](https://cloud.google.com/build/docs)
- [Artifact Registry ドキュメント](https://cloud.google.com/artifact-registry/docs)
