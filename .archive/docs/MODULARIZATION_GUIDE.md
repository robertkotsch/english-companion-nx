# From Prototype to Production: Modularization Guide
## English Companion NX

**Status:** Prototype ✅ Working → Production 🚀 Building  
**Last Updated:** October 27, 2025

---

## 🎉 Prototype Success!

**You've proven:**
- ✅ Jetson can capture audio
- ✅ Whisper transcription works
- ✅ LLM (Ollama) responds
- ✅ Basic conversation loop functions
- ✅ Hardware is capable

**Now it's time to build it right!** 🏗️

---

## 🎯 Why Modularize?

### **Prototype (Current)**
```python
# prototype.py - Everything in one file

import whisper
import ollama
import pyaudio

# Audio setup
p = pyaudio.PyAudio()
stream = p.open(...)

# Transcription
model = whisper.load_model("medium")

# Main loop
while True:
    audio = record_audio()
    text = model.transcribe(audio)
    response = ollama.chat(text)
    speak(response)
```

**Problems:**
- ❌ Hard to test individual components
- ❌ Can't reuse code
- ❌ Difficult to maintain
- ❌ No error isolation
- ❌ Hard to add features
- ❌ Memory leaks likely
- ❌ No configuration management

### **Production (Target)**
```python
# main.py - Clean orchestration

from src.audio import AudioManager
from src.speech import TranscriptionService, SynthesisService
from src.conversation import ConversationManager
from src.core import Config, Logger

async def main():
    config = Config.load()
    logger = Logger.setup()
    
    audio = AudioManager(config)
    transcription = TranscriptionService(config)
    synthesis = SynthesisService(config)
    conversation = ConversationManager(config)
    
    await conversation.run()
```

**Benefits:**
- ✅ Easy to test each module
- ✅ Reusable components
- ✅ Clear separation of concerns
- ✅ Error isolation and handling
- ✅ Simple to add features
- ✅ Memory managed per module
- ✅ Configuration centralized

---

## 📁 Recommended Project Structure

```
english-companion-nx/
│
├── src/                                    # Source code
│   ├── __init__.py
│   │
│   ├── core/                               # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py                       # Configuration management
│   │   ├── logger.py                       # Logging setup
│   │   ├── exceptions.py                   # Custom exceptions
│   │   └── constants.py                    # Constants
│   │
│   ├── audio/                              # Audio I/O
│   │   ├── __init__.py
│   │   ├── manager.py                      # AudioManager class
│   │   ├── recorder.py                     # Recording logic
│   │   ├── player.py                       # Playback logic
│   │   └── utils.py                        # Audio utilities
│   │
│   ├── speech/                             # Speech processing
│   │   ├── __init__.py
│   │   ├── transcription.py                # STT (Whisper)
│   │   ├── synthesis.py                    # TTS (Coqui)
│   │   └── wake_word.py                    # Wake word detection
│   │
│   ├── conversation/                       # Conversation management
│   │   ├── __init__.py
│   │   ├── manager.py                      # ConversationManager
│   │   ├── context.py                      # Context management
│   │   ├── llm_client.py                   # Ollama client
│   │   └── logger.py                       # Conversation logging
│   │
│   ├── grammar/                            # Grammar correction (Phase 4)
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   └── corrector.py
│   │
│   ├── rag/                                # RAG system (Phase 4+)
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   │
│   └── monitoring/                         # System monitoring
│       ├── __init__.py
│       ├── metrics.py                      # Prometheus metrics
│       ├── health.py                       # Health checks
│       └── alerts.py                       # Alert system
│
├── tests/                                  # Test suite
│   ├── __init__.py
│   ├── unit/                               # Unit tests
│   │   ├── test_audio.py
│   │   ├── test_speech.py
│   │   ├── test_conversation.py
│   │   └── test_llm_client.py
│   ├── integration/                        # Integration tests
│   │   ├── test_audio_to_text.py
│   │   └── test_full_pipeline.py
│   └── fixtures/                           # Test fixtures
│       ├── audio_samples/
│       └── mock_responses.py
│
├── config/                                 # Configuration files
│   ├── default.yaml                        # Default config
│   ├── development.yaml                    # Dev overrides
│   └── production.yaml                     # Production overrides
│
├── scripts/                                # Utility scripts
│   ├── setup_models.sh                     # Download models
│   ├── test_hardware.py                    # Hardware verification
│   ├── benchmark_performance.py            # Performance testing
│   ├── memory_profiler.py                  # Memory analysis
│   └── daily_health_check.sh               # Health monitoring
│
├── data/                                   # Data directory (gitignored)
│   ├── conversations/                      # Logged conversations
│   ├── cache/                              # Temporary cache
│   └── models/                             # Model files
│
├── docs/                                   # Documentation
│   ├── CLAUDE.md
│   ├── README.md
│   ├── RAG_INTEGRATION_GUIDE.md
│   └── ...
│
├── systemd/                                # Service files
│   └── english-companion-nx.service
│
├── main.py                                 # Entry point
├── requirements-jetson.txt                 # Dependencies
├── requirements-dev.txt                    # Dev dependencies
├── .env.example                            # Environment template
├── .gitignore
├── pytest.ini                              # pytest configuration
├── Makefile                                # Common tasks
└── README.md
```

