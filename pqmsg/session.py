"""Hybrid X3DH + Double Ratchet session.

v0.2 adds the DH half of Signal's Double Ratchet on top of the symmetric
ratchet from v0.1: every time the conversation flips direction, the next
sender generates a fresh X25519 keypair, attaches the public half to the
message header, and mixes DH(new_eph, peer_dh_pub) into the root key.

Out-of-order delivery within a single sending burst is supported via a
bounded skipped-key cache.
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

MAX_SKIP = 100  # max out-of-order messages tolerated per chain


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
    # DH ratchet state
    dh_send_priv: bytes  # raw X25519 private (32 B)
    dh_send_pub: bytes   # raw X25519 public  (32 B)
    dh_recv_pub: bytes | None = None  # peer's most recently seen DH pub
    send_index: int = 0
    recv_index: int = 0
    prev_send_count: int = 0  # messages sent in the previous sending chain
    # Cache: (dh_pub, msg_index) -> message_key, for out-of-order receives
    skipped_keys: dict = field(default_factory=dict)


def _kdf_root(root_key: bytes, dh_output: bytes) -> tuple[bytes, bytes]:
    """Advance root + return a fresh chain key. RFC 5869 style two-output KDF."""
    out = hkdf_shake256(
        salt=root_key, ikm=dh_output, info=b"pqmsg-dh-ratchet-v2",
        length=ROOT_KEY_LEN + CHAIN_KEY_LEN,
    )
    return out[:ROOT_KEY_LEN], out[ROOT_KEY_LEN:]


def _derive_session_keys(
    dh_shared: bytes, kem_shared: bytes,
    alice_x_pub: bytes, bob_x_pub: bytes, alice_eph_pub: bytes,
) -> tuple[bytes, bytes, bytes]:
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


def _new_dh_keypair() -> tuple[bytes, bytes]:
    sk = X25519PrivateKey.generate()
    return sk.private_bytes_raw(), sk.public_key().public_bytes_raw()


def _dh(priv: bytes, pub: bytes) -> bytes:
    return X25519PrivateKey.from_private_bytes(priv).exchange(
        X25519PublicKey.from_public_bytes(pub)
    )


def initiate_session(
    ours: Identity,
    peer_name: str,
    peer_x25519_pub: bytes,
    peer_ml_kem_pub: bytes,
) -> tuple[Session, Handshake]:
    """Alice-side: generate ephemeral, encapsulate, derive session keys.

    The X3DH ephemeral doubles as Alice's first DH-ratchet keypair. Bob's
    long-term X25519 public is used as Bob's first DH-ratchet pub until
    Bob sends his own message with a fresh DH pub.
    """
    eph_sk = X25519PrivateKey.generate()
    eph_priv_bytes = eph_sk.private_bytes_raw()
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
        dh_send_priv=eph_priv_bytes,
        dh_send_pub=eph_pk_bytes,
        dh_recv_pub=peer_x25519_pub,
    )
    handshake = Handshake(ephemeral_pk=eph_pk_bytes, kem_ciphertext=kem_ct)
    return session, handshake


def accept_session(
    ours: Identity,
    peer_name: str,
    peer_x25519_pub: bytes,
    handshake: Handshake,
) -> Session:
    """Bob-side: decapsulate, complete DH, derive session keys.

    Bob seeds his DH-ratchet send key with his own long-term X25519 pair
    initially (it matches Alice's `dh_recv_pub`); on his first reply he'll
    rotate to a fresh keypair and ratchet the root.
    """
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
        dh_send_priv=ours.x25519_private,
        dh_send_pub=ours.x25519_public,
        dh_recv_pub=handshake.ephemeral_pk,
    )


def _maybe_rotate_send_dh(session: Session) -> bool:
    """If we just received from the peer (recv_index advanced past 0 since
    last send) and we haven't yet rotated for this burst, generate a fresh
    DH keypair and re-key the send chain. Returns True if rotation happened."""
    # We rotate at the start of a new sending burst, which is signaled by
    # the receive index being > 0 since our last send. Bob's first reply is
    # also a new burst (after accept_session, recv_index == 0 and send_index
    # == 0; Bob's first send must rotate so Alice can ratchet on receive).
    needs_rotate = session.send_index == 0 and session.recv_index > 0
    if session.send_index > 0:
        # Mid-burst send — keep current DH keypair
        return False
    if session.dh_recv_pub is None:
        return False
    if not needs_rotate and session.send_index == 0 and session.recv_index == 0:
        # Brand-new session, Alice's very first message: keep ephemeral
        return False
    new_priv, new_pub = _new_dh_keypair()
    dh_out = _dh(new_priv, session.dh_recv_pub)
    new_root, new_chain = _kdf_root(session.root_key, dh_out)
    session.root_key = new_root
    session.chain_key_send = new_chain
    session.dh_send_priv = new_priv
    session.dh_send_pub = new_pub
    session.prev_send_count = 0  # reset for the new sending chain
    return True


def encrypt(
    session: Session,
    plaintext: bytes,
    *,
    is_first: bool,
    handshake: Optional[Handshake],
) -> dict:
    """Advance the send chain (rotating DH if a new burst) and encrypt."""
    if is_first and handshake is None:
        raise ValueError("is_first=True requires handshake")
    _maybe_rotate_send_dh(session)

    msg_key, next_chain = derive_chain_step(session.chain_key_send)
    nonce = os.urandom(12)
    aead = ChaCha20Poly1305(msg_key)
    ciphertext = aead.encrypt(nonce, plaintext, None)
    idx = session.send_index
    session.chain_key_send = next_chain
    session.send_index += 1
    return {
        "version": 2,
        "sender": "",
        "recipient": session.peer_name,
        "msg_index": idx,
        "kem_ciphertext": handshake.kem_ciphertext if is_first else None,
        "ephemeral_pk": handshake.ephemeral_pk if is_first else None,
        "dh_pub": session.dh_send_pub,
        "prev_chain_length": session.prev_send_count,
        "nonce": nonce,
        "ciphertext": ciphertext,
        "sent_at": "",
    }


def _try_skipped(session: Session, msg: dict) -> bytes | None:
    key = (msg["dh_pub"], msg["msg_index"])
    msg_key = session.skipped_keys.pop(key, None)
    if msg_key is None:
        return None
    aead = ChaCha20Poly1305(msg_key)
    return aead.decrypt(msg["nonce"], msg["ciphertext"], None)


def _skip_chain(session: Session, until: int, dh_pub: bytes) -> None:
    """Pre-derive and cache message keys [recv_index, until)."""
    if until - session.recv_index > MAX_SKIP:
        raise ValueError(
            f"too many skipped messages ({until - session.recv_index} > {MAX_SKIP})"
        )
    while session.recv_index < until:
        msg_key, next_chain = derive_chain_step(session.chain_key_recv)
        session.skipped_keys[(dh_pub, session.recv_index)] = msg_key
        session.chain_key_recv = next_chain
        session.recv_index += 1


def _dh_ratchet_recv(session: Session, new_dh_pub: bytes, prev_chain_length: int) -> None:
    """Peer rotated DH. Cache any unread keys from the old recv chain, then
    re-key recv side with DH(our_priv, new_dh_pub)."""
    if session.dh_recv_pub is not None and prev_chain_length > session.recv_index:
        _skip_chain(session, prev_chain_length, session.dh_recv_pub)

    # Step 1: ratchet recv chain with the peer's new pub
    dh_out = _dh(session.dh_send_priv, new_dh_pub)
    new_root, new_recv_chain = _kdf_root(session.root_key, dh_out)
    session.root_key = new_root
    session.chain_key_recv = new_recv_chain
    session.dh_recv_pub = new_dh_pub
    session.recv_index = 0
    # Note: send chain is *not* rotated here — that happens on our next send
    # (start of our next burst). prev_send_count stores how many we sent in
    # the burst we're about to close.
    session.prev_send_count = session.send_index
    session.send_index = 0


def decrypt(session: Session, msg: dict) -> bytes:
    """Decrypt a message, applying DH ratchet on direction flip and
    consulting the skipped-key cache for out-of-order delivery."""
    # 1. Skipped-key cache hit
    cached = _try_skipped(session, msg)
    if cached is not None:
        return cached

    # 2. New DH pub from peer → ratchet
    if msg["dh_pub"] != session.dh_recv_pub:
        _dh_ratchet_recv(session, msg["dh_pub"], msg.get("prev_chain_length", 0))

    # 3. Skip ahead in current chain if needed
    if msg["msg_index"] > session.recv_index:
        _skip_chain(session, msg["msg_index"], msg["dh_pub"])

    # 4. Standard symmetric step
    msg_key, next_chain = derive_chain_step(session.chain_key_recv)
    aead = ChaCha20Poly1305(msg_key)
    plaintext = aead.decrypt(msg["nonce"], msg["ciphertext"], None)
    session.chain_key_recv = next_chain
    session.recv_index += 1
    return plaintext
