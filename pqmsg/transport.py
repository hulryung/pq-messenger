"""Local-filesystem transport: one file per message, oldest-first FIFO.

Each message is written atomically (<name>.json.tmp -> rename -> <name>.json)
so a concurrent reader never sees a partial file. We sort by mtime for a
stable FIFO ordering.
"""
from __future__ import annotations
import uuid
from pathlib import Path


def _inbox_dir(inbox_root: Path, recipient: str) -> Path:
    d = Path(inbox_root) / recipient
    d.mkdir(parents=True, exist_ok=True)
    return d


def send_blob(*, inbox_root: Path, recipient: str, blob: bytes) -> Path:
    """Atomically write `blob` into recipient's inbox. Returns final path."""
    dirp = _inbox_dir(Path(inbox_root), recipient)
    mid = uuid.uuid4().hex
    final = dirp / f"{mid}.json"
    tmp = dirp / f"{mid}.json.tmp"
    tmp.write_bytes(blob)
    tmp.replace(final)
    return final


def list_inbox(*, inbox_root: Path, recipient: str) -> list[Path]:
    """List pending messages in mtime order (oldest first). Ignores .tmp files."""
    dirp = Path(inbox_root) / recipient
    if not dirp.exists():
        return []
    items = [p for p in dirp.iterdir() if p.suffix == ".json"]
    items.sort(key=lambda p: p.stat().st_mtime_ns)
    return items


def pop_message(*, inbox_root: Path, recipient: str) -> bytes | None:
    """Return and remove the oldest message, or None if inbox is empty."""
    items = list_inbox(inbox_root=inbox_root, recipient=recipient)
    if not items:
        return None
    oldest = items[0]
    data = oldest.read_bytes()
    oldest.unlink()
    return data
