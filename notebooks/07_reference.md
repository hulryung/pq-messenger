# Notebook 07 — Reference

The CLI commands and Python API surface, in one place.

## CLI commands

All commands honor the `PQMSG_HOME` environment variable (default: `~/.pq-messenger/`). State written under that directory: `identity.json`, `contacts/<alias>.json`, `sessions/<peer>.json`, `inbox/<recipient>/<uuid>.json`.

| Command           | Purpose                                                    |
| ----------------- | ---------------------------------------------------------- |
| `init`            | Generate a fresh Ed25519 + X25519 + ML-KEM-768 identity.   |
| `show-identity`   | Print the active identity (public components only).        |
| `export-contact`  | Write a public-only contact file for sharing out-of-band.  |
| `import-contact`  | Import a peer's contact file under a local alias.          |
| `send`            | Encrypt and enqueue a message into the recipient's inbox.  |
| `recv`            | Dequeue and decrypt the oldest message destined for us.    |
| `show-keys`       | Debug: print current ratchet state for a peer session.     |
| `reset`           | Delete `~/.pq-messenger/` (all identities/contacts/state). |

```text
pqmsg init               --name TEXT
pqmsg show-identity
pqmsg export-contact     [--output PATH]
pqmsg import-contact PATH --as ALIAS
pqmsg send  RECIPIENT BODY
pqmsg recv               [--all]
pqmsg show-keys PEER
pqmsg reset
```

## Python API

The whole library is small enough to enumerate. Re-exports from the package root: nothing; import from the submodule directly.

### `pqmsg.identity`

```{eval-rst}
.. automodule:: pqmsg.identity
   :members: Identity, Contact, generate_identity, save_identity, load_identity, export_contact, import_contact
   :undoc-members:
   :show-inheritance:
```

### `pqmsg.session`

```{eval-rst}
.. automodule:: pqmsg.session
   :members: Handshake, Session, initiate_session, accept_session, encrypt, decrypt
   :undoc-members:
   :show-inheritance:
```

### `pqmsg.kdf`

```{eval-rst}
.. automodule:: pqmsg.kdf
   :members: hkdf_shake256, derive_chain_step
```

### `pqmsg.transport`

```{eval-rst}
.. automodule:: pqmsg.transport
   :members: send_blob, list_inbox, pop_message
```

### `pqmsg.encoding`

```{eval-rst}
.. automodule:: pqmsg.encoding
   :members: MessageFormatError, serialize_message, parse_message
```

## On-disk wire format

Every queued message is a single JSON file:

```json
{
  "version": 1,
  "sender": "alice",
  "recipient": "bob",
  "msg_index": 0,
  "kem_ciphertext": "base64...",
  "ephemeral_pk": "base64...",
  "nonce": "base64...",
  "ciphertext": "base64...",
  "sent_at": "2026-04-22T15:30:00Z"
}
```

Only the first message in a session carries `kem_ciphertext` and `ephemeral_pk`; subsequent messages omit them. See [notebook 01 §Wire format](01_protocol_overview.ipynb) for the rationale.
