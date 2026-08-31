from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends, Request, Response, status as http_status

from ...auth import Identity
from ...permissions import ROLE_FULL_CONTROL, role_allows
from ...version import VERSION
from ..dependencies import (
    document_effective_role,
    public_document_meta,
    require_identity,
    services,
    visible_library_ids,
)


router = APIRouter(tags=["system"])


def application_version() -> str:
    return VERSION


def status_payload(request: Request, identity: Identity | None = None) -> dict[str, Any]:
    container = services(request)
    role = container.role()
    floating = container.floating_ip.status()
    sync = container.store.sync_status()
    if identity is not None:
        visible_documents = [
            item for item in container.store.list_documents(include_deleted=True)
            if document_effective_role(request, identity, item) is not None
        ]
        sync = {
            **sync,
            "documents": len(visible_documents),
            "active_documents": sum(1 for item in visible_documents if item.get("status") != "deleted"),
        }
    return {
        "node": container.settings.node_name,
        "role": role.role,
        "role_reason": role.reason,
        "owns_floating_ip": role.owns_floating_ip,
        "floating_ip": container.floating_ip.effective_ip or None,
        "floating_url": container.floating_ip.active_url or None,
        "active_url": container.floating_ip.active_url or None,
        "floating_ip_connector": floating,
        "retention_days": container.settings.retention_days,
        "sync_interval_seconds": container.settings.sync_interval_seconds,
        "max_image_size_mb": container.settings.max_image_size_mb,
        "sync": sync,
        "peers_configured": list(container.settings.peers),
        "git": container.store.git_status(),
        "version": application_version(),
    }


def public_status_payload(request: Request) -> dict[str, Any]:
    container = services(request)
    role = container.role()
    connector = container.floating_ip.status()
    return {
        "node": container.settings.node_name,
        "role": role.role,
        "role_reason": role.reason,
        "active_url": container.floating_ip.active_url or None,
        "floating_ip_connector": {
            "state": connector["state"],
            "error": connector["error"],
        },
        "sync_interval_seconds": container.settings.sync_interval_seconds,
        "version": application_version(),
    }


@router.get("/health")
def health(request: Request, response: Response) -> dict[str, Any]:
    container = services(request)
    role = container.role()
    connector = container.floating_ip.status()
    state = "unknown" if role.role == "unknown" else "degraded" if connector["state"] == "degraded" else "ok"
    if state == "unknown":
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": state,
        "role": role.role,
        "version": application_version(),
        "floating_ip_connector": connector["state"],
    }


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": application_version()}


@router.get("/public-status")
def public_status(request: Request) -> dict[str, Any]:
    return public_status_payload(request)


@router.get("/status")
def status(request: Request, identity: Identity = Depends(require_identity)) -> dict[str, Any]:
    return status_payload(request, identity)


@router.get("/dashboard")
def dashboard(request: Request, identity: Identity = Depends(require_identity)) -> dict[str, Any]:
    container = services(request)
    library_ids = visible_library_ids(request, identity)
    documents = [
        item for item in container.store.list_documents(include_deleted=True)
        if document_effective_role(request, identity, item) is not None
    ]
    statuses = Counter(item.get("status", "active") for item in documents)
    recent = [
        public_document_meta(request, identity, item)
        for item in documents if item.get("status") != "deleted"
    ][:8]
    administrative = (
        identity.identity_type == "person"
        and bool(identity.user_id)
        and role_allows(identity.role, ROLE_FULL_CONTROL)
    )
    return {
        "status": status_payload(request, identity),
        "counts": {
            "libraries": len(library_ids),
            "categories": sum(
                1 for category in container.store.list_categories()
                if str(category.get("library_id")) in library_ids
            ),
            "documents": statuses.get("active", 0),
            "archived": statuses.get("archived", 0),
            "deleted": statuses.get("deleted", 0),
        },
        "recent_documents": recent,
        "recent_activity": container.store.read_audit_page(limit=8)["items"] if administrative else [],
    }
