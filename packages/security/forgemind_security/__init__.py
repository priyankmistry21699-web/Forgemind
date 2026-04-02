"""forgemind-security — Authentication and authorization for the ForgeMind platform.

Provides JWT token helpers and pure RBAC permission matrices.
"""

from forgemind_security.jwt import create_token, decode_token, JWTConfig
from forgemind_security.rbac import (
    Action,
    WORKSPACE_PERMISSIONS,
    PROJECT_PERMISSIONS,
    is_workspace_action_allowed,
    is_project_action_allowed,
)

__all__ = [
    "create_token",
    "decode_token",
    "JWTConfig",
    "Action",
    "WORKSPACE_PERMISSIONS",
    "PROJECT_PERMISSIONS",
    "is_workspace_action_allowed",
    "is_project_action_allowed",
]
