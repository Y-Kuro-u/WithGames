#!/bin/bash

# GCP初期セットアップスクリプト
# このスクリプトは以下を自動化します:
# 1. GCPプロジェクトの作成（オプション）
# 2. 必要なAPIの有効化
# 3. Firestoreデータベースの作成
# 4. サービスアカウントの作成とIAM権限付与
# 5. Artifact Registryリポジトリの作成
# 6. Secret Managerでのシークレット保存

set -e  # エラーが発生したら終了

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト値
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="withgames-bot-sa"
REPO_NAME="withgames-bot"
DATABASE_ID="(default)"

# ヘルプメッセージ
show_help() {
    cat << EOF
GCP初期セットアップスクリプト

使用方法:
    $0 [OPTIONS]

オプション:
    --project-id PROJECT_ID     必須: GCPプロジェクトID
    --create-project            新しいプロジェクトを作成
    --region REGION             リージョン（デフォルト: asia-northeast1）
    --discord-token TOKEN       Discord Bot Token（Secret Managerに保存）
    --discord-app-id APP_ID     Discord Application ID（Secret Managerに保存）
    --webhook-url URL           Event Webhook URL（Secret Managerに保存、オプション）
    --skip-billing             課金の設定をスキップ
    --help                      このヘルプメッセージを表示

例:
    # 既存のプロジェクトでセットアップ
    $0 --project-id my-discord-bot-12345 --discord-token "YOUR_TOKEN"

    # 新しいプロジェクトを作成してセットアップ
    $0 --project-id my-discord-bot-12345 --create-project --discord-token "YOUR_TOKEN"

    # リージョンを指定
    $0 --project-id my-discord-bot-12345 --region us-central1 --discord-token "YOUR_TOKEN"

前提条件:
    - gcloud CLIがインストールされていること
    - gcloud auth loginで認証済みであること
    - プロジェクト作成時は課金アカウントが必要

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
PROJECT_ID=""
CREATE_PROJECT=false
DISCORD_TOKEN=""
DISCORD_APP_ID=""
WEBHOOK_URL=""
SKIP_BILLING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --create-project)
            CREATE_PROJECT=true
            shift
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --discord-token)
            DISCORD_TOKEN="$2"
            shift 2
            ;;
        --discord-app-id)
            DISCORD_APP_ID="$2"
            shift 2
            ;;
        --webhook-url)
            WEBHOOK_URL="$2"
            shift 2
            ;;
        --skip-billing)
            SKIP_BILLING=true
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
    show_help
    exit 1
fi

# gcloud CLIがインストールされているか確認
if ! command -v gcloud &> /dev/null; then
    show_error "gcloud CLI is not installed"
    echo "Please install gcloud CLI:"
    echo "  https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 認証確認
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    show_error "Not authenticated with gcloud"
    echo "Please run: gcloud auth login"
    exit 1
fi

echo "========================================"
echo "  WithGames Bot - GCP Setup"
echo "========================================"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT_NAME"
echo "========================================"
echo ""

# プロジェクト作成（オプション）
if [ "$CREATE_PROJECT" = true ]; then
    show_progress "Creating GCP project: $PROJECT_ID"
    
    if gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        show_warning "Project $PROJECT_ID already exists"
    else
        gcloud projects create "$PROJECT_ID" --name="WithGames Discord Bot"
        show_success "Project created"
    fi
    
    # 課金アカウントの設定
    if [ "$SKIP_BILLING" = false ]; then
        show_progress "Checking billing accounts..."
        BILLING_ACCOUNT=$(gcloud billing accounts list --filter=open=true --format="value(name)" --limit=1)
        
        if [ -z "$BILLING_ACCOUNT" ]; then
            show_warning "No active billing account found"
            echo "Please link a billing account manually:"
            echo "  https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
        else
            show_progress "Linking billing account..."
            gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT"
            show_success "Billing account linked"
        fi
    fi
fi

# プロジェクトを選択
show_progress "Setting current project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"
show_success "Project set"

