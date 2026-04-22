"""Click CLI for pq-messenger."""
from __future__ import annotations
import datetime
import os
import pickle
from pathlib import Path

import click

from . import identity as _identity
from . import session as _session
from . import transport as _transport
from . import encoding as _encoding


def _home() -> Path:
    return Path(os.environ.get("PQMSG_HOME", Path.home() / ".pq-messenger"))


def _identity_path() -> Path:
    return _home() / "identity.json"


def _contacts_dir() -> Path:
    d = _home() / "contacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sessions_dir() -> Path:
    d = _home() / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _inbox_root() -> Path:
    return _home() / "inbox"


def _load_own() -> _identity.Identity:
    path = _identity_path()
    if not path.exists():
        raise click.ClickException("no identity found — run `pqmsg init --name NAME` first")
    return _identity.load_identity(path)


def _load_contact(name: str) -> _identity.Contact:
    path = _contacts_dir() / f"{name}.pub"
    if not path.exists():
        raise click.ClickException(f"contact '{name}' not found — run `pqmsg import-contact`")
    return _identity.import_contact(path)


def _session_path(peer_name: str) -> Path:
    return _sessions_dir() / f"{peer_name}.session"


def _save_session(peer_name: str, sess: _session.Session) -> None:
    p = _session_path(peer_name)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_bytes(pickle.dumps(sess))
    tmp.replace(p)


def _load_session(peer_name: str) -> _session.Session | None:
    p = _session_path(peer_name)
    if not p.exists():
        return None
    return pickle.loads(p.read_bytes())


@click.group()
def main():
    """Post-quantum messenger CLI (educational)."""
    pass


@main.command()
@click.option("--name", required=True)
def init(name):
    """Generate a fresh identity."""
    path = _identity_path()
    if path.exists():
        raise click.ClickException(f"identity already exists at {path}; remove or run `pqmsg reset`")
    ident = _identity.generate_identity(name=name)
    _identity.save_identity(ident, path)
    click.echo(f"Generated identity for '{name}' at {path}")
    click.echo(f"Share your contact file: pqmsg export-contact --output /tmp/{name}.pub")


@main.command("show-identity")
def show_identity():
    """Show the active identity (public components)."""
    ident = _load_own()
    click.echo(f"name: {ident.name}")
    click.echo(f"x25519_public  ({len(ident.x25519_public)}B): {ident.x25519_public.hex()[:32]}...")
    click.echo(f"ed25519_public ({len(ident.ed25519_public)}B): {ident.ed25519_public.hex()[:32]}...")
    click.echo(f"ml_kem_public  ({len(ident.ml_kem_public)}B): {ident.ml_kem_public.hex()[:32]}...")


@main.command("export-contact")
@click.option("--output", type=click.Path(), default=None)
def export_contact_cmd(output):
    """Write public-only contact file for sharing."""
    ident = _load_own()
    if output is None:
        output = _contacts_dir() / f"{ident.name}.pub"
    _identity.export_contact(ident, Path(output))
    click.echo(f"exported to {output}")


@main.command("import-contact")
@click.argument("path", type=click.Path(exists=True))
@click.option("--as", "as_name", required=True, help="local alias")
def import_contact_cmd(path, as_name):
    """Import a peer's public contact file under a local alias."""
    contact = _identity.import_contact(Path(path))
    stored_path = _contacts_dir() / f"{as_name}.pub"
    _identity.export_contact(
        _identity.Identity(
            name=as_name,
            x25519_public=contact.x25519_public, x25519_private=b"",
            ed25519_public=contact.ed25519_public, ed25519_private=b"",
            ml_kem_public=contact.ml_kem_public, ml_kem_private=b"",
        ),
        stored_path,
    )
    click.echo(f"contact '{contact.name}' imported as '{as_name}'")


@main.command()
@click.argument("recipient")
@click.argument("body")
def send(recipient, body):
    """Encrypt and enqueue a message."""
    ours = _load_own()
    peer = _load_contact(recipient)
    sess = _load_session(recipient)
    handshake = None
    is_first = False
    if sess is None:
        sess, handshake = _session.initiate_session(
            ours=ours,
            peer_name=recipient,
            peer_x25519_pub=peer.x25519_public,
            peer_ml_kem_pub=peer.ml_kem_public,
        )
        is_first = True
    msg = _session.encrypt(sess, body.encode("utf-8"), is_first=is_first, handshake=handshake)
    msg["sender"] = ours.name
    msg["sent_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    blob = _encoding.serialize_message(**msg)
    _transport.send_blob(inbox_root=_inbox_root(), recipient=recipient, blob=blob)
    _save_session(recipient, sess)
    click.echo(f"sent message #{msg['msg_index']} to {recipient} ({len(blob)} bytes)")


@main.command()
@click.option("--all", "recv_all", is_flag=True)
def recv(recv_all):
    """Dequeue and decrypt messages destined for us."""
    ours = _load_own()
    name = ours.name
    count = 0
    while True:
        blob = _transport.pop_message(inbox_root=_inbox_root(), recipient=name)
        if blob is None:
            break
        try:
            msg = _encoding.parse_message(blob)
        except _encoding.MessageFormatError as e:
            click.echo(f"[malformed] {e}", err=True)
            continue
        sender = msg["sender"]
        sess = _load_session(sender)
        if sess is None:
            if not msg["kem_ciphertext"] or not msg["ephemeral_pk"]:
                click.echo(f"[no session with {sender} and no handshake in first message]", err=True)
                continue
            peer = _load_contact(sender)
            handshake = _session.Handshake(
                ephemeral_pk=msg["ephemeral_pk"],
                kem_ciphertext=msg["kem_ciphertext"],
            )
            sess = _session.accept_session(
                ours=ours, peer_name=sender,
                peer_x25519_pub=peer.x25519_public,
                handshake=handshake,
            )
        try:
            pt = _session.decrypt(sess, msg)
        except Exception as e:
            click.echo(f"[decryption failed from {sender}] {e}", err=True)
            continue
        click.echo(f"[from {sender}, msg #{msg['msg_index']}]: {pt.decode('utf-8', errors='replace')}")
        _save_session(sender, sess)
        count += 1
        if not recv_all:
            break
    if count == 0:
        click.echo("(no messages)")


@main.command("show-keys")
@click.argument("peer")
def show_keys(peer):
    """Debug: print current ratchet state for a peer."""
    sess = _load_session(peer)
    if sess is None:
        raise click.ClickException(f"no session with {peer}")
    click.echo(f"peer: {sess.peer_name}")
    click.echo(f"send_index: {sess.send_index}")
    click.echo(f"recv_index: {sess.recv_index}")
    click.echo(f"chain_key_send (first 8 bytes): {sess.chain_key_send[:8].hex()}")
    click.echo(f"chain_key_recv (first 8 bytes): {sess.chain_key_recv[:8].hex()}")


@main.command()
def reset():
    """Remove ~/.pq-messenger/ (all identities, contacts, sessions)."""
    import shutil
    home = _home()
    if home.exists():
        shutil.rmtree(home)
        click.echo(f"removed {home}")
    else:
        click.echo("nothing to remove")


if __name__ == "__main__":
    main()
