# pq-messenger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Signal-style post-quantum messenger CLI (`pqmsg`) in a sibling repo, using `pqc_edu.ml_kem` for the PQ half of a hybrid X3DH + symmetric ratchet protocol, with four teaching notebooks and GitHub Pages deployment.

**Architecture:** Fresh sibling repo at `/Users/dkkang/dev/pq-messenger/` (remote: `hulryung/pq-messenger`). Depends on `pqc-edu` via local editable install from `../ml-kem-notebooks`. Python package `pqmsg/` split into six small modules (identity, kdf, session, transport, encoding, cli). Four notebooks walk the protocol and run a live Alice↔Bob session via subprocess.

**Tech Stack:** Python 3.11+, numpy, `cryptography` (X25519, Ed25519, ChaCha20-Poly1305), `click` (CLI), `pqc-edu` (local editable), jupyter-book, pytest. No central server, no sockets.

**Spec:** `/Users/dkkang/dev/pqc/docs/superpowers/specs/2026-04-22-pq-messenger-design.md`

---

## Working Directory

**New repo location:** `/Users/dkkang/dev/pq-messenger/` (sibling to `/Users/dkkang/dev/pqc/` = ml-kem-notebooks)

**Remote:** `https://github.com/hulryung/pq-messenger` (to be created in Task 0)

Every bash command in this plan runs from `/Users/dkkang/dev/pq-messenger/` unless otherwise noted.

## File Structure

```
/Users/dkkang/dev/pq-messenger/
├── README.md
├── LICENSE                            # MIT (match ml-kem-notebooks pattern)
├── .gitignore
├── pyproject.toml                     # pqc-edu via ../ml-kem-notebooks editable install
├── pqmsg/                             # CLI package
│   ├── __init__.py
│   ├── kdf.py                         # HKDF-SHAKE256
│   ├── identity.py                    # Identity keypairs (Ed25519 + X25519 + ML-KEM)
│   ├── encoding.py                    # JSON wire format
│   ├── session.py                     # X3DH handshake + symmetric ratchet
│   ├── transport.py                   # File-queue send/recv with atomic writes
│   └── cli.py                         # click commands
├── tests/
│   ├── __init__.py
│   ├── test_kdf.py
│   ├── test_identity.py
│   ├── test_encoding.py
│   ├── test_session.py
│   ├── test_transport.py
│   └── test_cli.py                    # subprocess integration test
├── notebooks/
│   ├── 01_protocol_overview.ipynb
│   ├── 02_key_agreement.ipynb
│   ├── 03_ratcheting.ipynb
│   └── 04_full_session.ipynb
├── intro.md                           # Jupyter Book landing page
├── _config.yml
├── _toc.yml
├── _static/
│   ├── custom.css                     # copy from ml-kem-notebooks
│   └── lang-switcher.js               # (future, not used in Part 1 since no KO yet)
├── _extra/
│   └── robots.txt
├── _templates/
│   └── layout.html                    # google-site-verification (same as book)
├── .github/workflows/book.yml
└── docs/superpowers/
    ├── specs/2026-04-22-pq-messenger-design.md
    └── plans/2026-04-22-pq-messenger.md       (this file, copied)
```

---

## Task 0: Scaffold new repo

- [ ] **Step 1: Create directory and init git**

```bash
mkdir -p /Users/dkkang/dev/pq-messenger
cd /Users/dkkang/dev/pq-messenger
git init -b main
```

- [ ] **Step 2: Write `.gitignore`**

Create `/Users/dkkang/dev/pq-messenger/.gitignore`:

```
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
.pytest_cache/
*.egg-info/
dist/
build/
_build/
.pqmsg-test/
```

- [ ] **Step 3: Write `pyproject.toml`**

Create `/Users/dkkang/dev/pq-messenger/pyproject.toml`:

```toml
[project]
name = "pqmsg"
version = "0.1.0"
description = "Signal-style post-quantum messenger — educational CLI using ML-KEM"
requires-python = ">=3.11"
dependencies = [
    "cryptography>=42",
    "click>=8.1",
    "pqc-edu",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
book = [
    "jupyter-book>=0.15,<2",
    "sphinx-sitemap>=2.6",
    "sphinxext-opengraph>=0.9",
    "sphinx-last-updated-by-git>=0.3",
]

[project.scripts]
pqmsg = "pqmsg.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["pqmsg*"]

[tool.uv.sources]
# When running via uv/pip, allow local editable pqc-edu
pqc-edu = { path = "../ml-kem-notebooks", editable = true }
```

- [ ] **Step 4: Write `README.md`**

Create `/Users/dkkang/dev/pq-messenger/README.md`:

```markdown
# pq-messenger

A Signal-style post-quantum messenger CLI, built as an educational capstone for the [ML-KEM from Scratch](https://github.com/hulryung/ml-kem-notebooks) book.

## ⚠️ Educational only

This uses the pure-Python `pqc_edu` ML-KEM implementation (not constant-time, not KAT-validated), only the symmetric half of Signal's Double Ratchet, TOFU-only authentication, and a local-file transport. **Do not use for real messaging.**

## 📖 Read online

- Jupyter Book (protocol walk-through): https://pqmsg.hulryung.com/

## Setup

    # Clone both ml-kem-notebooks and pq-messenger as siblings:
    git clone https://github.com/hulryung/ml-kem-notebooks
    git clone https://github.com/hulryung/pq-messenger
    cd pq-messenger
    python -m venv .venv && source .venv/bin/activate
    pip install -e ../ml-kem-notebooks
    pip install -e ".[dev]"

## Two-terminal demo

    # Terminal A
    pqmsg init --name alice
    pqmsg export-contact --output /tmp/alice.pub

    # Terminal B
    pqmsg init --name bob
    pqmsg import-contact /tmp/alice.pub --as alice
    pqmsg export-contact --output /tmp/bob.pub
    pqmsg send alice "Hi from Bob, post-quantum greetings"

    # Back to Terminal A
    pqmsg import-contact /tmp/bob.pub --as bob
    pqmsg recv

## Testing

    pytest tests/ -v
```

- [ ] **Step 5: Verify setup**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ../pqc 2>&1 | tail -3   # note: local pqc-edu source is at /Users/dkkang/dev/pqc
pip install -e ".[dev]" 2>&1 | tail -3
python -c "import pqc_edu.ml_kem; import click; import cryptography; print('ok')"
```

Note: the earlier book's project directory `/Users/dkkang/dev/pqc/` IS the `pqc-edu` source. Adjust `pyproject.toml` if the `[tool.uv.sources]` block causes issues under plain pip — you can remove it and always rely on the preceding `pip install -e /Users/dkkang/dev/pqc`.

Expected: `ok`.

- [ ] **Step 6: Create remote repo and initial commit**

```bash
git add .gitignore pyproject.toml README.md
git commit -m "chore: scaffold pq-messenger repo"
gh repo create hulryung/pq-messenger --public --source=. --description "Signal-style post-quantum messenger — educational CLI using ML-KEM" --push
```

Expected: repo URL printed, first commit pushed.

---

## Task 1: `pqmsg/kdf.py` — HKDF-SHAKE256 + tests

**Files:**
- Create: `pqmsg/__init__.py`
- Create: `pqmsg/kdf.py`
- Create: `tests/__init__.py`
- Create: `tests/test_kdf.py`

- [ ] **Step 1: Create empty package init files**

```bash
mkdir -p pqmsg tests
```

Create `/Users/dkkang/dev/pq-messenger/pqmsg/__init__.py`:

```python
"""pqmsg — educational post-quantum messenger."""
```

Create `/Users/dkkang/dev/pq-messenger/tests/__init__.py`:

```python
```

- [ ] **Step 2: Write failing tests**

Create `/Users/dkkang/dev/pq-messenger/tests/test_kdf.py`:

```python
import pytest
from pqmsg.kdf import hkdf_shake256, derive_chain_step


def test_hkdf_length_32():
    out = hkdf_shake256(salt=b"salt", ikm=b"ikm", info=b"info", length=32)
    assert len(out) == 32


def test_hkdf_deterministic():
    a = hkdf_shake256(salt=b"s", ikm=b"ikm", info=b"i", length=64)
    b = hkdf_shake256(salt=b"s", ikm=b"ikm", info=b"i", length=64)
    assert a == b


def test_hkdf_salt_changes_output():
    a = hkdf_shake256(salt=b"s1", ikm=b"ikm", info=b"i", length=32)
    b = hkdf_shake256(salt=b"s2", ikm=b"ikm", info=b"i", length=32)
    assert a != b


def test_hkdf_info_changes_output():
    a = hkdf_shake256(salt=b"s", ikm=b"ikm", info=b"i1", length=32)
    b = hkdf_shake256(salt=b"s", ikm=b"ikm", info=b"i2", length=32)
    assert a != b


