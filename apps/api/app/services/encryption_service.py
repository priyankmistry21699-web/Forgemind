"""Encryption service — AES-256-GCM symmetric encryption for secrets.

FM-179: Provides encrypt/decrypt functions using a master key from
the FORGEMIND_ENCRYPTION_KEY environment variable. The key must be
a 32-byte (64 hex character) value.

Each ciphertext is prefixed with a 12-byte random nonce.
Format: nonce (12 bytes) + ciphertext + tag (16 bytes)
"""

import os
import secrets
import binascii

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_KEY_ENV = "FORGEMIND_ENCRYPTION_KEY"
_NONCE_SIZE = 12


def validate_encryption_key() -> None:
    """M-21: Call at startup to fail fast when the encryption key is absent or weak.

    Raises RuntimeError rather than letting a missing key cause silent plaintext
    storage later when encrypt() is called mid-request.
    """
    raw = os.environ.get(_KEY_ENV, "")
    if not raw:
        raise RuntimeError(
            f"{_KEY_ENV} is not set. "
            'Generate a key with: python -c "from app.services.encryption_service import generate_key_hex; print(generate_key_hex())"'
        )
    try:
        key = binascii.unhexlify(raw)
    except (ValueError, binascii.Error):
        raise RuntimeError(f"{_KEY_ENV} must be a valid hex string")
    if len(key) != 32:
        raise RuntimeError(f"{_KEY_ENV} must be exactly 32 bytes (64 hex chars)")


def _get_key() -> bytes:
    """Load the 256-bit master key from the environment."""
    raw = os.environ.get(_KEY_ENV, "")
    if not raw:
        raise RuntimeError(f"{_KEY_ENV} environment variable is not set")
    try:
        key = binascii.unhexlify(raw)
    except (ValueError, binascii.Error):
        raise RuntimeError(f"{_KEY_ENV} must be a valid hex string")
    if len(key) != 32:
        raise RuntimeError(f"{_KEY_ENV} must be exactly 32 bytes (64 hex chars)")
    return key


def encrypt(plaintext: str) -> bytes:
    """Encrypt a plaintext string → nonce + ciphertext + tag bytes."""
    key = _get_key()
    nonce = secrets.token_bytes(_NONCE_SIZE)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct


def decrypt(data: bytes) -> str:
    """Decrypt nonce-prefixed ciphertext → plaintext string."""
    if len(data) < _NONCE_SIZE + 16:
        raise ValueError("Ciphertext too short")
    key = _get_key()
    nonce = data[:_NONCE_SIZE]
    ct = data[_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def generate_key_hex() -> str:
    """Generate a new random 256-bit key as a hex string (utility)."""
    return secrets.token_hex(32)