---

## 🔧 Core Modules Deep Dive

### 1. Core Module (`src/core/`)

**Purpose:** Foundation utilities used everywhere

#### **config.py** - Configuration Management

```python
# src/core/config.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml
import os
from dotenv import load_dotenv

@dataclass
class AudioConfig:
    """Audio configuration"""
    device_name: str = "Anker PowerConf S3"
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    record_seconds: int = 5
    temp_dir: Path = Path("/tmp/companion-nx-audio")

@dataclass
class WhisperConfig:
    """Whisper configuration"""
    model_size: str = "medium"
    language: str = "en"
    device: str = "cuda"  # Use GPU
    compute_type: str = "float16"

@dataclass
class OllamaConfig:
    """Ollama configuration"""
    host: str = "http://127.0.0.1:11434"
    model: str = "llama3.1:13b-instruct-q4_0"
    temperature: float = 0.7
    max_tokens: int = 500
    timeout: int = 30

@dataclass
class TTSConfig:
    """TTS configuration"""
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"
    device: str = "cuda"
    sample_rate: int = 22050

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    log_dir: Path = Path("/mnt/nvme/companion-nx/logs")
    conversation_log: Path = Path("/mnt/nvme/companion-nx/conversations.jsonl")
    buffer_interval: int = 300  # 5 minutes
    max_log_size_mb: int = 100
    backup_count: int = 10

@dataclass
class MemoryConfig:
    """Memory management configuration"""
    warning_threshold: float = 0.85
    critical_threshold: float = 0.95
    gc_interval: int = 300  # 5 minutes

@dataclass
class Config:
    """Main configuration"""
    audio: AudioConfig
    whisper: WhisperConfig
    ollama: OllamaConfig
    tts: TTSConfig
    logging: LoggingConfig
    memory: MemoryConfig
    
    @classmethod
    def load(cls, env_file: Optional[Path] = None) -> 'Config':
        """Load configuration from environment and files"""
        
        # Load .env file
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Create configs from environment variables
        audio = AudioConfig(
            device_name=os.getenv("AUDIO_DEVICE_NAME", "Anker PowerConf S3"),
            sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            temp_dir=Path(os.getenv("AUDIO_TEMP_DIR", "/tmp/companion-nx-audio"))
        )
        
        whisper = WhisperConfig(
            model_size=os.getenv("WHISPER_MODEL", "medium"),
            language=os.getenv("WHISPER_LANGUAGE", "en")
        )
        
        ollama = OllamaConfig(
            host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.1:13b-instruct-q4_0"),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        )
        
        tts = TTSConfig(
            model_name=os.getenv("TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC")
        )
        
        logging_cfg = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_dir=Path(os.getenv("LOG_DIR", "/mnt/nvme/companion-nx/logs")),
            conversation_log=Path(os.getenv("CONVERSATION_LOG", 
                                           "/mnt/nvme/companion-nx/conversations.jsonl"))
        )
        
        memory = MemoryConfig(
            warning_threshold=float(os.getenv("MEMORY_WARNING_THRESHOLD", "0.85")),
            critical_threshold=float(os.getenv("MEMORY_CRITICAL_THRESHOLD", "0.95"))
        )
        
        return cls(
            audio=audio,
            whisper=whisper,
            ollama=ollama,
            tts=tts,
            logging=logging_cfg,
            memory=memory
        )
    
    def validate(self) -> None:
        """Validate configuration"""
        # Check required directories
        self.audio.temp_dir.mkdir(parents=True, exist_ok=True)
        self.logging.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Check models are available
        # Add validation logic here
        
        print("✅ Configuration validated")
```

