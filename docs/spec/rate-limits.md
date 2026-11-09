# 호출 제한과 남용 제어

상태: runtime-v1 이후 단계 제안. 공개 계정·서버 API의 초기 정책이며 측정된 용량이나 runtime-v1 기능이 아니다. 웹 가져오기 속도·동시성은 [core.md 8절](core.md), 게시 권한은 [sharing.md 3절](sharing.md)을 따른다.
영역 / 테스트 ID 접두사: RL / RL-01~12
기반: WAM `docs/spec/rate-limits.md`와 `docs/test/service-abuse-performance.md`를 DMEM 서버 호출에 적응.

## 1. 적용 원칙

익명 public read, 계정별 한도, 네트워크별 공용 한도를 함께 검사한다. 로그인은 IP 한도를 우회하지 않는다. 비싼 작업 전에 원자적으로 예약하며 거부 요청은 handler, 저장소 쓰기, outcome 반영을 실행하지 않는다. 첫 값은 제안이며 배포 전 부하 측정으로 조정한다.

| 호출 종류 | 초기 한도 제안 | 적용·비용 |
|---|---|---|
| `recall` | 익명 IP 60 units/min, burst 20; 계정 300/60, 공용 IP 600/120 | 요청당 3 units, 결과 최대 3 |
| `search`·공개 목록·vocab | 같은 익명/계정/IP bucket | 요청당 1 unit; 페이지 최대 20 |
| `expand`·미리보기 상세 | 같은 bucket | 요청당 2 units |
| `publish`·copy 등 쓰기 | 계정 300/60 및 공용 IP 600/120 | 요청당 5 units; publish는 계정당 1시간 10건 |
| 웹 `preview` + URL `import` | library당 분당 합계 30회, 동시 4건 | 서버 모드는 user당 계산. 초과 요청은 실행·상태 변경 없이 거부 |
| `outcome` | 계정 300/60 및 공용 IP 600/120 | 요청당 5 units; 유효 receipt와 멱등성 검사 병행 |
| 로그인 이메일 발송 | 이메일당 60초 cooldown, 시간당 최대 5회 | 브라우저/IP 제한도 추가 적용; challenge당 검증 실패 최대 5회 |
| `dmem link` challenge/poll | 계정/IP별 인증 bucket | 시작·승인·poll을 제한하고 별도 status bucket은 보장 |
| status·usage | IP 30/min, burst 10; 인증 계정도 30/min | action bucket과 분리해 제한 상태를 확인 가능 |

가중 token bucket은 지속 refill과 burst를 사용한다. 익명은 공개 읽기만 가능하고 계정 요청은 계정 및 신뢰된 네트워크 bucket 모두를 통과해야 한다. IPv4는 주소별, IPv6는 /64별로 묶는다. `core.md`의 웹 preview/import 30회·동시 4건 및 이 문서의 게시 10건/시간을 함께 적용한다.

## 2. 제한 응답과 복구

- 초과 응답은 HTTP 429, 고정 오류 `rate_limited`, 정수 `retry_after_seconds`, `Retry-After` 헤더를 반환한다. CLI 종료 코드는 [core.md 7절](core.md)의 6이다.
- 여러 한도를 넘긴 경우 해당 호출을 허용할 때까지 가장 긴 대기 시간을 안내한다. 입력 URL, 본문, IP, 계정 ID, bucket key, 현재 소유량은 응답에 넣지 않는다.
- 클라이언트는 서버가 안내한 대기 시간 뒤 사용자가 다시 시도하게 한다. 429 자동 재시도는 하지 않는다. 거부된 요청은 호출 사용량에 포함하지 않는다.
- 동시 처리량 소진이나 limiter 저장소 장애는 quota 초과와 구별한다. 포화는 `503 service_busy`, 공용 limiter 불능은 retry 가능한 `503 server_unavailable`로 닫힘(fail-closed) 처리하고 `Retry-After`를 준다.
- 서버 간 공유 limiter는 원자적이어야 한다. 다중 서버에서 프로세스별 카운터로 대체해 허용량을 늘리지 않는다. 부하 제한과 요청 크기·권한·SSRF 검사는 각각 별도로 유지한다.

## 3. 개인정보와 집계

네트워크 한도 키는 회전 secret으로 정규화 IP(/64 포함)를 HMAC한 값이며 짧은 TTL을 둔다. 원 IP·URL query·요청 본문·자격 증명은 limiter 저장소와 로그에 쓰지 않는다. 계정 bucket은 이메일·handle 대신 내부 account_id를 쓰며 요청별 내역을 보관하지 않는다. 사용량 집계·보관·opt-out은 [usage-analytics.md](usage-analytics.md)를 따른다.

## 4. 요구사항과 추적

| F-RL-nn | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-RL-01 | 익명/계정 요청별 admission | 공유 한도를 먼저 원자 적용하고 초과 작업은 실행하지 않는다. | RL-01, RL-02 |
| F-RL-02 | 검색·상세·쓰기 가중치 | 각 endpoint가 위 class·cost와 결과 상한을 따른다. | RL-03 |
| F-RL-03 | 신뢰된 IP 추출 | 임의 전달 헤더로 한도를 우회하지 못한다. | RL-04 |
| F-RL-04 | 오류 계약 | 429·Retry-After·rate_limited·retry_after_seconds와 종료 코드 6이 일치한다. | RL-05, RL-06 |
| F-RL-05 | 웹 URL 호출 상한 | preview/import 합계 30/min, 동시 4건을 적용한다. | RL-07 |
| F-RL-06 | 게시·outcome 제한 | 게시 10/hour와 outcome 계정 bucket을 적용하며 멱등 retry를 중복 집계하지 않는다. | RL-08, RL-09 |
| F-RL-07 | 저장소 장애·포화 | 제한 상태와 503 서비스 상태가 구별되고 fail-closed 한다. | RL-10 |
| F-RL-08 | 사용량·한도 조회 | 소유자만 자기 집계를 보며 별도 status quota는 남긴다. | RL-11 |
| F-RL-09 | 제한 키 개인정보 | 원 IP·요청별 URL/body가 남지 않고 계정 ID만 short-lived bucket에 쓴다. | RL-12 |

