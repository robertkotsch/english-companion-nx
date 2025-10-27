# Deployment Setup Guide
## English Companion NX: GitHub → Jetson Workflow

**Created:** October 27, 2025
**Your GitHub Username:** robertkotsch

---

## 📋 Quick Setup Checklist

### Step 1: Push to GitHub (Do This Now)

On your **development machine** (where you are now):

```bash
# Add GitHub remote (replace with your actual repo URL)
git remote add origin git@github.com:robertkotsch/english-companion-nx.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** If you haven't created the GitHub repository yet:
1. Go to https://github.com/new
2. Repository name: `english-companion-nx`
3. Keep it **Private** (recommended for personal AI project)
4. **Don't** initialize with README (we already have one)
5. Click "Create repository"
6. Then run the commands above

---

### Step 2: Set Up Jetson (On Your Jetson Orin NX)

#### 2.1 Generate SSH Deploy Key

```bash
# On Jetson, generate SSH key if not exists
ssh-keygen -t ed25519 -C "jetson-english-companion-nx"

# Display public key
cat ~/.ssh/id_ed25519.pub
```

**Copy the entire output** (starts with `ssh-ed25519 ...`)

#### 2.2 Add Deploy Key to GitHub

1. Go to: https://github.com/robertkotsch/english-companion-nx/settings/keys
2. Click "Add deploy key"
3. Title: `Jetson Orin NX - English Companion`
4. Paste the public key
5. ✅ Check "Allow write access" (optional, only if you want to commit from Jetson)
6. Click "Add key"

#### 2.3 Test SSH Connection

```bash
# On Jetson, test GitHub connection
ssh -T git@github.com
# Should see: "Hi robertkotsch! You've successfully authenticated..."
```

#### 2.4 Clone Repository

```bash
# On Jetson, create app directory
mkdir -p ~/apps
cd ~/apps

# Clone repository (SSH)
git clone git@github.com:robertkotsch/english-companion-nx.git
cd english-companion-nx

# Verify connection
git remote -v
# Should show: git@github.com:robertkotsch/english-companion-nx.git
```

#### 2.5 Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements-jetson.txt
```

#### 2.6 Configure Environment

```bash
# Create .env from template
cp .env.example .env

# Edit with your settings
nano .env

# Secure the file
chmod 600 .env
```

**Important settings to configure in `.env`:**
- `OLLAMA_HOST` - Keep as localhost if running Ollama locally
- `CONVERSATION_LOG` - Verify NVMe mount point exists
- `LOG_DIR` - Verify NVMe mount point exists

#### 2.7 Create Data Directories

```bash
# Create NVMe storage directories
sudo mkdir -p /mnt/nvme/companion/{logs,backups}
sudo chown -R $USER:$USER /mnt/nvme/companion

# Create tmpfs directory for audio
mkdir -p /tmp/companion-audio
```

---

### Step 3: Daily Development Workflow

#### On Development Machine

```bash
# 1. Make changes to code
# 2. Test locally (if possible)

# 3. Commit and push
git add .
git commit -m "feat: Your feature description"
git push origin main
```

#### On Jetson

```bash
# Quick update (automated)
cd ~/apps/english-companion-nx
./deploy.sh

# Or using Makefile
make deploy-update
```

**Manual update:**
```bash
cd ~/apps/english-companion-nx
git pull origin main
source .venv/bin/activate
pip install -r requirements-jetson.txt
systemctl --user restart english-companion-nx
```

---

## 🛠️ Useful Commands

### Check Status
```bash
make deploy-status
# Or: systemctl --user status english-companion-nx
```

### View Logs
```bash
make deploy-logs
# Or: journalctl --user -u english-companion-nx -f
```

### Pre-deployment Health Check
```bash
make deploy-check
```

### Rollback to Previous Version
```bash
make deploy-rollback
# Will show recent commits and prompt for hash
```

---

## 🔐 Security Reminders