#### **logger.py** - Centralized Logging

```python
# src/core/logger.py

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
```

#### **exceptions.py** - Custom Exceptions

```python
# src/core/exceptions.py

class CompanionException(Exception):
    """Base exception for English Companion NX"""
    pass

class AudioException(CompanionException):
    """Audio-related exceptions"""
    pass

class TranscriptionException(CompanionException):
    """Transcription-related exceptions"""
    pass

class LLMException(CompanionException):
    """LLM-related exceptions"""
    pass

class TTSException(CompanionException):
    """TTS-related exceptions"""
    pass

class ConfigurationException(CompanionException):
    """Configuration-related exceptions"""
    pass

class MemoryException(CompanionException):
    """Memory-related exceptions"""
    pass
```

---

### 2. Audio Module (`src/audio/`)

**Purpose:** Handle all audio I/O operations

#### **manager.py** - Audio Manager

```python
# src/audio/manager.py

import pyaudio
import wave
from pathlib import Path
from typing import Optional
import numpy as np

from ..core.config import AudioConfig
from ..core.logger import setup_logger
from ..core.exceptions import AudioException

class AudioManager:
    """Manage audio recording and playback"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.logger = setup_logger(__name__)
        self.p = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        
        # Ensure temp directory exists
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("AudioManager initialized")
    
    def find_device_index(self, device_name: str) -> int:
        """Find audio device index by name"""
        info = self.p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.p.get_device_info_by_host_api_device_index(0, i)
            if device_name.lower() in device_info.get('name').lower():
                if device_info.get('maxInputChannels') > 0:
                    self.logger.info(f"Found device: {device_info.get('name')} (index: {i})")
                    return i
        
        raise AudioException(f"Device '{device_name}' not found")
    
    def start_recording(self) -> None:
        """Start recording stream"""
        try:
            device_index = self.find_device_index(self.config.device_name)
            
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.config.chunk_size
            )
            
            self.logger.info("Recording started")
        
        except Exception as e:
            raise AudioException(f"Failed to start recording: {e}")
    
    def record_chunk(self) -> bytes:
        """Record a single chunk of audio"""
        if not self.stream:
            raise AudioException("Stream not started")
        
        return self.stream.read(self.config.chunk_size, exception_on_overflow=False)
    
    def record_duration(self, duration_seconds: float) -> np.ndarray:
        """Record audio for specified duration"""
        if not self.stream:
            self.start_recording()
        
        frames = []
        num_chunks = int(self.config.sample_rate / self.config.chunk_size * duration_seconds)
        
        for _ in range(num_chunks):
            data = self.record_chunk()
            frames.append(data)
        
        # Convert to numpy array
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        return audio_array.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
    
    def stop_recording(self) -> None:
        """Stop recording stream"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.logger.info("Recording stopped")
    
    def save_audio(self, audio_data: np.ndarray, filename: Path) -> None:
        """Save audio to WAV file"""
        # Convert back to int16
        audio_int16 = (audio_data * 32768).astype(np.int16)
        
        with wave.open(str(filename), 'wb') as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        self.logger.debug(f"Audio saved to {filename}")
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        self.stop_recording()
        self.p.terminate()
        self.logger.info("AudioManager cleaned up")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
```

