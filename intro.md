# pq-messenger

A Signal-style post-quantum messenger CLI, built as the capstone project for [ML-KEM from Scratch](https://hulryung.github.io/ml-kem-notebooks/). Alice and Bob exchange end-to-end encrypted messages over a local file queue, using a hybrid X25519 + ML-KEM-768 key agreement and a symmetric ratchet per direction.

> 🌐 English · <a href="ko/">한국어</a>

```{warning}
Educational only — uses the pure-Python `pqc_edu` ML-KEM implementation, omits the DH half of Signal's Double Ratchet, and has no authentication beyond TOFU. **Do not use for real messaging.**
```

## What you'll learn

- Why KEM alone is not enough for a messenger: the role of a symmetric ratchet
- Hybrid X3DH with a post-quantum half (forward-secret against both Shor and classical attacks)
- Forward secrecy — and where symmetric-only ratcheting breaks (key compromise → future messages exposed)
- How a minimal end-to-end session looks when you can see every byte

## Four chapters

1. **Protocol overview** — threat model, hybrid X3DH, ratchet, wire format
2. **Key agreement** — walk through `initiate_session` and `accept_session` with real keys
3. **Ratcheting** — 10-step symmetric chain; compromise simulation at step 5
4. **Full session** — two OS processes, five roundtrip messages over a shared file queue

## Prerequisites

This book assumes you've worked through (or are happy to skim) the ML-KEM internals from the companion book:

- [**ML-KEM spec**](https://hulryung.github.io/ml-kem-notebooks/notebooks/06_ml_kem_spec.html) — what `Encaps`/`Decaps` actually compute
- [**Hybrid KEM**](https://hulryung.github.io/ml-kem-notebooks/notebooks/08_hybrid_kem.html) — why we combine X25519 with ML-KEM-768
- [**Wrap-up**](https://hulryung.github.io/ml-kem-notebooks/notebooks/09_wrap_up.html) — gaps vs. production (we inherit them all)

The whole companion book: [ML-KEM from Scratch](https://hulryung.github.io/ml-kem-notebooks/).

## Source

[github.com/hulryung/pq-messenger](https://github.com/hulryung/pq-messenger)
