# OUTAGE: 모델 provider 장애 대기

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM 서버 worker의 분류·시도 없는 대기·대기 게이트·순환을 문서 검수에 적응했다. 수치는 WAM 승계(재확인 필요)이며 여러 worker 동시 탐침은 상한이 worker 수다.
영역 / 테스트 ID 접두사: `OUTAGE` (케이스: [`../test/functional-models.md`](../test/functional-models.md))
기반: [`model.md`](model.md), [`queue.md`](queue.md), [`gatekeeper.md`](gatekeeper.md), [실패 행렬](../test/failure-matrix.md)

## 1. 목적과 분류

provider 오류를 검토 요청의 결함과 분리한다. 재시도 가능한 장애와 고쳐야 하는 설정 거부 동안 요청은 `queued`로 남고 공개되지 않는다. 분류는 adapter가 provider 중립 범주로 정규화하며 응답 본문·키는 상태나 오류에 옮기지 않는다.

| 신호 | 분류 | 큐 동작 |
|---|---|---|
| 크레딧·쿼터 소진 신호(상태 코드보다 우선) | `credit_exhausted` | [model.md §2](model.md)의 일일 예산 게이트에서 시도 없이 대기 |
| HTTP 429(소진 아님), 408, 5xx, 연결 실패, timeout, 응답 본문 중단 | `transient` | `provider_outage` 게이트에서 시도 없이 대기 |
| 401, 403, 404(소진 아님) | `configuration_rejected` | `provider_rejected` 게이트에서 더 길게 시도 없이 대기 |
| 그 밖의 4xx, schema 불일치·잘못된 2xx 응답 | `permanent` | 보통 재시도 한도 적용; 한도 소진 시 `escalated` |

소진 신호가 429와 함께 있으면 `credit_exhausted`가 우선이다. `Retry-After`는 숫자 초 또는 HTTP 날짜로 읽고, 없거나 잘못되면 없는 것으로 본다. 401·403·404 본문은 분류를 바꾸는 데 쓰지 않는다.

## 2. 대기와 게이트

일시 장애가 난 worker는 현재 lease와 fencing token을 확인하고 대기 횟수 및 시도를 원자적으로 되돌린다. 요청은 `queued`에 남고 gate가 닫힌 동안 worker는 요청을 claim하거나 모델을 호출하지 않는다. gate가 열릴 때 각 worker는 최대 한 요청을 탐침하며, 동시에 실행 중인 worker가 있을 때 탐침 수는 worker 수를 넘지 않는다. 요청은 대기 횟수가 적은 순서, 동률이면 접수 시각과 요청 ID 순으로 고른다.

일시 장애 gate는 `max(Retry-After, backoff)`만큼 닫고 최소 30초를 둔다. backoff는 30초부터 연속 장애마다 두 배로 늘어 10분에서 멈춘다. provider 힌트는 최대 1시간으로 제한한다. 알려진 더 늦은 재개 시각을 뒤로 당기지 않는다.

401·403·404 설정 거부도 시도를 쓰지 않고 같은 내구성 gate를 닫되, pause는 1시간부터 연속 거부마다 두 배로 늘어 최대 6시간이다. 거부 pause는 장애보다 길며 사람이 설정·권한을 고쳐야 회복한다. 운영 상태는 고정 분류, 마지막 안전 오류 범주, 재개 시각과 필요한 설정 점검 항목을 알려 준다. key·model·endpoint 값 자체는 숨긴다.

한 job이 무한 대기로 큐를 독점하지 않도록 transient와 설정 거부를 합쳐 job마다 시도 없는 대기를 최대 8회 허용한다. 그 뒤 같은 분류가 반복되면 일반 시도 1회를 소비한다. 일반 실패는 최대 5회까지 재시도하며 소진 시 `escalated`되어 사람 검토를 기다린다. 이 한도는 모델 호출 시도만 세며 credit exhaustion은 별도 예산 대기다. 취소된 요청은 다시 순환하지 않는다.

## 3. 회복, 개인정보와 공개 경계

gate와 job별 대기 횟수는 worker 재시작 뒤에도 유지한다. 성공적으로 응답한 탐침은 해당 연속 장애·거부 횟수를 초기화하고 gate를 열며, 미완료 응답은 성공으로 취급하지 않는다. 설정을 고친 뒤 운영자는 대기 시간을 기다리거나 명시적으로 gate를 열 수 있다. gate가 열릴 때 대기 job은 다시 접수 순서에 따른 순환으로 처리한다.

provider 실패 동안 검수 결정, 카탈로그, 점수, 게시 상태는 변하지 않는다. 승인 후보를 받지 못했거나 검증하지 못한 버전은 공개하지 않는다(FAIL-22). provider 응답 본문·header·key·원문 문서는 error, event, queue status와 operator notice에서 제외한다. owner가 게시를 철회하면 대기 항목은 [PRIV-04](privacy.md)의 경계에 따라 `cancelled` 처리되고 payload를 삭제한다.

## 4. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-OUTAGE-01 | 오류 분류 우선순위 | quota 신호가 429보다 먼저 분류되고, transient·401/403/404·영구 오류가 표와 일치한다. | OUTAGE-01 |
| F-OUTAGE-02 | transient 시도 없는 대기 | 합성 503 및 연결 timeout 뒤 시도 수는 유지되고 gate 동안 추가 요청 0건이다. | OUTAGE-02 |
| F-OUTAGE-03 | 설정 거부 대기 | 401·403·404는 키·본문을 노출하지 않고 긴 재개 시각으로 대기한다. | OUTAGE-03 |
| F-OUTAGE-04 | retry 제한과 순환 | 2개 요청을 섞어 장애를 반복하면 낮은 대기 횟수가 먼저 탐침하고 한도 뒤에만 일반 시도를 소비한다. | OUTAGE-04 |
| F-OUTAGE-05 | 회복·재시작·철회 | 닫힌 gate는 재시작 후 유지되고 복구 후 초기화되며 철회 요청은 다시 호출되지 않는다. | OUTAGE-05 |
| F-OUTAGE-06 | fail-closed·비밀 비노출 | 장애 동안 공개 검색 결과 0건이고 오류·상태·로그에서 fixture body와 key가 0건이다. | OUTAGE-06 |

전송 장애를 되풀이하거나 provider가 설정을 거부해도 게시 상태는 바뀌지 않는다. WAM의 실제 provider 응답 모양은 재현하지 않았으므로 adapter 계약 fixture로만 검증하며 제품에 대한 검증 사실로 표시하지 않는다.