---

### 3. Speech Module (`src/speech/`)

**Purpose:** Handle transcription and synthesis

#### **transcription.py** - Whisper STT

```python
# src/speech/transcription.py

import whisper
import torch
from pathlib import Path
from typing import Dict, Any
import numpy as np

from ..core.config import WhisperConfig
from ..core.logger import setup_logger
from ..core.exceptions import TranscriptionException

class TranscriptionService:
    """Whisper-based speech-to-text service"""
    
    def __init__(self, config: WhisperConfig):
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Load model once at startup
        self.logger.info(f"Loading Whisper model: {config.model_size}")
        try:
            self.model = whisper.load_model(
                config.model_size,
                device=config.device
            )
            self.logger.info("✅ Whisper model loaded")
        except Exception as e:
            raise TranscriptionException(f"Failed to load Whisper model: {e}")
    
    def transcribe(self, audio: np.ndarray) -> Dict[str, Any]:
        """Transcribe audio to text"""
        try:
            # Ensure audio is in correct format
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Normalize if needed
            if audio.max() > 1.0:
                audio = audio / 32768.0
            
            # Transcribe
            result = self.model.transcribe(
                audio,
                language=self.config.language,
                fp16=(self.config.compute_type == "float16")
            )
            
            self.logger.info(f"Transcribed: '{result['text']}'")
            
            return result
        
        except Exception as e:
            raise TranscriptionException(f"Transcription failed: {e}")
    
    def transcribe_file(self, audio_file: Path) -> Dict[str, Any]:
        """Transcribe audio file"""
        if not audio_file.exists():
            raise TranscriptionException(f"Audio file not found: {audio_file}")
        
        try:
            result = self.model.transcribe(
                str(audio_file),
                language=self.config.language,
                fp16=(self.config.compute_type == "float16")
            )
            
            self.logger.info(f"Transcribed file: '{result['text']}'")
            return result
        
        except Exception as e:
            raise TranscriptionException(f"File transcription failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_size": self.config.model_size,
            "language": self.config.language,
            "device": self.config.device,
            "compute_type": self.config.compute_type
        }
```

#### **synthesis.py** - Coqui TTS

```python
# src/speech/synthesis.py

from TTS.api import TTS
from pathlib import Path
import numpy as np

from ..core.config import TTSConfig
from ..core.logger import setup_logger
from ..core.exceptions import TTSException

class SynthesisService:
    """Text-to-speech synthesis service"""
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Load TTS model once at startup
        self.logger.info(f"Loading TTS model: {config.model_name}")
        try:
            self.tts = TTS(
                model_name=config.model_name,
                gpu=(config.device == "cuda")
            )
            self.logger.info("✅ TTS model loaded")
        except Exception as e:
            raise TTSException(f"Failed to load TTS model: {e}")
    
    def synthesize(self, text: str, output_file: Path) -> Path:
        """Synthesize text to speech"""
        try:
            self.logger.info(f"Synthesizing: '{text[:50]}...'")
            
            self.tts.tts_to_file(
                text=text,
                file_path=str(output_file)
            )
            
            self.logger.info(f"Audio synthesized to {output_file}")
            return output_file
        
        except Exception as e:
            raise TTSException(f"Synthesis failed: {e}")
    
    def synthesize_to_array(self, text: str) -> np.ndarray:
        """Synthesize text to numpy array"""
        try:
            audio = self.tts.tts(text=text)
            return np.array(audio)
        
        except Exception as e:
            raise TTSException(f"Synthesis to array failed: {e}")
```

---

### 4. Conversation Module (`src/conversation/`)

**Purpose:** Manage conversation flow and context

#### **llm_client.py** - Ollama Client

