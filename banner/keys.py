"""Node keys. Ed25519, via OpenSSL, so the loop stays free of packages.

The private key stays in `banner-data/keys/<node>.pem`. The log stores
only the public key, on the `node.joined` event that first binds the
name. Replay checks signatures and never needs the private half.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

_ID = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
# SubjectPublicKeyInfo prefix for an Ed25519 key, RFC 8410.
_SPKI = bytes.fromhex("302a300506032b6570032100")


def canonical(event: dict) -> bytes:
    body = {key: event[key] for key in event if key != "sig"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def verify(pub_hex: str, message: bytes, sig_hex: str) -> bool:
    try:
        pub = bytes.fromhex(pub_hex)
        sig = bytes.fromhex(sig_hex)
    except ValueError:
        return False
    if len(pub) != 32 or len(sig) != 64:
        return False
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        der = folder / "pub.der"
        sig_path = folder / "sig"
        message_path = folder / "msg"
        der.write_bytes(_SPKI + pub)
        sig_path.write_bytes(sig)
        message_path.write_bytes(message)
        result = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                str(der),
                "-keyform",
                "DER",
                "-rawin",
                "-in",
                str(message_path),
                "-sigfile",
                str(sig_path),
            ],
            capture_output=True,
            check=False,
        )
    return result.returncode == 0


class KeyStore:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)

    def path(self, node: str) -> Path:
        if _ID.fullmatch(node) is None:
            raise ValueError(f"bad node id: {node!r}")
        return self.root / f"{node}.pem"

    def exists(self, node: str) -> bool:
        return self.path(node).is_file()

    def create(self, node: str) -> str:
        dest = self.path(node)
        if dest.exists():
            raise ValueError(f"{node} already has a key")
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(dest)],
            check=True,
            capture_output=True,
        )
        os.chmod(dest, 0o600)
        return self.public_hex(node)

    def public_hex(self, node: str) -> str:
        dest = self.path(node)
        if not dest.is_file():
            raise ValueError(f"no key for {node}. run: python -m banner node new {node}")
        der = subprocess.run(
            ["openssl", "pkey", "-in", str(dest), "-pubout", "-outform", "DER"],
            check=True,
            capture_output=True,
        ).stdout
        if not der.startswith(_SPKI) or len(der) != len(_SPKI) + 32:
            raise ValueError("openssl returned an unexpected public key")
        return der[len(_SPKI) :].hex()

    def sign(self, node: str, message: bytes) -> str:
        dest = self.path(node)
        if not dest.is_file():
            raise ValueError(f"no key for {node}. run: python -m banner node new {node}")
        with tempfile.TemporaryDirectory() as tmp:
            message_path = Path(tmp) / "msg"
            message_path.write_bytes(message)
            sig = subprocess.run(
                [
                    "openssl",
                    "pkeyutl",
                    "-sign",
                    "-inkey",
                    str(dest),
                    "-rawin",
                    "-in",
                    str(message_path),
                ],
                check=True,
                capture_output=True,
            ).stdout
        if len(sig) != 64:
            raise ValueError("openssl returned an unexpected signature")
        return sig.hex()
