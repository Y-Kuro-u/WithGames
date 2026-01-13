#!/bin/bash

# Cloud Runへのデプロイスクリプト
# Dockerイメージをビルドし、Artifact Registryにプッシュし、Cloud Runにデプロイします

set -e  # エラーが発生したら終了

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト値
REGION="${REGION:-asia-northeast1}"
REPO_NAME="${REPO_NAME:-withgames-bot}"
SERVICE_NAME="${SERVICE_NAME:-withgames-bot}"

# ヘルプメッセージ
show_help() {
    cat << EOF
Cloud Runデプロイスクリプト

使用方法:
    $0 [OPTIONS]

オプション:
    --project-id PROJECT_ID     GCPプロジェクトID（環境変数 PROJECT_ID でも可）
    --region REGION             リージョン（デフォルト: asia-northeast1）
    --tag TAG                   Dockerイメージタグ（デフォルト: git commit hash）
    --no-build                  Dockerイメージのビルドをスキップ
    --no-push                   イメージのプッシュをスキップ
    --help                      このヘルプメッセージを表示

環境変数:
    PROJECT_ID                  GCPプロジェクトID
    REGION                      デプロイ先リージョン
    REPO_NAME                   Artifact Registryリポジトリ名
    SERVICE_NAME                Cloud Runサービス名

例:
    # 基本的な使用方法
    $0 --project-id my-discord-bot-12345

    # 環境変数で指定
    PROJECT_ID="my-discord-bot-12345" $0

    # カスタムタグを指定
    $0 --project-id my-discord-bot-12345 --tag v1.0.0

    # ビルドのみ（デプロイしない）
    $0 --project-id my-discord-bot-12345 --no-push

前提条件:
    - gcloud CLIで認証済み（gcloud auth login）
    - Dockerがインストールされていること
    - GCPセットアップが完了していること（scripts/setup_gcp.sh）

EOF
}

# プログレスインジケーター
show_progress() {
    local message=$1
    echo -e "${BLUE}▶${NC} $message"
}

# 成功メッセージ
show_success() {
    local message=$1
    echo -e "${GREEN}✓${NC} $message"
}

# 警告メッセージ
show_warning() {
    local message=$1
    echo -e "${YELLOW}⚠${NC} $message"
}

# エラーメッセージ
show_error() {
    local message=$1
    echo -e "${RED}❌${NC} $message"
}

# 引数を解析
PROJECT_ID="${PROJECT_ID:-}"
TAG=""
DO_BUILD=true
DO_PUSH=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-build)
            DO_BUILD=false
            shift
            ;;
        --no-push)
            DO_PUSH=false
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            show_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# 必須パラメータのチェック
if [ -z "$PROJECT_ID" ]; then
    show_error "PROJECT_ID is required"
    echo "Set it via environment variable or --project-id flag"
    show_help
    exit 1
fi

# Dockerがインストールされているか確認
if ! command -v docker &> /dev/null; then
    show_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# gcloud CLIがインストールされているか確認
if ! command -v gcloud &> /dev/null; then
    show_error "gcloud CLI is not installed"
    echo "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# プロジェクトを設定
show_progress "Setting GCP project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"
show_success "Project set"

# イメージタグの決定
if [ -z "$TAG" ]; then
    # Gitリポジトリならコミットハッシュを使用
    if git rev-parse --git-dir > /dev/null 2>&1; then
        TAG=$(git rev-parse --short HEAD)
        show_progress "Using git commit hash as tag: $TAG"
    else
        TAG="latest"
        show_warning "Not a git repository, using 'latest' tag"
    fi
fi

# イメージ名
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
IMAGE_TAG="${IMAGE_NAME}:${TAG}"
IMAGE_LATEST="${IMAGE_NAME}:latest"

echo "========================================"
echo "  WithGames Bot - Deployment"
echo "========================================"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE_TAG"
echo "========================================"
echo ""

# Dockerイメージのビルド
if [ "$DO_BUILD" = true ]; then
    show_progress "Building Docker image..."
    docker build \
        -t "$IMAGE_TAG" \
        -t "$IMAGE_LATEST" \
        .
    show_success "Docker image built"
else
    show_warning "Skipping Docker build (--no-build)"
fi

# イメージのプッシュ
if [ "$DO_PUSH" = true ]; then
    show_progress "Pushing image to Artifact Registry..."
    
    # Docker認証の確認
    if ! docker-credential-gcloud list > /dev/null 2>&1; then
        show_progress "Configuring Docker authentication..."
        gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
    fi
    
    docker push "$IMAGE_TAG"
    docker push "$IMAGE_LATEST"
    show_success "Image pushed to Artifact Registry"
else
    show_warning "Skipping image push (--no-push)"
    exit 0
fi

# Cloud Runにデプロイ
show_progress "Deploying to Cloud Run..."

SERVICE_ACCOUNT_EMAIL="withgames-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_TAG" \
    --platform=managed \
    --region="$REGION" \
    --service-account="$SERVICE_ACCOUNT_EMAIL" \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},REMINDER_MINUTES=30,GUILD_ID=886979245409189921" \
    --set-secrets="DISCORD_TOKEN=discord-bot-token:latest,DISCORD_APPLICATION_ID=discord-app-id:latest,EVENT_WEBHOOK_URL=event-webhook-url:latest" \
    --cpu=1 \
    --memory=512Mi \
    --min-instances=1 \
    --max-instances=2 \
    --cpu-boost \
    --no-allow-unauthenticated \
    --timeout=60s \
    --concurrency=80 \
    --quiet

show_success "Deployed to Cloud Run"

# デプロイ情報の取得
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

# 完了メッセージ
echo ""
echo "========================================"
echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
echo "========================================"
echo ""
echo "Service URL: $SERVICE_URL"
echo "Service Name: $SERVICE_NAME"
echo "Image: $IMAGE_TAG"
echo "Region: $REGION"
echo ""
echo "Logs:"
echo "  gcloud run logs tail $SERVICE_NAME --region=$REGION"
echo ""
echo "Console:"
echo "  https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}?project=${PROJECT_ID}"
echo ""

# ログを確認するか尋ねる
read -p "View logs now? (yes/no): " view_logs
if [ "$view_logs" = "yes" ]; then
    gcloud run logs tail "$SERVICE_NAME" --region="$REGION"
fi
