#!/bin/bash
set -e

echo "🚀 Deploying English Companion NX updates..."

cd ~/apps/english-companion-nx

# Pull latest
echo "📥 Pulling from GitHub..."
git pull origin main

# Update dependencies
echo "📦 Updating dependencies..."
source .venv/bin/activate
pip install -q -r requirements.txt

# Restart service
echo "🔄 Restarting service..."
systemctl --user restart english-companion-nx

# Wait for startup
sleep 3

# Check status
echo "✅ Checking status..."
if systemctl --user is-active english-companion-nx > /dev/null; then
    echo "✨ Service is running!"
else
    echo "❌ Service failed to start!"
    exit 1
fi

echo "📊 Recent logs:"
journalctl --user -u english-companion-nx -n 10 --no-pager

echo ""
echo "✨ Deployment complete!"
