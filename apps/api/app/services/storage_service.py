"""FM-218: Object storage service (MinIO / S3 compatible).

Large artifact content (patches, PR diffs, test output > 4 KB) is stored
in object storage rather than PostgreSQL TEXT columns.  The DB row keeps
only a `storage_key`; downloads use short-lived signed URLs.

When the minio SDK is unavailable (e.g. in tests) the service falls back
to a local file-system store under /tmp/forgemind_storage so that all code
paths remain exercisable without infrastructure.

Environment:
    STORAGE_ENDPOINT   — MinIO/S3 endpoint (default "localhost:9000")
    STORAGE_ACCESS_KEY — access key (default "minioadmin")
    STORAGE_SECRET_KEY — secret key (default "minioadmin")
    STORAGE_BUCKET     — bucket name (default "forgemind-artifacts")
    STORAGE_SECURE     — "true" for HTTPS (default "false")
    STORAGE_ENABLED    — "false" to force local FS fallback
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import timedelta
from pathlib import Path
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

_ENDPOINT = os.getenv("STORAGE_ENDPOINT", "localhost:9000")
_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY", "minioadmin")
_SECRET_KEY = os.getenv("STORAGE_SECRET_KEY", "minioadmin")
_BUCKET = os.getenv("STORAGE_BUCKET", "forgemind-artifacts")
_SECURE = os.getenv("STORAGE_SECURE", "false").lower() == "true"
_ENABLED = os.getenv("STORAGE_ENABLED", "true").lower() != "false"

_LOCAL_BASE = Path(os.getenv("STORAGE_LOCAL_BASE", "/tmp/forgemind_storage"))
_INLINE_THRESHOLD_BYTES = 4 * 1024  # 4 KB

_minio_client = None
_minio_checked = False


def _get_minio():
    global _minio_client, _minio_checked
    if _minio_checked:
        return _minio_client
    _minio_checked = True
    if not _ENABLED:
        logger.info("storage: STORAGE_ENABLED=false — local FS fallback")
        return None
    try:
        from minio import Minio

        client = Minio(_ENDPOINT, access_key=_ACCESS_KEY, secret_key=_SECRET_KEY, secure=_SECURE)
        # Ensure bucket exists
        if not client.bucket_exists(_BUCKET):
            client.make_bucket(_BUCKET)
        _minio_client = client
        logger.info("storage: MinIO connected at %s bucket=%s", _ENDPOINT, _BUCKET)
    except Exception as exc:
        logger.info("storage: MinIO unavailable (%s) — local FS fallback", exc)
        _minio_client = None
    return _minio_client


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


def _local_path(storage_key: str) -> Path:
    p = _LOCAL_BASE / storage_key.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


async def upload_artifact(content: str | bytes, *, content_type: str = "text/plain") -> str:
    """Upload content and return a storage_key.

    The key is <uuid4>/<uuid4> to avoid hot-spot prefixes.
    """
    if isinstance(content, str):
        data = content.encode()
    else:
        data = content

    storage_key = f"{uuid.uuid4()}/{uuid.uuid4()}"
    client = _get_minio()

    if client is not None:
        import io

        try:
            client.put_object(
                _BUCKET,
                storage_key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            logger.debug("storage: uploaded %s (%d bytes)", storage_key, len(data))
            return storage_key
        except Exception as exc:
            logger.warning("storage: MinIO upload failed (%s) — falling back to FS", exc)

    # Local FS fallback
    _local_path(storage_key).write_bytes(data)
    logger.debug("storage: wrote %s locally (%d bytes)", storage_key, len(data))
    return storage_key


async def get_signed_url(storage_key: str, *, expires_minutes: int = 15) -> str:
    """Return a presigned URL (MinIO) or a local-serve path (fallback)."""
    client = _get_minio()
    if client is not None:
        try:
            url = client.presigned_get_object(
                _BUCKET, storage_key, expires=timedelta(minutes=expires_minutes)
            )
            return url
        except Exception as exc:
            logger.warning("storage: presign failed (%s)", exc)

    # Local fallback — not a real HTTP URL, but usable in testing
    return f"local-storage://{storage_key}"


async def download_artifact(storage_key: str) -> bytes:
    """Download artifact content as raw bytes."""
    client = _get_minio()
    if client is not None:
        try:
            response = client.get_object(_BUCKET, storage_key)
            data = response.read()
            response.close()
            return data
        except Exception as exc:
            logger.warning("storage: MinIO download failed (%s) — trying FS", exc)

    p = _local_path(storage_key)
    if p.exists():
        return p.read_bytes()
    raise FileNotFoundError(f"Storage key not found: {storage_key}")


async def delete_artifact(storage_key: str) -> None:
    """Remove object from storage (called on soft-delete of Artifact)."""
    client = _get_minio()
    if client is not None:
        try:
            client.remove_object(_BUCKET, storage_key)
            return
        except Exception:
            pass

    p = _local_path(storage_key)
    if p.exists():
        p.unlink(missing_ok=True)


def should_offload(content: str | bytes) -> bool:
    """Return True when content exceeds the inline threshold."""
    size = len(content.encode() if isinstance(content, str) else content)
    return size > _INLINE_THRESHOLD_BYTES
