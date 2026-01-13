#!/bin/bash

# ローカル開発用のBot起動スクリプト
# Firestore エミュレータを起動し、その後Botを起動します

set -e  # エラーが発生したら終了

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ヘルプメッセージ
show_help() {
    cat << EOF
ローカル開発用のDiscord Bot起動スクリプト

使用方法:
    $0 [OPTIONS]

オプション:
    --emulator      Firestoreエミュレータを使用（デフォルト）
    --production    本番Firestoreを使用（警告: 実際のデータベースを使用）
    --docker        docker-composeを使用してエミュレータとBotを起動
    --help          このヘルプメッセージを表示

例:
    # Firestoreエミュレータを使用（推奨）
    $0 --emulator

    # 本番Firestoreを使用（注意）
    $0 --production

    # Dockerを使用
    $0 --docker

環境変数（.envファイルまたはexportで設定）:
    DISCORD_TOKEN              必須: Discord Bot Token
    DISCORD_APPLICATION_ID     オプション: Discord Application ID
    REMINDER_MINUTES          オプション: リマインダー時間（デフォルト: 30分）
    FIRESTORE_EMULATOR_HOST   自動設定: localhost:8080
    GCP_PROJECT_ID            自動設定: demo-project（エミュレータモード）
    ENVIRONMENT               自動設定: development

EOF
}

# エミュレータのプロセスを保存
EMULATOR_PID=""

# クリーンアップ関数
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    
    # Botプロセスを終了
    if [ -n "$BOT_PID" ]; then
        echo "Stopping bot (PID: $BOT_PID)..."
        kill $BOT_PID 2>/dev/null || true
    fi
    
    # エミュレータを終了
    if [ -n "$EMULATOR_PID" ]; then
        echo "Stopping Firestore emulator (PID: $EMULATOR_PID)..."
        kill $EMULATOR_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Cleanup completed${NC}"
    exit 0
}

# Ctrl+C で終了時にクリーンアップ
trap cleanup SIGINT SIGTERM

# 引数を解析
MODE="emulator"

for arg in "$@"; do
    case $arg in
        --emulator)
            MODE="emulator"
            ;;
        --production)
            MODE="production"
            ;;
        --docker)
            MODE="docker"
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            show_help
            exit 1
            ;;
    esac
done

# プロジェクトルートに移動
cd "$PROJECT_ROOT"

# .envファイルを読み込む
if [ -f .env ]; then
    echo -e "${GREEN}✓ Loading .env file${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
fi

# DISCORD_TOKENが設定されているか確認
if [ -z "$DISCORD_TOKEN" ]; then
    echo -e "${RED}❌ DISCORD_TOKEN is not set${NC}"
    echo "Please create a .env file with your Discord token:"
    echo '  echo "DISCORD_TOKEN=your-token-here" > .env'
    exit 1
fi

# Dockerモード
if [ "$MODE" == "docker" ]; then
    echo -e "${GREEN}Starting with Docker Compose...${NC}"
    echo "Press Ctrl+C to stop"
    docker-compose up
    exit 0
fi

# 本番モード
if [ "$MODE" == "production" ]; then
    echo -e "${RED}⚠️  WARNING: Using production Firestore${NC}"
    read -p "Are you sure you want to use production database? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
    
    # 本番環境変数を設定
    export ENVIRONMENT="production"
    
    # GCP_PROJECT_IDが設定されているか確認
    if [ -z "$GCP_PROJECT_ID" ]; then
        echo -e "${RED}❌ GCP_PROJECT_ID is not set${NC}"
        echo 'Please set it in .env: echo "GCP_PROJECT_ID=your-project-id" >> .env'
        exit 1
    fi
    
    echo -e "${GREEN}✓ Using production Firestore (Project: $GCP_PROJECT_ID)${NC}"
    
    # Botを起動
    echo -e "${GREEN}Starting bot...${NC}"
    uv run python -m src.main
    exit 0
fi

# エミュレータモード（デフォルト）
echo -e "${GREEN}Starting Firestore Emulator...${NC}"

# エミュレータが既に起動しているか確認
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Firestore emulator is already running on port 8080${NC}"
    read -p "Use existing emulator? (yes/no): " use_existing
    if [ "$use_existing" != "yes" ]; then
        echo "Please stop the existing emulator first:"
        echo "  pkill -f firestore"
        exit 1
    fi
else
    # gcloud CLIがインストールされているか確認
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is not installed${NC}"
        echo "Please install gcloud CLI:"
        echo "  https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Firestoreエミュレータがインストールされているか確認
    if ! gcloud emulators firestore --help &> /dev/null; then
        echo -e "${YELLOW}Installing Firestore emulator...${NC}"
        gcloud components install cloud-firestore-emulator
    fi
    
    # エミュレータをバックグラウンドで起動
    echo "Starting emulator on port 8080..."
    gcloud emulators firestore start --host-port=localhost:8080 > /dev/null 2>&1 &
    EMULATOR_PID=$!
    
    # エミュレータが起動するまで待機
    echo -n "Waiting for emulator to start"
    for i in {1..30}; do
        if curl -s http://localhost:8080 > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}✓ Firestore emulator started (PID: $EMULATOR_PID)${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    if ! curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo ""
        echo -e "${RED}❌ Failed to start Firestore emulator${NC}"
        cleanup
        exit 1
    fi
fi

# 環境変数を設定
export FIRESTORE_EMULATOR_HOST="localhost:8080"
export GCP_PROJECT_ID="demo-project"
export ENVIRONMENT="development"

echo ""
echo -e "${GREEN}✓ Environment configured:${NC}"
echo "  FIRESTORE_EMULATOR_HOST=$FIRESTORE_EMULATOR_HOST"
echo "  GCP_PROJECT_ID=$GCP_PROJECT_ID"
echo "  ENVIRONMENT=$ENVIRONMENT"
echo ""

# Botを起動
echo -e "${GREEN}Starting bot...${NC}"
echo "Press Ctrl+C to stop both emulator and bot"
echo ""
echo "----------------------------------------"

# Botを起動してPIDを保存
uv run python -m src.main &
BOT_PID=$!

# Botプロセスが終了するまで待機
wait $BOT_PID

# 正常終了時もクリーンアップ
cleanup
