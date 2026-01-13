# トラブルシューティングガイド

このドキュメントでは、WithGames Discord Botの一般的な問題と解決方法を説明します。

## 目次

1. [権限エラー](#権限エラー)
2. [デプロイエラー](#デプロイエラー)
3. [その他のエラー](#その他のエラー)

## 権限エラー

### エラー: ボットに適切な権限があることを確認してください

**症状:**
イベント投稿時に権限エラーが発生する。

**解決方法:**

1. **ボットの権限を確認**
   - Discordサーバー設定 → ロール → WithGames Bot
   - 以下の権限が有効になっているか確認:
     - ✅ メッセージを送信
     - ✅ 埋め込みリンク
     - ✅ ファイルを添付
     - ✅ メッセージ履歴を読む
     - ✅ リアクションを追加
     - ✅ 外部の絵文字を使用

2. **チャンネル固有の権限を確認**
   - イベントを投稿したいチャンネル設定を開く
   - 「権限」タブ → WithGames Bot
   - 上記の権限が許可されているか確認

3. **Webhookの権限を確認**
   - Webhook自体には特別な権限は不要
   - Webhookが投稿するチャンネルで「メッセージを送信」権限があれば十分

## デプロイエラー

### GCP Cloud Runでの権限エラー

**症状:**
Cloud Runにデプロイ後、イベント作成時にエラーが発生する。

**解決方法:**

1. **Secret ManagerのWebhook URLを確認**
   ```bash
   # シークレットが存在するか確認
   gcloud secrets describe event-webhook-url

   # シークレットの値を確認（最初の50文字のみ）
   gcloud secrets versions access latest --secret=event-webhook-url | head -c 50
   ```

2. **シークレットが存在しない場合は作成**
   ```bash
   echo -n "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" | \
     gcloud secrets create event-webhook-url \
       --data-file=- \
       --replication-policy="automatic"
   ```

3. **サービスアカウントに権限を付与**
   ```bash
   gcloud secrets add-iam-policy-binding event-webhook-url \
     --member="serviceAccount:withgames-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

4. **Cloud Runサービスを再デプロイ**
   ```bash
   ./scripts/deploy.sh --project-id YOUR_PROJECT_ID
   ```

## その他のエラー

### ボットがオンラインにならない

**解決方法:**

1. **Discord Tokenを確認**
   ```bash
   # .envファイルのDISCORD_TOKENが正しいか確認
   cat .env | grep DISCORD_TOKEN
   ```

2. **ログを確認**
   ```bash
   # エラーメッセージを確認
   tail -n 100 logs/bot.log
   ```

3. **Discord Developer Portalで確認**
   - [Discord Developer Portal](https://discord.com/developers/applications)
   - アプリケーションを選択
   - Bot設定で以下が有効か確認:
     - Presence Intent: オン
     - Server Members Intent: オン
     - Message Content Intent: オン

### イベント作成が完了しない

**解決方法:**

1. **Firestoreの接続を確認**
   ```bash
   # ローカル環境の場合、Firestoreエミュレータが起動しているか確認
   ps aux | grep firestore
   ```

2. **環境変数を確認**
   ```bash
   cat .env | grep GCP_PROJECT_ID
   cat .env | grep GOOGLE_APPLICATION_CREDENTIALS
   ```

3. **サービスアカウントの権限を確認**（本番環境）
   ```bash
   # サービスアカウントにFirestore権限があるか確認
   gcloud projects get-iam-policy YOUR_PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:withgames-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"
   ```

## ログの確認方法

### ローカル環境

```bash
# リアルタイムでログを確認
tail -f logs/bot.log

# エラーのみを確認
grep ERROR logs/bot.log

# 特定のエラーを検索
grep "403 Forbidden" logs/bot.log
```

### GCP Cloud Run

```bash
# 最新のログを確認
gcloud run logs read withgames-bot --region=asia-northeast1 --limit=50

# リアルタイムでログを確認
gcloud run logs tail withgames-bot --region=asia-northeast1

# エラーのみを確認
gcloud run logs read withgames-bot --region=asia-northeast1 --limit=100 | grep ERROR
```

## サポート

問題が解決しない場合は、以下の情報を含めてGitHubでissueを作成してください:

1. エラーメッセージ全文
2. 発生した手順
3. 環境（ローカル/GCP）
4. ログの関連部分（機密情報は除く）

GitHub Issues: https://github.com/anthropics/withgames-bot/issues
