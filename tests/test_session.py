import pytest
from pqmsg.identity import generate_identity
from pqmsg.session import (
    Session, initiate_session, accept_session, encrypt, decrypt,
)


def test_x3dh_both_sides_derive_same_root():
    alice = generate_identity("alice")
    bob = generate_identity("bob")

    sess_a, handshake = initiate_session(
        ours=alice,
        peer_name=bob.name,
        peer_x25519_pub=bob.x25519_public,
        peer_ml_kem_pub=bob.ml_kem_public,
    )
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

    for i in range(5):
        pt = f"message {i} from alice".encode()
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
    msg["ciphertext"] = msg["ciphertext"][:-4] + b"\x00\x00\x00\x00"
    with pytest.raises(Exception):
        decrypt(sess_b, msg)
