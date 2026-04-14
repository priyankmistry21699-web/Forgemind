"""IP allowlist middleware — enforce CIDR-based access control.

FM-178: Checks incoming request IPs against workspace-scoped allowlists.
Only enforced when the workspace has ip_enforcement_enabled in governance_settings.
Requests to non-workspace routes and health checks are always allowed.
"""

import logging
import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Pattern to extract workspace_id from workspace-scoped API paths
_WORKSPACE_PATH_RE = re.compile(r"/api/v1/workspaces/([0-9a-f-]{36})")


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Middleware that blocks requests from non-allowed IPs for workspaces
    with ip_enforcement_enabled governance setting.

    Enforcement flow:
    1. Extract workspace_id from the URL (if present)
    2. Check if workspace has ip_enforcement_enabled=True
    3. If yes, load active allowlist entries and check client IP
    4. Block with 403 if IP not in any active CIDR range
    """

    async def dispatch(self, request: Request, call_next):
        # Extract workspace_id from path
        match = _WORKSPACE_PATH_RE.search(request.url.path)
        if not match:
            # Not a workspace-scoped route — allow
            return await call_next(request)

        workspace_id_str = match.group(1)

        # Get client IP
        client_ip = request.client.host if request.client else None
        if not client_ip:
            return await call_next(request)

        # Lazy imports to avoid circular dependencies
        import uuid
        from app.db.session import async_session_factory
        from app.models.workspace import Workspace
        from app.services.ip_allowlist_service import (
            get_workspace_allowlist,
            check_ip_against_allowlist,
        )

        try:
            workspace_id = uuid.UUID(workspace_id_str)
        except ValueError:
            return await call_next(request)

        try:
            async with async_session_factory() as db:
                # Check governance settings
                ws = await db.get(Workspace, workspace_id)
                if ws is None:
                    return await call_next(request)

                gov = ws.governance_settings or {}
                if not gov.get("ip_enforcement_enabled", False):
                    return await call_next(request)

                # IP enforcement is enabled — check allowlist
                entries = await get_workspace_allowlist(db, workspace_id)
                if not entries:
                    # No entries configured but enforcement enabled => allow
                    # (admin hasn't configured entries yet)
                    return await call_next(request)

                if not check_ip_against_allowlist(client_ip, entries):
                    logger.warning(
                        "ip_blocked: workspace=%s ip=%s",
                        workspace_id,
                        client_ip,
                    )
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Access denied: IP address not in allowlist"
                        },
                    )
        except Exception:
            # Middleware should not crash the app — fail open with warning
            logger.exception("ip_allowlist_middleware: error checking IP")

        return await call_next(request)
