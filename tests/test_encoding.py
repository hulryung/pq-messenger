import pytest
from pqmsg.encoding import serialize_message, parse_message, MessageFormatError


SAMPLE = {
    "version": 2,
    "sender": "alice",
    "recipient": "bob",
    "msg_index": 3,
    "kem_ciphertext": None,
    "ephemeral_pk": None,
    "dh_pub": b"\xaa" * 32,
    "prev_chain_length": 0,
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
    bad = blob.replace(b'"version": 2', b'"version": 99')
    with pytest.raises(MessageFormatError):
        parse_message(bad)


def test_parse_rejects_v1_messages():
    """v1 wire format is no longer accepted (no dh_pub field)."""
    v1_blob = (
        b'{"version": 1, "sender": "a", "recipient": "b", "msg_index": 0, '
        b'"kem_ciphertext": null, "ephemeral_pk": null, '
        b'"nonce": "AAAA", "ciphertext": "AAAA", "sent_at": ""}'
    )
    with pytest.raises(MessageFormatError):
        parse_message(v1_blob)
