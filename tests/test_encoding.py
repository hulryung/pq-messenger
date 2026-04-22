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
