"""HKDF over SHAKE256.

We use SHAKE256 (variable-length XOF) so the protocol is consistent with
ML-KEM's internal hash choice. HKDF construction (RFC 5869 style)::

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
    """Derive `length` bytes of keying material from (salt, ikm, info)."""
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
    """Advance the symmetric ratchet. Returns (message_key, next_chain_key)."""
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
