"""System monitoring and metrics."""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict

class MetricsCollector:
    """Collects and tracks system metrics."""
    
    def __init__(self, metrics_path: str = "logs/metrics.jsonl"):
        self.metrics_path = Path(metrics_path)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_metrics = defaultdict(list)
    
    def record_query(self, query_id: str, latency_ms: float, 
                    retrieval_recall: float, ranker_ndcg: float,
                    llm_refused: bool, confidence: float):
        """Record metrics for a query."""
        record = {
            "query_id": query_id,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
            "retrieval_recall": retrieval_recall,
            "ranker_ndcg": ranker_ndcg,
            "llm_refused": llm_refused,
            "confidence": confidence
        }
        
        with open(self.metrics_path, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        # Track in memory for quick stats
        self.current_metrics["latency"].append(latency_ms)
        self.current_metrics["recall"].append(retrieval_recall)
        self.current_metrics["ndcg"].append(ranker_ndcg)
        self.current_metrics["refused"].append(llm_refused)
        self.current_metrics["confidence"].append(confidence)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get statistics of current session."""
        stats = {}
        
        for metric_name, values in self.current_metrics.items():
            if values:
                stats[f"{metric_name}_p50"] = sorted(values)[len(values)//2]
                stats[f"{metric_name}_p95"] = sorted(values)[int(len(values)*0.95)]
                stats[f"{metric_name}_mean"] = sum(values) / len(values)
        
        return stats
    
    def detect_drift(self) -> Dict[str, Any]:
        """Detect if metrics have drifted from baseline."""
        stats = self.get_current_stats()
        
        # Simple drift detection: compare recent stats to thresholds
        baseline = {
            "latency_p95_ms": 1000,
            "recall_mean": 0.7,
            "refused_rate": 0.1
        }
        
        drift_detected = {}
        
        if stats.get("latency_p95") and stats["latency_p95"] > baseline["latency_p95_ms"]:
            drift_detected["latency"] = f"P95 latency {stats['latency_p95']} > {baseline['latency_p95_ms']}"
        
        if stats.get("recall_mean") and stats["recall_mean"] < baseline["recall_mean"]:
            drift_detected["recall"] = f"Recall {stats['recall_mean']} < {baseline['recall_mean']}"
        
        refused = sum(1 for r in self.current_metrics["refused"] if r) / len(self.current_metrics["refused"]) if self.current_metrics["refused"] else 0
        if refused > baseline["refused_rate"]:
            drift_detected["refusal"] = f"Refusal rate {refused} > {baseline['refused_rate']}"
        
        return drift_detected

class HealthCheck:
    """Health check endpoint data."""
    
    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.startup_time = datetime.utcnow()
    
    def get_health(self) -> Dict[str, Any]:
        """Return health check status."""
        uptime_seconds = (datetime.utcnow() - self.startup_time).total_seconds()
        
        drift = self.metrics.detect_drift()
        is_healthy = len(drift) == 0
        
        return {
            "status": "ok" if is_healthy else "degraded",
            "uptime_seconds": uptime_seconds,
            "drift_detected": drift,
            "timestamp": datetime.utcnow().isoformat()
        }