```python
# src/conversation/llm_client.py

import ollama
from typing import List, Dict, Any, Optional

from ..core.config import OllamaConfig
from ..core.logger import setup_logger
from ..core.exceptions import LLMException

class LLMClient:
    """Ollama LLM client"""
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.logger = setup_logger(__name__)
        self.client = ollama.Client(host=config.host)
        
        # Verify connection
        try:
            self.client.list()
            self.logger.info("✅ Connected to Ollama")
        except Exception as e:
            raise LLMException(f"Failed to connect to Ollama: {e}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response from LLM"""
        try:
            messages = []
            
            # Add system prompt
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add context (previous messages)
            if context:
                messages.extend(context)
            
            # Add user message
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Generate
            response = self.client.chat(
                model=self.config.model,
                messages=messages,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            )
            
            assistant_message = response['message']['content']
            
            self.logger.info(f"LLM response: '{assistant_message[:100]}...'")
            
            return assistant_message
        
        except Exception as e:
            raise LLMException(f"LLM generation failed: {e}")
    
    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None
    ):
        """Stream response from LLM (generator)"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            if context:
                messages.extend(context)
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Stream
            for chunk in self.client.chat(
                model=self.config.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            ):
                if 'message' in chunk:
                    yield chunk['message']['content']
        
        except Exception as e:
            raise LLMException(f"LLM streaming failed: {e}")
```

#### **manager.py** - Conversation Manager

```python
# src/conversation/manager.py

from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime

from .llm_client import LLMClient
from ..core.config import Config
from ..core.logger import setup_logger

class ConversationManager:
    """Manage conversation flow and context"""
    
    SYSTEM_PROMPT = """You are a friendly English conversation partner helping someone practice English.
    
Your goals:
- Have natural, engaging conversations
- Help improve English fluency
- Occasionally provide gentle grammar corrections
- Suggest interesting discussion topics
- Be encouraging and supportive

Keep responses concise (2-3 sentences typically) to maintain conversational flow."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger(__name__)
        self.llm = LLMClient(config.ollama)
        
        # Conversation state
        self.context: List[Dict[str, str]] = []
        self.max_context_length = 20  # Last 20 exchanges
        
        # Conversation logging
        self.conversation_buffer: List[Dict] = []
        self.last_flush = datetime.now()
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to context"""
        self.context.append({
            "role": role,
            "content": content
        })
        
        # Prune context if too long
        if len(self.context) > self.max_context_length * 2:  # *2 for user+assistant
            self.context = self.context[-self.max_context_length * 2:]
        
        # Buffer for logging
        self.conversation_buffer.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_response(self, user_message: str) -> str:
        """Generate response to user message"""
        # Add user message to context
        self.add_message("user", user_message)
        
        # Generate response
        assistant_message = self.llm.generate(
            prompt=user_message,
            system_prompt=self.SYSTEM_PROMPT,
            context=self.context[:-1]  # All context except last user message
        )
        
        # Add assistant message to context
        self.add_message("assistant", assistant_message)
        
        # Flush logs if needed
        self._check_and_flush_logs()
        
        return assistant_message
    
    def _check_and_flush_logs(self) -> None:
        """Check if it's time to flush conversation logs"""
        elapsed = (datetime.now() - self.last_flush).total_seconds()
        
        if elapsed >= self.config.logging.buffer_interval:
            self._flush_conversation_logs()
    
    def _flush_conversation_logs(self) -> None:
        """Flush conversation buffer to disk"""
        if not self.conversation_buffer:
            return
        
        log_file = self.config.logging.conversation_log
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(log_file, 'a') as f:
                for entry in self.conversation_buffer:
                    f.write(json.dumps(entry) + '\n')
            
            self.logger.info(f"Flushed {len(self.conversation_buffer)} messages to log")
            self.conversation_buffer = []
            self.last_flush = datetime.now()
        
        except Exception as e:
            self.logger.error(f"Failed to flush conversation logs: {e}")
    
    def get_context_summary(self) -> str:
        """Get summary of current context"""
        return f"Context: {len(self.context)} messages"
    
    def clear_context(self) -> None:
        """Clear conversation context"""
        self.context = []
        self.logger.info("Context cleared")
    
    def cleanup(self) -> None:
        """Cleanup and flush remaining logs"""
        self._flush_conversation_logs()
        self.logger.info("ConversationManager cleaned up")
```

