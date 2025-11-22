"""ScribeSparrow agent for centralized logging.

ScribeSparrow is responsible for persisting data about the user's sessions,
including utterance logs and session summaries.
"""

import json
import time
import os
from typing import Dict, Any, List
from dataclasses import asdict

class ScribeSparrow:
    """Agent responsible for logging and data persistence."""

    def __init__(self, data_dir: str = "data/progress"):
        """
        Args:
            data_dir: Base directory for storing logs.
        """
        self.data_dir = data_dir
        self.utterance_log_path = os.path.join(data_dir, "utterance_logs.jsonl")
        self.session_dir = os.path.join(data_dir, "session_summaries")
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.session_dir, exist_ok=True)

    def log_utterance(self, utterance_data: Dict[str, Any]):
        """Append an utterance record to the JSONL log.
        
        Args:
            utterance_data: Dictionary containing utterance details, signals, etc.
        """
        # Add timestamp if missing
        if "timestamp" not in utterance_data:
            utterance_data["timestamp"] = time.time()
            
        # Append to file
        try:
            with open(self.utterance_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(utterance_data) + "\n")
        except Exception as e:
            print(f"ScribeSparrow Error logging utterance: {e}")

    def save_session_summary(self, session_data: Dict[str, Any]) -> str:
        """Save a session summary to a JSON file.
        
        Args:
            session_data: Dictionary containing session stats.
            
        Returns:
            Path to the saved file.
        """
        session_id = session_data.get("session_id", f"session_{int(time.time())}")
        filename = f"{session_id}.json"
        filepath = os.path.join(self.session_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2)
            return filepath
        except Exception as e:
            print(f"ScribeSparrow Error saving session summary: {e}")
            return ""

    def get_recent_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent utterance logs (e.g., for dashboard).
        
        Args:
            limit: Max number of records to return (from end of file).
            
        Returns:
            List of utterance records.
        """
        logs = []
        try:
            if not os.path.exists(self.utterance_log_path):
                return []
                
            # Efficiently read last N lines (simple implementation for MVP)
            with open(self.utterance_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"ScribeSparrow Error reading stats: {e}")
    def generate_session_summary(
        self,
        session_id: str,
        utterances: List[Dict[str, Any]],
        start_time: float,
        end_time: float,
        focus: str,
        session_type: str
    ) -> Dict[str, Any]:
        """Generate a summary of the session statistics.
        
        Args:
            session_id: Unique session identifier.
            utterances: List of utterance records from the session.
            start_time: Unix timestamp of session start.
            end_time: Unix timestamp of session end.
            focus: The session's focus area.
            session_type: Type of session (quick, full, free).
            
        Returns:
            Dictionary containing the session summary.
        """
        duration_min = (end_time - start_time) / 60.0
        
        # Initialize stats
        total_words = 0
        fillers_detected = 0
        grammar_errors = 0
        vocab_used = set()
        drills_offered = 0
        drills_completed = 0
        
        # Aggregate from utterances
        for u in utterances:
            # Word count (rough estimate)
            text = u.get("text", "")
            total_words += len(text.split())
            
            # Signals
            for signal in u.get("signals", []):
                sig_type = signal.get("type")
                if sig_type == "filler_detected":
                    fillers_detected += signal.get("data", {}).get("count", 0)
                elif sig_type == "grammar_error":
                    grammar_errors += 1
                elif sig_type == "vocab_used":
                    word = signal.get("data", {}).get("word")
                    if word:
                        vocab_used.add(word)
                        
            # Actions/Drills
            action = u.get("action", {})
            if action.get("type") == "drill":
                drills_offered += 1
                if action.get("completed"):
                    drills_completed += 1

        # Calculate rates
        wpm = (total_words / duration_min) if duration_min > 0 else 0
        filler_rate = (fillers_detected / duration_min) if duration_min > 0 else 0
        
        summary = {
            "session_id": session_id,
            "date": time.strftime("%Y-%m-%d", time.localtime(start_time)),
            "type": session_type,
            "focus": focus,
            "duration_min": round(duration_min, 1),
            "stats": {
                "total_utterances": len(utterances),
                "total_words": total_words,
                "wpm": round(wpm, 1),
                "fillers_detected": fillers_detected,
                "filler_rate_per_min": round(filler_rate, 1),
                "grammar_errors": grammar_errors,
                "vocab_used_count": len(vocab_used),
                "vocab_list": list(vocab_used)
            },
            "drills": {
                "offered": drills_offered,
                "completed": drills_completed,
                "completion_rate": round(drills_completed / drills_offered, 2) if drills_offered > 0 else 0.0
            }
        }
        
        return summary