def test_derive_chain_step_returns_two_keys():
    ck_in = b"\x00" * 32
    msg_key, ck_out = derive_chain_step(ck_in)
    assert len(msg_key) == 32
    assert len(ck_out) == 32
    assert msg_key != ck_out
    assert ck_out != ck_in


def test_derive_chain_step_is_deterministic():
    ck = b"\x11" * 32
    a = derive_chain_step(ck)
    b = derive_chain_step(ck)
    assert a == b


def test_derive_chain_step_forward_only():
    """We cannot recover ck_in from (msg_key, ck_out)."""
    ck_in = b"\x22" * 32
    msg_key, ck_out = derive_chain_step(ck_in)
    # There is no inverse function; the test here is sanity that each step
    # produces different output for different inputs.
    ck_in2 = bytes([(b ^ 0x01) for b in ck_in])
    msg_key2, ck_out2 = derive_chain_step(ck_in2)
    assert msg_key != msg_key2
    assert ck_out != ck_out2
```

- [ ] **Step 3: Run tests — expect ImportError**

```bash
pytest tests/test_kdf.py -v
```

- [ ] **Step 4: Implement `pqmsg/kdf.py`**

Create `/Users/dkkang/dev/pq-messenger/pqmsg/kdf.py`:

```python
"""HKDF over SHAKE256.

We use SHAKE256 (variable-length XOF) so the protocol is consistent with
ML-KEM's internal hash choice. cryptography.hazmat's HKDF wraps HMAC-SHA
which would be perfectly fine too, but this keeps things aligned with the
book's chapter on sampling.

HKDF construction (RFC 5869 style):
    PRK = HMAC(salt, ikm)
    OKM = HMAC(PRK, info || counter) || ...

With SHAKE256 we collapse both steps into a single XOF invocation keyed
by salt || ikm, domain-separated by info. This is a standard educational
construction and is sufficient for our toy messenger.
"""
from __future__ import annotations
import hashlib

CHAIN_KEY_LEN = 32
MESSAGE_KEY_LEN = 32
ROOT_KEY_LEN = 32


def hkdf_shake256(salt: bytes, ikm: bytes, info: bytes, length: int) -> bytes:
    """Derive `length` bytes of keying material from (salt, ikm, info).

    Domain-separated so that two derivations with different `info` produce
    independent outputs even if salt and ikm are identical.
    """
    if length < 1 or length > 2048:
        raise ValueError(f"length must be in [1, 2048], got {length}")
    shake = hashlib.shake_256()
    shake.update(b"pqmsg-hkdf-v1|")
    shake.update(len(salt).to_bytes(4, "big"))
    shake.update(salt)
    shake.update(len(ikm).to_bytes(4, "big"))
    shake.update(ikm)
    shake.update(len(info).to_bytes(4, "big"))
    shake.update(info)
    return shake.digest(length)


def derive_chain_step(chain_key: bytes) -> tuple[bytes, bytes]:
    """Advance the symmetric ratchet.

    Returns (message_key, next_chain_key). The message key is used to
    encrypt exactly one message; the next chain key replaces the current
    state. HKDF one-wayness gives forward secrecy: disclosing
    next_chain_key does NOT reveal past message_keys.
    """
    if len(chain_key) != CHAIN_KEY_LEN:
        raise ValueError(f"chain_key must be {CHAIN_KEY_LEN} bytes")
    msg_key = hkdf_shake256(
        salt=b"pqmsg-ratchet-msg", ikm=chain_key,
        info=b"msg_key", length=MESSAGE_KEY_LEN,
    )
    next_ck = hkdf_shake256(
        salt=b"pqmsg-ratchet-adv", ikm=chain_key,
        info=b"chain_advance", length=CHAIN_KEY_LEN,
    )
    return msg_key, next_ck
```

- [ ] **Step 5: Run tests — expect 7 passed**

```bash
pytest tests/test_kdf.py -v
```

- [ ] **Step 6: Commit**

```bash
git add pqmsg/__init__.py pqmsg/kdf.py tests/__init__.py tests/test_kdf.py
git commit -m "feat(kdf): HKDF-SHAKE256 + symmetric ratchet step"
```

---

## Task 2: `pqmsg/identity.py` — keypair generation & storage

**Files:**
- Create: `pqmsg/identity.py`
- Create: `tests/test_identity.py`

- [ ] **Step 1: Write failing tests**

Create `/Users/dkkang/dev/pq-messenger/tests/test_identity.py`:

```python
import json
import os
import pytest
from pathlib import Path
from pqmsg.identity import (
    Identity, generate_identity, load_identity, save_identity,
    export_contact, import_contact,
)


def test_generate_identity_has_all_keys():
    ident = generate_identity(name="alice")
    assert ident.name == "alice"
    assert len(ident.x25519_public) == 32
    assert len(ident.x25519_private) == 32
    assert len(ident.ed25519_public) == 32
    assert len(ident.ed25519_private) == 32
    # ML-KEM-768 key sizes
    assert len(ident.ml_kem_public) == 1184
    assert len(ident.ml_kem_private) >= 1184  # dk includes ek + seeds


def test_save_load_roundtrip(tmp_path):
    ident = generate_identity(name="bob")
    path = tmp_path / "identity.json"
    save_identity(ident, path)
    loaded = load_identity(path)
    assert loaded.name == ident.name
    assert loaded.x25519_public == ident.x25519_public
    assert loaded.x25519_private == ident.x25519_private
    assert loaded.ed25519_public == ident.ed25519_public
    assert loaded.ed25519_private == ident.ed25519_private
    assert loaded.ml_kem_public == ident.ml_kem_public
    assert loaded.ml_kem_private == ident.ml_kem_private


def test_export_contact_has_only_public_keys(tmp_path):
    ident = generate_identity(name="carol")
    path = tmp_path / "carol.pub"
    export_contact(ident, path)
    raw = json.loads(path.read_text())
    assert raw["name"] == "carol"
    assert "x25519_public" in raw
    assert "ed25519_public" in raw
    assert "ml_kem_public" in raw
    assert "x25519_private" not in raw
    assert "ed25519_private" not in raw
    assert "ml_kem_private" not in raw


def test_import_contact_returns_public_only(tmp_path):
    alice = generate_identity(name="alice")
    pub_path = tmp_path / "alice.pub"
    export_contact(alice, pub_path)
    contact = import_contact(pub_path)
    assert contact.name == "alice"
    assert contact.x25519_public == alice.x25519_public
    assert contact.ed25519_public == alice.ed25519_public
    assert contact.ml_kem_public == alice.ml_kem_public
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/test_identity.py -v
```

- [ ] **Step 3: Implement `pqmsg/identity.py`**

```python
"""Identity keypairs for pq-messenger.

Each identity owns three keypairs:
  - Ed25519 (signing)  — reserved; unused in this scope but provisioned
  - X25519  (DH)       — classical half of hybrid X3DH
  - ML-KEM-768         — post-quantum half of hybrid X3DH

Keys are stored in JSON with base64-encoded bytes. The private identity
lives at ~/.pq-messenger/identity.json; the public-only export lives in
~/.pq-messenger/contacts/<name>.pub.
"""
from __future__ import annotations
import base64
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
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
    """Generate a fresh identity with all three keypairs."""
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
    """Write ONLY public keys to `path` — for sharing."""
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
```

- [ ] **Step 4: Run — expect 4 passed**

```bash
pytest tests/test_identity.py -v
```

- [ ] **Step 5: Commit**

```bash
git add pqmsg/identity.py tests/test_identity.py
git commit -m "feat(identity): Ed25519 + X25519 + ML-KEM-768 keypair generation and JSON storage"
```

---

## Task 3: `pqmsg/encoding.py` — wire format + tests

**Files:**
- Create: `pqmsg/encoding.py`
- Create: `tests/test_encoding.py`

- [ ] **Step 1: Write failing tests**

Create `/Users/dkkang/dev/pq-messenger/tests/test_encoding.py`:

```python
import pytest
from pqmsg.encoding import serialize_message, parse_message, MessageFormatError


SAMPLE = {
    "version": 1,
    "sender": "alice",
    "recipient": "bob",
    "msg_index": 3,
    "kem_ciphertext": None,
    "ephemeral_pk": None,
    "nonce": b"\x01" * 12,
    "ciphertext": b"\xff" * 64,
    "sent_at": "2026-04-22T15:30:00Z",
}


def test_serialize_parse_roundtrip():
    blob = serialize_message(**SAMPLE)
    assert isinstance(blob, bytes)
    parsed = parse_message(blob)
    assert parsed == SAMPLE


def test_roundtrip_with_kem_fields():
    fields = {**SAMPLE, "msg_index": 0, "kem_ciphertext": b"\xab" * 1088, "ephemeral_pk": b"\xcd" * 32}
    blob = serialize_message(**fields)
    parsed = parse_message(blob)
    assert parsed == fields


def test_parse_rejects_invalid_json():
    with pytest.raises(MessageFormatError):
        parse_message(b"{not json}")


