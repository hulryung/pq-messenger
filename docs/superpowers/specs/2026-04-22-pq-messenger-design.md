# pq-messenger — Post-Quantum Messenger Capstone Design

- **작성일**: 2026-04-22
- **작성자**: dkkang
- **상태**: Draft (사용자 승인됨)
- **맥락**: 기존 ML-KEM 책 (Parts 1–5, 19 notebooks 완료)의 **원 3대 탑3 계획** 중 마지막 조각. Signal-스타일 PQ 메신저를 사이블링 저장소로 구축.
- **사이블링 저장소**: `pq-messenger` (신규 GitHub repo, `hulryung/pq-messenger`)

## 1. 목적

`pqc_edu` 패키지에서 만든 ML-KEM을 **실제 프로토콜**에서 써 본다. Signal의 X3DH + Symmetric Ratchet을 축소 재현해, 두 터미널에서 E2E 암호화 메시지를 주고받는 CLI 도구를 만든다. 교육용·포트폴리오용.

**학습 성공 기준**: 독자가 "KEM만으론 안전한 메신저가 안 되는 이유"(forward secrecy, 반복 사용)를 이해하고, symmetric ratchet이 과거 메시지를 어떻게 보호하는지 키 탈취 시뮬레이션으로 직접 본다.

## 2. 스코프

### In-Scope

- CLI 도구 `pqmsg` (Python + click)
- 장기 identity 키 쌍 (X25519 signing/KEM + ML-KEM)
- 하이브리드 X3DH 간소화 구현 (X25519 + ML-KEM-768)
- Symmetric message ratchet (HKDF-SHAKE256 기반 chain key)
- 로컬 파일 큐 전송 (`~/.pq-messenger/inbox/<recipient>/`)
- 4개 노트북으로 프로토콜 원리 설명
- Jupyter Book + GitHub Pages 배포
- 영어 먼저, 한글은 추후

### Non-Goals

- ❌ 중앙 서버 / 실 네트워크 소켓
- ❌ **Full** Double Ratchet (DH ratchet 포함) — Symmetric만
- ❌ Prekey bundles / one-time prekeys
- ❌ 멀티 디바이스 / 그룹 채팅
- ❌ Authentication beyond TOFU (trust-on-first-use)
- ❌ Metadata privacy / Deniability
- ❌ 사이드채널 방어 / 상수 시간 연산
- ❌ iOS/Android/Web UI
- ❌ 한글 번역 (Part 1 마일스톤)

## 3. 의사결정 요약

| 항목 | 결정 | 근거 |
|------|------|------|
| 저장소 형태 | 사이블링 (`pq-messenger` 별도 repo) | 관심사 분리, 책과 독립 배포 |
| KEM 소스 | `pqc_edu.ml_kem` (책 재활용) | 학습 연속성; 프로덕션 금지 경고 명시 |
| 프로토콜 | X3DH 간소화 + Symmetric Ratchet | Full Double Ratchet은 과도. Symmetric만도 forward secrecy 시연 충분 |
| 하이브리드 | X25519 + ML-KEM-768 | TLS 1.3 hybrid 패턴, 책 nb08 재활용 |
| 전송 | 로컬 파일 큐 | 한 머신 두 터미널로 충분. 서버/소켓 복잡도 회피 |
| 언어 | Python | `pqc_edu` 바로 import, 책과 일관 |
| 노트북 수 | 4 | 캡스톤 범위 |
| 배포 | Jupyter Book + GH Pages | 책과 동일 패턴 |

## 4. 프로젝트 구조

```
pq-messenger/                          # 신규 GitHub repo
├── README.md                          # 사용법 + 프로덕션 금지 경고
├── pyproject.toml                     # 의존성: numpy, cryptography, click, pqc-edu(로컬)
├── pqmsg/                             # CLI 패키지
│   ├── __init__.py
│   ├── identity.py                    # 장기 키 쌍 생성·저장
│   ├── session.py                     # X3DH 합의 + ratchet 상태
│   ├── transport.py                   # 파일 큐 송수신
│   ├── kdf.py                         # HKDF-SHAKE256
│   ├── encoding.py                    # 메시지 직렬화
│   └── cli.py                         # click 커맨드
├── notebooks/
│   ├── 01_protocol_overview.ipynb
│   ├── 02_key_agreement.ipynb
│   ├── 03_ratcheting.ipynb
│   └── 04_full_session.ipynb
├── tests/
│   ├── test_identity.py
│   ├── test_session.py
│   ├── test_transport.py
│   └── test_kdf.py
├── docs/superpowers/
│   ├── specs/2026-04-22-design.md     # (이 문서 복사본)
│   └── plans/2026-04-22-plan.md
├── intro.md
├── _config.yml
├── _toc.yml
└── .github/workflows/book.yml
```

