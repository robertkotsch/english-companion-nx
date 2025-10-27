# Git-Based Deployment Workflow
## English Companion NX: Dev Machine → GitHub → Jetson

**Last Updated:** October 27, 2025

---

## 🎯 Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Machine                       │
│  (Windows/Mac/Linux - Your main workstation)               │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ git push origin main
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                       GitHub Repository                      │
│              github.com/<you>/english-companion-nx            │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ git pull (SSH deploy key)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Jetson Orin NX                           │
│              ~/apps/english-companion-nx/                      │
│                  (Production runtime)                        │
└─────────────────────────────────────────────────────────────┘
```

**Principle:** Git is the single source of truth. Jetson is **read-only** from GitHub.

---

## 🔧 Initial Setup

### 1. Development Machine Setup

```bash
# Create project
mkdir english-companion-nx
cd english-companion-nx
git init

# Add remote
git remote add origin git@github.com:<your-username>/english-companion-nx.git

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/
.pytest_cache/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/*.log
*.log

# Data
data/conversations.jsonl
data/conversations.db
data/backups/

# Models (download on Jetson)
models/*.pt
models/*.bin
models/*.pth

# System
.DS_Store
Thumbs.db

# Temporary
tmp/
temp/
*.tmp
EOF

# Create essential files
touch README.md
touch requirements.txt
touch .env.example

# Initial commit
git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main
```

### 2. Create `.env.example` (Template)

```bash
# .env.example - Commit this to Git
# Copy to .env and customize on Jetson

# Ollama
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_MODEL=llama3.1:13b-instruct-q4_0

# Audio
AUDIO_TEMP_DIR=/tmp/companion-audio
AUDIO_SAMPLE_RATE=16000

# Storage
CONVERSATION_LOG=/mnt/nvme/companion/conversations.jsonl
CONVERSATION_BUFFER_INTERVAL=300

# Memory
MEMORY_WARNING_THRESHOLD=0.85
MEMORY_CRITICAL_THRESHOLD=0.95

# Logging
LOG_LEVEL=INFO
LOG_DIR=/mnt/nvme/companion/logs
```

**Note:** Never commit `.env` with real credentials!

### 3. Jetson Setup (One-Time)

**On Jetson:**

```bash
# Generate SSH key (if not exists)
ssh-keygen -t ed25519 -C "jetson-english-companion-nx"

# Display public key
cat ~/.ssh/id_ed25519.pub
```

**Copy the public key, then on GitHub:**
1. Go to: `github.com/<you>/english-companion-nx/settings/keys`
2. Click "Add deploy key"
3. Paste public key
4. Title: "Jetson Orin NX - English Companion NX"
5. ✅ Check "Allow write access" if you want to commit from Jetson (optional)
6. Click "Add key"

**Back on Jetson:**

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone repository (SSH)
git clone git@github.com:<your-username>/english-companion-nx.git
cd english-companion-nx

# Verify connection
git remote -v
# Should show: git@github.com:<your-username>/english-companion-nx.git

# Configure Git
git config --local user.name "Jetson"
git config --local user.email "jetson@companion"

# Create Python virtual environment
python3 -m venv .venv

# Activate and install dependencies
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
nano .env  # Customize for Jetson

# Secure .env
chmod 600 .env

# Create data directories
mkdir -p /mnt/nvme/companion/{logs,backups}
mkdir -p /tmp/companion-audio
```

---

## 🔄 Daily Development Workflow

### On Development Machine

```bash
# 1. Make changes
cd ~/projects/english-companion-nx
code .  # Or your editor

# Edit files...
# - src/audio/recorder.py
# - src/conversation/manager.py
# - etc.

# 2. Test locally (if possible)
source .venv/bin/activate
python -m pytest tests/

# 3. Commit changes
git add .
git commit -m "feat: Add conversation context pruning"

# 4. Push to GitHub
git push origin main
```

### On Jetson (Update & Restart)

**Manual update:**
```bash
cd ~/apps/english-companion-nx

# Pull latest changes
git pull origin main

# Update dependencies (if requirements.txt changed)
source .venv/bin/activate
pip install -r requirements.txt

# Restart service
systemctl --user restart english-companion-nx

# Check status
systemctl --user status english-companion-nx

# View logs
journalctl --user -u english-companion-nx -f
```

**Or use automated script:**
```bash
# Create deployment script
cat > ~/apps/english-companion-nx/deploy.sh << 'EOF'
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
systemctl --user is-active english-companion-nx && echo "Service is running!" || echo "❌ Service failed!"

echo "📊 Recent logs:"
journalctl --user -u english-companion-nx -n 10 --no-pager

echo "✨ Deployment complete!"
EOF

chmod +x ~/apps/english-companion-nx/deploy.sh

# Run deployment
~/apps/english-companion-nx/deploy.sh
```

---

## 📝 Makefile Integration

Add to your `Makefile` on Jetson:

```makefile
# Deployment targets

.PHONY: deploy-update
deploy-update:
	@echo "🚀 Deploying updates from GitHub..."
	git pull origin main
	.venv/bin/pip install -q -r requirements.txt
	systemctl --user restart english-companion-nx
	@echo "✅ Deployment complete!"

.PHONY: deploy-status
deploy-status:
	@echo "📊 Service Status:"
	systemctl --user status english-companion-nx

.PHONY: deploy-logs
deploy-logs:
	@echo "📋 Recent Logs:"
	journalctl --user -u english-companion-nx -n 50 --no-pager

.PHONY: deploy-check
deploy-check:
	@echo "🔍 Pre-deployment checks:"
	@echo "Git status:"
	@git status
	@echo "\nPython environment:"
	@.venv/bin/python --version
	@echo "\nOllama status:"
	@systemctl is-active ollama || echo "❌ Ollama not running"
	@echo "\nDisk space:"
	@df -h /mnt/nvme | grep nvme
	@echo "\nMemory:"
	@free -h | grep Mem

.PHONY: deploy-rollback
deploy-rollback:
	@echo "⏪ Rolling back to previous version..."
	git log --oneline -n 5
	@read -p "Enter commit hash to rollback to: " commit; \
	git reset --hard $$commit
	systemctl --user restart english-companion-nx
	@echo "✅ Rollback complete!"
```

**Usage:**
```bash
# Quick update
make deploy-update

# Check before deploying
make deploy-check

# View status
make deploy-status

# View logs
make deploy-logs

# Rollback if needed
make deploy-rollback
```

---

## 🔐 Security Best Practices

### What to Commit ✅

```
✅ Source code
✅ Configuration templates (.env.example)
✅ Documentation
✅ Requirements files
✅ Scripts
✅ Tests
✅ .gitignore
```

### What NOT to Commit ❌

```
❌ .env (actual credentials)
❌ API keys
❌ Conversation logs
❌ Model files (download separately)
❌ Virtual environment (.venv/)
❌ __pycache__/
❌ Personal data
```

### Protect Secrets

```bash
# On Jetson, secure .env file
chmod 600 .env

# Verify it's gitignored
git check-ignore .env
# Should output: .env

# If accidentally committed
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

---

## 🚨 Emergency Procedures

### Service Fails After Update

```bash
# 1. Check logs
journalctl --user -u english-companion-nx -n 50

# 2. Rollback to last working version
cd ~/apps/english-companion-nx
git log --oneline -n 10
git reset --hard <last-good-commit>
systemctl --user restart english-companion-nx

# 3. Report issue on development machine
# Fix bug, push new commit
```

### Lost Connection to GitHub

```bash
# Test SSH connection
ssh -T git@github.com
# Should see: "Hi <username>! You've successfully authenticated..."

# If fails, check SSH key
cat ~/.ssh/id_ed25519.pub
# Re-add to GitHub deploy keys if needed

# Verify remote URL
git remote -v
# Should be: git@github.com:...
```

### Merge Conflicts (Rare)

```bash
# If you somehow edited on Jetson and dev machine
git pull origin main
# If conflicts:
git status  # See conflicted files
nano <conflicted-file>  # Resolve manually
git add <resolved-file>
git commit -m "Resolve merge conflict"
git push origin main
```

**Best practice:** Only edit on dev machine!

---

## 🔄 Branch Strategy

### Simple (Recommended for Solo Development)

```
main branch only
├── All development happens here
├── Test locally before pushing
└── Jetson always pulls from main
```

### Advanced (For Experimentation)

```
main          (production)
├── dev       (testing)
└── feature/* (experiments)
```

**On dev machine:**
```bash
# Create feature branch
git checkout -b feature/voice-cloning

# Work on feature...
git commit -m "Add voice cloning"

# Merge when ready
git checkout main
git merge feature/voice-cloning
git push origin main
```

**On Jetson:**
```bash
# Stay on main (production)
git pull origin main

# Or test dev branch
git checkout dev
git pull origin dev
systemctl --user restart english-companion-nx
```

---

## 📊 Deployment Checklist

### Before Pushing to GitHub

- [ ] Code tested locally (if possible)
- [ ] Tests pass (`pytest`)
- [ ] No sensitive data in code
- [ ] `.env` not committed
- [ ] `requirements.txt` updated
- [ ] Commit message descriptive
- [ ] Changes documented in code

### After Pulling on Jetson

- [ ] Git pull successful
- [ ] Dependencies installed
- [ ] Service restarted
- [ ] Service running (check status)
- [ ] No errors in logs
- [ ] Quick functionality test (if possible)

---

## 🛠️ Useful Git Commands

```bash
# Check current status
git status

# View commit history
git log --oneline -n 10

# See what changed
git diff

# Discard local changes
git restore <file>
git restore .  # All files

# View remote info
git remote show origin

# Update from GitHub
git fetch origin
git pull origin main

# Force pull (discard local changes)
git fetch origin
git reset --hard origin/main

# Check which branch
git branch

# View last commit
git show HEAD
```

---

## 🔍 Troubleshooting

### Problem: `git pull` fails with "Permission denied"

**Solution:**
```bash
# Test SSH connection
ssh -T git@github.com

# If fails, check SSH key exists
ls -la ~/.ssh/id_ed25519*

# If missing, regenerate
ssh-keygen -t ed25519 -C "jetson-english-companion-nx"

# Add public key to GitHub deploy keys
cat ~/.ssh/id_ed25519.pub
```

### Problem: `git pull` says "Already up to date" but you know there are updates

**Solution:**
```bash
# Force fetch
git fetch --all

# Check remote commits
git log origin/main --oneline -n 5

# Hard reset to remote
git reset --hard origin/main
```

### Problem: Local changes prevent pull

**Solution:**
```bash
# Stash local changes
git stash

# Pull updates
git pull origin main

# Reapply local changes (if needed)
git stash pop

# Or discard local changes permanently
git reset --hard HEAD
git pull origin main
```

### Problem: Service won't start after update

**Solution:**
```bash
# Check what changed
git log -1 --stat

# Check logs for errors
journalctl --user -u english-companion-nx -n 50

# Rollback
git reset --hard HEAD~1
systemctl --user restart english-companion-nx

# Fix on dev machine, push new commit
```

---

## 📈 Monitoring Deployments

### Track Deployment History

```bash
# Create deployment log
cat >> ~/deployment_log.txt << EOF
$(date): Deployed commit $(git rev-parse --short HEAD)
EOF

# View deployment history
cat ~/deployment_log.txt
```

### Automated Deployment Logging

Add to `deploy.sh`:

```bash
# Log deployment
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployed $(git rev-parse --short HEAD): $(git log -1 --pretty=%B)" >> ~/.deployment_history
```

---

## 🎯 Best Practices Summary

### ✅ DO

1. **Always develop on dev machine**
2. **Test before pushing** (when possible)
3. **Use meaningful commit messages**
4. **Keep .env out of Git** (use .env.example)
5. **Pull before restarting** service
6. **Check logs after deployment**
7. **Use deploy scripts** (automation)
8. **Document breaking changes**

### ❌ DON'T

1. **Don't edit code on Jetson** (Git is source of truth)
2. **Don't commit secrets** (API keys, passwords)
3. **Don't commit large files** (models, data)
4. **Don't force push** (unless you know why)
5. **Don't skip testing** (avoid breaking prod)
6. **Don't commit .venv/** (bloat)

---

## 📚 Quick Reference

### Common Workflow

```bash
# On dev machine
git add .
git commit -m "feat: Add feature X"
git push origin main

# On Jetson
make deploy-update
# Or:
cd ~/apps/english-companion-nx && ./deploy.sh
```

### Emergency Rollback

```bash
# On Jetson
cd ~/apps/english-companion-nx
git reset --hard HEAD~1
systemctl --user restart english-companion-nx
```

### Check Everything

```bash
# On Jetson
make deploy-check
# Shows: Git status, Python version, Ollama status, disk, memory
```

---

## 🎓 Related Documentation

- [CLAUDE.md](./CLAUDE.md) - Development guide
- [Jetson Deployment Guide](./jetson-orin-nx-deployment-guide.md) - General patterns
- [Infrastructure Comparison](./infrastructure-comparison.md) - Architecture decisions

---

**Remember:** Git is your safety net. Commit often, push regularly, pull before restarting. This workflow keeps production stable and development flexible! 🚀

**Last Updated:** October 27, 2025  
**Workflow:** Dev Machine → GitHub → Jetson (read-only)
