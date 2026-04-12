"""Audit logging — DB-backed events for accountability."""

from app.modules.audit_logs.service import record_audit_event

__all__ = ["record_audit_event"]