def test_parse_rejects_missing_fields():
    with pytest.raises(MessageFormatError):
        parse_message(b'{"version": 1}')


def test_parse_rejects_wrong_version():
    blob = serialize_message(**SAMPLE)
    bad = blob.replace(b'"version": 1', b'"version": 99')
    with pytest.raises(MessageFormatError):
        parse_message(bad)
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/test_encoding.py -v
```

- [ ] **Step 3: Implement `pqmsg/encoding.py`**

```python
"""Wire format for messages: JSON with base64-encoded byte fields."""
from __future__ import annotations
import base64
import json
from typing import Any

WIRE_VERSION = 1


class MessageFormatError(ValueError):
    pass


_REQUIRED_FIELDS = {
    "version", "sender", "recipient", "msg_index",
    "kem_ciphertext", "ephemeral_pk",
    "nonce", "ciphertext", "sent_at",
}


def serialize_message(
    *,
    version: int,
    sender: str,
    recipient: str,
    msg_index: int,
    kem_ciphertext: bytes | None,
    ephemeral_pk: bytes | None,
    nonce: bytes,
    ciphertext: bytes,
    sent_at: str,
) -> bytes:
    if version != WIRE_VERSION:
        raise MessageFormatError(f"only version {WIRE_VERSION} supported")
    body: dict[str, Any] = {
        "version": version,
        "sender": sender,
        "recipient": recipient,
        "msg_index": msg_index,
        "kem_ciphertext": base64.b64encode(kem_ciphertext).decode("ascii") if kem_ciphertext else None,
        "ephemeral_pk": base64.b64encode(ephemeral_pk).decode("ascii") if ephemeral_pk else None,
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "sent_at": sent_at,
    }
    return json.dumps(body).encode("utf-8")


def parse_message(blob: bytes) -> dict[str, Any]:
    try:
        raw = json.loads(blob)
    except json.JSONDecodeError as e:
        raise MessageFormatError(f"invalid JSON: {e}")
    if not isinstance(raw, dict):
        raise MessageFormatError("top-level must be object")
    missing = _REQUIRED_FIELDS - raw.keys()
    if missing:
        raise MessageFormatError(f"missing fields: {sorted(missing)}")
    if raw["version"] != WIRE_VERSION:
        raise MessageFormatError(f"unsupported version {raw['version']}")
    return {
        "version": raw["version"],
        "sender": raw["sender"],
        "recipient": raw["recipient"],
        "msg_index": raw["msg_index"],
        "kem_ciphertext": base64.b64decode(raw["kem_ciphertext"]) if raw["kem_ciphertext"] else None,
        "ephemeral_pk": base64.b64decode(raw["ephemeral_pk"]) if raw["ephemeral_pk"] else None,
        "nonce": base64.b64decode(raw["nonce"]),
        "ciphertext": base64.b64decode(raw["ciphertext"]),
        "sent_at": raw["sent_at"],
    }
```

- [ ] **Step 4: Run — expect 5 passed**

```bash
pytest tests/test_encoding.py -v
```

- [ ] **Step 5: Commit**

```bash
git add pqmsg/encoding.py tests/test_encoding.py
git commit -m "feat(encoding): JSON wire format with base64 byte fields"
```

---

## Task 4: `pqmsg/session.py` — X3DH + symmetric ratchet + tests

**Files:**
- Create: `pqmsg/session.py`
- Create: `tests/test_session.py`

- [ ] **Step 1: Write failing tests**

Create `/Users/dkkang/dev/pq-messenger/tests/test_session.py`:

```python
import os
import pytest
from pqmsg.identity import generate_identity
from pqmsg.session import (
    Session, initiate_session, accept_session, encrypt, decrypt,
)


def test_x3dh_both_sides_derive_same_root():
    alice = generate_identity("alice")
    bob = generate_identity("bob")

    # Alice initiates against Bob's public bundle.
    sess_a, handshake = initiate_session(
        ours=alice,
        peer_name=bob.name,
        peer_x25519_pub=bob.x25519_public,
        peer_ml_kem_pub=bob.ml_kem_public,
    )
    # Bob accepts using his private keys + the handshake.
    sess_b = accept_session(
        ours=bob,
        peer_name=alice.name,
        peer_x25519_pub=alice.x25519_public,
        handshake=handshake,
    )
    assert sess_a.chain_key_send == sess_b.chain_key_recv
    assert sess_a.chain_key_recv == sess_b.chain_key_send
    assert sess_a.root_key == sess_b.root_key


def test_single_message_roundtrip():
    alice = generate_identity("alice")
    bob = generate_identity("bob")

    sess_a, handshake = initiate_session(
        ours=alice, peer_name=bob.name,
        peer_x25519_pub=bob.x25519_public,
        peer_ml_kem_pub=bob.ml_kem_public,
    )
    sess_b = accept_session(
        ours=bob, peer_name=alice.name,
        peer_x25519_pub=alice.x25519_public,
        handshake=handshake,
    )

    plaintext = b"Hello from Alice, post-quantum greetings"
    msg = encrypt(sess_a, plaintext, is_first=True, handshake=handshake)
    recovered = decrypt(sess_b, msg)
    assert recovered == plaintext


def test_five_roundtrip_ratchet():
    alice = generate_identity("alice")
    bob = generate_identity("bob")
    sess_a, handshake = initiate_session(
        ours=alice, peer_name=bob.name,
        peer_x25519_pub=bob.x25519_public,
        peer_ml_kem_pub=bob.ml_kem_public,
    )
    sess_b = accept_session(
        ours=bob, peer_name=alice.name,
        peer_x25519_pub=alice.x25519_public,
        handshake=handshake,
    )

    # Alice sends 5 messages; Bob decrypts each in order.
    sent = []
    for i in range(5):
        pt = f"message {i} from alice".encode()
        sent.append(pt)
        msg = encrypt(sess_a, pt, is_first=(i == 0), handshake=handshake if i == 0 else None)
        recovered = decrypt(sess_b, msg)
        assert recovered == pt


