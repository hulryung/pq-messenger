"""Double-ratchet semantics: post-compromise security and out-of-order delivery."""
import pytest

from pqmsg.identity import generate_identity
from pqmsg.session import (
    initiate_session, accept_session, encrypt, decrypt,
)


def _setup_pair():
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
    return sess_a, sess_b, handshake


def _round(sess_a, sess_b, body: bytes, handshake=None, is_first=False) -> bytes:
    msg = encrypt(sess_a, body, is_first=is_first, handshake=handshake)
    return decrypt(sess_b, msg)


# --- Post-compromise security ----------------------------------------------

def test_post_compromise_recovers_after_dh_ping_pong():
    """Models the scenario from notebook 03: an attacker captures Alice's
    send chain key after step 5. With the DH ratchet, once the conversation
    flips direction (Bob replies), Alice's *next* sending burst rotates the
    chain key with fresh entropy from a new DH exchange — entropy the
    attacker has not seen. The leaked key can no longer derive the next
    message key."""
    from pqmsg.kdf import derive_chain_step

    sess_a, sess_b, hs = _setup_pair()

    # Five Alice -> Bob messages
    for i in range(5):
        assert _round(sess_a, sess_b, f"a->b {i}".encode(),
                      handshake=hs if i == 0 else None, is_first=(i == 0)) == f"a->b {i}".encode()

    # Attacker steals Alice's chain key right after step 5
    leaked_chain = sess_a.chain_key_send

    # Direction flips: Bob replies. This carries Bob's new DH pub to Alice.
    assert _round(sess_b, sess_a, b"b->a") == b"b->a"

    # Alice's next send is the first of a new burst → DH ratchet rotates her
    # send chain via HKDF(root_key, DH(new_eph, bob_dh_pub)). The attacker
    # cannot reproduce this without bob_dh_pub *and* the new ephemeral.
    msg6 = encrypt(sess_a, b"healed", is_first=False, handshake=None)

    # The naive attacker would have advanced `leaked_chain` once to predict
    # the next message key. Verify that prediction does NOT decrypt msg6.
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
    predicted_msg_key, _ = derive_chain_step(leaked_chain)
    aead = ChaCha20Poly1305(predicted_msg_key)
    with pytest.raises(InvalidTag):
        aead.decrypt(msg6["nonce"], msg6["ciphertext"], None)

    # Bob, who saw Alice's new DH pub in msg6's header, decrypts cleanly:
    assert decrypt(sess_b, msg6) == b"healed"


def test_dh_pub_present_on_every_message():
    """Wire format v2 carries dh_pub on every message (not just the first)."""
    sess_a, sess_b, hs = _setup_pair()
    msg0 = encrypt(sess_a, b"hello", is_first=True, handshake=hs)
    assert "dh_pub" in msg0 and msg0["dh_pub"] is not None
    decrypt(sess_b, msg0)
    msg1 = encrypt(sess_a, b"second", is_first=False, handshake=None)
    assert "dh_pub" in msg1 and msg1["dh_pub"] is not None


def test_root_key_changes_on_direction_flip():
    """When the conversation direction flips, the DH ratchet step must
    advance the root key on at least one side per message."""
    sess_a, sess_b, hs = _setup_pair()
    initial_root = sess_a.root_key

    # Alice -> Bob
    _round(sess_a, sess_b, b"a->b 0", handshake=hs, is_first=True)
    # Bob -> Alice (direction flip)
    _round(sess_b, sess_a, b"b->a 0")
    # Alice's next send rotates her DH again
    encrypt(sess_a, b"a->b 1", is_first=False, handshake=None)

    assert sess_a.root_key != initial_root
    assert sess_b.root_key != initial_root


# --- Out-of-order delivery (skipped-key cache) -----------------------------

def test_out_of_order_within_chain_decrypts():
    """Alice sends three messages in a burst. Bob receives them in order
    [0, 2, 1] — message 1 must still decrypt thanks to the skipped-key cache."""
    sess_a, sess_b, hs = _setup_pair()

    m0 = encrypt(sess_a, b"msg 0", is_first=True, handshake=hs)
    m1 = encrypt(sess_a, b"msg 1", is_first=False, handshake=None)
    m2 = encrypt(sess_a, b"msg 2", is_first=False, handshake=None)

    assert decrypt(sess_b, m0) == b"msg 0"
    assert decrypt(sess_b, m2) == b"msg 2"   # skips index 1, caches its key
    assert decrypt(sess_b, m1) == b"msg 1"   # uses cached key


def test_skipped_key_cache_bounded():
    """A flood of bogus indices must not exhaust memory — the cache is
    bounded. Receiving an index too far ahead must raise."""
    sess_a, sess_b, hs = _setup_pair()
    m0 = encrypt(sess_a, b"first", is_first=True, handshake=hs)
    decrypt(sess_b, m0)

    # Create one legitimate message, then forge a far-future index header
    # that exceeds the skipped-key cache window.
    legit = encrypt(sess_a, b"legit", is_first=False, handshake=None)
    legit["msg_index"] = 10_000   # pretend Alice raced ahead 10k messages
    with pytest.raises(Exception):
        decrypt(sess_b, legit)
