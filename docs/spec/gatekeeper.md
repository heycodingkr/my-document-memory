# GK: 공개 게시 검수

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM의 기여 게이트와 browser replay를 명시적 게시 검수 및 StandardDoc/export 검사로 바꿨다. 공개 검수는 runtime-v1 이후 다중 사용자 단계다.
영역 / 테스트 ID 접두사: `GK` (케이스: [`../test/functional-review.md`](../test/functional-review.md))
기반: [`sharing.md`](sharing.md), [`memory.md`](memory.md), [`web-import.md`](web-import.md), [`formats.md`](formats.md), [`privacy.md`](privacy.md)

## 1. 목적

공개 게시 요청에서 동의·안전·사용권·중복·문서 구조를 확인한다. 고정 규칙과 검증 증거가 정상인 경우 agent가 판정하고 공개한다. 모호함, 충돌, 정책 예외는 사람에게 넘기며 검토 중에는 공개하지 않는다.

## 2. 입력과 결과

입력은 소유자, `memory_id`와 불변 `version`, `visibility`, 선택한 어휘 내 `license`, 게시 동의다. 원본 prompt, credentials, 원 URL의 query, 원문 비밀값은 agent 판단 입력이나 audit에 넣지 않는다. 결정 기록은 검수 단계, 정책 버전, 결과 코드, 증거 digest만 남긴다.

판정은 `approve`, `reject(reason)`, `escalate_to_human`이다. 고정 reason enum은 `secret`, `personal_data`, `license`, `duplicate`, `structure`, `injection`, `takedown_match`이다. 거절 응답·감사에는 이 코드와 안전한 요약만 둔다.

## 3. 검수 파이프라인

| 단계 | 계약 |
|---|---|
| R0 접수·동의 | 소유자와 버전을 확인한다. 공유 동의는 게시마다 `consent=true`, 현재 `consent_version=share-v1`이어야 한다. 불충분하면 쓰기·큐잉 없이 `consent_required`. |
| R1 자동 scrub | 게시 직전 다시 검사한다. 비밀값, 남은 개인 정보, L1 주입형 문구는 각각 `secret`, `personal_data`, `injection`으로 거절한다. 숨김·제로폭 텍스트는 제거한 뒤 검증·해시하며, 매크로·외부 관계·DDE·OLE 등 악성 OOXML은 `structure`로 거절한다. |
| R2 사용권 | 라이선스 어휘와 감지 출처를 확인한다. 검출 신호가 user claim보다 우선한다. 제3자 `user_asserted`/ `unverified`, `unknown` 또는 상충하는 `derived_from` 체인은 공개를 막는다. 모든 체인의 attribution·라이선스 조건을 만족해야 한다. takedown fingerprint 일치 시 `takedown_match`. |
| R3 중복 | 공개 버전의 정확한 `content_hash` 일치와 정규화 StandardDoc의 근접 중복을 검사한다. 확정 중복은 `duplicate`; 근접 후보가 모호하면 공개하지 않고 사람에게 올린다. |
| R4 구조 | `stddoc/1` 스키마와 form family를 검증한다. 문서 export `md`, `html`, `docx`를 재가져와 지원 블록 순서·슬롯이 유지되고, HTML에 실행 코드가 없음을 확인한다. deck은 지원되는 `md`·`html`만 확인한다. 실패는 `structure`. |
| R5 판정·게시 | 정상 케이스는 agent가 승인 또는 고정 reason으로 거절한다. 불확실성·상충 증거·정책 예외는 사람에게 escalates. 승인된 버전만 immutable `public`으로 노출한다. |

`visibility=team`은 R0과 자동 R1 scrub만 거친 뒤 바로 팀에 보인다. R2~R5 공개 검수 큐에는 들어가지 않는다. scrub 실패는 같은 고정 reason으로 거절한다. `private` 전환은 검수 없이 즉시 unpublish한다.

## 4. 게시 수명과 안전

게시된 버전의 내용은 바꾸지 않는다. 롤백은 이전 승인 버전을 새 게시 대상으로 지정하고, 되돌린 버전도 보존한다. takedown은 공개 조회에서 즉시 숨기고 fingerprint를 차단 목록에 남겨 같은 내용의 재게시를 거절한다. 복사본은 그대로 남되 takedown 출처의 재게시에는 사용할 수 없다.

## 5. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-GK-01 | 동의·소유자 확인 | share-v1 동의와 소유자/버전이 맞을 때만 접수 | GK-01~02 |
| F-GK-02 | 게시 전 scrub | secret·PII·L1 injection 차단, 숨김 텍스트 제거, OOXML 위험 거절 | GK-03~07 |
| F-GK-03 | 라이선스·출처 확인 | 어휘·claim·derived_from·takedown 규칙 적용 | GK-08~11 |
| F-GK-04 | 공개 중복 방지 | exact hash 거절, 근접 중복은 거절 또는 예외 검토 | GK-12~13 |
| F-GK-05 | 팀 공유 경계 | 자동 scrub만 수행하고 review queue에는 넣지 않음 | GK-14 |
| F-GK-06 | 구조·export 검증 | 유효한 StandardDoc과 안전한 지원 export만 승인 후보 | GK-15~16 |
| F-GK-07 | agent 판정과 복구 | 고정 reason, 사람 예외, immutable publish·rollback·takedown | GK-17~20 |

모든 공개 경로는 fail closed다. 구현과 모델의 실제 판정 품질은 이 설계 명세만으로 검증된 것으로 간주하지 않는다.
