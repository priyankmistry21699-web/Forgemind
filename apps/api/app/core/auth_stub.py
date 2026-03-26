"""Temporary auth stub — replaced by Clerk JWT extraction in FM-011+.

Provides a FastAPI dependency that returns a hardcoded owner UUID.
All routes that need the current user should depend on `get_current_user_id`
so that swapping in real auth requires changing only this file.
"""

import uuid

from fastapi import Depends

# Placeholder until Clerk is wired
_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user_id() -> uuid.UUID:
    """Return the authenticated user's ID.

    TODO(FM-011): Replace with Clerk JWT token verification.
    """
    return _STUB_USER_ID