### 원칙

- `pqc-edu`는 `pip install -e ../ml-kem-notebooks` 형태 로컬 설치 (또는 PyPI 발행 시 직접 의존성)
- CLI는 각 단계가 독립 모듈 — `cli.py`는 얇은 dispatcher, 로직은 `identity`/`session`/`transport`에
- 파일 큐: JSON line 하나가 하나의 메시지. 원자적 rename으로 race condition 회피
- 모든 상태는 `~/.pq-messenger/` 아래 (identity, contacts, sessions, inbox)

## 5. 프로토콜 설계

### 5.1 Identity (장기)

각 사용자는 세 개의 키 쌍:
- `ik_sign` (X25519 → Ed25519 서명) — 향후 인증용 (이번 스코프에선 미사용, 자리만 확보)
- `ik_dh` (X25519) — X3DH 합의의 고전 반쪽
- `ek` / `dk` (ML-KEM-768) — X3DH 합의의 PQ 반쪽

공개키 세 개 + 이름을 JSON으로 `.pub` 파일로 export.

### 5.2 Hybrid X3DH (간소화)

Alice가 Bob에게 첫 메시지 보내기:

1. Alice는 Bob의 `ik_dh_B`, `ek_B`를 가짐 (import-contact 명령)
2. Alice 생성: ephemeral X25519 `eph_A`, 랜덤 32-byte `m`
3. Alice 실행:
   - `dh_shared = X25519(eph_A_sk, ik_dh_B)`
   - `(kem_shared, kem_ct) = ML-KEM.Encaps(ek_B)`
4. `SK = HKDF-SHAKE256(salt=\"pqmsg-x3dh-v1\", ikm=dh_shared || kem_shared, info=ik_A_pub || ik_B_pub || eph_A_pub, L=64)` → 32B root_key + 32B chain_key
5. Alice는 메시지 포함 ciphertext 전송: `{eph_A_pub, kem_ct, header, body_ciphertext}`
6. Bob은 inbox에서 메시지 수신 후:
   - `dh_shared = X25519(ik_dh_B_sk, eph_A_pub)`
   - `kem_shared = ML-KEM.Decaps(dk_B, kem_ct)`
   - 동일한 KDF로 `SK` 유도 → 동일한 root/chain key
7. 세션 상태 저장 (root_key, chain_key, counter)

### 5.3 Symmetric Ratchet

메시지 i를 보낼 때:
```
message_key_i = HKDF(chain_key, info=b"msg_key", L=32)
new_chain_key = HKDF(chain_key, info=b"chain_advance", L=32)
chain_key := new_chain_key
```

각 `message_key`는 1회용. ChaCha20-Poly1305로 body 암호화. 수신 측도 동일 체인 전진.

**Forward secrecy**: chain_key가 탈취되어도 **과거** message_key는 복원 불가 (HKDF one-way).

**Non-goal (DH ratchet)**: 체인 키가 탈취되면 **미래** 메시지는 노출됨. Full Double Ratchet은 주기적 DH 재협상으로 이를 방어 — 본 스코프 밖.

### 5.4 Message Format

```json
{
  "version": 1,
  "sender": "alice",
  "recipient": "bob",
  "msg_index": 3,
  "kem_ciphertext": "base64...",      // X3DH 첫 메시지에만; 이후엔 null
  "ephemeral_pk": "base64...",         // X3DH 첫 메시지에만
  "nonce": "base64...12B",             // ChaCha20 nonce
  "ciphertext": "base64...",           // body + Poly1305 tag
  "sent_at": "2026-04-22T15:30:00Z"
}
```

원자적 쓰기: `inbox/<recipient>/<id>.json.tmp` → rename `<id>.json`.

## 6. 학습 흐름 (노트북)

