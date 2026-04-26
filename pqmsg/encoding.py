"""Wire format v2 for messages: JSON with base64-encoded byte fields.

v2 (added in pqmsg 0.2.0): every message carries the sender's current DH
public key (`dh_pub`) and the length of the previous send chain
(`prev_chain_length`) so the receiver can run the DH ratchet and skip
unread keys for out-of-order delivery. v1 messages are rejected.
"""
from __future__ import annotations
import base64
import json
from typing import Any

WIRE_VERSION = 2


class MessageFormatError(ValueError):
    pass


_REQUIRED_FIELDS = {
    "version", "sender", "recipient", "msg_index",
    "kem_ciphertext", "ephemeral_pk",
    "dh_pub", "prev_chain_length",
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
    dh_pub: bytes,
    prev_chain_length: int,
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
        "dh_pub": base64.b64encode(dh_pub).decode("ascii"),
        "prev_chain_length": prev_chain_length,
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
        "dh_pub": base64.b64decode(raw["dh_pub"]),
        "prev_chain_length": raw["prev_chain_length"],
        "nonce": base64.b64decode(raw["nonce"]),
        "ciphertext": base64.b64decode(raw["ciphertext"]),
        "sent_at": raw["sent_at"],
    }
