import os
import pathlib
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
import redis
import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models import KnowledgeItem
from celery_app import celery_app

def require_console_access(x_console_token: Optional[str] = Header(None, alias="X-Console-Token")):
    token = os.getenv("CONSOLE_API_TOKEN")
    if token and x_console_token != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized console access")


router = APIRouter(
    prefix="/internal/console",
    tags=["Console"],
    dependencies=[Depends(require_console_access)],
)

def _now() -> str:
    return datetime.utcnow().isoformat()


def _status_payload(ok: bool, detail: Optional[str] = None) -> Dict[str, Any]:
    return {
        "status": "healthy" if ok else "unhealthy",
        "detail": detail,
        "checked_at": _now(),
    }


def _check_postgres(db: Session) -> Dict[str, Any]:
    try:
        db.execute(text("SELECT 1"))
        return _status_payload(True)
    except Exception as exc:  # pragma: no cover - defensive
        return _status_payload(False, str(exc))


def _check_redis() -> Dict[str, Any]:
    try:
        broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        client = redis.from_url(broker_url)
        client.ping()
        return _status_payload(True)
    except Exception as exc:
        return _status_payload(False, str(exc))


def _check_minio() -> Dict[str, Any]:
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            region_name="us-east-1",
        )
        bucket = os.getenv("MINIO_BUCKET", "synapse")
        s3_client.head_bucket(Bucket=bucket)
        return _status_payload(True)
    except Exception as exc:
        return _status_payload(False, str(exc))


def _check_stt() -> Dict[str, Any]:
    try:
        configured = os.getenv("STT_SERVICE_URL", "http://localhost:5000/transcribe")
        base_url = configured.rsplit("/", 1)[0] if configured.endswith("/transcribe") else configured
        health_url = os.getenv("STT_HEALTH_URL", f"{base_url}/health")
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        detail = f"model={data.get('model')}" if isinstance(data, dict) else None
        return _status_payload(True, detail)
    except Exception as exc:
        return _status_payload(False, str(exc))


def _check_worker() -> Dict[str, Any]:
    try:
        inspector = celery_app.control.inspect(timeout=1)
        if not inspector:
            return _status_payload(False, "Inspector unavailable")
        ping = inspector.ping()
        if not ping:
            return _status_payload(False, "No workers responded")
        workers = ", ".join(ping.keys())
        return _status_payload(True, f"workers={workers}")
    except Exception as exc:
        return _status_payload(False, str(exc))


@router.get("/health")
def get_console_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return {
        "components": {
            "api": _status_payload(True),
            "postgres": _check_postgres(db),
            "redis": _check_redis(),
            "minio": _check_minio(),
            "stt_service": _check_stt(),
            "worker": _check_worker(),
        }
    }


@router.get("/metrics")
def get_console_metrics() -> Dict[str, Any]:
    try:
        inspector = celery_app.control.inspect(timeout=1)
        if not inspector:
            raise RuntimeError("Celery inspector unavailable")
    except Exception as exc:  # pragma: no cover - Celery misconfig
        raise HTTPException(status_code=500, detail=f"Unable to inspect Celery: {exc}")

    stats = inspector.stats() or {}
    active = inspector.active() or {}
    reserved = inspector.reserved() or {}
    scheduled = inspector.scheduled() or {}

    queues: Dict[str, int] = {}
    for dataset in (reserved, scheduled):
        for tasks in dataset.values():
            for task in tasks:
                queue_name = task.get("delivery_info", {}).get("routing_key", task.get("name", "default"))
                queues[queue_name] = queues.get(queue_name, 0) + 1

    metrics = {
        "workers": [
            {
                "name": worker,
                "processed": data.get("total", {}),
                "pid": data.get("pid"),
                "uptime": data.get("uptime"),
                "loadavg": data.get("loadavg"),
            }
            for worker, data in stats.items()
        ],
        "active_tasks": {worker: len(tasks) for worker, tasks in active.items()},
        "queued_tasks": queues,
    }
    return metrics


@router.get("/knowledge-items")
def list_knowledge_items(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    base_query = db.query(KnowledgeItem)
    if status_filter:
        base_query = base_query.filter(KnowledgeItem.status == status_filter)

    total = base_query.count()
    items = (
        base_query.order_by(KnowledgeItem.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "items": [
            {
                "id": str(item.id),
                "source_type": item.source_type,
                "status": item.status,
                "processed_at": item.processed_at.isoformat() if item.processed_at else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "last_error": item.last_error,
                "title": item.title,
                "source_url": item.source_url,
                "has_transcript": bool(item.processed_text_content),
            }
            for item in items
        ],
    }


def _celery_task_for_source(source_type: str) -> str:
    if source_type == "webpage":
        return "tasks.process_webpage"
    if source_type == "voicememo":
        return "tasks.process_voicememo"
    return "tasks.process_media"


@router.post("/knowledge-items/{item_id}/retry")
def retry_knowledge_item(item_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    item: Optional[KnowledgeItem] = (
        db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    task_name = _celery_task_for_source(item.source_type)
    item.status = "pending"
    item.processed_at = None
    item.last_error = None
    item.processed_text_content = None
    item.processed_html_content = None
    db.commit()

    celery_app.send_task(task_name, args=[item_id])
    return {"status": "queued", "task": task_name}


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    last_error: Optional[str] = None


ALLOWED_STATUSES = {"pending", "processing", "ready_for_distillation", "error"}


@router.patch("/knowledge-items/{item_id}")
def update_knowledge_item(
    item_id: str,
    payload: KnowledgeItemUpdate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    item: Optional[KnowledgeItem] = (
        db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if payload.status and payload.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status value",
        )

    if payload.title is None and payload.status is None and payload.last_error is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided",
        )

    if payload.title is not None:
        item.title = payload.title
    if payload.status is not None:
        item.status = payload.status
    if payload.last_error is not None:
        stripped = payload.last_error.strip()
        item.last_error = stripped if stripped else None

    db.commit()
    db.refresh(item)

    return {
        "id": str(item.id),
        "source_type": item.source_type,
        "status": item.status,
        "processed_at": item.processed_at.isoformat() if item.processed_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "last_error": item.last_error,
        "title": item.title,
        "source_url": item.source_url,
        "has_transcript": bool(item.processed_text_content),
    }


@router.get("/logs")
def tail_logs(lines: int = Query(200, ge=1, le=500)) -> Dict[str, Any]:
    log_path = os.getenv("API_LOG_PATH", os.path.join(os.path.dirname(__file__), "app.log"))
    path = pathlib.Path(log_path)
    if not path.exists():
        return {"lines": []}

    with path.open("r") as log_file:
        content = log_file.readlines()

    tail = [line.rstrip("\n") for line in content[-lines:]]
    return {"lines": tail}
