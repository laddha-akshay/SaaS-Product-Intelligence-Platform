"""FastAPI routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.pipeline import run_pipeline
from app.monitoring import MetricsCollector, HealthCheck
from app.feedback import FeedbackCollector

router = APIRouter()
metrics = MetricsCollector()
health = HealthCheck()
feedback = FeedbackCollector()

class Query(BaseModel):
    query: str

class FeedbackRequest(BaseModel):
    query_id: str
    helpful: bool
    feedback: Optional[str] = None

@router.post("/query")
async def query(q: Query) -> Dict[str, Any]:
    """Answer a query about SaaS product metrics."""
    return run_pipeline(q.query)

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """System health and drift detection."""
    h = health.get_health()
    return {
        "status": h["status"],
        "uptime_seconds": h["uptime_seconds"],
        "drift_detected": h["drift_detected"],
        "message": "System operational" if h["status"] == "ok" else "System degraded - check metrics"
    }

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Current system metrics."""
    return metrics.get_current_stats()

@router.post("/feedback")
async def submit_feedback(f: FeedbackRequest) -> Dict[str, str]:
    """Submit feedback on an answer."""
    feedback.log_feedback(f.query_id, f.helpful, f.feedback)
    return {"status": "feedback recorded", "query_id": f.query_id}

@router.get("/feedback/stats")
async def feedback_stats() -> Dict[str, Any]:
    """Feedback statistics."""
    return feedback.get_feedback_stats()

