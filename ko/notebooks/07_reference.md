# 노트북 07 — 레퍼런스

CLI 명령과 파이썬 API 표면을 한 곳에 모아둡니다.

## CLI 명령

모든 명령은 `PQMSG_HOME` 환경 변수를 따릅니다(기본값: `~/.pq-messenger/`). 해당 디렉터리 아래에 기록되는 상태: `identity.json`, `contacts/<alias>.json`, `sessions/<peer>.json`, `inbox/<recipient>/<uuid>.json`.

| 명령              | 목적                                                              |
| ----------------- | ----------------------------------------------------------------- |
| `init`            | 새로운 Ed25519 + X25519 + ML-KEM-768 신원 생성.                   |
| `show-identity`   | 활성 신원의 공개 컴포넌트만 출력.                                 |
| `export-contact`  | 외부 채널 공유용 공개 전용 컨택트 파일 작성.                      |
| `import-contact`  | 상대방 컨택트 파일을 로컬 alias로 임포트.                         |
| `send`            | 메시지를 암호화하여 수신자의 inbox에 큐잉.                        |
| `recv`            | 우리에게 도착한 가장 오래된 메시지를 디큐 후 복호화.              |
| `show-keys`       | 디버그: 특정 피어 세션의 현재 래칫 상태 출력.                     |
| `reset`           | `~/.pq-messenger/` 삭제 (모든 신원/컨택트/상태).                  |

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

## 파이썬 API

라이브러리 전체가 한 화면에 들어올 만큼 작습니다. 패키지 루트에서의 재노출은 없으니 서브모듈에서 직접 import 하세요.

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

## 디스크 와이어 포맷

큐에 저장되는 모든 메시지는 단일 JSON 파일입니다:

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

세션의 첫 메시지에만 `kem_ciphertext`와 `ephemeral_pk`가 포함됩니다; 이후 메시지에서는 생략됩니다. 근거는 [노트북 01 §와이어 포맷](01_protocol_overview.ipynb) 참조.
