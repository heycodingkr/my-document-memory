# QUE: 게시 검수 큐

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM 큐의 lease·fencing·백프레셔·예산 대기 원칙을 게시 검수에 적응했다. WAM의 기여자·기기 우선순위, PostgreSQL batch·curator 세부는 제외한다.
영역 / 테스트 ID 접두사: `QUE` (케이스: [`../test/functional-models.md`](../test/functional-models.md))
기반: [`gatekeeper.md`](gatekeeper.md), [`model.md`](model.md), [`provider-outage.md`](provider-outage.md), [`privacy.md`](privacy.md), [`sharing.md`](sharing.md)

## 1. 목적

소유자가 공개 게시를 요청한 메모리 버전을 잃지 않고 비동기 검수한다. 큐 접수와 게시 요청은 분리하며, 검수 완료 전에는 공개 카탈로그에 나타나지 않는다.

## 2. 상태와 전이

| 상태 | 의미 |
|---|---|
| `queued` | 접수됐고 lease 대기 중. 모델 예산·provider 게이트가 닫혀도 이 상태를 유지한다. |
| `leased` | worker가 만료 시각과 fencing token을 받아 검수 중이다. |
| `approved` | Gatekeeper 판정 승인. 이 상태만으로 공개 게시가 완료된 것은 아니다. |
| `rejected` | 고정 reason으로 검수 거절. 제한된 진단 payload는 7일 보관 후 삭제한다. |
| `escalated` | 정책 예외 또는 불확실성으로 사람 검토가 필요하다. |
| `cancelled` | 소유자가 게시 요청을 취소하거나 공개를 철회했다. |

새 요청은 `queued`로 시작한다. 유효 lease의 결과만 `approved`, `rejected`, `escalated` 중 하나로 끝난다. `queued` 또는 `leased` 요청은 소유자가 게시를 취소·철회하면 `cancelled`가 된다. terminal 상태에서 새 검수는 새 요청으로 시작한다.

## 3. 접수, 용량, 중복

검수 큐의 멱등 키는 `(memory_id, version)`이다. 같은 버전에 대한 재요청은 기존 요청 식별자와 상태를 반환하며 중복 job이나 모델 호출을 만들지 않는다. 다른 버전은 별도 요청이다.

큐 깊이는 설정된 전체 및 소유자별 용량 한도를 넘지 않는다. 용량이 가득 차면 새 요청만 429 또는 503으로 거부하고 `Retry-After`를 제공할 수 있다. 이미 접수한 요청을 버려 공간을 만들지 않는다. 임계값은 배포 설정이며 기본 숫자는 미정이다.

## 4. Lease와 fencing

Worker는 `queued` 항목을 원자적으로 claim하고 `lease_owner`, 만료 시각, 단조 증가 generation을 발급한다. heartbeat는 만료를 연장할 수 있다. 만료 후 재claim에는 더 큰 generation을 발급한다. 결정 저장과 게시 반영은 현재 owner·generation 및 최신 소유자 동의를 한 트랜잭션에서 다시 확인한다. 오래된 worker의 결과는 거부하고 게시·귀속 효과를 만들지 않는다.

모델 호출 중 DB 트랜잭션을 열어 두지 않는다. worker 중단은 항목을 유실시키지 않으며 lease 만료 후 재처리한다. 재처리와 같은 버전의 중복 접수는 중복 게시를 만들지 않는다.

## 5. 예산, 취소, 보관

모델 예산 게이트가 닫혔을 때 worker는 새 요청을 lease하지 않는다. 접수된 요청은 `queued`로 남고 비용이 들지 않는다([모델 예산](model.md), [provider 장애](provider-outage.md)). 게이트가 열리면 오래 기다린 요청부터 다시 처리한다. 예산 대기는 검수 실패나 거절로 세지 않는다.

게시 취소·unpublish는 PRIV-04 동의 철회 경계를 따른다. 대기 요청은 즉시 `cancelled` 처리하고 payload를 지운다. 이미 lease된 결과는 commit 직전에 최신 동의를 확인하며, 취소가 먼저 반영됐으면 공개 상태를 바꾸지 못한다. 승인 결과와 공개 version 반영은 원자적으로 연결한다.

거절된 payload는 [privacy.md §5](privacy.md)의 목적·접근 제한에 따라 최대 7일 보관한 뒤 삭제한다. 큐 상태와 필요한 비식별 감사 근거만 별도 보존 기간을 적용한다.

## 6. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-QUE-01 | 요청 접수·멱등 | 동일 `(memory_id, version)` 재접수는 같은 요청을 반환하고 job·호출은 하나다. | QUE-01 |
| F-QUE-02 | 상태 전이 | 허용된 여섯 상태만 관찰되고 lease 결과만 검수 결정을 만든다. | QUE-02 |
| F-QUE-03 | lease fencing | 만료 후 새 generation이 발급되며 이전 worker의 늦은 commit은 거부된다. | QUE-03 |
| F-QUE-04 | 백프레셔 | 용량 초과 새 접수는 명시적으로 거절되고 기존 접수 항목은 보존된다. | QUE-04 |
| F-QUE-05 | 예산 대기 | 예산 게이트가 닫힌 동안 요청은 queued로 남고 모델 호출 수는 늘지 않는다. | QUE-05 |
| F-QUE-06 | 소유자 취소·철회 | 취소된 대기·lease 요청은 공개 효과를 만들지 않고 payload 정책을 지킨다. | QUE-06 |
| F-QUE-07 | 거절 보관 | 거절 진단 payload는 7일 이후 삭제되고 그 전에는 접근 제한을 받는다. | QUE-07 |
| F-QUE-08 | 승인과 게시 원자성 | 승인 결정만으로 공개되지 않고 최신 동의 확인 뒤에만 해당 version이 노출된다. | QUE-08 |
