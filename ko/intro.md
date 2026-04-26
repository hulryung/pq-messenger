# pq-messenger (한국어)

[ML-KEM from Scratch (한국어)](https://pqc.hulryung.com/ko/)의 캡스톤 프로젝트로 만든, Signal 스타일의 포스트 양자 메신저 CLI입니다. Alice와 Bob은 로컬 파일 큐를 통해 종단 간 암호화된 메시지를 주고받으며, X25519 + ML-KEM-768 하이브리드 키 합의와 방향별 대칭 래칫(symmetric ratchet)을 사용합니다.

> 🌐 <a href="../">English version</a> · 한국어 · **v1.0** · <a href="https://github.com/hulryung/pq-messenger/blob/main/CHANGELOG.md">Changelog</a>

```{warning}
교육용으로만 사용하세요 — 순수 파이썬 `pqc_edu` ML-KEM 구현을 사용하고, Signal Double Ratchet의 DH 절반을 생략했으며, TOFU 외에는 인증이 없습니다. **실제 메시징에는 절대 사용하지 마세요.**
```

## 무엇을 배우게 되나요

- KEM만으로는 메신저를 만들 수 없는 이유: 대칭 래칫의 역할
- 포스트 양자 절반이 포함된 하이브리드 X3DH (Shor와 고전 공격 모두에 대해 전방 비밀성 보장)
- 전방 비밀성(forward secrecy) — 그리고 대칭 전용 래칫이 깨지는 지점 (키 노출 → 이후 메시지 노출)
- 모든 바이트를 직접 볼 수 있는 최소한의 종단 간 세션이 어떻게 보이는지

## 4개의 챕터

1. **프로토콜 개요** — 위협 모델, 하이브리드 X3DH, 래칫, 와이어 포맷
2. **키 합의** — 실제 키로 `initiate_session`과 `accept_session` 따라가기
3. **래칫팅** — 10단계 대칭 체인; 5단계에서 노출 시뮬레이션
4. **전체 세션** — 공유 파일 큐를 통한 두 OS 프로세스, 5번의 왕복 메시지

## 사전 학습

이 책은 자매 도서의 ML-KEM 내부 구조를 이미 학습했거나 훑어볼 수 있다고 가정합니다:

- [**ML-KEM 사양**](https://pqc.hulryung.com/ko/notebooks/06_ml_kem_spec.html) — `Encaps`/`Decaps`가 실제로 무엇을 계산하는지
- [**하이브리드 KEM**](https://pqc.hulryung.com/ko/notebooks/08_hybrid_kem.html) — 왜 X25519와 ML-KEM-768을 결합하는지
- [**마무리**](https://pqc.hulryung.com/ko/notebooks/09_wrap_up.html) — 실제 운영 환경과의 격차 (이 책도 모두 동일하게 상속)

전체 자매 도서: [ML-KEM from Scratch (한국어)](https://pqc.hulryung.com/ko/).

## 소스

[github.com/hulryung/pq-messenger](https://github.com/hulryung/pq-messenger)
