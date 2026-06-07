# English Companion NX Project - Documentation Index

**AI-Powered English Conversation Partner for Jetson Orin NX**

---

## 📚 Documentation Overview

This project includes comprehensive documentation based on production-tested patterns from Domain Radar NX, adapted for conversational AI use cases.

### 🎯 Core Documents

1. **[Project Specification](./ai-english-companion-nx-project-spec.md)** (Main document)
   - Complete project vision and requirements
   - Hardware specifications
   - Feature breakdown by phase
   - Timeline and milestones
   - **Start here for project overview**

2. **[CLAUDE.md](./CLAUDE.md)** (Development guide)
   - Critical constraints (memory, SSD)
   - Development guidelines
   - Code patterns and best practices
   - Emergency procedures
   - **Read before writing code**

3. **[Git Deployment Workflow](./git-deployment-workflow.md)** (Operations)
   - Dev machine → GitHub → Jetson workflow
   - Initial setup instructions
   - Daily deployment process
   - Troubleshooting guide
   - **Follow for deployment**

### 🔧 Technical References

4. **[Jetson Orin NX Deployment Guide](./jetson-orin-nx-deployment-guide.md)** (General)
   - Jetson-specific best practices
   - Container management (Podman)
   - Network configuration
   - Performance tuning
   - **Reference for Jetson operations**

5. **[Infrastructure Comparison](./infrastructure-comparison.md)** (Architecture)
   - Domain Radar vs English Companion NX
   - Why different approaches
   - When to use each pattern
   - Migration paths
   - **Understand architecture decisions**

6. **[RAG Integration Guide](./RAG_INTEGRATION_GUIDE.md)** (Phase 4-5)
   - Adding semantic memory with Qdrant
   - Long-term conversation context
   - Implementation details
   - Resource impact analysis
   - **Future enhancement**

7. **[JETSON_PECULIARITIES.md](./JETSON_PECULIARITIES.md)** (Lessons learned)
   - Production quirks and gotchas
   - From Domain Radar deployment
   - ARM64-specific issues
   - **Learn from experience**

---

## 🚀 Quick Start Guide

### For First-Time Setup

**1. Read these (in order):**
   - [ ] Project Specification (understand vision)
   - [ ] CLAUDE.md (understand constraints)
   - [ ] Git Deployment Workflow (understand process)

**2. On Jetson (one-time):**
   ```bash
   # Setup SSH deploy key
   ssh-keygen -t ed25519 -C "jetson-companion"
   # Add public key to GitHub deploy keys
   
   # Clone repository
   git clone git@github.com:<you>/english-companion-nx.git
   cd english-companion-nx
   
   # Setup environment
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-jetson.txt
   
   # Configure
   cp .env.example .env
   nano .env
   chmod 600 .env
   ```

**3. Daily workflow:**
   - Develop on dev machine
   - Push to GitHub
   - Pull on Jetson
   - Restart service

---

## 🎯 Key Principles

### Architecture Philosophy

**Simplicity First**
- ❌ No PostgreSQL (JSONL is sufficient)
- ❌ No Redis (no caching needed)
- ❌ No Qdrant (no vector search initially)
- ✅ Just Ollama + JSONL + systemd

**Load Once, Run Forever**
- Models loaded at startup
- Keep in RAM indefinitely
- Service restarts only when updating

**Git as Source of Truth**
- Develop on dev machine
- Push to GitHub
- Jetson pulls only (read-only)
- No editing on Jetson

### Resource Management

**Memory (16GB Total, 11GB Usable):**
```
System:              3.0 GB
Whisper Small:       1.0 GB
Qwen 2.5 3B-Instruct: 2.5 GB
TTS (Coqui VITS):    0.5 GB
Application:         1.0 GB
Buffers:             0.5 GB
Safety margin:       2.5 GB
```

**SSD Writes (200MB/day budget):**
- Buffer conversation logs (5-min intervals)
- Use tmpfs for audio temps (zero writes)
- Log rotation with compression
- Way under 50GB/day safety limit

