"""Deterministic tile renderer.

This is the stand-in for a pinned container image. `banner-tile:1` is
the image id a charter binds to. A worker and an attestor who both
speak that id produce the same bytes, so the result hash is a fact,
not a claim. A real job later replaces this function with an OCI
digest. The lease rules do not change when that happens.
"""

from __future__ import annotations

import hashlib

IMAGE = "banner-tile:1"
SIZE = 32

_MASK = 0xFFFFFFFFFFFFFFFF


def render(seed: str, tx: int, ty: int, size: int = SIZE) -> bytes:
    """Return a PPM (P6) whose pixels are a pure function of the inputs."""
    state = int.from_bytes(
        hashlib.sha256(f"{seed}:{tx}:{ty}".encode()).digest()[:8], "big"
    ) or 1

    def nxt() -> int:
        nonlocal state
        state ^= (state << 13) & _MASK
        state ^= state >> 7
        state ^= (state << 17) & _MASK
        return state

    raw = bytearray(size * size * 3)
    i = 0
    for py in range(size):
        for px in range(size):
            v = nxt()
            if px in (0, size - 1) or py in (0, size - 1):
                raw[i : i + 3] = b"\x10\x10\x10"
            else:
                raw[i] = (48 + tx * 28 + (v & 0x3F)) & 0xFF
                raw[i + 1] = (48 + ty * 28 + ((v >> 8) & 0x3F)) & 0xFF
                raw[i + 2] = (96 + ((tx * 17 + ty * 13) & 0x3F) + ((v >> 16) & 0x1F)) & 0xFF
            i += 3
    header = f"P6\n{size} {size}\n255\n".encode()
    return header + bytes(raw)


def digest(ppm: bytes) -> str:
    return hashlib.sha256(ppm).hexdigest()