# 必要なAPIを有効化
show_progress "Enabling required APIs..."
APIS=(
    "firestore.googleapis.com"
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "  - $api"
    gcloud services enable "$api" --quiet
done
show_success "APIs enabled"

# Firestoreデータベースの作成
show_progress "Creating Firestore database..."
if gcloud firestore databases describe --database="$DATABASE_ID" &> /dev/null; then
    show_warning "Firestore database already exists"
else
    gcloud firestore databases create \
        --location="$REGION" \
        --type=firestore-native \
        --quiet
    show_success "Firestore database created"
fi

# サービスアカウントの作成
show_progress "Creating service account: $SERVICE_ACCOUNT_NAME"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" &> /dev/null; then
    show_warning "Service account already exists"
else
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="WithGames Bot Service Account" \
        --description="Service account for WithGames Discord Bot on Cloud Run"
    show_success "Service account created"
fi

# IAM権限の付与
show_progress "Granting IAM permissions..."
ROLES=(
    "roles/datastore.user"
    "roles/secretmanager.secretAccessor"
    "roles/logging.logWriter"
    "roles/cloudtrace.agent"
    "roles/monitoring.metricWriter"
)

for role in "${ROLES[@]}"; do
    echo "  - $role"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role" \
        --quiet > /dev/null
done
show_success "IAM permissions granted"

# Artifact Registryリポジトリの作成
show_progress "Creating Artifact Registry repository: $REPO_NAME"
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &> /dev/null; then
    show_warning "Artifact Registry repository already exists"
else
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Docker images for WithGames Bot"
    show_success "Artifact Registry repository created"
fi

# Docker認証の設定
show_progress "Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
show_success "Docker authentication configured"

# Secret Managerでシークレットを保存
if [ -n "$DISCORD_TOKEN" ]; then
    show_progress "Storing Discord Bot Token in Secret Manager..."
    
    if gcloud secrets describe discord-bot-token &> /dev/null; then
        show_warning "Secret 'discord-bot-token' already exists, creating new version..."
        echo -n "$DISCORD_TOKEN" | gcloud secrets versions add discord-bot-token --data-file=-
    else
        echo -n "$DISCORD_TOKEN" | gcloud secrets create discord-bot-token \
            --data-file=- \
            --replication-policy="automatic"
        
        # サービスアカウントにアクセス権限を付与
        gcloud secrets add-iam-policy-binding discord-bot-token \
            --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
            --role="roles/secretmanager.secretAccessor" \
            --quiet
    fi
    show_success "Discord Bot Token stored"
fi

if [ -n "$DISCORD_APP_ID" ]; then
    show_progress "Storing Discord Application ID in Secret Manager..."

    if gcloud secrets describe discord-app-id &> /dev/null; then
        show_warning "Secret 'discord-app-id' already exists, creating new version..."
        echo -n "$DISCORD_APP_ID" | gcloud secrets versions add discord-app-id --data-file=-
    else
        echo -n "$DISCORD_APP_ID" | gcloud secrets create discord-app-id \
            --data-file=- \
            --replication-policy="automatic"

        # サービスアカウントにアクセス権限を付与
        gcloud secrets add-iam-policy-binding discord-app-id \
            --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
            --role="roles/secretmanager.secretAccessor" \
            --quiet
    fi
    show_success "Discord Application ID stored"
fi

if [ -n "$WEBHOOK_URL" ]; then
    show_progress "Storing Event Webhook URL in Secret Manager..."

    if gcloud secrets describe event-webhook-url &> /dev/null; then
        show_warning "Secret 'event-webhook-url' already exists, creating new version..."
        echo -n "$WEBHOOK_URL" | gcloud secrets versions add event-webhook-url --data-file=-
    else
        echo -n "$WEBHOOK_URL" | gcloud secrets create event-webhook-url \
            --data-file=- \
            --replication-policy="automatic"

        # サービスアカウントにアクセス権限を付与
        gcloud secrets add-iam-policy-binding event-webhook-url \
            --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
            --role="roles/secretmanager.secretAccessor" \
            --quiet
    fi
    show_success "Event Webhook URL stored"
fi

# 予算アラートの設定（オプション）
if [ "$SKIP_BILLING" = false ]; then
    show_progress "Setting up budget alert (optional)..."
    echo "To set up budget alerts, visit:"
    echo "  https://console.cloud.google.com/billing/budget?project=$PROJECT_ID"
    echo ""
    echo "Recommended budget: $10-20/month for small-scale operation"
fi

# セットアップ完了
echo ""
echo "========================================"
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Build and push Docker image:"
echo "   docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/withgames-bot:latest ."
echo "   docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/withgames-bot:latest"
echo ""
echo "2. Deploy to Cloud Run:"
echo "   gcloud run deploy withgames-bot \\"
echo "     --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/withgames-bot:latest \\"
echo "     --platform=managed \\"
echo "     --region=${REGION} \\"
echo "     --service-account=$SERVICE_ACCOUNT_EMAIL \\"
echo "     --set-env-vars=\"ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID}\" \\"
echo "     --set-secrets=\"DISCORD_TOKEN=discord-bot-token:latest,DISCORD_APPLICATION_ID=discord-app-id:latest,EVENT_WEBHOOK_URL=event-webhook-url:latest\" \\"
echo "     --min-instances=1 \\"
echo "     --no-allow-unauthenticated"
echo ""
echo "Or use the deploy script:"
echo "   ./scripts/deploy.sh"
echo ""
echo "3. Sync Discord commands:"
echo "   uv run python scripts/sync_commands.py --guild-id YOUR_GUILD_ID"
echo ""
echo "For more details, see:"
echo "  - docs/DEPLOYMENT.md"
echo "  - docs/GCP_SETUP.md"
echo ""

# 環境変数のエクスポート（参考用）
echo "Environment variables for reference:"
echo "  export PROJECT_ID=\"$PROJECT_ID\""
echo "  export REGION=\"$REGION\""
echo "  export SERVICE_ACCOUNT_EMAIL=\"$SERVICE_ACCOUNT_EMAIL\""
echo "  export IMAGE_NAME=\"${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/withgames-bot\""
echo ""
