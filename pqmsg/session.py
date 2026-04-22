"""Hybrid X3DH + symmetric ratchet session."""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from pqc_edu.params import ML_KEM_768
from pqc_edu.ml_kem import ml_kem_encaps, ml_kem_decaps

from .identity import Identity
from .kdf import hkdf_shake256, derive_chain_step, ROOT_KEY_LEN, CHAIN_KEY_LEN


@dataclass
class Handshake:
    ephemeral_pk: bytes
    kem_ciphertext: bytes


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
        chain_key_send=chain_b2a,
        chain_key_recv=chain_a2b,
    )


def encrypt(
    session: Session,
    plaintext: bytes,
    *,
    is_first: bool,
    handshake: Optional[Handshake],
) -> dict:
    """Advance the send chain and encrypt."""
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
        "sender": "",
        "recipient": session.peer_name,
        "msg_index": idx,
        "kem_ciphertext": handshake.kem_ciphertext if is_first else None,
        "ephemeral_pk": handshake.ephemeral_pk if is_first else None,
        "nonce": nonce,
        "ciphertext": ciphertext,
        "sent_at": "",
    }


def decrypt(session: Session, msg: dict) -> bytes:
    """Advance the receive chain and decrypt."""
    msg_key, next_chain = derive_chain_step(session.chain_key_recv)
    aead = ChaCha20Poly1305(msg_key)
    plaintext = aead.decrypt(msg["nonce"], msg["ciphertext"], None)
    session.chain_key_recv = next_chain
    session.recv_index += 1
    return plaintext
