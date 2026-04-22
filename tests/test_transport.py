import time
import pytest
from pathlib import Path
from pqmsg.transport import send_blob, list_inbox, pop_message


def test_send_and_list(tmp_path):
    inbox_root = tmp_path / "inbox"
    send_blob(inbox_root=inbox_root, recipient="bob", blob=b"hello world")
    items = list_inbox(inbox_root=inbox_root, recipient="bob")
    assert len(items) == 1
    assert items[0].read_bytes() == b"hello world"


def test_pop_returns_oldest_first(tmp_path):
    inbox_root = tmp_path / "inbox"
    for i in range(3):
        send_blob(inbox_root=inbox_root, recipient="bob", blob=f"msg{i}".encode())
        time.sleep(0.01)
    first = pop_message(inbox_root=inbox_root, recipient="bob")
    assert first == b"msg0"
    second = pop_message(inbox_root=inbox_root, recipient="bob")
    assert second == b"msg1"
    third = pop_message(inbox_root=inbox_root, recipient="bob")
    assert third == b"msg2"
    assert pop_message(inbox_root=inbox_root, recipient="bob") is None


def test_atomic_write_no_partial_files(tmp_path):
    inbox_root = tmp_path / "inbox"
    send_blob(inbox_root=inbox_root, recipient="bob", blob=b"x")
    leftovers = list((inbox_root / "bob").glob("*.tmp"))
    assert leftovers == []


def test_list_empty_inbox(tmp_path):
    inbox_root = tmp_path / "inbox"
    assert list_inbox(inbox_root=inbox_root, recipient="bob") == []


def test_pop_ignores_tmp_files(tmp_path):
    inbox_root = tmp_path / "inbox"
    (inbox_root / "bob").mkdir(parents=True)
    (inbox_root / "bob" / "partial.tmp").write_bytes(b"should be ignored")
    assert pop_message(inbox_root=inbox_root, recipient="bob") is None
