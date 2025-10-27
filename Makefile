.PHONY: help deploy-update deploy-status deploy-logs deploy-check deploy-rollback

help:
	@echo "English Companion NX - Deployment Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  deploy-update    - Pull latest changes and restart service"
	@echo "  deploy-status    - Show service status"
	@echo "  deploy-logs      - View recent logs"
	@echo "  deploy-check     - Run pre-deployment checks"
	@echo "  deploy-rollback  - Rollback to previous version"

deploy-update:
	@echo "🚀 Deploying updates from GitHub..."
	git pull origin main
	.venv/bin/pip install -q -r requirements.txt
	systemctl --user restart english-companion-nx
	@echo "✅ Deployment complete!"

deploy-status:
	@echo "📊 Service Status:"
	systemctl --user status english-companion-nx

deploy-logs:
	@echo "📋 Recent Logs:"
	journalctl --user -u english-companion-nx -n 50 --no-pager

deploy-check:
	@echo "🔍 Pre-deployment checks:"
	@echo "Git status:"
	@git status
	@echo ""
	@echo "Python environment:"
	@.venv/bin/python --version
	@echo ""
	@echo "Ollama status:"
	@systemctl is-active ollama || echo "❌ Ollama not running"
	@echo ""
	@echo "Disk space (NVMe):"
	@df -h /mnt/nvme 2>/dev/null || echo "NVMe not mounted"
	@echo ""
	@echo "Memory:"
	@free -h | grep Mem

deploy-rollback:
	@echo "⏪ Rolling back to previous version..."
	@git log --oneline -n 5
	@read -p "Enter commit hash to rollback to: " commit; \
	git reset --hard $$commit
	systemctl --user restart english-companion-nx
	@echo "✅ Rollback complete!"