### ✅ Files Safe to Commit
- Source code (`.py` files)
- Documentation (`.md` files)
- Configuration templates (`.env.example`)
- Requirements (`requirements-jetson.txt`)
- Scripts (`.sh`, `Makefile`)

### ❌ Files to NEVER Commit
- `.env` (actual credentials)
- Conversation logs (`conversations.jsonl`)
- Database files (`conversations.db`)
- Model files (`*.pt`, `*.bin`, `*.gguf`)
- Personal data

### Verify `.env` is Ignored
```bash
# Should output: .env
git check-ignore .env

# If accidentally committed
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

---

## 🚨 Troubleshooting

### Problem: Can't push to GitHub

**Solution:**
```bash
# Check remote URL
git remote -v

# If HTTPS, switch to SSH
git remote set-url origin git@github.com:robertkotsch/english-companion-nx.git
```

### Problem: Deploy key authentication fails

**Solution:**
```bash
# Check SSH key exists
ls -la ~/.ssh/id_ed25519*

# Test connection
ssh -T git@github.com

# If fails, regenerate and re-add to GitHub
ssh-keygen -t ed25519 -C "jetson-english-companion-nx"
cat ~/.ssh/id_ed25519.pub
```

### Problem: Service won't start after update

**Solution:**
```bash
# Check logs for errors
journalctl --user -u english-companion-nx -n 50

# Rollback to last working version
cd ~/apps/english-companion-nx
git reset --hard HEAD~1
systemctl --user restart english-companion-nx
```

### Problem: Merge conflicts

**Solution:**
```bash
# If you edited on both dev machine and Jetson (try to avoid this!)
git pull origin main
# If conflicts:
git status  # See conflicted files
nano <conflicted-file>  # Resolve manually
git add <resolved-file>
git commit -m "Resolve merge conflict"
git push origin main
```

---

## 📊 Deployment Checklist

### Before Pushing (Dev Machine)
- [ ] Code tested locally (if possible)
- [ ] Tests pass (`pytest`)
- [ ] No `.env` in commit
- [ ] `requirements-jetson.txt` updated if dependencies changed
- [ ] Commit message is descriptive
- [ ] Code documented

### After Pulling (Jetson)
- [ ] Git pull successful
- [ ] Dependencies installed
- [ ] Service restarted
- [ ] Service running (`systemctl --user is-active english-companion-nx`)
- [ ] No errors in logs
- [ ] Quick functionality test

---

## 🎯 Next Steps

### Immediate (Today)
1. ✅ Push code to GitHub (Step 1 above)
2. Set up Jetson SSH key (Step 2.1-2.2)
3. Clone repository on Jetson (Step 2.4)
4. Set up Python environment (Step 2.5-2.7)

### This Week
1. Create systemd service file for auto-start
2. Install and configure Ollama
3. Download required models (Llama 3.1 13B)
4. Test basic audio pipeline

### Phase 1 (Week 1-2)
1. Implement basic audio recording
2. Integrate Whisper transcription
3. Add TTS (Coqui or Piper)
4. Test end-to-end pipeline

---

## 📚 Related Documentation

- [CLAUDE.md](./CLAUDE.md) - Development guide and best practices
- [git-deployment-workflow.md](./git-deployment-workflow.md) - Detailed workflow guide
- [README.md](./README.md) - Project overview
- [ai-english-companion-nx-project-spec.md](./ai-english-companion-nx-project-spec.md) - Complete specification

---

## 💡 Tips

1. **Commit often, push regularly** - Don't let changes pile up
2. **Test before pushing** - Catch errors on dev machine when possible
3. **Use meaningful commit messages** - Future you will thank you
4. **Check logs after deployment** - Ensure service started correctly
5. **Use the Makefile** - `make deploy-update` is faster than manual steps

---

**Your Repository:** https://github.com/robertkotsch/english-companion-nx
**Workflow:** Dev Machine → GitHub → Jetson (read-only from GitHub)
**Principle:** Git is single source of truth. Jetson pulls, never pushes (unless explicitly needed).

**Last Updated:** October 27, 2025