def test_wrong_ciphertext_rejected():
    alice = generate_identity("alice")
    bob = generate_identity("bob")
    sess_a, handshake = initiate_session(
        ours=alice, peer_name=bob.name,
        peer_x25519_pub=bob.x25519_public,
        peer_ml_kem_pub=bob.ml_kem_public,
    )
    sess_b = accept_session(
        ours=bob, peer_name=alice.name,
        peer_x25519_pub=alice.x25519_public,
        handshake=handshake,
    )
    msg = encrypt(sess_a, b"secret", is_first=True, handshake=handshake)
    # Tamper with ciphertext.
    msg["ciphertext"] = msg["ciphertext"][:-4] + b"\x00\x00\x00\x00"
    with pytest.raises(Exception):
        decrypt(sess_b, msg)
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/test_session.py -v
```

- [ ] **Step 3: Implement `pqmsg/session.py`**

```python
"""Hybrid X3DH + symmetric ratchet session.

The first message Alice sends to Bob embeds a handshake:
  - Alice's ephemeral X25519 public key
  - A ML-KEM ciphertext encapsulated to Bob's public KEM key
Bob decapsulates, runs the same X25519 DH on his end, and derives the
same root_key and two directional chain_keys. Each message consumes one
symmetric-ratchet step on the relevant chain.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from pqc_edu.params import ML_KEM_768
from pqc_edu.ml_kem import ml_kem_encaps, ml_kem_decaps

from .identity import Identity
from .kdf import hkdf_shake256, derive_chain_step, ROOT_KEY_LEN, CHAIN_KEY_LEN


@dataclass
class Handshake:
    """Wire-format handshake data sent with the first message."""
    ephemeral_pk: bytes         # 32 bytes X25519
    kem_ciphertext: bytes       # ML-KEM-768 ciphertext (1088 bytes)


@dataclass
class Session:
    peer_name: str
    root_key: bytes
    chain_key_send: bytes
    chain_key_recv: bytes
    send_index: int = 0
    recv_index: int = 0


def _derive_session_keys(
    dh_shared: bytes, kem_shared: bytes,
    alice_x_pub: bytes, bob_x_pub: bytes, alice_eph_pub: bytes,
) -> tuple[bytes, bytes, bytes]:
    """Derive root_key and two directional chain keys (alice_send, bob_send)."""
    material = hkdf_shake256(
        salt=b"pqmsg-x3dh-v1",
        ikm=dh_shared + kem_shared,
        info=alice_x_pub + bob_x_pub + alice_eph_pub,
        length=ROOT_KEY_LEN + 2 * CHAIN_KEY_LEN,
    )
    root_key = material[:ROOT_KEY_LEN]
    chain_alice_to_bob = material[ROOT_KEY_LEN : ROOT_KEY_LEN + CHAIN_KEY_LEN]
    chain_bob_to_alice = material[ROOT_KEY_LEN + CHAIN_KEY_LEN :]
    return root_key, chain_alice_to_bob, chain_bob_to_alice


def initiate_session(
    ours: Identity,
    peer_name: str,
    peer_x25519_pub: bytes,
    peer_ml_kem_pub: bytes,
) -> tuple[Session, Handshake]:
    """Alice-side: generate ephemeral, encapsulate, derive session keys."""
    eph_sk = X25519PrivateKey.generate()
    eph_pk_bytes = eph_sk.public_key().public_bytes_raw()
    dh_shared = eph_sk.exchange(X25519PublicKey.from_public_bytes(peer_x25519_pub))
    kem_shared, kem_ct = ml_kem_encaps(ML_KEM_768, peer_ml_kem_pub)

    root_key, chain_a2b, chain_b2a = _derive_session_keys(
        dh_shared=dh_shared, kem_shared=kem_shared,
        alice_x_pub=ours.x25519_public, bob_x_pub=peer_x25519_pub,
        alice_eph_pub=eph_pk_bytes,
    )
    session = Session(
        peer_name=peer_name,
        root_key=root_key,
        chain_key_send=chain_a2b,
        chain_key_recv=chain_b2a,
    )
    handshake = Handshake(ephemeral_pk=eph_pk_bytes, kem_ciphertext=kem_ct)
    return session, handshake


def accept_session(
    ours: Identity,
    peer_name: str,
    peer_x25519_pub: bytes,
    handshake: Handshake,
) -> Session:
    """Bob-side: decapsulate, complete DH, derive session keys."""
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    bob_x_sk = X25519PrivateKey.from_private_bytes(ours.x25519_private)
    dh_shared = bob_x_sk.exchange(X25519PublicKey.from_public_bytes(handshake.ephemeral_pk))
    kem_shared = ml_kem_decaps(ML_KEM_768, ours.ml_kem_private, handshake.kem_ciphertext)

    root_key, chain_a2b, chain_b2a = _derive_session_keys(
        dh_shared=dh_shared, kem_shared=kem_shared,
        alice_x_pub=peer_x25519_pub, bob_x_pub=ours.x25519_public,
        alice_eph_pub=handshake.ephemeral_pk,
    )
    return Session(
        peer_name=peer_name,
        root_key=root_key,
        chain_key_send=chain_b2a,   # Bob's sends advance the b2a chain
        chain_key_recv=chain_a2b,   # Bob's receives advance the a2b chain
    )


def encrypt(
    session: Session,
    plaintext: bytes,
    *,
    is_first: bool,
    handshake: Optional[Handshake],
) -> dict:
    """Advance the send chain and encrypt plaintext. Returns a dict compatible with
    pqmsg.encoding.serialize_message(**result)."""
    if is_first and handshake is None:
        raise ValueError("is_first=True requires handshake")
    msg_key, next_chain = derive_chain_step(session.chain_key_send)
    nonce = os.urandom(12)
    aead = ChaCha20Poly1305(msg_key)
    ciphertext = aead.encrypt(nonce, plaintext, None)
    idx = session.send_index
    session.chain_key_send = next_chain
    session.send_index += 1
    return {
        "version": 1,
        "sender": "",          # filled in by caller
        "recipient": session.peer_name,
        "msg_index": idx,
        "kem_ciphertext": handshake.kem_ciphertext if is_first else None,
        "ephemeral_pk": handshake.ephemeral_pk if is_first else None,
        "nonce": nonce,
        "ciphertext": ciphertext,
        "sent_at": "",        # filled in by caller
    }


def decrypt(session: Session, msg: dict) -> bytes:
    """Advance the receive chain and decrypt."""
    msg_key, next_chain = derive_chain_step(session.chain_key_recv)
    aead = ChaCha20Poly1305(msg_key)
    plaintext = aead.decrypt(msg["nonce"], msg["ciphertext"], None)
    session.chain_key_recv = next_chain
    session.recv_index += 1
    return plaintext
```

- [ ] **Step 4: Run — expect 4 passed**

```bash
pytest tests/test_session.py -v
```

The tests exercise both the symmetric ratchet (5 roundtrip) and AEAD tamper detection.

- [ ] **Step 5: Commit**

```bash
git add pqmsg/session.py tests/test_session.py
git commit -m "feat(session): hybrid X3DH + symmetric ratchet with ChaCha20-Poly1305 AEAD"
```

---

## Task 5: `pqmsg/transport.py` — file-queue transport + tests

**Files:**
- Create: `pqmsg/transport.py`
- Create: `tests/test_transport.py`

- [ ] **Step 1: Write failing tests**

Create `/Users/dkkang/dev/pq-messenger/tests/test_transport.py`:

```python
import json
import os
import pytest
from pathlib import Path
from pqmsg.transport import send_blob, list_inbox, pop_message


def test_send_and_list(tmp_path):
    inbox_root = tmp_path / "inbox"
    send_blob(inbox_root=inbox_root, recipient="bob", blob=b"hello world")
    items = list_inbox(inbox_root=inbox_root, recipient="bob")
    assert len(items) == 1
    assert items[0].read_bytes() == b"hello world"


def test_pop_returns_oldest_first(tmp_path):
    inbox_root = tmp_path / "inbox"
    import time
    for i in range(3):
        send_blob(inbox_root=inbox_root, recipient="bob", blob=f"msg{i}".encode())
        time.sleep(0.01)
    first = pop_message(inbox_root=inbox_root, recipient="bob")
    assert first == b"msg0"
    second = pop_message(inbox_root=inbox_root, recipient="bob")
    assert second == b"msg1"
    third = pop_message(inbox_root=inbox_root, recipient="bob")
    assert third == b"msg2"
    assert pop_message(inbox_root=inbox_root, recipient="bob") is None


def test_atomic_write_no_partial_files(tmp_path):
    inbox_root = tmp_path / "inbox"
    send_blob(inbox_root=inbox_root, recipient="bob", blob=b"x")
    # No .tmp file should remain after send.
    leftovers = list((inbox_root / "bob").glob("*.tmp"))
    assert leftovers == []


def test_list_empty_inbox(tmp_path):
    inbox_root = tmp_path / "inbox"
    assert list_inbox(inbox_root=inbox_root, recipient="bob") == []


def test_pop_ignores_tmp_files(tmp_path):
    inbox_root = tmp_path / "inbox"
    (inbox_root / "bob").mkdir(parents=True)
    (inbox_root / "bob" / "partial.tmp").write_bytes(b"should be ignored")
    assert pop_message(inbox_root=inbox_root, recipient="bob") is None
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/test_transport.py -v
```

- [ ] **Step 3: Implement `pqmsg/transport.py`**

```python
"""Local-filesystem transport: one file per message, oldest-first FIFO.

Each message is written atomically (<name>.json.tmp → rename → <name>.json)
so a concurrent reader never sees a partial file. We sort by mtime for a
stable FIFO ordering.
"""
from __future__ import annotations
import os
import uuid
from pathlib import Path


def _inbox_dir(inbox_root: Path, recipient: str) -> Path:
    d = Path(inbox_root) / recipient
    d.mkdir(parents=True, exist_ok=True)
    return d


def send_blob(*, inbox_root: Path, recipient: str, blob: bytes) -> Path:
    """Atomically write `blob` into recipient's inbox. Returns final path."""
    dirp = _inbox_dir(Path(inbox_root), recipient)
    mid = uuid.uuid4().hex
    final = dirp / f"{mid}.json"
    tmp = dirp / f"{mid}.json.tmp"
    tmp.write_bytes(blob)
    tmp.replace(final)
    return final


def list_inbox(*, inbox_root: Path, recipient: str) -> list[Path]:
    """List pending messages in mtime order (oldest first). Ignores .tmp files."""
    dirp = Path(inbox_root) / recipient
    if not dirp.exists():
        return []
    items = [p for p in dirp.iterdir() if p.suffix == ".json"]
    items.sort(key=lambda p: p.stat().st_mtime_ns)
    return items


def pop_message(*, inbox_root: Path, recipient: str) -> bytes | None:
    """Return and remove the oldest message, or None if inbox is empty."""
    items = list_inbox(inbox_root=inbox_root, recipient=recipient)
    if not items:
        return None
    oldest = items[0]
    data = oldest.read_bytes()
    oldest.unlink()
    return data
```

- [ ] **Step 4: Run — expect 5 passed**

```bash
pytest tests/test_transport.py -v
```

- [ ] **Step 5: Commit**

```bash
git add pqmsg/transport.py tests/test_transport.py
git commit -m "feat(transport): atomic file-queue send/list/pop"
```

---

## Task 6: `pqmsg/cli.py` — click CLI

**Files:**
- Create: `pqmsg/cli.py`

No dedicated unit tests — exercised by integration test in Task 7.

- [ ] **Step 1: Implement**

Create `/Users/dkkang/dev/pq-messenger/pqmsg/cli.py`:

```python
"""Click CLI for pq-messenger."""
from __future__ import annotations
import datetime
import json
import os
import pickle
import sys
from pathlib import Path

import click

