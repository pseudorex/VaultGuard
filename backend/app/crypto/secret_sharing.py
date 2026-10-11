import os
from typing import List, Tuple

# Galois Field GF(2^8) with AES irreducible polynomial: x^8 + x^4 + x^3 + x + 1 (0x11B)
# Generator alpha = 3 (0x03)
GF_EXP = [0] * 512
GF_LOG = [0] * 256

def _init_gf_tables():
    x = 1
    for i in range(255):
        GF_EXP[i] = x
        GF_LOG[x] = i
        # Multiply by 3 in GF(2^8)
        # x * 3 = (x * 2) ^ x
        x2 = (x << 1) ^ (0x11B if (x & 0x80) else 0)
        x = x2 ^ x
    for i in range(255, 512):
        GF_EXP[i] = GF_EXP[i - 255]

_init_gf_tables()


def gf_add(a: int, b: int) -> int:
    """Addition in GF(2^8) is bitwise XOR."""
    return a ^ b


def gf_sub(a: int, b: int) -> int:
    """Subtraction in GF(2^8) is bitwise XOR."""
    return a ^ b


def gf_mul(a: int, b: int) -> int:
    """Multiplication in GF(2^8)."""
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]


def gf_div(a: int, b: int) -> int:
    """Division in GF(2^8)."""
    if b == 0:
        raise ZeroDivisionError("Division by zero in GF(2^8)")
    if a == 0:
        return 0
    return GF_EXP[(GF_LOG[a] - GF_LOG[b] + 255) % 255]


def evaluate_polynomial(coefficients: List[int], x: int) -> int:
    """
    Evaluate polynomial f(x) = c_0 + c_1 * x + ... + c_{k-1} * x^{k-1} in GF(2^8).
    coefficients[0] is the secret constant term c_0.
    """
    result = 0
    for coef in reversed(coefficients):
        result = gf_add(gf_mul(result, x), coef)
    return result


def lagrange_interpolate_zero(points: List[Tuple[int, int]]) -> int:
    """
    Find f(0) using Lagrange interpolation in GF(2^8) from points (x_i, y_i).
    f(0) = sum_i [ y_i * prod_{j != i} (0 - x_j) / (x_i - x_j) ]
    """
    secret = 0
    k = len(points)
    for i in range(k):
        xi, yi = points[i]
        num = 1
        den = 1
        for j in range(k):
            if i == j:
                continue
            xj, _ = points[j]
            # (0 - xj) in GF(2^8) is xj
            num = gf_mul(num, xj)
            # (xi - xj) in GF(2^8) is xi ^ xj
            den = gf_mul(den, gf_sub(xi, xj))
        
        basis = gf_div(num, den)
        term = gf_mul(yi, basis)
        secret = gf_add(secret, term)
    return secret


def split_secret(secret_bytes: bytes, threshold: int = 2, total_shares: int = 3) -> List[str]:
    """
    Split arbitrary secret bytes into `total_shares` shares with recovery `threshold` k-of-n.
    Returns list of formatted share strings: "<index>:<hex_payload>".
    """
    if threshold < 2:
        raise ValueError("Threshold must be at least 2")
    if total_shares < threshold:
        raise ValueError("Total shares cannot be less than threshold")
    if total_shares > 255:
        raise ValueError("Total shares cannot exceed 255 in GF(2^8)")
    if not secret_bytes:
        raise ValueError("Secret bytes cannot be empty")

    shares_data = [bytearray() for _ in range(total_shares)]

    for byte in secret_bytes:
        # coefficients: [secret_byte, rand_1, rand_2, ..., rand_{threshold-1}]
        # Using cryptographically secure random bytes
        random_coeffs = list(os.urandom(threshold - 1))
        coeffs = [byte] + random_coeffs

        # Evaluate at x = 1, 2, ..., total_shares
        for idx in range(total_shares):
            x = idx + 1
            y = evaluate_polynomial(coeffs, x)
            shares_data[idx].append(y)

    formatted_shares: List[str] = []
    for idx in range(total_shares):
        share_str = f"{idx + 1}:{shares_data[idx].hex()}"
        formatted_shares.append(share_str)

    return formatted_shares


def combine_shares(share_strings: List[str]) -> bytes:
    """
    Reconstruct original secret bytes from a list of share strings.
    Requires at least `threshold` unique valid shares.
    """
    if not share_strings:
        raise ValueError("No shares provided for reconstruction")

    parsed_shares: List[Tuple[int, bytes]] = []
    seen_indices = set()

    for s in share_strings:
        s = s.strip()
        if not s or ":" not in s:
            continue
        parts = s.split(":", 1)
        try:
            x = int(parts[0])
            payload = bytes.fromhex(parts[1])
        except (ValueError, IndexError):
            continue

        if x < 1 or x > 255:
            continue
        if x in seen_indices:
            continue  # ignore duplicate share index

        seen_indices.add(x)
        parsed_shares.append((x, payload))

    if len(parsed_shares) < 2:
        raise ValueError(f"Insufficient distinct shares provided: got {len(parsed_shares)}, required >= 2")

    length = len(parsed_shares[0][1])
    if any(len(p[1]) != length for p in parsed_shares):
        raise ValueError("All shares must have identical length")

    reconstructed = bytearray(length)
    for byte_idx in range(length):
        points = [(x, payload[byte_idx]) for x, payload in parsed_shares]
        secret_byte = lagrange_interpolate_zero(points)
        reconstructed[byte_idx] = secret_byte

    return bytes(reconstructed)
