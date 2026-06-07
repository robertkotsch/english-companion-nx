#!/bin/bash
# Quick setup script to add English Companion shortcuts to .bashrc on Jetson

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  English Companion NX - Shortcuts Setup"
echo "═══════════════════════════════════════════════════════"
echo ""

# Add all aliases to .bashrc
cat >> ~/.bashrc << 'EOF'

# ═══════════════════════════════════════════════════════
# English Companion NX - Quick Shortcuts
# ═══════════════════════════════════════════════════════

# Go to project and activate venv
alias ec='cd ~/apps/english-companion-nx && source .venv/bin/activate'

# Run voice assistant directly
alias ecrun='cd ~/apps/english-companion-nx && source .venv/bin/activate && python voice_assistant.py'

# View service logs (live)
alias eclogs='journalctl --user -u english-companion-nx -f'

# View service status
alias ecstatus='systemctl --user status english-companion-nx'

# Git pull latest changes
alias ecupdate='cd ~/apps/english-companion-nx && git pull'

# Service control shortcuts
alias ecstart='systemctl --user start english-companion-nx'
alias ecstop='systemctl --user stop english-companion-nx'
alias ecrestart='systemctl --user restart english-companion-nx'

# Quick test commands
alias ectest='cd ~/apps/english-companion-nx && source .venv/bin/activate && python tests/test_audio.py'
alias ecwake='cd ~/apps/english-companion-nx && source .venv/bin/activate && python tests/test_wake_word.py basic 30'

# Monitor resources
alias ecmem='free -h && echo "" && nvidia-smi'
alias ectemp='cat /sys/class/thermal/thermal_zone*/temp | awk '\''{print $1/1000"°C"}'\'''

EOF

echo "✅ Shortcuts added to ~/.bashrc!"
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Available shortcuts:"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  🏠 Navigation & Activation:"
echo "     ec          - Go to project and activate venv"
echo "     ecrun       - Run voice assistant directly"
echo ""
echo "  🔧 Service Control:"
echo "     ecstart     - Start the service"
echo "     ecstop      - Stop the service"
echo "     ecrestart   - Restart the service"
echo "     ecstatus    - View service status"
echo "     eclogs      - View service logs (live)"
echo ""
echo "  🔄 Updates & Testing:"
echo "     ecupdate    - Git pull latest changes"
echo "     ectest      - Test audio hardware"
echo "     ecwake      - Test wake word detection (30s)"
echo ""
echo "  📊 Monitoring:"
echo "     ecmem       - View memory & GPU usage"
echo "     ectemp      - View CPU/GPU temperatures"
echo ""
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "To use these shortcuts now, run:"
echo "  source ~/.bashrc"
echo ""
echo "Or just log out and log back in."
echo ""