from . import identity as _identity
from . import session as _session
from . import transport as _transport
from . import encoding as _encoding


def _home() -> Path:
    return Path(os.environ.get("PQMSG_HOME", Path.home() / ".pq-messenger"))


def _identity_path() -> Path:
    return _home() / "identity.json"


def _contacts_dir() -> Path:
    d = _home() / "contacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sessions_dir() -> Path:
    d = _home() / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _inbox_root() -> Path:
    return _home() / "inbox"


def _load_own() -> _identity.Identity:
    path = _identity_path()
    if not path.exists():
        raise click.ClickException("no identity found — run `pqmsg init --name NAME` first")
    return _identity.load_identity(path)


def _load_contact(name: str) -> _identity.Contact:
    path = _contacts_dir() / f"{name}.pub"
    if not path.exists():
        raise click.ClickException(f"contact '{name}' not found — run `pqmsg import-contact`")
    return _identity.import_contact(path)


def _session_path(peer_name: str) -> Path:
    return _sessions_dir() / f"{peer_name}.session"


def _save_session(peer_name: str, sess: _session.Session) -> None:
    p = _session_path(peer_name)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_bytes(pickle.dumps(sess))
    tmp.replace(p)


def _load_session(peer_name: str) -> _session.Session | None:
    p = _session_path(peer_name)
    if not p.exists():
        return None
    return pickle.loads(p.read_bytes())


@click.group()
def main():
    """Post-quantum messenger CLI (educational)."""
    pass


@main.command()
@click.option("--name", required=True)
def init(name):
    """Generate a fresh identity."""
    path = _identity_path()
    if path.exists():
        raise click.ClickException(f"identity already exists at {path}; remove or run `pqmsg reset`")
    ident = _identity.generate_identity(name=name)
    _identity.save_identity(ident, path)
    click.echo(f"Generated identity for '{name}' at {path}")
    click.echo(f"Share your contact file: pqmsg export-contact --output /tmp/{name}.pub")


@main.command("show-identity")
def show_identity():
    """Show the active identity (public components)."""
    ident = _load_own()
    click.echo(f"name: {ident.name}")
    click.echo(f"x25519_public  ({len(ident.x25519_public)}B): {ident.x25519_public.hex()[:32]}...")
    click.echo(f"ed25519_public ({len(ident.ed25519_public)}B): {ident.ed25519_public.hex()[:32]}...")
    click.echo(f"ml_kem_public  ({len(ident.ml_kem_public)}B): {ident.ml_kem_public.hex()[:32]}...")


@main.command("export-contact")
@click.option("--output", type=click.Path(), default=None)
def export_contact_cmd(output):
    """Write public-only contact file for sharing."""
    ident = _load_own()
    if output is None:
        output = _contacts_dir() / f"{ident.name}.pub"
    _identity.export_contact(ident, Path(output))
    click.echo(f"exported to {output}")


@main.command("import-contact")
@click.argument("path", type=click.Path(exists=True))
@click.option("--as", "as_name", required=True, help="local alias")
def import_contact_cmd(path, as_name):
    """Import a peer's public contact file under a local alias."""
    contact = _identity.import_contact(Path(path))
    # Store under as_name for local lookup.
    stored_path = _contacts_dir() / f"{as_name}.pub"
    _identity.export_contact(
        _identity.Identity(
            name=as_name,
            x25519_public=contact.x25519_public, x25519_private=b"",
            ed25519_public=contact.ed25519_public, ed25519_private=b"",
            ml_kem_public=contact.ml_kem_public, ml_kem_private=b"",
        ),
        stored_path,
    )
    click.echo(f"contact '{contact.name}' imported as '{as_name}'")


