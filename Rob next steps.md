● 🎯 Next Steps - English Companion NX

  Current Status

  ✅ Phase 1 Prototype: Working conversation loop
  - Whisper (GPU) → Ollama → TTS (GPU) → Playback
  - Total latency: ~12-15s per exchange
  - Good transcription accuracy (Whisper small)
  - Natural speech output (Coqui VITS)

  ⚠️ Known Issue: Numpy Dependency Conflict
  - During pip install, numpy gets downgraded from 1.26.4 → 1.22.0
  - Breaks JetPack system packages (jax, tensorflow, chex, ultralytics)
  - **Fix:** See QUICK_FIX_NUMPY.md or run ./fix_numpy_jetson.sh
  - **Root cause:** openai-whisper dependency forces old numpy
  - **Prevention:** Use requirements-jetson.txt (installs numpy first)

  ---
  Immediate Next Steps (Complete Phase 1)

  1. Conversation Logging ⏱️ ~30 min

  Add buffered JSONL logging as designed in CLAUDE.md:
  - Save conversations to ~/companion-data/conversations.jsonl
  - Buffer writes (flush every 5 minutes)
  - Include metadata (timestamps, response times, topics)
  - Why: Track conversations, analyze patterns, enable future features

  2. Systemd Service ⏱️ ~45 min

  Set up 24/7 always-running service:
  - Create systemd user service
  - Auto-start on boot
  - Memory limits (MemoryMax=11G)
  - Log rotation
  - Why: True 24/7 companion (no manual starting)

  3. Memory Management ⏱️ ~30 min

  Add monitoring and periodic cleanup:
  - Track memory usage
  - Periodic garbage collection (every 10 conversations)
  - CUDA cache clearing
  - Context pruning
  - Why: Prevent memory leaks, ensure stability

  ---
  Phase 2: Wake Word & Always-On ⏱️ ~6-10 hours

  ✅ Research Complete (See MD/WAKE_WORD_SUMMARY.md)

  Wake Word Detection (Porcupine)

  Replace "Press Enter" with "Hey Companion" (or custom phrase):
  - ✅ Porcupine selected (~1% CPU expected on Jetson)
  - ✅ Dual wake word support (START + STOP triggers)
  - ✅ 14 built-in keywords OR custom training available
  - ⚠️ Must test ARM64 compatibility: python test_porcupine.py
  - Why: Hands-free, natural interaction

  Phase 2A: Basic Wake Word ⏱️ ~4-6 hours
  1. Test Porcupine on Jetson (python test_porcupine.py)
  2. Get Picovoice AccessKey (free tier, 1 device)
  3. Implement src/audio/wake_word.py module
  4. Integrate with conversation_prototype.py
  5. Test and tune sensitivity

  Phase 2B: Dual Wake Word + State Machine ⏱️ ~3-4 hours
  - Add STOP keyword detection
  - Implement conversation state management (IDLE/LISTENING/PROCESSING/SPEAKING)
  - Add timeout handling (auto-stop after N minutes)
  - Test start/stop flow end-to-end

  Always-On Mode

  - Continuous listening loop
  - Automatic conversation flow
  - Smart timeout (return to listening after response)
  - Why: True conversational experience

  📄 Documentation Created:
  - MD/PORCUPINE_RESEARCH.md (full research, 14 sections)
  - MD/WAKE_WORD_IMPLEMENTATION_GUIDE.md (step-by-step guide)
  - MD/WAKE_WORD_SUMMARY.md (executive summary)
  - test_porcupine.py (compatibility test script)
  - .env.example (updated with Porcupine config)

  ---
  Phase 3: MCP Topic Integration ⏱️ ~2 hours

  Connect to your existing MCP topic curation:
  - Fetch trending topics
  - Suggest conversation starters
  - Context-aware topic injection
  - Why: Keep conversations fresh and engaging

  ---
  Phase 4: Grammar Correction ⏱️ ~2-3 hours

  Background grammar analysis:
  - Detect errors while LLM generates
  - Gentle correction in responses
  - Track progress over time
  - Why: Teaching component for language learning

  ---
  Phase 5: Polish & Optimization ⏱️ ~1-2 days

  - Performance tuning
  - Error recovery
  - Health monitoring dashboard
  - Mobile companion app (optional)
  - Why: Production-ready system

  ---
  🤔 What Should We Do Next?

  My recommendation:

  Option A: Complete Phase 1 (Recommended) ⏱️ ~2 hours
  Make the current prototype production-ready:
  1. Add conversation logging
  2. Set up systemd service
  3. Add memory monitoring
  → Result: 24/7 running companion you can use daily

  Option B: Jump to Wake Word (Phase 2) ⏱️ ~4 hours
  Make it hands-free immediately:
  - Skip logging/service for now
  - Focus on Porcupine integration
  - Always-on listening mode
  → Result: "Hey Companion" activation

  Option C: Incremental ⏱️ Your pace
  Pick individual features one at a time based on what excites you most.

  ---
  What's your priority?
  - A: Make it production-ready (logging, service, monitoring)
  - B: Make it hands-free (wake word)
  - C: Something specific you want to add?

  Let me know what direction you'd like to take! 🚀

  Todos
  ☐ Complete Phase 1: Add conversation logging (buffered JSONL)
  ☐ Complete Phase 1: Create systemd service for 24/7 operation
  ☐ Complete Phase 1: Add memory monitoring and cleanup
  ✅ Phase 2: Research wake word detection options (Porcupine selected)
  ☐ Phase 2A: Test Porcupine compatibility (run test_porcupine.py on Jetson)
  ☐ Phase 2A: Get Picovoice AccessKey (https://console.picovoice.ai/)
  ☐ Phase 2A: Choose wake words (built-in or train custom)
  ☐ Phase 2A: Implement src/audio/wake_word.py module
  ☐ Phase 2A: Integrate wake word with conversation_prototype.py
  ☐ Phase 2B: Add STOP keyword detection
  ☐ Phase 2B: Implement conversation state machine
  ☐ Phase 2B: Create always-on listening mode
  ☐ Phase 3: Integrate MCP for topic suggestions
  ☐ Phase 4: Add background grammar correction
  ☐ Phase 5: Performance optimization and polish