**Thermal Management:**
- Monitor temps (70°C warning, 80°C critical)
- Ensure active cooling
- Adaptive power modes

---

## 📋 Project Phases

### Phase 1: Core Audio Pipeline ✅
- [x] Audio capture (Anker PowerConf S3)
- [x] Whisper transcription
- [x] Basic TTS output
- [x] Simple echo loop

### Phase 2: Conversation Engine ✅
- [x] Wake word detection (OpenWakeWord)
- [x] Ollama LLM integration
- [x] Context management
- [x] Buffered logging

### Phase 3: Topic Integration 🚧
- [x] MCP client connection
- [ ] Topic suggestions
- [x] Conversation threading

### Phase 4: Learning Features 🚧
- [x] Grammar correction (background)
- [ ] Vocabulary tracking
- [ ] Progress metrics
- [ ] **RAG with Qdrant** (semantic memory)

### Phase 5: Polish & Advanced ⏳
- [ ] Voice cloning option
- [ ] Emotion detection
- [ ] Multi-language support

---

## 🛠️ Development Workflow

### On Development Machine

```bash
# 1. Code changes
cd ~/projects/english-companion-nx
code .  # Edit files

# 2. Test (if possible)
pytest tests/

# 3. Commit and push
git add .
git commit -m "feat: Add feature X"
git push origin main
```

### On Jetson

```bash
# Update and restart
cd ~/apps/english-companion-nx
make deploy-update

# Or manually:
git pull origin main
source .venv/bin/activate
pip install -r requirements-jetson.txt
systemctl --user restart english-companion-nx

# Check status
systemctl --user status english-companion-nx

# View logs
journalctl --user -u english-companion-nx -f
```

---

## 🔍 Troubleshooting

### Service Won't Start

```bash
# Check logs
journalctl --user -u english-companion-nx -n 50

# Common issues:
# 1. Models not loaded
ollama list

# 2. Insufficient memory
free -h

# 3. Port conflict
sudo ss -ltnp | grep 8000

# 4. Permission issues
ls -la .env  # Should be 600
```

### Memory Issues

```bash
# Check usage
free -h
jtop

# Force cleanup
systemctl --user restart english-companion-nx

# Check for leaks
python scripts/memory_leak_detector.py
```

### High Temperature

```bash
# Check temp
cat /sys/class/thermal/thermal_zone*/temp

# Reduce power
sudo nvpmodel -m 2  # 10W mode

# Stop temporarily
systemctl --user stop english-companion-nx
# Wait for cooldown
```

---

## 📊 Monitoring

### Daily Health Check

```bash
# Manual check
~/apps/english-companion-nx/scripts/daily_health_check.sh

# Automated (cron)
0 2 * * * ~/apps/english-companion-nx/scripts/daily_health_check.sh >> ~/health.log
```

### Key Metrics

- **Memory usage:** Should stay stable around 11-12GB
- **Temperature:** Keep below 70°C normally
- **SSD writes:** ~200MB/day typical
- **Conversations:** Track daily count
- **Response time:** Target <3 seconds

### Prometheus/Grafana (Optional)

If you add monitoring in Phase 4+:
- Metrics: http://localhost:8001/metrics
- Grafana: http://localhost:3000

---

## 🔐 Security

### Best Practices

✅ **DO:**
- Keep `.env` out of Git
- Use SSH deploy keys (read-only)
- Set file permissions (`chmod 600 .env`)
- Rotate credentials periodically
- Keep system updated

❌ **DON'T:**
- Commit API keys or passwords
- Expose services to internet without auth
- Use default passwords
- Run as root
- Skip security updates

---

## 🎓 Learning Resources

### Understanding Jetson