@main.command()
@click.argument("recipient")
@click.argument("body")
def send(recipient, body):
    """Encrypt and enqueue a message."""
    ours = _load_own()
    peer = _load_contact(recipient)
    sess = _load_session(recipient)
    handshake = None
    is_first = False
    if sess is None:
        sess, handshake = _session.initiate_session(
            ours=ours,
            peer_name=recipient,
            peer_x25519_pub=peer.x25519_public,
            peer_ml_kem_pub=peer.ml_kem_public,
        )
        is_first = True
    msg = _session.encrypt(sess, body.encode("utf-8"), is_first=is_first, handshake=handshake)
    msg["sender"] = ours.name
    msg["sent_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    blob = _encoding.serialize_message(**msg)
    _transport.send_blob(inbox_root=_inbox_root(), recipient=recipient, blob=blob)
    _save_session(recipient, sess)
    click.echo(f"sent message #{msg['msg_index']} to {recipient} ({len(blob)} bytes)")


@main.command()
@click.option("--all", "recv_all", is_flag=True)
def recv(recv_all):
    """Dequeue and decrypt messages destined for us."""
    ours = _load_own()
    name = ours.name
    count = 0
    while True:
        blob = _transport.pop_message(inbox_root=_inbox_root(), recipient=name)
        if blob is None:
            break
        try:
            msg = _encoding.parse_message(blob)
        except _encoding.MessageFormatError as e:
            click.echo(f"[malformed] {e}", err=True)
            continue
        sender = msg["sender"]
        sess = _load_session(sender)
        if sess is None:
            # First message: expect handshake fields.
            if not msg["kem_ciphertext"] or not msg["ephemeral_pk"]:
                click.echo(f"[no session with {sender} and no handshake in first message]", err=True)
                continue
            peer = _load_contact(sender)
            handshake = _session.Handshake(
                ephemeral_pk=msg["ephemeral_pk"],
                kem_ciphertext=msg["kem_ciphertext"],
            )
            sess = _session.accept_session(
                ours=ours, peer_name=sender,
                peer_x25519_pub=peer.x25519_public,
                handshake=handshake,
            )
        try:
            pt = _session.decrypt(sess, msg)
        except Exception as e:
            click.echo(f"[decryption failed from {sender}] {e}", err=True)
            continue
        click.echo(f"[from {sender}, msg #{msg['msg_index']}]: {pt.decode('utf-8', errors='replace')}")
        _save_session(sender, sess)
        count += 1
        if not recv_all:
            break
    if count == 0:
        click.echo("(no messages)")


@main.command("show-keys")
@click.argument("peer")
def show_keys(peer):
    """Debug: print current ratchet state for a peer."""
    sess = _load_session(peer)
    if sess is None:
        raise click.ClickException(f"no session with {peer}")
    click.echo(f"peer: {sess.peer_name}")
    click.echo(f"send_index: {sess.send_index}")
    click.echo(f"recv_index: {sess.recv_index}")
    click.echo(f"chain_key_send (first 8 bytes): {sess.chain_key_send[:8].hex()}")
    click.echo(f"chain_key_recv (first 8 bytes): {sess.chain_key_recv[:8].hex()}")


@main.command()
def reset():
    """Remove ~/.pq-messenger/ (all identities, contacts, sessions)."""
    import shutil
    home = _home()
    if home.exists():
        shutil.rmtree(home)
        click.echo(f"removed {home}")
    else:
        click.echo("nothing to remove")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test**

```bash
cd /Users/dkkang/dev/pq-messenger
source .venv/bin/activate
export PQMSG_HOME=/tmp/pqmsg-smoke-alice
pqmsg reset 2>&1 | tail -1
pqmsg init --name alice 2>&1 | tail -1
pqmsg show-identity | head -4
pqmsg reset
```

Expected output lines ending in `Generated identity for 'alice' at ...`, followed by `name: alice` etc.

- [ ] **Step 3: Commit**

```bash
git add pqmsg/cli.py
git commit -m "feat(cli): click commands for init/send/recv/contacts"
```

---

## Task 7: Integration test — two-process Alice↔Bob session

**Files:**
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the test**

Create `/Users/dkkang/dev/pq-messenger/tests/test_cli.py`:

```python
import os
import subprocess
import tempfile
from pathlib import Path


def _run(env_home: Path, shared_inbox: Path, args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PQMSG_HOME"] = str(env_home)
    # Point both parties at the same inbox root by sharing one PQMSG_HOME for
    # the inbox; for this test we use a single HOME for both users and only
    # isolate identities by `PQMSG_HOME` swap. Simpler: we use per-user HOMEs,
    # but the `send` command writes to `<HOME>/inbox/<recipient>/`. We
    # therefore symlink the inbox directory between the two HOMEs so both
    # users share it.
    env["PQMSG_INBOX_SHARED"] = str(shared_inbox)
    return subprocess.run(
        ["pqmsg"] + args, env=env, capture_output=True, text=True, timeout=60
    )


def test_five_roundtrip_between_two_processes(tmp_path):
    """Full end-to-end: Alice and Bob each have their own HOME but share an inbox.

    We symlink the inbox directory so `send` from one writes into the other.
    """
    alice_home = tmp_path / "alice"
    bob_home = tmp_path / "bob"
    alice_home.mkdir(); bob_home.mkdir()
    shared_inbox = tmp_path / "shared_inbox"
    shared_inbox.mkdir()
    # Make alice's inbox and bob's inbox both point to shared.
    (alice_home / "inbox").symlink_to(shared_inbox, target_is_directory=True)
    (bob_home / "inbox").symlink_to(shared_inbox, target_is_directory=True)

    def run_alice(*a):
        return _run(alice_home, shared_inbox, list(a))

    def run_bob(*a):
        return _run(bob_home, shared_inbox, list(a))

    # Init both identities.
    assert run_alice("init", "--name", "alice").returncode == 0
    assert run_bob("init", "--name", "bob").returncode == 0

    # Export + import contacts.
    alice_pub = tmp_path / "alice.pub"
    bob_pub = tmp_path / "bob.pub"
    assert run_alice("export-contact", "--output", str(alice_pub)).returncode == 0
    assert run_bob("export-contact", "--output", str(bob_pub)).returncode == 0
    assert run_alice("import-contact", str(bob_pub), "--as", "bob").returncode == 0
    assert run_bob("import-contact", str(alice_pub), "--as", "alice").returncode == 0

    # Five Alice -> Bob messages.
    for i in range(5):
        msg = f"hello from alice, round {i}"
        r = run_alice("send", "bob", msg)
        assert r.returncode == 0, r.stderr
        r = run_bob("recv")
        assert r.returncode == 0, r.stderr
        assert msg in r.stdout, f"expected '{msg}' in output, got: {r.stdout}"
```

- [ ] **Step 2: Run the test — expect PASS**

```bash
pytest tests/test_cli.py -v
```

Expected: 1 passed. Total runtime ~10-20 seconds (5 ML-KEM keygen + encaps cycles).

- [ ] **Step 3: Full regression test run**

```bash
pytest tests/ -v
```

Expected: all tests pass (kdf 7 + identity 4 + encoding 5 + session 4 + transport 5 + cli 1 = 26 tests).

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py
git commit -m "test(cli): five-roundtrip integration test via subprocess + shared inbox"
```

---

## Task 8: Notebook 01 — Protocol overview

**Files:**
- Create: `notebooks/01_protocol_overview.ipynb`

Pure-markdown notebook (no code cells). Use `nbformat` to construct.

Cells:

1. **Markdown**: `# Notebook 01 — Protocol overview`\n\nBefore we write code, we lay out the threat model, the protocol (hybrid X3DH + symmetric ratchet), and where each building block comes from.

2. **Markdown**: `## Threat model\n\nIn our toy world, Alice and Bob want to exchange messages over a **public channel** (our shared file queue). We assume an adversary that can:\n\n- **Eavesdrop** on every ciphertext\n- **Tamper** with ciphertexts (we use AEAD to detect this)\n- **Later compromise** Alice's long-term private keys (forward secrecy goal)\n\nWe do *not* defend against:\n\n- Metadata privacy (sender/recipient are plaintext)\n- Active server impersonation (no PKI beyond TOFU)\n- Deniability, future secrecy (no DH ratchet)\n- Side-channel or fault attacks on our Python code`

3. **Markdown**: `## Why KEM alone is not enough\n\nYou might think: *Alice and Bob each have ML-KEM keypairs; Alice just encapsulates to Bob's public key every message*. That works for confidentiality, but it has two problems:\n\n1. **No forward secrecy**: if Bob's ML-KEM private key is compromised tomorrow, an attacker can decrypt every message ever sent.\n2. **No efficient continuation**: each message would redo the full KEM handshake — ciphertext size stays ~1KB for a 5-byte "ok".\n\nSignal solved this for RSA/ECC with the **Double Ratchet**. We use its simpler **symmetric-only** half.`

4. **Markdown**: `## Hybrid X3DH (simplified)\n\nAlice's first message to Bob runs a one-shot handshake:\n\n1. Alice generates an ephemeral X25519 keypair $(eph_{sk}, eph_{pk})$.\n2. Alice computes a classical shared secret: $dh = X25519(eph_{sk}, bob_{pub})$.\n3. Alice encapsulates a post-quantum shared secret to Bob: $(k_{kem}, c_{kem}) = \text{ML-KEM-Encaps}(bob_{ek})$.\n4. Alice derives the root key: $SK = \text{HKDF-SHAKE256}(salt, dh \| k_{kem}, info)$.\n5. Alice sends $(eph_{pk}, c_{kem}, \text{body ciphertext})$.\n6. Bob: $dh = X25519(bob_{sk}, eph_{pk})$, $k_{kem} = \text{ML-KEM-Decaps}(bob_{dk}, c_{kem})$, derives same $SK$.\n\nBoth sides now hold a 96-byte derived material: 32 B root key + 32 B Alice-to-Bob chain key + 32 B Bob-to-Alice chain key.\n\n**Hybrid**: an attacker needs to break *both* X25519 and ML-KEM-768 to recover $SK$. Kills Shor (breaks X25519 but not ML-KEM) and kills unknown lattice attacks (they might break ML-KEM but not X25519 today).`

5. **Markdown**: `## Symmetric ratchet\n\nOnce the root key is established, each side has a **chain key** per direction. To encrypt message $i$:\n\n```\nmessage_key_i   = HKDF(chain_key, info="msg_key")\nnew_chain_key   = HKDF(chain_key, info="chain_advance")\nchain_key      := new_chain_key\n```\n\nEach `message_key_i` is used exactly once with ChaCha20-Poly1305 AEAD. Because HKDF is one-way:\n\n- **Forward secrecy**: learning `chain_key` at message $i+1$ does *not* reveal message keys 0..i.\n- **Backward non-secrecy**: learning `chain_key` at message $i+1$ *does* reveal message $i+1$ and later.\n\nThe Double Ratchet's DH step fixes backward non-secrecy by periodically re-running a fresh DH exchange. We leave that out here — notebook 03 shows exactly where this limitation bites.`

6. **Markdown**: `## Wire format\n\nEvery message is a JSON object with base64-encoded byte fields:\n\n\`\`\`json\n{\n  "version": 1,\n  "sender": "alice",\n  "recipient": "bob",\n  "msg_index": 0,\n  "kem_ciphertext": "base64...",\n  "ephemeral_pk": "base64...",\n  "nonce": "base64...",\n  "ciphertext": "base64...",\n  "sent_at": "2026-04-22T15:30:00Z"\n}\n\`\`\`\n\nOnly the first message carries \`kem_ciphertext\` and \`ephemeral_pk\` — subsequent messages rely on the established chain. Our transport writes each message as one file in \`~/.pq-messenger/inbox/<recipient>/<uuid>.json\`.`

7. **Markdown**: `## Reading order\n\n- **02**: Walk through hybrid X3DH step by step with real keys.\n- **03**: Demonstrate forward secrecy *and* the ratchet's limitation under key compromise.\n- **04**: Run a live two-process session over the file queue.`

Build, execute, commit:

```bash
python /tmp/build_nb01.py
rm /tmp/build_nb01.py
jupyter nbconvert --to notebook --execute notebooks/01_protocol_overview.ipynb --output 01_protocol_overview.ipynb
git add notebooks/01_protocol_overview.ipynb
git commit -m "docs(nb01): protocol overview — threat model, hybrid X3DH, ratchet"
```

---

## Task 9: Notebook 02 — Key agreement

**File:** Create `notebooks/02_key_agreement.ipynb`

Cells:

1. **Markdown**: `# Notebook 02 — Hybrid X3DH key agreement`\n\nWe run the hybrid handshake between two fresh identities and verify both sides derive the same 96 bytes of keying material.

2. **Code**:
```
from pqmsg.identity import generate_identity
from pqmsg.session import initiate_session, accept_session, Handshake
```

3. **Markdown**: `## Step 1 — generate identities`

4. **Code**:
```
alice = generate_identity("alice")
bob   = generate_identity("bob")
print("alice X25519 pub (first 8B):", alice.x25519_public[:8].hex())
print("bob   X25519 pub (first 8B):", bob.x25519_public[:8].hex())
print("alice ML-KEM pub size      :", len(alice.ml_kem_public))
print("bob   ML-KEM pub size      :", len(bob.ml_kem_public))
```

5. **Markdown**: `## Step 2 — Alice initiates\n\n\`initiate_session\` runs X25519 DH, ML-KEM encapsulation, and the HKDF derivation.`

6. **Code**:
```
sess_a, handshake = initiate_session(
    ours=alice, peer_name=bob.name,
    peer_x25519_pub=bob.x25519_public,
    peer_ml_kem_pub=bob.ml_kem_public,
)
print("root_key (first 8B):        ", sess_a.root_key[:8].hex())
print("chain_key_send (first 8B):  ", sess_a.chain_key_send[:8].hex())
print("chain_key_recv (first 8B):  ", sess_a.chain_key_recv[:8].hex())
print("ephemeral_pk size:           ", len(handshake.ephemeral_pk))
print("kem_ciphertext size:         ", len(handshake.kem_ciphertext))
```

7. **Markdown**: `## Step 3 — Bob accepts\n\n\`accept_session\` uses Bob's private keys and the handshake fields Alice sent.`

8. **Code**:
```
sess_b = accept_session(
    ours=bob, peer_name=alice.name,
    peer_x25519_pub=alice.x25519_public,
    handshake=handshake,
)
print("root_key match:        ", sess_a.root_key == sess_b.root_key)
print("chain_a2b mirrored:    ", sess_a.chain_key_send == sess_b.chain_key_recv)
print("chain_b2a mirrored:    ", sess_a.chain_key_recv == sess_b.chain_key_send)
```

9. **Markdown**: `## Why both lines must succeed\n\nThe two chain keys are **directional**: one for Alice→Bob, one for Bob→Alice. After this handshake, each party can encrypt and the other can decrypt, independently. The next notebook cranks the symmetric ratchet ten steps to show forward secrecy — and where it stops.`

Build + execute + commit:

```bash
python /tmp/build_nb02.py && rm /tmp/build_nb02.py
jupyter nbconvert --to notebook --execute notebooks/02_key_agreement.ipynb --output 02_key_agreement.ipynb
git add notebooks/02_key_agreement.ipynb
git commit -m "docs(nb02): hybrid X3DH walk-through"
```

---

## Task 10: Notebook 03 — Ratcheting + key compromise

**File:** Create `notebooks/03_ratcheting.ipynb`

Cells:

1. **Markdown**: `# Notebook 03 — Ratcheting and key compromise`\n\nWe crank the symmetric ratchet through 10 messages, then simulate a key-compromise at step 5 to see what's safe and what isn't.

2. **Code**:
```
from pqmsg.kdf import derive_chain_step
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os
```

3. **Markdown**: `## Step 1 — watch the chain advance`

4. **Code**:
```
chain_key = os.urandom(32)
ciphertexts = []
msg_keys = []
for i in range(10):
    msg_key, next_ck = derive_chain_step(chain_key)
    aead = ChaCha20Poly1305(msg_key)
    nonce = os.urandom(12)
    ct = aead.encrypt(nonce, f"message {i}".encode(), None)
    ciphertexts.append((nonce, ct))
    msg_keys.append(msg_key)
    print(f"msg {i}: msg_key[:4]={msg_key[:4].hex()}  chain_key[:4]={next_ck[:4].hex()}")
    chain_key = next_ck
```

5. **Markdown**: `## Step 2 — simulate compromise at step 5\n\nSuppose an attacker steals \`chain_key\` at step 5 (after message 4 has been sent).`

6. **Code**:
```
# Re-run, but save the chain key state after message 4 separately.
chain_key = os.urandom(32)
stolen = None
saved_cts = []
saved_keys = []
for i in range(10):
    if i == 5:
        stolen = chain_key   # attacker grabs the chain_key at this moment
    msg_key, next_ck = derive_chain_step(chain_key)
    aead = ChaCha20Poly1305(msg_key)
    nonce = os.urandom(12)
    ct = aead.encrypt(nonce, f"message {i}".encode(), None)
    saved_cts.append((nonce, ct))
    saved_keys.append(msg_key)
    chain_key = next_ck

print("stolen chain_key (first 8B):", stolen[:8].hex())
```

7. **Markdown**: `## Step 3 — can the attacker decrypt past messages?\n\nFrom the stolen chain_key, the attacker tries to derive message keys 0..4.`

8. **Code**:
```
# The attacker can advance forward from `stolen`, but has no way to "run backwards".
ck = stolen
attacker_keys_future = []
for i in range(5, 10):
    mk, nxt = derive_chain_step(ck)
    attacker_keys_future.append(mk)
    ck = nxt

print("Future messages (5..9): attacker reconstructs every msg_key.")
for i in range(5, 10):
    matches = attacker_keys_future[i - 5] == saved_keys[i]
    print(f"  msg {i} key reconstructed: {matches}")

print("\nPast messages (0..4): attacker has chain_key at step 5, and HKDF is one-way.")
print("  There is NO function that turns next_chain into previous chain_key.")
print("  Attacker CANNOT compute msg_keys 0..4 from `stolen`.")
```

9. **Markdown**: `## Takeaways\n\n1. **Forward secrecy holds**: messages before the compromise stay confidential because HKDF is one-way.\n2. **Backward secrecy fails**: every message from the compromise onward is readable.\n\nThe **full Double Ratchet** adds a DH step every few messages — so a fresh X25519/ML-KEM exchange refreshes the chain key with entropy the attacker hasn't seen. That closes the backward-secrecy gap. We deliberately omit it here so the limitation is explicit. In a real messenger (Signal, iMessage PQ3), you always want the full ratchet.`

Build, execute, commit:

```bash
python /tmp/build_nb03.py && rm /tmp/build_nb03.py
jupyter nbconvert --to notebook --execute notebooks/03_ratcheting.ipynb --output 03_ratcheting.ipynb
git add notebooks/03_ratcheting.ipynb
git commit -m "docs(nb03): symmetric ratchet forward-secrecy demo + compromise sim"
```

---

## Task 11: Notebook 04 — Full CLI session

**File:** Create `notebooks/04_full_session.ipynb`

This notebook runs real CLI subprocesses. Use a `tempdir` and `PQMSG_HOME` env vars.

Cells:

1. **Markdown**: `# Notebook 04 — Full Alice↔Bob session via CLI\n\nWe spawn two real CLI processes sharing an inbox directory, and watch five roundtrip messages.`

2. **Code**:
```
import os, subprocess, tempfile, shutil
from pathlib import Path

workdir = Path(tempfile.mkdtemp(prefix="pqmsg_nb04_"))
alice_home = workdir / "alice"; alice_home.mkdir()
bob_home   = workdir / "bob";   bob_home.mkdir()
shared_inbox = workdir / "shared_inbox"; shared_inbox.mkdir()
# Symlink each user's inbox to the shared one.
(alice_home / "inbox").symlink_to(shared_inbox, target_is_directory=True)
(bob_home / "inbox").symlink_to(shared_inbox, target_is_directory=True)
print("workdir:", workdir)
```

3. **Code**:
```
def run(home, *args):
    env = os.environ.copy()
    env["PQMSG_HOME"] = str(home)
    r = subprocess.run(["pqmsg"] + list(args), env=env, capture_output=True, text=True, timeout=60)
    return r

# Init both identities.
print(run(alice_home, "init", "--name", "alice").stdout.strip())
print(run(bob_home,   "init", "--name", "bob").stdout.strip())
```

4. **Code**:
```
# Export + import contacts.
alice_pub = workdir / "alice.pub"
bob_pub   = workdir / "bob.pub"
run(alice_home, "export-contact", "--output", str(alice_pub))
run(bob_home,   "export-contact", "--output", str(bob_pub))
run(alice_home, "import-contact", str(bob_pub),   "--as", "bob")
run(bob_home,   "import-contact", str(alice_pub), "--as", "alice")
print("contacts exchanged")
```

5. **Code**:
```
# Five Alice -> Bob messages.
for i in range(5):
    msg = f"round {i}: hello from alice"
    r = run(alice_home, "send", "bob", msg)
    print("ALICE:", r.stdout.strip())
    r = run(bob_home, "recv")
    print("BOB:  ", r.stdout.strip())
```

6. **Markdown**: `## Each "ALICE" line advances the Alice-to-Bob chain key; each "BOB" line advances Bob's Alice-to-Bob receive chain. Both sides stay in lockstep.`

7. **Code**:
```
# Inspect Alice's session state after 5 sends.
print("--- Alice session state ---")
print(run(alice_home, "show-keys", "bob").stdout)
print("--- Bob session state ---")
print(run(bob_home, "show-keys", "alice").stdout)
```

8. **Code**:
```
# Cleanup.
shutil.rmtree(workdir, ignore_errors=True)
print("cleaned", workdir)
```

9. **Markdown**: `## What you just saw\n\n- Two independent OS processes, each with its own \`~/.pq-messenger\` directory.\n- A shared file-queue "network".\n- Five encrypted-and-decrypted round trips with a single hybrid X3DH handshake up front.\n- Monotonically advancing send/recv indices — the symmetric ratchet in action.\n\nFor a real deployment you'd want the full Double Ratchet (DH re-keying), proper mutual authentication (signatures + published prekeys), and a server for offline delivery. Those are the *next* levels of complexity, intentionally left for the reader.`

Build, execute, commit:

```bash
python /tmp/build_nb04.py && rm /tmp/build_nb04.py
jupyter nbconvert --to notebook --execute notebooks/04_full_session.ipynb --output 04_full_session.ipynb
git add notebooks/04_full_session.ipynb
git commit -m "docs(nb04): end-to-end two-process Alice-Bob session"
```

---

## Task 12: Jupyter Book — config, TOC, intro

**Files:**
- Create: `_config.yml`
- Create: `_toc.yml`
- Create: `intro.md`
- Create: `_static/custom.css`
- Create: `_extra/robots.txt`
- Create: `_templates/layout.html`

- [ ] **Step 1: `_config.yml`**

Create `/Users/dkkang/dev/pq-messenger/_config.yml`:

```yaml
title: "pq-messenger"
author: "hulryung"
copyright: "2026"
logo: ""

only_build_toc_files: true

exclude_patterns:
  - .venv
  - _build
  - _extra
  - tests
  - pqmsg
  - pqmsg.egg-info
  - docs
  - .pytest_cache
  - node_modules
  - "**.ipynb_checkpoints"

execute:
  execute_notebooks: cache
  timeout: 180
  allow_errors: false

repository:
  url: https://github.com/hulryung/pq-messenger
  branch: main

html:
  use_issues_button: true
  use_repository_button: true
  use_edit_page_button: false

sphinx:
  extra_extensions:
    - sphinx_sitemap
    - sphinxext.opengraph
    - sphinx_last_updated_by_git
  config:
    html_show_copyright: false
    html_last_updated_fmt: "%Y-%m-%dT%H:%M:%S+00:00"
    html_baseurl: "https://pqmsg.hulryung.com/"
    html_static_path: ["_static"]
    html_extra_path: ["_extra"]
    templates_path: ["_templates"]
    html_css_files:
      - custom.css
    html_meta:
      description: "Signal-style post-quantum messenger CLI — educational capstone using ML-KEM. Hybrid X3DH + symmetric ratchet in pure Python."
      keywords: "post-quantum cryptography, ML-KEM, Kyber, Signal, X3DH, ratchet, messenger, Python"
      author: "hulryung"
    sitemap_url_scheme: "{link}"
    sitemap_show_lastmod: true
    sitemap_indent: 2
    ogp_site_url: "https://pqmsg.hulryung.com/"
    ogp_site_name: "pq-messenger"
    ogp_description_length: 200
    ogp_type: "article"
    html_theme_options:
      use_download_button: true
```

- [ ] **Step 2: `_toc.yml`**

Create `/Users/dkkang/dev/pq-messenger/_toc.yml`:

```yaml
format: jb-book
root: intro
chapters:
  - file: notebooks/01_protocol_overview
  - file: notebooks/02_key_agreement
  - file: notebooks/03_ratcheting
  - file: notebooks/04_full_session
```

- [ ] **Step 3: `intro.md`**

Create `/Users/dkkang/dev/pq-messenger/intro.md`:

```markdown
# pq-messenger

A Signal-style post-quantum messenger CLI, built as the capstone project for [ML-KEM from Scratch](https://pqc.hulryung.com/). Alice and Bob exchange end-to-end encrypted messages over a local file queue, using a hybrid X25519 + ML-KEM-768 key agreement and a symmetric ratchet per direction.

```{warning}
Educational only — uses the pure-Python `pqc_edu` ML-KEM implementation, omits the DH half of Signal's Double Ratchet, and has no authentication beyond TOFU. **Do not use for real messaging.**
```

## What you'll learn

- Why KEM alone is not enough for a messenger: the role of a symmetric ratchet
- Hybrid X3DH with a post-quantum half (forward-secret against both Shor and classical attacks)
- Forward secrecy — and where symmetric-only ratcheting breaks (key compromise → future messages exposed)
- How a minimal end-to-end session looks when you can see every byte

## Four chapters

1. **Protocol overview** — threat model, hybrid X3DH, ratchet, wire format
2. **Key agreement** — walk through `initiate_session` and `accept_session` with real keys
3. **Ratcheting** — 10-step symmetric chain; compromise simulation at step 5
4. **Full session** — two OS processes, five roundtrip messages over a shared file queue

## Source

[github.com/hulryung/pq-messenger](https://github.com/hulryung/pq-messenger)
```

- [ ] **Step 4: Copy shared assets from ml-kem-notebooks**

```bash
cd /Users/dkkang/dev/pq-messenger
mkdir -p _static _extra _templates
cp /Users/dkkang/dev/pqc/_static/custom.css _static/custom.css
cp /Users/dkkang/dev/pqc/_extra/robots.txt _extra/robots.txt
cp /Users/dkkang/dev/pqc/_templates/layout.html _templates/layout.html
# Fix robots.txt sitemap URLs to point at pq-messenger
```

Then edit `_extra/robots.txt` to be:

```
User-agent: *
Allow: /

Sitemap: https://pqmsg.hulryung.com/sitemap.xml
```

- [ ] **Step 5: Build book locally**

```bash
pip install -e ".[book]" 2>&1 | tail -3
jupyter-book build . 2>&1 | tail -3
```

Expected: `build succeeded`.

- [ ] **Step 6: Commit**

```bash
git add _config.yml _toc.yml intro.md _static _extra _templates
git commit -m "feat(book): jupyter-book config, TOC, and intro for pq-messenger"
```

---

## Task 13: GitHub Actions workflow + deploy

- [ ] **Step 1: Create workflow**

Create `/Users/dkkang/dev/pq-messenger/.github/workflows/book.yml`:

```yaml
name: deploy-book

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout pq-messenger
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          path: pq-messenger

      - name: Checkout ml-kem-notebooks (pqc-edu source)
        uses: actions/checkout@v4
        with:
          repository: hulryung/ml-kem-notebooks
          path: ml-kem-notebooks

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ./ml-kem-notebooks
          pip install -e "./pq-messenger[dev,book]"

      - name: Run tests
        run: |
          cd pq-messenger && pytest tests/ -v

      - name: Build the book
        run: |
          cd pq-messenger && jupyter-book build .

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: pq-messenger/_build/html

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit and push**

```bash
git add .github/workflows/book.yml
git commit -m "ci: github pages deploy workflow"
git push origin main
```

- [ ] **Step 3: Enable GitHub Pages**

```bash
gh api -X POST /repos/hulryung/pq-messenger/pages -f 'build_type=workflow'
```

- [ ] **Step 4: Wait for deploy + verify live**

```bash
sleep 60
gh run list --repo hulryung/pq-messenger --limit 1
```

Once the run completes:

```bash
for nb in 01_protocol_overview 02_key_agreement 03_ratcheting 04_full_session; do
  curl -sI "https://pqmsg.hulryung.com/notebooks/${nb}.html" | head -1
done
curl -sI "https://pqmsg.hulryung.com/" | head -1
curl -sI "https://pqmsg.hulryung.com/sitemap.xml" | head -1
```

Expected: all `HTTP/2 200`.

- [ ] **Step 5: Copy spec + plan into the new repo**

```bash
cd /Users/dkkang/dev/pq-messenger
mkdir -p docs/superpowers/specs docs/superpowers/plans
cp /Users/dkkang/dev/pqc/docs/superpowers/specs/2026-04-22-pq-messenger-design.md docs/superpowers/specs/
cp /Users/dkkang/dev/pqc/docs/superpowers/plans/2026-04-22-pq-messenger.md docs/superpowers/plans/
git add docs/
git commit -m "docs: include design spec and implementation plan"
git push origin main
```

---

## Self-Review Checklist

- [x] **Spec coverage**: every spec section has tasks — §4 structure → Task 0; §5 protocol → Tasks 1, 2, 4; §6 notebook flow → Tasks 8–11; §7 CLI → Task 6; §8 tests → Tasks 1, 2, 3, 4, 5, 7; §10 deployment → Tasks 12, 13.
- [x] **Placeholder scan**: no TBD/TODO; every step has complete code.
- [x] **Type consistency**: `Identity`, `Contact`, `Session`, `Handshake`, `hkdf_shake256`, `derive_chain_step`, `initiate_session`, `accept_session`, `encrypt`, `decrypt`, `send_blob`, `pop_message`, `list_inbox`, `serialize_message`, `parse_message`, `MessageFormatError` — names match across all tasks.
- [x] **Scope check**: single project (sibling repo), well-bounded. ~14 tasks, ~26 unit tests + 1 integration test, 4 notebooks, GH Pages deploy. Doable.

## Known Risk Points

- **`pqc-edu` local install**: if the sibling repo is cloned somewhere other than `../ml-kem-notebooks`, `pip install` will fail. Task 0 Step 5 notes this. GH Actions workflow (Task 13) explicitly checks out both repos to resolve it.
- **Test timing**: Task 7 integration test spins up 12 subprocesses; on slow machines this may approach the 60-second per-subprocess timeout. The timeout is already generous for ML-KEM keygen time in pure Python.
- **Ed25519 is unused in this scope**: we generate the keypair but never sign anything. That's intentional (spec §5.1: "자리만 확보"). Do not add signing without expanding the spec.
- **Pickle for session state**: Task 6 uses `pickle` for session storage. This is safe because we only ever load sessions we wrote ourselves. Not for untrusted data.

Debug order if tests fail: `test_kdf.py` → `test_identity.py` → `test_encoding.py` → `test_session.py` → `test_transport.py` → `test_cli.py`. A failure in kdf or identity invalidates everything downstream.
