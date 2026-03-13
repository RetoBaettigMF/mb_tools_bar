#!/bin/bash
# install-service.sh - Install systemd service for crm-chat
# Run this with sudo: sudo bash install-service.sh

set -e

echo "Installing crm-chat systemd service..."

cp crm-chat.service /etc/systemd/system/
chmod 644 /etc/systemd/system/crm-chat.service
systemctl daemon-reload
systemctl enable crm-chat
systemctl start crm-chat

echo ""
echo "Service installed and started!"
echo "Status:"
systemctl status crm-chat --no-pager -l
