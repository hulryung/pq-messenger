import json
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
