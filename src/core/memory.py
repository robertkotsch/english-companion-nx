"""
Memory monitoring and management for English Companion NX

Tracks system and GPU memory usage, provides cleanup utilities,
and prevents OOM errors on Jetson Orin NX (16GB RAM limit).
"""

import gc
import time
import psutil
from typing import Dict, Optional
from datetime import datetime

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from src.core.config import Config


class MemoryMonitor:
    """Monitor and manage system memory usage"""

    def __init__(
        self,
        warning_threshold: float = 0.85,
        critical_threshold: float = 0.95,
        cleanup_interval: int = 10
    ):
        """
        Initialize memory monitor

        Args:
            warning_threshold: Memory usage % to trigger warning (default: 85%)
            critical_threshold: Memory usage % to trigger critical action (default: 95%)
            cleanup_interval: Perform cleanup every N conversations (default: 10)
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.cleanup_interval = cleanup_interval

        # Track conversation count for periodic cleanup
        self.conversation_count = 0
        self.last_cleanup_time = time.time()

        # GPU availability
        self.gpu_available = TORCH_AVAILABLE and torch.cuda.is_available()

        # Memory statistics
        self.stats = {
            "peak_ram_percent": 0.0,
            "peak_ram_mb": 0,
            "total_cleanups": 0,
            "warnings_triggered": 0,
            "critical_triggered": 0
        }

        print(f"🧠 Memory monitor initialized")
        print(f"   Warning threshold: {self.warning_threshold * 100:.0f}%")
        print(f"   Critical threshold: {self.critical_threshold * 100:.0f}%")
        print(f"   Cleanup interval: every {self.cleanup_interval} conversations")

    def get_system_memory(self) -> Dict[str, float]:
        """
        Get current system memory usage

        Returns:
            Dict with total, used, available, and percent
        """
        mem = psutil.virtual_memory()

        return {
            "total_mb": mem.total / (1024 * 1024),
            "used_mb": mem.used / (1024 * 1024),
            "available_mb": mem.available / (1024 * 1024),
            "percent": mem.percent / 100.0  # Convert to 0-1 range
        }

    def get_gpu_memory(self) -> Optional[Dict[str, float]]:
        """
        Get current GPU memory usage (if CUDA available)

        Returns:
            Dict with allocated, reserved, and total memory, or None
        """
        if not self.gpu_available:
            return None

        try:
            allocated = torch.cuda.memory_allocated(0) / (1024 * 1024)  # MB
            reserved = torch.cuda.memory_reserved(0) / (1024 * 1024)    # MB
            total = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)

            return {
                "allocated_mb": allocated,
                "reserved_mb": reserved,
                "total_mb": total,
                "percent": allocated / total if total > 0 else 0.0
            }
        except Exception as e:
            print(f"⚠️  Failed to get GPU memory: {e}")
            return None

    def check_memory_status(self) -> Dict[str, any]:
        """
        Check current memory status and determine if action needed

        Returns:
            Dict with status, system_memory, gpu_memory, and action_needed
        """
        sys_mem = self.get_system_memory()
        gpu_mem = self.get_gpu_memory()

        # Update peak stats
        if sys_mem["percent"] > self.stats["peak_ram_percent"]:
            self.stats["peak_ram_percent"] = sys_mem["percent"]
            self.stats["peak_ram_mb"] = sys_mem["used_mb"]

        # Determine status
        ram_percent = sys_mem["percent"]

        if ram_percent >= self.critical_threshold:
            status = "critical"
            action_needed = "immediate_cleanup"
            self.stats["critical_triggered"] += 1
        elif ram_percent >= self.warning_threshold:
            status = "warning"
            action_needed = "schedule_cleanup"
            self.stats["warnings_triggered"] += 1
        else:
            status = "ok"
            action_needed = None

        return {
            "status": status,
            "system_memory": sys_mem,
            "gpu_memory": gpu_mem,
            "action_needed": action_needed,
            "timestamp": datetime.now().isoformat()
        }

    def cleanup(self, force: bool = False):
        """
        Perform memory cleanup

        Args:
            force: Force cleanup even if interval not reached
        """
        if not force:
            # Check if cleanup interval reached
            if self.conversation_count % self.cleanup_interval != 0:
                return

        print("🧹 Running memory cleanup...")
        start_time = time.time()

        # Get memory before cleanup
        before = self.get_system_memory()

        # Run Python garbage collection
        collected = gc.collect()

        # Clear CUDA cache if GPU available
        if self.gpu_available:
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        # Get memory after cleanup
        after = self.get_system_memory()

        cleanup_time = time.time() - start_time
        freed_mb = before["used_mb"] - after["used_mb"]

        self.stats["total_cleanups"] += 1
        self.last_cleanup_time = time.time()

        print(f"✅ Cleanup complete ({cleanup_time:.2f}s)")
        print(f"   Objects collected: {collected}")
        print(f"   Memory freed: {freed_mb:.1f} MB")
        print(f"   RAM usage: {before['percent']*100:.1f}% → {after['percent']*100:.1f}%")

    def on_conversation_complete(self):
        """
        Call this after each conversation completes

        Increments counter and performs periodic cleanup
        """
        self.conversation_count += 1

        # Check memory status
        status = self.check_memory_status()

        # Handle critical memory
        if status["action_needed"] == "immediate_cleanup":
            print(f"⚠️  CRITICAL: RAM at {status['system_memory']['percent']*100:.1f}%")
            self.cleanup(force=True)
            return

        # Handle warning
        if status["action_needed"] == "schedule_cleanup":
            print(f"⚠️  WARNING: RAM at {status['system_memory']['percent']*100:.1f}%")

        # Regular periodic cleanup
        if self.conversation_count % self.cleanup_interval == 0:
            self.cleanup(force=False)

    def get_memory_summary(self) -> str:
        """
        Get human-readable memory summary

        Returns:
            Formatted string with current memory stats
        """
        sys_mem = self.get_system_memory()
        gpu_mem = self.get_gpu_memory()

        summary = f"RAM: {sys_mem['used_mb']:.0f}/{sys_mem['total_mb']:.0f} MB ({sys_mem['percent']*100:.1f}%)"

        if gpu_mem:
            summary += f" | GPU: {gpu_mem['allocated_mb']:.0f}/{gpu_mem['total_mb']:.0f} MB ({gpu_mem['percent']*100:.1f}%)"

        return summary

    def log_memory_stats(self):
        """Log detailed memory statistics"""
        sys_mem = self.get_system_memory()
        gpu_mem = self.get_gpu_memory()

        print("\n" + "=" * 60)
        print("📊 Memory Statistics")
        print("=" * 60)
        print(f"Conversations processed: {self.conversation_count}")
        print(f"Total cleanups: {self.stats['total_cleanups']}")
        print(f"Warnings triggered: {self.stats['warnings_triggered']}")
        print(f"Critical alerts: {self.stats['critical_triggered']}")
        print()
        print(f"Current RAM: {sys_mem['used_mb']:.0f} MB / {sys_mem['total_mb']:.0f} MB ({sys_mem['percent']*100:.1f}%)")
        print(f"Available RAM: {sys_mem['available_mb']:.0f} MB")
        print(f"Peak RAM usage: {self.stats['peak_ram_mb']:.0f} MB ({self.stats['peak_ram_percent']*100:.1f}%)")

        if gpu_mem:
            print()
            print(f"GPU allocated: {gpu_mem['allocated_mb']:.0f} MB")
            print(f"GPU reserved: {gpu_mem['reserved_mb']:.0f} MB")
            print(f"GPU total: {gpu_mem['total_mb']:.0f} MB")
            print(f"GPU usage: {gpu_mem['percent']*100:.1f}%")

        print("=" * 60 + "\n")

    def get_stats(self) -> Dict:
        """
        Get memory statistics dictionary

        Returns:
            Dict with all tracked statistics
        """
        status = self.check_memory_status()

        return {
            "conversation_count": self.conversation_count,
            "system_memory": status["system_memory"],
            "gpu_memory": status["gpu_memory"],
            "peak_ram_percent": self.stats["peak_ram_percent"],
            "peak_ram_mb": self.stats["peak_ram_mb"],
            "total_cleanups": self.stats["total_cleanups"],
            "warnings_triggered": self.stats["warnings_triggered"],
            "critical_triggered": self.stats["critical_triggered"],
            "status": status["status"]
        }


def get_memory_info() -> Dict[str, float]:
    """
    Quick function to get current memory info without creating monitor

    Returns:
        Dict with system and GPU memory info
    """
    mem = psutil.virtual_memory()

    info = {
        "ram_total_mb": mem.total / (1024 * 1024),
        "ram_used_mb": mem.used / (1024 * 1024),
        "ram_percent": mem.percent / 100.0
    }

    if TORCH_AVAILABLE and torch.cuda.is_available():
        try:
            info["gpu_allocated_mb"] = torch.cuda.memory_allocated(0) / (1024 * 1024)
            info["gpu_total_mb"] = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
        except Exception:
            pass

    return info
