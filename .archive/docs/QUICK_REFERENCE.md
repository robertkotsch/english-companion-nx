# English Companion NX - Quick Reference Card

**One-page cheat sheet for daily operations**

---

## 🚀 Daily Workflow

### On Dev Machine
```bash
# Edit code
code ~/projects/english-companion-nx

# Commit & push
git add .
git commit -m "feat: Your change"
git push origin main
```

### On Jetson
```bash
# Quick update
cd ~/apps/english-companion-nx
make deploy-update

# Or manual
git pull && source .venv/bin/activate && pip install -r requirements-jetson.txt
systemctl --user restart english-companion-nx
```

---

## 🔍 Essential Commands

### Service Management
```bash
# Status
systemctl --user status english-companion-nx

# Start/Stop/Restart
systemctl --user start english-companion-nx
systemctl --user stop english-companion-nx
systemctl --user restart english-companion-nx

# Enable (auto-start)
systemctl --user enable english-companion-nx

# Logs (live)
journalctl --user -u english-companion-nx -f

# Logs (last 50 lines)
journalctl --user -u english-companion-nx -n 50
```

### System Monitoring
```bash
# Overall system stats
jtop

# Memory
free -h

# Temperature
cat /sys/class/thermal/thermal_zone0/temp

# Disk usage
df -h /mnt/nvme

# SSD health
sudo smartctl -a /dev/nvme0n1
```

### Ollama
```bash
# Status
systemctl status ollama

# List models
ollama list

# Pull model
ollama pull llama3.1:13b-instruct-q4_0

# Test model
ollama run llama3.1:13b "Hello"
```

---

## ⚠️ Emergency Procedures

### Service Won't Start
```bash
# 1. Check logs
journalctl --user -u english-companion-nx -n 50

# 2. Check Ollama
systemctl status ollama

# 3. Check memory
free -h

# 4. Rollback if needed
cd ~/apps/english-companion-nx
git reset --hard HEAD~1
systemctl --user restart english-companion-nx
```

### High Memory (>95%)
```bash
# Immediate restart
systemctl --user restart english-companion-nx

# If persists
sudo swapoff -a && sudo swapon -a
sudo sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
```

### High Temperature (>80°C)
```bash
# Reduce power
sudo nvpmodel -m 2  # 10W mode

# Stop service temporarily
systemctl --user stop english-companion-nx

# Wait for cooldown
watch -n 1 'cat /sys/class/thermal/thermal_zone0/temp'

# Resume
sudo nvpmodel -m 0  # 25W mode
systemctl --user start english-companion-nx
```

---

## 📊 Health Checks

### Quick Status
```bash
# All-in-one check
make deploy-check

# Manual checks
systemctl --user is-active english-companion-nx  # Service
systemctl is-active ollama                     # LLM
free -h | grep Mem                             # Memory
df -h /mnt/nvme | tail -1                      # Disk
cat /sys/class/thermal/thermal_zone0/temp      # Temp
```

### Daily Health
```bash
# Run health check
~/apps/english-companion-nx/scripts/daily_health_check.sh
```

---

## 🐛 Debugging

### Check Logs for Errors
```bash
# Service logs with errors only
journalctl --user -u english-companion-nx -p err -n 50

# Full logs
journalctl --user -u english-companion-nx --since "1 hour ago"

# System logs
sudo dmesg | tail -50
```

### Test Components
```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Test Whisper
python -m src.speech.transcription

# Test LLM
python -m src.conversation.llm_client

# Test TTS
python -m src.speech.synthesis
```

---

## 🔧 Maintenance

### Weekly
- [ ] Check service status
- [ ] Review logs for errors
- [ ] Check disk usage
- [ ] Verify temperature normal

### Monthly
- [ ] Run full health check
- [ ] Backup conversations
- [ ] Check SSD health
- [ ] Update system packages

### Commands
```bash
# Backup conversations
cp /mnt/nvme/companion/conversations.jsonl ~/backups/conversations-$(date +%Y%m%d).jsonl

# Check SSD health
sudo smartctl -a /dev/nvme0n1 | grep -E "Percentage|Temperature"

# Update system
sudo apt update && sudo apt upgrade
```

---

## 📁 Important Paths

```
Code:           ~/apps/english-companion-nx
Logs:           /mnt/nvme/companion/logs
Conversations:  /mnt/nvme/companion/conversations.jsonl
Models:         /opt/ollama/models
Temp audio:     /tmp/companion-audio
Config:         ~/apps/english-companion-nx/.env
```

---

## 🎯 Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Memory | <13GB | >15GB |
| Temperature | <70°C | >80°C |
| Response time | <3s | >5s |
| SSD writes | <500MB/day | >5GB/day |
| Uptime | >99% | <95% |

---

## 📞 Quick Help

**Service issues?** → Check logs first
**Memory problems?** → Restart service
**Hot device?** → Check cooling, reduce power
**Slow responses?** → Check temperature, memory
**Git issues?** → Check SSH key, network

---

## 🔗 Documentation

- **Full docs:** `~/apps/english-companion-nx/README.md`
- **Dev guide:** `~/apps/english-companion-nx/CLAUDE.md`
- **Deployment:** `~/apps/english-companion-nx/git-deployment-workflow.md`

---

## 💡 Pro Tips

1. **Always check logs first** when something fails
2. **Monitor temperature** in summer months
3. **Backup regularly** (conversations are valuable)
4. **Test locally** before pushing to production
5. **Keep .env secure** (chmod 600)
6. **Update weekly** (git pull + restart)

---

## 🚨 Know These by Heart

```bash
# Service status
systemctl --user status english-companion-nx

# View logs
journalctl --user -u english-companion-nx -f

# Restart service
systemctl --user restart english-companion-nx

# Deploy updates
cd ~/apps/english-companion-nx && make deploy-update

# Rollback
git reset --hard HEAD~1 && systemctl --user restart english-companion-nx
```

---

**Print this page and keep it handy!** 📄

**Last Updated:** October 27, 2025
