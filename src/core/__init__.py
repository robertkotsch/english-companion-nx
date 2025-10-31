"""Core modules for English Companion NX"""

from .config import Config
from .memory import MemoryMonitor, get_memory_info

__all__ = ['Config', 'MemoryMonitor', 'get_memory_info']
