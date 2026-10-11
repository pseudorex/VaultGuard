import struct
from typing import NamedTuple

MAGIC_HEADER = b"VLTG"
FORMAT_VERSION = 1
ALGORITHM_AES_256_GCM = 1
NONCE_LENGTH = 12
TAG_LENGTH = 16

# Header layout: 4s (magic) + B (version) + B (alg) + B (nonce_len) + B (reserved) = 8 bytes
HEADER_FORMAT = ">4sBBBB"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class EncryptedContainer(NamedTuple):
    version: int
    algorithm: int
    nonce: bytes
    ciphertext_with_tag: bytes


def pack_container(nonce: bytes, ciphertext_with_tag: bytes) -> bytes:
    """Pack nonce and ciphertext with authentication tag into a standardized versioned binary container."""
    if len(nonce) != NONCE_LENGTH:
        raise ValueError(f"Nonce must be exactly {NONCE_LENGTH} bytes")
    
    header = struct.pack(
        HEADER_FORMAT,
        MAGIC_HEADER,
        FORMAT_VERSION,
        ALGORITHM_AES_256_GCM,
        NONCE_LENGTH,
        0  # reserved
    )
    return header + nonce + ciphertext_with_tag


def unpack_container(payload: bytes) -> EncryptedContainer:
    """Unpack a standardized versioned binary container."""
    if len(payload) < HEADER_SIZE + NONCE_LENGTH + TAG_LENGTH:
        raise ValueError("Payload is too short to be a valid VaultGuard encrypted container")

    magic, version, algorithm, nonce_len, _ = struct.unpack(
        HEADER_FORMAT, payload[:HEADER_SIZE]
    )

    if magic != MAGIC_HEADER:
        raise ValueError("Invalid magic header in encrypted container")
    if version != FORMAT_VERSION:
        raise ValueError(f"Unsupported payload version: {version}")
    if algorithm != ALGORITHM_AES_256_GCM:
        raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
    if nonce_len != NONCE_LENGTH:
        raise ValueError(f"Invalid nonce length: {nonce_len}")

    nonce_start = HEADER_SIZE
    nonce_end = nonce_start + NONCE_LENGTH
    nonce = payload[nonce_start:nonce_end]
    ciphertext_with_tag = payload[nonce_end:]

    return EncryptedContainer(
        version=version,
        algorithm=algorithm,
        nonce=nonce,
        ciphertext_with_tag=ciphertext_with_tag
    )
