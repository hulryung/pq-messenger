# pq-messenger

A Signal-style post-quantum messenger CLI, built as an educational capstone for the [ML-KEM from Scratch](https://github.com/hulryung/ml-kem-notebooks) book.

## Educational only

This uses the pure-Python `pqc_edu` ML-KEM implementation (not constant-time, not KAT-validated), only the symmetric half of Signal's Double Ratchet, TOFU-only authentication, and a local-file transport. **Do not use for real messaging.**

## Read online

Jupyter Book (protocol walk-through): https://hulryung.github.io/pq-messenger/

## Setup

    # Clone both repos as siblings:
    git clone https://github.com/hulryung/ml-kem-notebooks
    git clone https://github.com/hulryung/pq-messenger
    cd pq-messenger
    python -m venv .venv && source .venv/bin/activate
    pip install -e ../ml-kem-notebooks   # installs pqc-edu
    pip install -e ".[dev]"

## Two-terminal demo

    # Terminal A
    pqmsg init --name alice
    pqmsg export-contact --output /tmp/alice.pub

    # Terminal B
    pqmsg init --name bob
    pqmsg import-contact /tmp/alice.pub --as alice
    pqmsg export-contact --output /tmp/bob.pub
    pqmsg send alice "Hi from Bob, post-quantum greetings"

    # Back to Terminal A
    pqmsg import-contact /tmp/bob.pub --as bob
    pqmsg recv

## Testing

    pytest tests/ -v
