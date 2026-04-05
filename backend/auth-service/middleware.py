from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy.orm import Session

import models

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_ctx.set(cid)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


def log_audit_event(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    detail: Optional[str] = None,
):
    event = models.AuditEvent(
        correlation_id=get_correlation_id(),
        user_id=user_id,
        user_email=user_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(event)
    db.commit()