- [Jetson Linux Documentation](https://docs.nvidia.com/jetson/)
- [JetPack SDK Guide](https://developer.nvidia.com/embedded/jetpack)
- [Jetson Stats (jtop)](https://github.com/rbonghi/jetson_stats)

### AI/ML on Jetson

- [Ollama Documentation](https://ollama.ai/)
- [Whisper by OpenAI](https://github.com/openai/whisper)
- [Coqui TTS](https://github.com/coqui-ai/TTS)

### Python Development

- [FastAPI](https://fastapi.tiangolo.com/)
- [AsyncIO Guide](https://docs.python.org/3/library/asyncio.html)
- [pytest Documentation](https://docs.pytest.org/)

---

## 🤝 Contributing

### For Yourself

1. Follow CLAUDE.md guidelines
2. Test before pushing
3. Use meaningful commit messages
4. Document new features
5. Update requirements-jetson.txt

### Code Standards

- Use type hints
- Write docstrings
- Follow PEP 8
- Add tests for new features
- Keep functions focused

---

## 📝 Changelog

### Current Status (June 2026)

**✅ Operational**
- [x] Full voice pipeline live: wake word → VAD → Whisper STT (GPU) → local LLM (Ollama) → neural TTS
- [x] Running 24/7 as a systemd service
- [x] Multi-agent "Zoo" layer: listener agents → orchestrator → coaching, emitting typed signals
- [x] Buffered JSONL logging, tmpfs audio temps, thermal-aware power modes
- [x] Git-based deploy workflow (dev → GitHub → Jetson, pull-only)

**🚧 In Progress**
- [ ] Expanding Zoo coaching and memory agents
- [ ] Longitudinal progress metrics

**📋 Next**
- [ ] RAG with Qdrant for semantic long-term memory
- [ ] Optional voice cloning, emotion detection

---

## 🎯 Success Criteria

### Technical

- [ ] 24/7 uptime (>99%)
- [ ] Response time <3 seconds
- [ ] Memory stable (no leaks)
- [ ] Temperature <70°C normally
- [ ] SSD writes <500MB/day

### User Experience

- [ ] Natural conversations
- [ ] Helpful grammar corrections
- [ ] Interesting topic suggestions
- [ ] Reliable wake word detection
- [ ] Clear, natural voice output

---

## 📞 Support

### Getting Help

1. Check CLAUDE.md for guidelines
2. Review troubleshooting sections
3. Search GitHub issues
4. Check system logs
5. Verify hardware connections

### Documentation Issues

If you find:
- Incorrect information
- Missing details
- Unclear instructions
- Broken links

Update the docs and commit!

---

## 🙏 Acknowledgments

**Based on patterns from:**
- Domain Radar NX (production deployment experience)
- Jetson community best practices
- Real-world embedded AI deployments

**Technologies:**
- NVIDIA Jetson Orin NX
- Ollama running Qwen 2.5 3B-Instruct (LLM runtime)
- OpenAI Whisper small (STT)
- Coqui TTS / VITS (voice synthesis)
- OpenWakeWord (wake word)

---

## 📄 License

MIT

---

## 🎉 Getting Started

**Ready to begin?**

1. ✅ Read Project Specification
2. ✅ Read CLAUDE.md  
3. ✅ Setup Jetson (Git Deployment Workflow)
4. ✅ Start Phase 1 development
5. ✅ Deploy and test
6. ✅ Iterate and improve

**Welcome to the English Companion NX project!** 🚀

---

**Last Updated:** June 2026
**Project Status:** Operational — running 24/7 as a systemd service on Jetson Orin NX
**Deployment Model:** Git-based (Dev → GitHub → Jetson, pull-only)

---

## 📂 Document Index

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [Project Spec](./ai-english-companion-nx-project-spec.md) | Vision & requirements | Planning |
| [CLAUDE.md](./CLAUDE.md) | Development guide | Before coding |
| [Git Workflow](./git-deployment-workflow.md) | Deployment process | Before deploying |
| [Jetson Guide](./jetson-orin-nx-deployment-guide.md) | General Jetson ops | Reference |
| [Infrastructure](./infrastructure-comparison.md) | Architecture decisions | Understanding design |
| [Peculiarities](./JETSON_PECULIARITIES.md) | Lessons learned | Troubleshooting |

**Start with Project Spec → CLAUDE.md → Git Workflow** 📚