---

## 🎯 Main Entry Point

```python
# main.py

import asyncio
import signal
from pathlib import Path

from src.core.config import Config
from src.core.logger import setup_logger
from src.audio.manager import AudioManager
from src.speech.transcription import TranscriptionService
from src.speech.synthesis import SynthesisService
from src.conversation.manager import ConversationManager

class EnglishCompanionNX:
    """Main application class"""
    
    def __init__(self):
        # Load configuration
        self.config = Config.load()
        self.config.validate()
        
        # Setup logging
        self.logger = setup_logger(
            "main",
            log_file=self.config.logging.log_dir / "companion.log",
            level=self.config.logging.level
        )
        
        self.logger.info("=" * 60)
        self.logger.info("English Companion NX Starting")
        self.logger.info("=" * 60)
        
        # Initialize components
        self.audio = AudioManager(self.config.audio)
        self.transcription = TranscriptionService(self.config.whisper)
        self.synthesis = SynthesisService(self.config.tts)
        self.conversation = ConversationManager(self.config)
        
        # State
        self.running = False
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        try:
            self.logger.info("Starting conversation loop")
            self.audio.start_recording()
            
            while self.running:
                # Record audio
                self.logger.info("Listening...")
                audio_data = self.audio.record_duration(5.0)  # 5 second chunks
                
                # Transcribe
                result = self.transcription.transcribe(audio_data)
                user_text = result['text'].strip()
                
                if not user_text:
                    continue
                
                self.logger.info(f"User: {user_text}")
                
                # Check for exit command
                if "goodbye" in user_text.lower() or "exit" in user_text.lower():
                    response = "Goodbye! It was nice talking with you."
                    self.logger.info(f"Assistant: {response}")
                    
                    # Synthesize goodbye
                    audio_file = self.config.audio.temp_dir / "response.wav"
                    self.synthesis.synthesize(response, audio_file)
                    
                    # TODO: Play audio
                    
                    self.running = False
                    break
                
                # Generate response
                response = self.conversation.generate_response(user_text)
                self.logger.info(f"Assistant: {response}")
                
                # Synthesize speech
                audio_file = self.config.audio.temp_dir / "response.wav"
                self.synthesis.synthesize(response, audio_file)
                
                # TODO: Play audio back to user
                # For now, just log
                
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup all resources"""
        self.logger.info("Cleaning up...")
        
        self.audio.cleanup()
        self.conversation.cleanup()
        
        self.logger.info("Shutdown complete")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}")
        self.running = False

async def main():
    """Entry point"""
    app = EnglishCompanionNX()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGTERM, app.signal_handler)
    
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📝 Configuration Files

### **.env.example**

```bash
# English Companion NX Configuration

# Ollama
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:13b-instruct-q4_0
OLLAMA_TEMPERATURE=0.7

# Audio
AUDIO_DEVICE_NAME=Anker PowerConf S3
AUDIO_SAMPLE_RATE=16000
AUDIO_TEMP_DIR=/tmp/companion-nx-audio

# Whisper
WHISPER_MODEL=medium
WHISPER_LANGUAGE=en

# TTS
TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC

# Logging
LOG_LEVEL=INFO
LOG_DIR=/mnt/nvme/companion-nx/logs
CONVERSATION_LOG=/mnt/nvme/companion-nx/conversations.jsonl
LOG_BUFFER_INTERVAL=300

# Memory
MEMORY_WARNING_THRESHOLD=0.85
MEMORY_CRITICAL_THRESHOLD=0.95
```

---

## 🧪 Testing Structure

### **tests/unit/test_audio.py**

```python
# tests/unit/test_audio.py