| # | 노트북 | 핵심 질문 | 주요 산출 |
|---|--------|-----------|-----------|
| 01 | protocol_overview | 왜 KEM만으론 안전한 메신저가 안 되나? | 위협 모델 (active attacker, key compromise), X3DH·ratchet 다이어그램, Signal PQXDH 배경 |
| 02 | key_agreement | 하이브리드 X3DH는 어떻게 동작? | X25519 + ML-KEM-768 결합 실행, KDF 체인 시연, wire format |
| 03 | ratcheting | Forward secrecy를 눈으로 | 체인 키 10단계 전진, 키 탈취 시점 시뮬레이션, 과거는 복원 불가 / 미래는 노출 시연 |
| 04 | full_session | 실제 CLI로 | subprocess로 Alice/Bob 별개 세션, 파일 큐 5회 왕복, 로그 캡처 |

## 7. CLI 명세

```
pqmsg init --name NAME
pqmsg show-identity
pqmsg export-contact [--output PATH]
pqmsg import-contact PATH --as NAME
pqmsg send RECIPIENT "message body"
pqmsg recv [RECIPIENT] [--all]
pqmsg show-keys RECIPIENT     # debug: 현재 chain_key, counter
pqmsg reset                   # ~/.pq-messenger/ 지움
```

기본 디렉터리: `$PQMSG_HOME` 또는 `~/.pq-messenger/`.

## 8. 테스트 전략

### Level 1 — 단위 테스트 (pytest)

| 파일 | 검증 |
|------|------|
| `test_kdf.py` | HKDF-SHAKE256 test vector, info/salt 분리 |
| `test_identity.py` | keypair 생성·저장·로드 왕복 |
| `test_session.py` | X3DH 양쪽 같은 SK 유도, 10단계 symmetric ratchet chain key 일치 |
| `test_transport.py` | 원자적 파일 쓰기, 동시 쓰기 race, 손상된 JSON 무시 |

### Level 2 — 통합 테스트

- Python `subprocess`로 두 프로세스 스폰 → Alice↔Bob 5회 왕복 → 양쪽 평문 일치
- 노트북 04가 이 흐름을 그대로 수행

### Level 3 — 공격 시뮬레이션 (노트북 03)

- 3번째 메시지 이후 Alice의 chain_key 탈취 가정
- 과거 메시지 1, 2 복호 시도 → 실패 (HKDF 역산 불가)
- 미래 메시지 4, 5 복호 시도 → 성공 (Symmetric ratchet 한계)
- 결론: "Full Double Ratchet이 필요한 이유"

## 9. 리스크 & 완화

| 리스크 | 완화 |
|--------|------|
| `pqc-edu` 로컬 경로 의존성 설치 불편 | `pyproject.toml`의 `[tool.setuptools.find]`로 `../ml-kem-notebooks` 경로 자동 탐색, README에 단계별 설치 명시 |
| 파일 큐 race condition | 원자적 rename + fcntl 파일 락 (선택). 테스트로 검증 |
| X3DH 첫 메시지 재전송 공격 | msg_index + ephemeral_pk 중복 검출. out-of-scope이나 nice-to-have |
| Symmetric ratchet만이라 future secrecy 없음 | README·노트북 03에서 명시. 책의 "hybrid with X25519"와 같은 정직성 |
| 한 머신 두 터미널이 어색한 사용자 경험 | README에 `tmux`/split-pane 가이드 + 노트북 04의 subprocess 데모 |

## 10. 성공 기준

1. `pip install -e "."` 후 `pytest` 전체 통과
2. 두 터미널에서 Alice↔Bob **5회 연속 왕복** 성공 (평문 일치)
3. 4 노트북 `nbconvert --execute` 통과
4. Jupyter Book 빌드 + GitHub Pages (EN) 배포 완료
5. 키 탈취 시뮬레이션: 과거 복원 불가 / 미래 복원 가능 실증
6. **학습 성공**: 독자가 "왜 Signal은 Double Ratchet을 쓰는가, Symmetric만으론 뭐가 부족한가"를 한 문단 설명 가능

## 11. 다음 단계

본 설계 승인 후 `writing-plans` 스킬로 태스크별 구현 계획서 작성.

마일스톤:
1. Repo scaffold + identity + KDF (Tasks 0–3)
2. X3DH + Symmetric ratchet + transport (Tasks 4–6)
3. CLI + integration (Tasks 7–8)
4. Notebooks 01–04 (Tasks 9–12)
5. Jupyter Book + Pages 배포 (Task 13)
6. (Optional) 한글 번역 및 ko/ 확장 (이번 스코프 밖)
