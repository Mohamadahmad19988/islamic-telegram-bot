#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  Islamic Bot — GitHub Auto-Setup Script
#  Usage: bash setup.sh YOUR_GITHUB_TOKEN YOUR_GITHUB_USERNAME
# ══════════════════════════════════════════════════════════════

set -e

GITHUB_TOKEN="${1:-}"
GITHUB_USER="${2:-}"
REPO_NAME="islamic-telegram-bot"

# ── Validate args ──────────────────────────────────────────────
if [[ -z "$GITHUB_TOKEN" || -z "$GITHUB_USER" ]]; then
  echo ""
  echo "❌  Usage: bash setup.sh GITHUB_TOKEN GITHUB_USERNAME"
  echo ""
  echo "   GITHUB_TOKEN  — Personal Access Token (needs 'repo' scope)"
  echo "   Get one from: https://github.com/settings/tokens/new?scopes=repo"
  echo ""
  exit 1
fi

echo ""
echo "🌙  Islamic Telegram Bot — GitHub Setup"
echo "════════════════════════════════════════"
echo ""

# ── Create GitHub repository ───────────────────────────────────
echo "📦  Creating GitHub repository: $GITHUB_USER/$REPO_NAME ..."

HTTP_CODE=$(curl -s -o /tmp/gh_response.json -w "%{http_code}" \
  -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"بوت تيليجرام إسلامي ينشر تلقائياً في @noraalas\",
    \"private\": false,
    \"auto_init\": false
  }")

if [[ "$HTTP_CODE" == "201" ]]; then
  echo "✅  Repository created successfully."
elif [[ "$HTTP_CODE" == "422" ]]; then
  echo "ℹ️   Repository already exists — will push to existing repo."
else
  echo "❌  Failed to create repository (HTTP $HTTP_CODE)"
  cat /tmp/gh_response.json
  exit 1
fi

REPO_URL="https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git"

# ── Init git & push ────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "📤  Pushing code to GitHub..."

if [[ ! -d ".git" ]]; then
  git init -b main
fi

git config user.email "bot@islamic-telegram-bot.com"
git config user.name "Islamic Bot"

git add -A
git commit -m "🌙 Islamic Telegram Bot — ready for Render deployment" 2>/dev/null || \
  git commit --allow-empty -m "🌙 Update bot files"

if git remote get-url origin &>/dev/null; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

git push -u origin main --force

echo ""
echo "════════════════════════════════════════"
echo "✅  Code pushed successfully!"
echo ""
echo "🚀  Next step — Deploy on Render.com:"
echo ""
echo "   1. Go to: https://render.com/new"
echo "   2. Choose: Web Service"
echo "   3. Connect: github.com/$GITHUB_USER/$REPO_NAME"
echo "   4. Settings:"
echo "      Build:  pip install -r requirements.txt"
echo "      Start:  python3 bot.py"
echo "      Plan:   Free"
echo ""
echo "   5. Add Environment Variables:"
echo "      TELEGRAM_BOT_TOKEN  = (your bot token)"
echo "      TELEGRAM_CHANNEL_ID = @noraalas"
echo "      GEMINI_API_KEY      = (your Gemini key)"
echo ""
echo "   6. Click Deploy! 🌙"
echo "════════════════════════════════════════"
echo ""
