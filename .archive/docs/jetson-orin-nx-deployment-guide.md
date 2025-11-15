# Jetson Orin NX — General Deployment Guide
## Production-Ready Configuration for AI/ML Applications

**Last Updated:** October 27, 2025  
**Hardware:** Jetson Orin NX (ARM64)  
**OS:** JetPack 6.x (Ubuntu 22.04 LTS)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture Strategies](#system-architecture-strategies)
3. [Storage & Filesystem](#storage--filesystem)
4. [Container Management (Podman)](#container-management-podman)
5. [Network Configuration](#network-configuration)
6. [Python Environment Setup](#python-environment-setup)
7. [Ollama Configuration](#ollama-configuration)
8. [Systemd Service Management](#systemd-service-management)
9. [Git-Based Deployment](#git-based-deployment)
10. [Performance Tuning](#performance-tuning)
11. [Security Best Practices](#security-best-practices)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Resource Limits & Monitoring](#resource-limits--monitoring)

---

## 🎯 Overview

This guide captures Jetson Orin NX-specific behaviors, commands, and best practices discovered through production deployment. These lessons apply to any AI/ML application running on Jetson hardware.

### Hardware Specifications

**Jetson Orin NX (16GB Model)**
- Architecture: ARM64 (aarch64)
- CPU: 8-core ARM Cortex-A78AE @ 2.0 GHz
- GPU: 1024-core NVIDIA Ampere with 32 Tensor Cores
- RAM: 16GB LPDDR5
- AI Performance: 100 TOPS (INT8)
- Storage: NVMe + eMMC/microSD support

### Typical Deployment Strategy

**Recommended Architecture:**
```
┌─────────────────────────────────────────┐
│         Infrastructure Layer            │
│    (Containerized with Podman)          │
├─────────────────────────────────────────┤
│ • Database (PostgreSQL/SQLite)          │
│ • Cache (Redis)                         │
│ • Vector Store (Qdrant/Chroma)          │
│ • Monitoring (Prometheus/Grafana)       │
└─────────────────────────────────────────┘
              ↓ localhost
┌─────────────────────────────────────────┐
│        Application Layer                │
│         (Native Python)                 │
├─────────────────────────────────────────┤
│ • FastAPI/Flask services                │
│ • Custom Python applications            │
│ • Data processing pipelines             │
└─────────────────────────────────────────┘
              ↓ localhost
┌─────────────────────────────────────────┐
│          AI/ML Layer                    │
│        (Native on Host)                 │
├─────────────────────────────────────────┤
│ • Ollama (LLMs)                         │
│ • Whisper (transcription)               │
│ • TTS engines                           │
│ • Custom models                         │
└─────────────────────────────────────────┘
```

**Why This Architecture:**
- ✅ Infrastructure in containers = easy updates, isolation
- ✅ Apps native = direct GPU access, no container overhead
- ✅ AI/ML native = maximum performance, CUDA acceleration
- ✅ Localhost networking = simple, secure, fast

---

## 🗄️ Storage & Filesystem

### Recommended Directory Structure

```
/var/lib/
├── <project-name>/           # Project-specific data
│   ├── postgres/             # Database files
│   ├── redis/                # Cache data
│   ├── qdrant/               # Vector database
│   ├── prometheus/           # Metrics
│   └── grafana/              # Dashboards

/home/<user>/
├── apps/
│   └── <project-name>/       # Application code
│       ├── .venv/            # Python virtual environment
│       ├── .env              # Environment configuration
│       ├── models/           # Downloaded AI models
│       ├── logs/             # Application logs
│       └── data/             # Working data

/opt/
└── ollama/                   # Ollama models (default)
    └── models/
```

### Storage Setup

**Create persistent storage directories:**

```bash
# Replace <project-name> with your actual project name
sudo mkdir -p /var/lib/<project-name>/{postgres,redis,qdrant,prometheus,grafana}
sudo chown -R $(id -u):$(id -g) /var/lib/<project-name>
```

**For NVMe SSD (Recommended):**

```bash
# Check if NVMe is detected
lsblk | grep nvme

# Format and mount (if new drive)
sudo mkfs.ext4 /dev/nvme0n1p1
sudo mkdir -p /mnt/nvme
sudo mount /dev/nvme0n1p1 /mnt/nvme

# Add to fstab for persistence
echo "/dev/nvme0n1p1 /mnt/nvme ext4 defaults 0 2" | sudo tee -a /etc/fstab

# Create project directories on NVMe
sudo mkdir -p /mnt/nvme/<project-name>
sudo chown -R $(id -u):$(id -g) /mnt/nvme/<project-name>

# Symlink for convenience
ln -s /mnt/nvme/<project-name> /var/lib/<project-name>
```

**Storage Recommendations:**
- **OS/System:** eMMC or microSD (minimal writes)
- **Models/Data:** NVMe SSD (fast access, large files)
- **Databases:** NVMe SSD (I/O intensive)
- **Logs:** eMMC/SD with rotation (write-heavy)

---

## 🐳 Container Management (Podman)

### Why Podman on Jetson

**Advantages over Docker:**
- ✅ Rootless by default (better security)
- ✅ No daemon (lighter resource usage)
- ✅ systemd integration
- ✅ Docker-compatible commands
- ✅ Better suited for embedded systems

### Installation

```bash
sudo apt update
sudo apt install -y podman
```

### Rootless Volume Permissions

**Critical for ARM64/Jetson:**

Podman rootless uses UID/GID mapping. Container UIDs don't match host UIDs.

**Two solutions:**

**Option 1: Use `:U` flag (Recommended)**
```bash
podman run -v /host/path:/container/path:U <image>
```
The `:U` flag tells Podman to handle UID mapping automatically.

**Option 2: Manual UID fixing (if `:U` doesn't work)**
```bash
# PostgreSQL (UID 999 in container)
podman unshare chown -R 999:999 /var/lib/<project>/postgres

# Redis (usually root, 0:0)
podman unshare chown -R 0:0 /var/lib/<project>/redis

# Qdrant (UID 1000)
podman unshare chown -R 1000:1000 /var/lib/<project>/qdrant

# Prometheus (UID 65534 - nobody)
podman unshare chown -R 65534:65534 /var/lib/<project>/prometheus

# Grafana (UID 472)
podman unshare chown -R 472:472 /var/lib/<project>/grafana
```

**Check container UID:**
```bash
podman run --rm <image> id
# Shows: uid=999(postgres) gid=999(postgres) groups=999(postgres)
```

### Container Examples

#### PostgreSQL 15

```bash
podman run -d --name project-postgres \
  --restart unless-stopped \
  -e POSTGRES_DB=mydb \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypass \
  -p 127.0.0.1:5432:5432 \
  -v /var/lib/<project>/postgres:/var/lib/postgresql/data:U \
  docker.io/postgres:15-alpine \
  -c shared_buffers=512MB \
  -c work_mem=32MB \
  -c maintenance_work_mem=128MB \
  -c effective_cache_size=1500MB
```

**Performance Tuning:**
- `shared_buffers`: 25% of RAM (max 2GB recommended)
- `effective_cache_size`: 50% of RAM
- `work_mem`: 32-64MB (adjust per connection)

#### Redis 7

```bash
podman run -d --name project-redis \
  --restart unless-stopped \
  -p 127.0.0.1:6379:6379 \
  -v /var/lib/<project>/redis:/data:U \
  docker.io/redis:7-alpine \
  --save "" \
  --appendonly no \
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru \
  --protected-mode no \
  --bind 0.0.0.0
```

**Memory Limits:**
- Adjust `--maxmemory` based on available RAM
- For 16GB Jetson: 256-512MB is reasonable
- LRU policy ensures oldest keys are evicted first

#### Qdrant (Vector Database)

```bash
podman run -d --name project-qdrant \
  --restart unless-stopped \
  -p 127.0.0.1:6333:6333 \
  -p 127.0.0.1:6334:6334 \
  -v /var/lib/<project>/qdrant:/qdrant/storage:U \
  --health-cmd='curl -sSf http://localhost:6333/readyz || exit 1' \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  docker.io/qdrant/qdrant:v1.7.4
```

**Important Notes:**
- Port 6333: REST API
- Port 6334: gRPC API
- Health endpoint: `/readyz` (not `/health` in v1.7.x)
- Verify: `curl http://127.0.0.1:6333/collections`

#### Prometheus (Monitoring)

```bash
podman run -d --name project-prometheus \
  --restart unless-stopped \
  -p 127.0.0.1:9090:9090 \
  -v /var/lib/<project>/prometheus:/prometheus:U \
  -v ~/apps/<project>/config/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
  docker.io/prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=7d \
  --storage.tsdb.retention.size=500MB \
  --web.enable-lifecycle \
  --web.listen-address=0.0.0.0:9090
```

#### Grafana (Dashboards)

```bash
podman run -d --name project-grafana \
  --restart unless-stopped \
  -p 127.0.0.1:3000:3000 \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD=secure_password \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -v /var/lib/<project>/grafana:/var/lib/grafana:U \
  docker.io/grafana/grafana:latest
```

### Container Management Commands

```bash
# List running containers
podman ps

# View logs
podman logs -f project-postgres
podman logs --tail 50 project-redis

# Stop/start containers
podman stop project-postgres
podman start project-postgres

# Restart container
podman restart project-redis

# Remove container (stops first if running)
podman rm -f project-postgres

# Execute command in container
podman exec -it project-postgres psql -U myuser -d mydb

# Check resource usage
podman stats

# Inspect container
podman inspect project-postgres

# Export container as systemd unit
podman generate systemd --name project-postgres --files --new
```

### Handling Port Conflicts

```bash
# Check what's using a port
sudo ss -ltnp | grep :5432
sudo lsof -i :6379

# Stop conflicting host services
sudo systemctl stop postgresql
sudo systemctl stop redis-server
sudo systemctl disable postgresql
sudo systemctl disable redis-server
```

---

## 🌐 Network Configuration

### Localhost Binding (Recommended)

**Security principle:** Bind services to localhost by default.

```bash
# Good: Only accessible from localhost
-p 127.0.0.1:5432:5432

# Bad: Accessible from network (security risk)
-p 5432:5432
-p 0.0.0.0:5432:5432
```

### Remote Access Options

**Option 1: SSH Tunneling (Recommended)**

```bash
# From remote machine, tunnel to Jetson
ssh -L 5432:127.0.0.1:5432 user@jetson-ip
ssh -L 6333:127.0.0.1:6333 user@jetson-ip

# Now access via localhost:5432 on remote machine
```

**Option 2: Reverse Proxy (nginx/caddy)**

```bash
# Install nginx
sudo apt install nginx

# Configure reverse proxy for API
sudo nano /etc/nginx/sites-available/myapp

# Example config:
server {
    listen 80;
    server_name jetson.local;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Option 3: Tailscale/Wireguard VPN**

Secure, encrypted access without exposing ports.

### Firewall Configuration

```bash
# Install ufw
sudo apt install ufw

# Default deny incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow specific services (only if needed)
sudo ufw allow from 192.168.1.0/24 to any port 8000

# Enable firewall
sudo ufw enable
sudo ufw status
```

---

## 🐍 Python Environment Setup

### Virtual Environment (Always Use)

```bash
cd ~/apps/<project>

# Create venv
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements-jetson.txt
```

### Environment Files

**Structure:**
```
.env.example        # Template (commit to git)
.env.prod          # Production config (DO NOT commit)
.env               # Active config (symlink or copy)
```

**Setup:**
```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env

# Secure permissions
chmod 600 .env

# Verify no CRLF (Windows line endings)
dos2unix .env  # or
sed -i 's/\r$//' .env
```

**Example .env for Jetson:**
```bash
# Database
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=mydb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Qdrant
QDRANT_HOST=127.0.0.1
QDRANT_PORT=6333

# Ollama
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Common Python Issues on ARM64

**Issue: aiofiles==23.2.0 yanked warning**
```bash
# Safe to ignore on Linux (only affects Windows)
# Or upgrade to newer version
pip install "aiofiles>=23.2.1,<24"
```

**Issue: Numpy/SciPy build failures**
```bash
# Install system dependencies first
sudo apt install -y libatlas-base-dev libopenblas-dev gfortran
pip install numpy scipy
```

**Issue: Pillow (PIL) build errors**
```bash
sudo apt install -y libjpeg-dev zlib1g-dev
pip install Pillow
```

---

## 🤖 Ollama Configuration

### Installation

```bash
# Official install script
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### Model Management

```bash
# Pull models
ollama pull llama3.1:8b-instruct-q4_0
ollama pull llama3.1:13b-instruct-q4_0
ollama pull nomic-embed-text
ollama pull mistral:7b-instruct

# List installed models
ollama list

# Remove model
ollama rm llama3.1:70b

# Show model info
ollama show llama3.1:13b
```

### Configuration

**Environment variables:**
```bash
# In .env or systemd service
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_MODELS=/mnt/nvme/ollama/models  # Custom model location
```

**Service configuration:**
```bash
# Edit systemd service
sudo systemctl edit ollama

# Add:
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_MODELS=/mnt/nvme/ollama/models"
Environment="OLLAMA_NUM_PARALLEL=1"

# Restart
sudo systemctl restart ollama
```

### Performance Tuning

**For 16GB Jetson Orin NX:**
```bash
# Run 8B models easily
ollama run llama3.1:8b-instruct-q4_0

# 13B models work but use more RAM
ollama run llama3.1:13b-instruct-q4_0

# Avoid 70B models (too large)
```

**Quantization levels:**
- `q4_0`: 4-bit, fast, good quality
- `q5_0`: 5-bit, better quality, slower
- `q8_0`: 8-bit, best quality, slowest

**Recommendation:** Use `q4_0` for balance of speed/quality

### Testing Ollama

```bash
# Test generation
ollama run llama3.1:8b "Hello, how are you?"

# Test API
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'

# Test embeddings
curl http://127.0.0.1:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "The quick brown fox jumps over the lazy dog"
}'
```

---

## ⚙️ Systemd Service Management

### User Services (Recommended for Non-Root Apps)

**Enable lingering (services start without login):**
```bash
loginctl enable-linger $USER
```

**Create service file:**
```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/myapp.service
```

**Example service:**
```ini
[Unit]
Description=My AI Application
After=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/apps/<project>
EnvironmentFile=%h/apps/<project>/.env
ExecStart=%h/apps/<project>/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

**Manage service:**
```bash
# Reload systemd
systemctl --user daemon-reload

# Enable (start on boot)
systemctl --user enable myapp

# Start service
systemctl --user start myapp

# Check status
systemctl --user status myapp

# View logs
journalctl --user -u myapp -f

# Stop service
systemctl --user stop myapp

# Restart service
systemctl --user restart myapp
```

### System Services (Root-Level)

**For Ollama, containers, etc.:**
```bash
sudo systemctl status ollama
sudo systemctl enable ollama
sudo systemctl restart ollama
```

### Container to Systemd

**Generate unit from Podman container:**
```bash
# Generate systemd unit file
podman generate systemd --name project-postgres --files --new --restart-policy=always

# This creates: container-project-postgres.service

# Move to systemd directory
mv container-project-postgres.service ~/.config/systemd/user/

# Enable and start
systemctl --user daemon-reload
systemctl --user enable container-project-postgres.service
systemctl --user start container-project-postgres.service
```

---

## 🔄 Git-Based Deployment

### Initial Setup

**Generate SSH key (if not exists):**
```bash
ssh-keygen -t ed25519 -C "jetson@hostname"
cat ~/.ssh/id_ed25519.pub
```

**Add as Deploy Key to GitHub/GitLab:**
- Settings → Deploy Keys → Add key (read-only)

**Clone repository:**
```bash
mkdir -p ~/apps
cd ~/apps
git clone --depth=1 git@github.com:username/repo.git project-name
cd project-name
```

### Update Workflow

**Manual update:**
```bash
cd ~/apps/project-name
git pull
source .venv/bin/activate
pip install -r requirements-jetson.txt
systemctl --user restart myapp
```

**Makefile automation:**
```makefile
.PHONY: deploy-update
deploy-update:
	@echo "Pulling latest code..."
	git pull origin main
	@echo "Installing dependencies..."
	.venv/bin/pip install -r requirements-jetson.txt
	@echo "Restarting service..."
	systemctl --user restart myapp
	@echo "Deployment complete!"
```

```bash
make deploy-update
```

### Git Configuration

```bash
# Set default branch
git config --global init.defaultBranch main

# Ignore file permissions (useful on Jetson)
git config --global core.fileMode false

# Credential helper
git config --global credential.helper store
```

---

## ⚡ Performance Tuning

### Power Modes

```bash
# Check current power mode
sudo nvpmodel -q

# List available modes
sudo nvpmodel -m

# Set to max performance (25W)
sudo nvpmodel -m 0

# Set to balanced (15W)
sudo nvpmodel -m 2
```

**Modes for Orin NX:**
- Mode 0: MAXN (25W) - Maximum performance
- Mode 1: 15W - Balanced
- Mode 2: 10W - Power saving

### CPU Governor

```bash
# Check current governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Set to performance
sudo sh -c 'echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'

# Make persistent (add to /etc/rc.local or systemd service)
```

### Jetson Stats (jtop)

```bash
# Install
sudo pip3 install jetson-stats

# Run
sudo jtop
```

**Monitor:**
- CPU/GPU usage
- RAM usage
- Temperature
- Power consumption
- Thermal throttling

### Swap Configuration

```bash
# Check swap
free -h

# Increase swap (if needed)
sudo systemctl disable nvzramconfig

# Create swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make persistent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Disable Unnecessary Services

```bash
# Disable GUI (if running headless)
sudo systemctl set-default multi-user.target

# Re-enable GUI
sudo systemctl set-default graphical.target

# Disable unwanted services
sudo systemctl disable cups  # Printing
sudo systemctl disable bluetooth  # If not needed
```

---

## 🔒 Security Best Practices

### File Permissions

```bash
# Secure .env files
chmod 600 .env
chmod 600 ~/.ssh/id_ed25519

# Secure directories
chmod 700 ~/.ssh
chmod 755 ~/apps/<project>
```

### Secrets Management

**DO NOT:**
- ❌ Commit `.env` files to git
- ❌ Use default passwords
- ❌ Expose services to public internet without auth

**DO:**
- ✅ Use `.env.example` templates
- ✅ Rotate credentials regularly
- ✅ Use strong, unique passwords
- ✅ Bind services to localhost
- ✅ Use SSH tunnels for remote access

### Update Strategy

```bash
# System updates
sudo apt update
sudo apt upgrade

# Python packages
pip install --upgrade pip
pip list --outdated
pip install --upgrade <package>

# Container images
podman pull docker.io/postgres:15-alpine
podman restart project-postgres
```

---

## 🔧 Troubleshooting Guide

### Container Issues

**Problem: Permission denied on volumes**
```bash
# Solution: Use :U flag or fix with podman unshare
podman unshare chown -R <uid>:<gid> /var/lib/<project>/<service>
```

**Problem: Port already in use**
```bash
# Find what's using the port
sudo ss -ltnp | grep :5432

# Stop conflicting service
sudo systemctl stop postgresql
```

**Problem: Container won't start**
```bash
# Check logs
podman logs project-postgres

# Inspect container
podman inspect project-postgres

# Remove and recreate
podman rm -f project-postgres
# Run container command again
```

### Python Issues

**Problem: CRLF line endings in .env**
```bash
# Symptoms: Variables like "127.0.0.1ostgres"
# Solution:
dos2unix .env
# Or:
sed -i 's/\r$//' .env
```

**Problem: Module not found**
```bash
# Ensure venv is activated
source .venv/bin/activate
which python  # Should show .venv path

# Reinstall dependencies
pip install -r requirements-jetson.txt
```

**Problem: Permission denied on venv**
```bash
# Fix ownership
chown -R $(id -u):$(id -g) .venv
```

### Network Issues

**Problem: Can't connect to localhost services**
```bash
# Don't use 0.0.0.0 as client
# Bad:  curl http://0.0.0.0:5432
# Good: curl http://127.0.0.1:5432

# Check service is listening
sudo ss -ltnp | grep :5432
```

**Problem: Firewall blocking connections**
```bash
# Check firewall rules
sudo ufw status verbose

# Allow specific port (if needed)
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

### Qdrant Specific

**Problem: /health endpoint returns 404**
```bash
# Solution: Use /readyz in v1.7.x
curl http://127.0.0.1:6333/readyz

# Or check collections
curl http://127.0.0.1:6333/collections
```

### Storage Issues

**Problem: SMART warnings on eMMC**
```bash
# Install smartmontools
sudo apt install smartmontools

# Check SMART status
sudo smartctl -a /dev/mmcblk0

# eMMC may not support SMART - safe to ignore
```

**Problem: Disk full**
```bash
# Check disk usage
df -h

# Find large files
du -sh /* | sort -hr | head -n 10

# Clean Docker/Podman
podman system prune -a

# Clean package cache
sudo apt clean
sudo apt autoremove
```

### Performance Issues

**Problem: Thermal throttling**
```bash
# Check temperature
tegrastats

# Ensure active cooling
# Check fan is spinning
# Consider additional cooling

# Reduce power mode
sudo nvpmodel -m 2
```

**Problem: Out of memory**
```bash
# Check memory usage
free -h

# Increase swap
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make persistent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📊 Resource Limits & Monitoring

### Recommended Resource Allocation (16GB Jetson)

```
System:           2GB
GPU (shared):     2-4GB
Ollama (13B):     8-10GB
PostgreSQL:       512MB
Redis:            256MB
Qdrant:           512MB
Python App:       1-2GB
Buffer:           2GB
```

### Container Resource Limits

```bash
# Limit memory for container
podman run -d --name project-redis \
  --memory=256m \
  --memory-swap=512m \
  docker.io/redis:7-alpine

# Limit CPU
podman run -d --name project-postgres \
  --cpus=2 \
  docker.io/postgres:15-alpine
```

### Monitoring with Prometheus

**Prometheus config:** (`prometheus.yml`)
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'jetson'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'app'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'ollama'
    static_configs:
      - targets: ['localhost:11434']
```

### Log Rotation

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/myapp

# Add:
/home/<user>/apps/<project>/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}

# Test
sudo logrotate -f /etc/logrotate.d/myapp
```

---

## 📚 Quick Reference

### Essential Commands

```bash
# Container management
podman ps                          # List containers
podman logs -f <name>              # View logs
podman restart <name>              # Restart container
podman stats                       # Resource usage

# Service management
systemctl --user status <service>  # Check service
systemctl --user restart <service> # Restart service
journalctl --user -u <service> -f  # View logs

# System monitoring
jtop                               # Jetson stats
htop                               # Process monitor
df -h                              # Disk usage
free -h                            # Memory usage

# Git deployment
git pull                           # Update code
make deploy-update                 # Automated update

# Python environment
source .venv/bin/activate          # Activate venv
pip install -r requirements-jetson.txt    # Install deps
```

### Port Checklist

```
5432  - PostgreSQL
6379  - Redis
6333  - Qdrant REST
6334  - Qdrant gRPC
9090  - Prometheus
3000  - Grafana
11434 - Ollama
8000  - Application API (example)
```

### Health Check URLs

```bash
# Qdrant
curl http://127.0.0.1:6333/readyz
curl http://127.0.0.1:6333/collections

# Ollama
curl http://127.0.0.1:11434/api/tags

# Prometheus
curl http://127.0.0.1:9090/-/healthy

# Application (example)
curl http://127.0.0.1:8000/health
```

---

## 🎓 Best Practices Summary

### ✅ DO

1. **Use rootless Podman** for containers
2. **Bind services to localhost** (127.0.0.1)
3. **Use NVMe for models/data** (fast I/O)
4. **Always use Python venvs** (isolation)
5. **Secure .env files** (chmod 600)
6. **Git-based deployment** (version control)
7. **Enable systemd user services** (reliability)
8. **Monitor resources** (jtop, prometheus)
9. **Use `:U` for volumes** (permissions)
10. **Regular backups** (databases, models)

### ❌ DON'T

1. **Don't expose services publicly** without auth
2. **Don't commit secrets** to git
3. **Don't run as root** unless necessary
4. **Don't ignore thermal warnings** (cooling!)
5. **Don't mix architectures** (ARM64 only)
6. **Don't use 0.0.0.0 as client** (use 127.0.0.1)
7. **Don't skip updates** (security patches)
8. **Don't overload RAM** (causes swapping)
9. **Don't forget log rotation** (disk fills up)
10. **Don't assume Docker compatibility** (test on ARM64)

---

## 📖 Additional Resources

**Official Documentation:**
- Jetson Linux: https://docs.nvidia.com/jetson/
- JetPack: https://developer.nvidia.com/embedded/jetpack
- Podman: https://docs.podman.io/

**Community:**
- NVIDIA Jetson Forums: https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/
- Jetson Hacks: https://jetsonhacks.com/

**Tools:**
- jetson-stats: https://github.com/rbonghi/jetson_stats
- Ollama: https://ollama.ai/

---

**Document Version:** 1.0  
**Based on:** Production deployment experience (Domain Radar NX)  
**Applicable to:** Any AI/ML project on Jetson Orin NX  
**Last Updated:** October 27, 2025

---

## 📝 Notes

This guide is distilled from real production deployment experience. Adapt configurations to your specific project needs, but the principles and patterns remain consistent across Jetson-based AI applications.

For project-specific configurations, create a `DEPLOYMENT.md` in your repository referencing this guide and documenting your specific setup.