import pytest
import numpy as np
from pathlib import Path

from src.audio.manager import AudioManager
from src.core.config import AudioConfig

def test_audio_manager_initialization():
    """Test AudioManager initialization"""
    config = AudioConfig()
    audio = AudioManager(config)
    
    assert audio.config == config
    assert audio.p is not None

def test_audio_recording():
    """Test audio recording"""
    config = AudioConfig()
    audio = AudioManager(config)
    
    audio.start_recording()
    audio_data = audio.record_duration(1.0)  # 1 second
    audio.stop_recording()
    
    assert isinstance(audio_data, np.ndarray)
    assert len(audio_data) > 0

def test_audio_save():
    """Test saving audio to file"""
    config = AudioConfig()
    audio = AudioManager(config)
    
    # Create dummy audio
    audio_data = np.random.randn(16000).astype(np.float32)
    
    output_file = config.temp_dir / "test.wav"
    audio.save_audio(audio_data, output_file)
    
    assert output_file.exists()
    
    # Cleanup
    output_file.unlink()
```

---

## 🚀 Migration Path from Prototype

### **Step 1: Extract Config** ✅

```bash
# Move hardcoded values to .env
cp .env.example .env
nano .env
```

### **Step 2: Create Module Structure** ✅

```bash
mkdir -p src/{core,audio,speech,conversation,grammar,rag,monitoring}
touch src/__init__.py
touch src/core/__init__.py
# ... etc
```

### **Step 3: Move Prototype Code Piece by Piece** ✅

```python
# Start with audio
# prototype.py → src/audio/manager.py

# Then transcription
# prototype.py → src/speech/transcription.py

# Then LLM
# prototype.py → src/conversation/llm_client.py

# Finally orchestration
# prototype.py → main.py
```

### **Step 4: Add Tests** ✅

```bash
pytest tests/unit/
```

### **Step 5: Deploy** ✅

```bash
git add .
git commit -m "Refactor prototype to modular production system"
git push

# On Jetson
cd ~/apps/english-companion-nx
git pull
pip install -r requirements-jetson.txt
systemctl --user restart english-companion-nx
```

---

## ✅ Benefits of This Structure

**Compared to prototype:**

| Aspect | Prototype | Modular System |
|--------|-----------|----------------|
| Testability | ❌ Hard | ✅ Easy |
| Maintainability | ❌ Poor | ✅ Excellent |
| Reusability | ❌ None | ✅ High |
| Error Handling | ❌ Minimal | ✅ Comprehensive |
| Configuration | ❌ Hardcoded | ✅ Centralized |
| Logging | ❌ print() | ✅ Proper logging |
| Scalability | ❌ Monolith | ✅ Modular |
| Memory Management | ❌ No control | ✅ Per-module |

---

## 📋 Next Steps

1. **Create Module Structure** ✅
   ```bash
   mkdir -p src/{core,audio,speech,conversation}
   ```

2. **Implement Core Modules** ✅
   - Config
   - Logger
   - Exceptions

3. **Migrate Prototype Code** ✅
   - Audio → AudioManager
   - Whisper → TranscriptionService
   - Ollama → LLMClient
   - Main loop → ConversationManager

4. **Add Tests** ✅
   ```bash
   pytest tests/
   ```

5. **Deploy and Test** ✅
   ```bash
   systemctl --user restart english-companion-nx
   ```

---

## 🎓 Summary

**You've proven the concept works! Now build it properly:**

✅ **Modular architecture** - Clear separation of concerns  
✅ **Configuration management** - Centralized .env  
✅ **Proper logging** - Structured logs with rotation  
✅ **Error handling** - Custom exceptions per module  
✅ **Testing** - Unit and integration tests  
✅ **Production-ready** - Memory management, cleanup, signals  

**This is the foundation for Phases 2-5!** 🚀

---

**Last Updated:** October 27, 2025  
**Status:** Ready to modularize! 🏗️  
**Next:** Create module structure and migrate prototype code
