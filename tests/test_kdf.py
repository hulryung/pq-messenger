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
    ck_in = b"\x22" * 32
    msg_key, ck_out = derive_chain_step(ck_in)
    ck_in2 = bytes([(b ^ 0x01) for b in ck_in])
    msg_key2, ck_out2 = derive_chain_step(ck_in2)
    assert msg_key != msg_key2
    assert ck_out != ck_out2
