# Changelog

All notable changes are kept in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [0.2.0] — 2026-04-26

### Added

- **DH ratchet** in `pqmsg.session` — every direction flip rotates an X25519 keypair and mixes `DH(new_eph, peer_dh_pub)` into the root key via `HKDF`. Closes the post-compromise-security gap demonstrated in notebook 03.
- **Skipped-key cache** (`MAX_SKIP = 100`) — out-of-order delivery within a chain decrypts cleanly; far-future indices are rejected.
- `tests/test_dh_ratchet.py` — five new tests covering post-compromise security, DH presence on every message, root-key advancement, out-of-order delivery, and cache bounds.
- `notebooks/03_ratcheting` — second half rebuilt as a live "v0.1 leaks → v0.2 heals" demo using the real session API.
- Mermaid diagrams (`sphinxcontrib.mermaid`) for the X3DH handshake and the ratchet step in notebook 01.

### Changed

- **Wire format → v2.** Every message now carries `dh_pub` and `prev_chain_length`. v1 messages are rejected.
- Notebook 05 §1 (DH ratchet) and §3 (skipped-key cache) marked ✅ added in v0.2; summary table updated.
- Notebook 06 comparison table — `Continuous rekey` row reflects symmetric + DH; pq-messenger ↔ Signal pairwise observation rewritten (no cryptographic-core gap).

## [0.1.0] — 2026-04-22

### Added

- Hybrid X25519 + ML-KEM-768 X3DH handshake (`pqmsg.session.initiate_session` / `accept_session`).
- Symmetric ratchet per direction with ChaCha20-Poly1305 AEAD.
- Local file-queue transport (`pqmsg.transport`), CLI (`pqmsg`), Click-based commands (`init`, `send`, `recv`, `export-contact`, `import-contact`, `show-keys`, `show-identity`, `reset`).
- Jupyter Book — four-chapter walk-through (`01_protocol_overview` … `04_full_session`).
- Korean translation served at `/ko/`; cross-linked to companion book *ML-KEM from Scratch*.
- New chapters 05 (omitted gaps), 06 (comparison with Signal/PQ3/WireGuard/MLS), 07 (CLI + Sphinx-autodoc API reference).
- GitHub Pages deploy workflow building both languages.
- MIT `LICENSE`.

[0.2.0]: https://github.com/hulryung/pq-messenger/releases/tag/v0.2.0
[0.1.0]: https://github.com/hulryung/pq-messenger/releases/tag/v0.1.0
