import os
import subprocess
from pathlib import Path


def _run(env_home: Path, args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PQMSG_HOME"] = str(env_home)
    return subprocess.run(
        ["pqmsg"] + args, env=env, capture_output=True, text=True, timeout=60
    )


def test_five_roundtrip_between_two_processes(tmp_path):
    """Full end-to-end: Alice and Bob each have their own HOME but share an inbox
    via symlink. Demonstrates the ratchet across 5 messages from Alice to Bob."""
    alice_home = tmp_path / "alice"
    bob_home = tmp_path / "bob"
    alice_home.mkdir()
    bob_home.mkdir()
    shared_inbox = tmp_path / "shared_inbox"
    shared_inbox.mkdir()
    (alice_home / "inbox").symlink_to(shared_inbox, target_is_directory=True)
    (bob_home / "inbox").symlink_to(shared_inbox, target_is_directory=True)

    def run_alice(*a):
        return _run(alice_home, list(a))

    def run_bob(*a):
        return _run(bob_home, list(a))

    assert run_alice("init", "--name", "alice").returncode == 0
    assert run_bob("init", "--name", "bob").returncode == 0

    alice_pub = tmp_path / "alice.pub"
    bob_pub = tmp_path / "bob.pub"
    assert run_alice("export-contact", "--output", str(alice_pub)).returncode == 0
    assert run_bob("export-contact", "--output", str(bob_pub)).returncode == 0
    assert run_alice("import-contact", str(bob_pub), "--as", "bob").returncode == 0
    assert run_bob("import-contact", str(alice_pub), "--as", "alice").returncode == 0

    for i in range(5):
        msg = f"hello from alice, round {i}"
        r = run_alice("send", "bob", msg)
        assert r.returncode == 0, r.stderr
        r = run_bob("recv")
        assert r.returncode == 0, r.stderr
        assert msg in r.stdout, f"expected '{msg}' in output, got: {r.stdout}"
