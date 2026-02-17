"""Feedback collection and logging."""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

class FeedbackCollector:
    """Collects and logs user feedback for continuous improvement."""
    
    def __init__(self, log_path: str = "logs/feedback.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_interaction(self, query: str, answer: Dict[str, Any], 
                       user_feedback: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a query-answer interaction and optional user feedback.
        
        Args:
            query: user query
            answer: response from reasoning layer
            user_feedback: {"helpful": bool, "corrected_answer": str, "rating": int}
        
        Returns:
            interaction_id for tracking
        """
        interaction_id = str(uuid.uuid4())
        
        record = {
            "interaction_id": interaction_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "answer": answer.get("answer"),
            "citations": answer.get("citations", []),
            "confidence": answer.get("confidence", 0.0),
            "refused": answer.get("refused", False),
            "user_feedback": user_feedback or {}
        }
        
        # Append to JSONL log
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        return interaction_id
    
    def load_feedback_logs(self, limit: int = 1000) -> list:
        """Load recent feedback logs for analysis."""
        logs = []
        if not self.log_path.exists():
            return logs
        
        with open(self.log_path, 'r') as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        return logs
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Compute feedback statistics for monitoring."""
        logs = self.load_feedback_logs()
        if not logs:
            return {"total": 0}
        
        total = len(logs)
        refused = sum(1 for l in logs if l.get("refused", False))
        with_feedback = sum(1 for l in logs if l.get("user_feedback", {}))
        helpful = sum(1 for l in logs if l.get("user_feedback", {}).get("helpful", False))
        
        avg_confidence = sum(l.get("confidence", 0) for l in logs) / total if total > 0 else 0
        
        return {
            "total_interactions": total,
            "refused_rate": refused / total if total > 0 else 0,
            "feedback_rate": with_feedback / total if total > 0 else 0,
            "helpful_rate": helpful / with_feedback if with_feedback > 0 else 0,
            "avg_confidence": avg_confidence
        }
    
    def log_feedback(self, interaction_id: str, helpful: bool, feedback: Optional[str] = None) -> None:
        """Update an interaction with user feedback."""
        logs = self.load_feedback_logs(limit=10000)
        
        # Find and update interaction
        updated = False
        for log in logs:
            if log.get("interaction_id") == interaction_id:
                log["user_feedback"] = {
                    "helpful": helpful,
                    "feedback": feedback,
                    "feedback_timestamp": datetime.utcnow().isoformat()
                }
                updated = True
                break
        
        if updated:
            # Rewrite log file
            with open(self.log_path, 'w') as f:
                for log in logs:
                    f.write(json.dumps(log) + '\n')

