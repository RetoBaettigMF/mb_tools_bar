#!/bin/bash
# update-crm-chat.sh - Update script for crm-chat application
# Usage: ./update-crm-chat.sh

set -e

APP_DIR="/home/reto/Development/mb_tools_bar/crm-chat"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "=== CRM Chat Update ==="
echo "Working directory: $APP_DIR"

# Pull latest changes (if using git)
if [ -d "$APP_DIR/.git" ]; then
    echo "Pulling latest changes from git..."
    cd "$APP_DIR"
    git pull
fi

# Update backend dependencies
echo "Installing/updating Python dependencies..."
cd "$BACKEND_DIR"
pip3 install -r requirements.txt --break-system-packages --quiet

# Update and build frontend
echo "Installing/updating Node dependencies..."
cd "$FRONTEND_DIR"
npm install

echo "Building frontend for production..."
npm run build

# Restart the service
echo "Restarting crm-chat service..."
sudo systemctl restart crm-chat

echo ""
echo "=== Update complete ==="
echo "Service status:"
sudo systemctl status crm-chat --no-pager -l
