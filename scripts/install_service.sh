#!/bin/bash
# Installation script for English Companion NX systemd service
# Run this on the Jetson Orin NX

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  English Companion NX - Service Installation              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# Check we're in the right directory
if [ ! -f "conversation_prototype.py" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "   cd ~/apps/english-companion-nx"
    exit 1
fi

# Check virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Create with: python3 -m venv .venv --system-site-packages"
    exit 1
fi

# Create systemd user directory if it doesn't exist
SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

# Copy service file
echo "📋 Installing systemd service file..."
cp systemd/english-companion-nx.service "$SYSTEMD_DIR/"
echo "   ✅ Copied to $SYSTEMD_DIR/english-companion-nx.service"

# Reload systemd daemon
echo
echo "🔄 Reloading systemd daemon..."
systemctl --user daemon-reload
echo "   ✅ Daemon reloaded"

# Check service status
echo
echo "📊 Service Status:"
systemctl --user status english-companion-nx --no-pager || true

echo
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Installation Complete!                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "Service Commands:"
echo "  Start service:    systemctl --user start english-companion-nx"
echo "  Stop service:     systemctl --user stop english-companion-nx"
echo "  Service status:   systemctl --user status english-companion-nx"
echo "  View logs:        journalctl --user -u english-companion-nx -f"
echo "  Enable on boot:   systemctl --user enable english-companion-nx"
echo "  Disable on boot:  systemctl --user disable english-companion-nx"
echo
echo "⚠️  NOTE: The service is NOT enabled by default."
echo "   This is intentional - the current prototype is interactive."
echo "   Once Phase 2 (wake word detection) is complete, enable it for 24/7 operation."
echo
echo "To enable auto-start on boot:"
echo "  systemctl --user enable english-companion-nx"
echo "  loginctl enable-linger \$USER"
echo
