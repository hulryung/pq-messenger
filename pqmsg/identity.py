"""Identity keypairs for pq-messenger.

Each identity owns three keypairs:
  - Ed25519 (signing)  — reserved; unused in this scope but provisioned
  - X25519  (DH)       — classical half of hybrid X3DH
  - ML-KEM-768         — post-quantum half of hybrid X3DH
"""
from __future__ import annotations
import base64
import json
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from pqc_edu.params import ML_KEM_768
from pqc_edu.ml_kem import ml_kem_keygen


@dataclass
class Identity:
    name: str
    x25519_public: bytes
    x25519_private: bytes
    ed25519_public: bytes
    ed25519_private: bytes
    ml_kem_public: bytes
    ml_kem_private: bytes


@dataclass
class Contact:
    """Public-only projection of an Identity."""
    name: str
    x25519_public: bytes
    ed25519_public: bytes
    ml_kem_public: bytes


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s)


def generate_identity(name: str) -> Identity:
    x_sk = X25519PrivateKey.generate()
    x_sk_bytes = x_sk.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    x_pk_bytes = x_sk.public_key().public_bytes_raw()

    e_sk = Ed25519PrivateKey.generate()
    e_sk_bytes = e_sk.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    e_pk_bytes = e_sk.public_key().public_bytes_raw()

    ek, dk = ml_kem_keygen(ML_KEM_768)

    return Identity(
        name=name,
        x25519_public=x_pk_bytes,
        x25519_private=x_sk_bytes,
        ed25519_public=e_pk_bytes,
        ed25519_private=e_sk_bytes,
        ml_kem_public=ek,
        ml_kem_private=dk,
    )


def save_identity(ident: Identity, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "name": ident.name,
        "x25519_public": _b64(ident.x25519_public),
        "x25519_private": _b64(ident.x25519_private),
        "ed25519_public": _b64(ident.ed25519_public),
        "ed25519_private": _b64(ident.ed25519_private),
        "ml_kem_public": _b64(ident.ml_kem_public),
        "ml_kem_private": _b64(ident.ml_kem_private),
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def load_identity(path: Path) -> Identity:
    raw = json.loads(Path(path).read_text())
    return Identity(
        name=raw["name"],
        x25519_public=_b64d(raw["x25519_public"]),
        x25519_private=_b64d(raw["x25519_private"]),
        ed25519_public=_b64d(raw["ed25519_public"]),
        ed25519_private=_b64d(raw["ed25519_private"]),
        ml_kem_public=_b64d(raw["ml_kem_public"]),
        ml_kem_private=_b64d(raw["ml_kem_private"]),
    )


def export_contact(ident: Identity, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "name": ident.name,
        "x25519_public": _b64(ident.x25519_public),
        "ed25519_public": _b64(ident.ed25519_public),
        "ml_kem_public": _b64(ident.ml_kem_public),
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def import_contact(path: Path) -> Contact:
    raw = json.loads(Path(path).read_text())
    return Contact(
        name=raw["name"],
        x25519_public=_b64d(raw["x25519_public"]),
        ed25519_public=_b64d(raw["ed25519_public"]),
        ml_kem_public=_b64d(raw["ml_kem_public"]),
    )
