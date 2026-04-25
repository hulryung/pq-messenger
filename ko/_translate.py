"""One-shot translator: replace markdown cell sources with KO equivalents."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "notebooks"
DST = ROOT / "ko" / "notebooks"

# Map (notebook_filename, cell_id) -> translated markdown source (list of lines)
TRANSLATIONS: dict[tuple[str, str], list[str]] = {}


def add(nb: str, cell_id: str, text: str) -> None:
    lines = text.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            out.append(line + "\n")
        else:
            if line:
                out.append(line)
    TRANSLATIONS[(nb, cell_id)] = out


# ====== 02_key_agreement ======
add("02_key_agreement.ipynb", "33670ea6", """# 노트북 02 — 하이브리드 X3DH 키 합의

새로 생성한 두 신원(identity) 사이에서 하이브리드 핸드셰이크를 실행하고, 양쪽이 동일한 96바이트의 키 자료를 유도하는지 확인합니다.""")

add("02_key_agreement.ipynb", "6d4d44a6", """## 단계 1 — 신원 생성""")

add("02_key_agreement.ipynb", "5fda9b8a", """## 단계 2 — Alice가 세션 개시

`initiate_session`은 X25519 DH, ML-KEM 캡슐화, 그리고 HKDF 유도를 수행합니다.""")

add("02_key_agreement.ipynb", "75ec6d5a", """## 단계 3 — Bob이 세션 수락

`accept_session`은 Bob의 개인키와 Alice가 보낸 핸드셰이크 필드를 사용합니다.""")

add("02_key_agreement.ipynb", "e16cd574", """## 두 줄 모두가 성공해야 하는 이유

두 체인 키는 **방향성**을 가집니다: 하나는 Alice→Bob용, 다른 하나는 Bob→Alice용입니다. 이 핸드셰이크 이후, 양 당사자는 독립적으로 암호화하고 상대방은 복호화할 수 있습니다. 다음 노트북에서는 대칭 래칫을 10단계 굴려서 전방 비밀성을 보여주고 — 어디에서 멈추는지도 함께 살펴봅니다.""")

# ====== 03_ratcheting ======
add("03_ratcheting.ipynb", "8c519eb5", """# 노트북 03 — 래칫팅과 키 노출

대칭 래칫을 10개의 메시지 동안 굴려보고, 5단계에서 키 노출을 시뮬레이션하여 무엇이 안전하고 무엇이 그렇지 않은지 확인합니다.""")

add("03_ratcheting.ipynb", "167b4937", """## 단계 1 — 체인이 전진하는 모습 관찰""")

add("03_ratcheting.ipynb", "d72f1f3a", """## 단계 2 — 5단계에서 노출 시뮬레이션

공격자가 5단계 시점(메시지 4가 전송된 후)의 `chain_key`를 훔쳤다고 가정합니다.""")

add("03_ratcheting.ipynb", "44535727", """## 단계 3 — 공격자가 과거 메시지를 복호화할 수 있을까?

훔친 chain_key로부터 공격자는 메시지 키 0..4를 유도하려고 시도합니다.""")

add("03_ratcheting.ipynb", "c8c257f9", """## 핵심 정리

1. **전방 비밀성은 유지됩니다**: 노출 이전의 메시지는 HKDF가 단방향이기 때문에 기밀이 유지됩니다.
2. **후방 비밀성은 깨집니다**: 노출 시점 이후의 모든 메시지는 읽을 수 있게 됩니다.

**완전한 Double Ratchet**은 몇 메시지마다 DH 단계를 추가합니다 — 새로운 X25519/ML-KEM 교환이 공격자가 보지 못한 엔트로피로 체인 키를 갱신합니다. 이것이 후방 비밀성 공백을 메웁니다. 여기서는 그 한계를 명확하게 드러내기 위해 의도적으로 생략했습니다. 실제 메신저(Signal, iMessage PQ3)에서는 항상 완전한 래칫을 사용해야 합니다.""")

# ====== 04_full_session ======
add("04_full_session.ipynb", "cfd1a0af", """# 노트북 04 — CLI를 통한 Alice↔Bob 전체 세션

inbox 디렉터리를 공유하는 두 개의 실제 CLI 프로세스를 띄우고, 5번의 왕복 메시지를 관찰합니다.""")

add("04_full_session.ipynb", "cd5a6ff3", """## 각 \"ALICE\" 줄은 Alice→Bob 체인 키를 전진시키고, 각 \"BOB\" 줄은 Bob의 Alice→Bob 수신 체인을 전진시킵니다. 양쪽이 동기화된 상태로 유지됩니다.""")

add("04_full_session.ipynb", "0c4c0c05", """## 방금 본 것

- 각각 자체 `~/.pq-messenger` 디렉터리를 가진 두 개의 독립적인 OS 프로세스.
- 공유 파일 큐 \"네트워크\".
- 단일 하이브리드 X3DH 핸드셰이크를 앞에 두고, 5번의 암호화/복호화 왕복.
- 단조 증가하는 송신/수신 인덱스 — 동작 중인 대칭 래칫.

실제 배포에서는 완전한 Double Ratchet(DH 재키잉), 적절한 상호 인증(서명 + 발행된 prekey), 그리고 오프라인 전송을 위한 서버를 원할 것입니다. 이는 *다음 단계*의 복잡성으로, 의도적으로 독자에게 남겨두었습니다.""")


def translate_notebook(name: str) -> None:
    src = SRC / name
    dst = DST / name
    nb = json.loads(src.read_text())
    for cell in nb["cells"]:
        if cell["cell_type"] == "markdown":
            key = (name, cell["id"])
            if key not in TRANSLATIONS:
                raise SystemExit(f"missing translation: {key}")
            cell["source"] = TRANSLATIONS[key]
        elif cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
            cell.pop("metadata", None)
            cell["metadata"] = {}
    dst.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
    print(f"wrote {dst}")


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for name in ["02_key_agreement.ipynb", "03_ratcheting.ipynb", "04_full_session.ipynb"]:
        translate_notebook(name)


if __name__ == "__main__":
    main()
