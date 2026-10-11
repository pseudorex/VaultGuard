import os
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from app.core.errors import TamperDetectedException
from app.crypto.formats import (
    NONCE_LENGTH,
    pack_container,
    unpack_container
)

KEY_SIZE_BYTES = 32  # 256 bits


def generate_dek() -> bytes:
    """Generate a cryptographically secure 256-bit Data Encryption Key (DEK)."""
    return os.urandom(KEY_SIZE_BYTES)


def generate_nonce() -> bytes:
    """Generate a cryptographically secure 96-bit (12-byte) nonce for AES-GCM."""
    return os.urandom(NONCE_LENGTH)


def encrypt_bytes(plaintext: bytes, dek: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext using AES-256-GCM.
    Returns: (nonce, packed_container_bytes)
    """
    if len(dek) != KEY_SIZE_BYTES:
        raise ValueError(f"DEK must be {KEY_SIZE_BYTES} bytes (256 bits)")

    nonce = generate_nonce()
    aesgcm = AESGCM(dek)
    
    # AESGCM.encrypt appends the 16-byte authentication tag to the ciphertext
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)
    
    # Pack into container format
    container_bytes = pack_container(nonce, ciphertext_with_tag)
    return nonce, container_bytes


def decrypt_container(container_bytes: bytes, dek: bytes) -> bytes:
    """
    Authenticate and decrypt a VaultGuard container payload.
    Raises TamperDetectedException if authentication fails.
    """
    if len(dek) != KEY_SIZE_BYTES:
        raise ValueError(f"DEK must be {KEY_SIZE_BYTES} bytes (256 bits)")

    try:
        container = unpack_container(container_bytes)
    except ValueError as e:
        raise TamperDetectedException(f"Container format invalid: {str(e)}")

    aesgcm = AESGCM(dek)
    try:
        plaintext = aesgcm.decrypt(container.nonce, container.ciphertext_with_tag, None)
        return plaintext
    except InvalidTag:
        raise TamperDetectedException("AES-GCM authentication tag verification failed. Ciphertext has been tampered with or corrupted.")


def verify_ciphertext_integrity(container_bytes: bytes, dek: bytes) -> bool:
    """
    Verify the cryptographic integrity of the ciphertext using the reconstructed DEK.
    Returns True if valid, False if tampered.
    """
    try:
        decrypt_container(container_bytes, dek)
        return True
    except TamperDetectedException:
        return False
    except Exception:
        return False
