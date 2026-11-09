# 이메일 인증·호출 제한·사용량 테스트

상태: 테스트 명세 초안 (문서 우선, 구현·검증 전). 이메일 링크와 사용량 집계는 공개 사용자 기능이며 runtime-v1 이후 단계다.
영역 / 테스트 ID 접두사: `EMAIL`, `RL`, `USAGE`
기반: [계정·공개 기여](../spec/accounts-community-v1.md) 계정 계약, [운영 설정](../spec/accounts-operations-v1.md) 로컬 자격 증명·Resend / Cloudflare, [랜딩 이메일 링크](../spec/landing-email-links-v1.md) Email link contract, [공통 오류·한도](../spec/core.md) 7~8절, [공유](../spec/sharing.md) 8절 F-SHR-13, [기존 기능 케이스](functional-tests.md) SHR-19, [개인정보](../spec/privacy.md) 2·4~5절. WAM: `docs/spec/email-auth.md`, `rate-limits.md`, `usage-analytics.md`; `docs/test/email-auth.md`, `service-abuse-performance.md`.

모든 검사는 합성 계정·메일 주소·문서만 사용하고 격리 DB, 캡처 메일러, 결정적 UTC 시계를 쓴다. 외부 Resend 발송은 하지 않는다. 테스트용 제한값 `N`은 주입한다(검색·recall·outcome의 고정 기본치는 이 계약에 없다). 게시 10건/시간은 SHR-19의 제안값이며 preview/import 30회/분·동시 4건도 `core.md` 8절 제안값이다.

## 1. 이메일 링크와 세션

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| EMAIL-01 | 새 브라우저에서 허용 Origin으로 `POST /v1/auth/email/link`에 공백·대문자가 섞인 합성 이메일을 보낸다. 캡처 메일러와 응답 body를 검사한다. | `202`와 `no-store`; 주소는 정규화되어 메일러에 한 번 전달되고 로그인 proof는 메일 링크 fragment에만 있다. 응답·계정·세션에는 proof가 없고 consume 전 계정 생성도 없다. |
| EMAIL-02 | 캡처한 링크를 메일 미리보기 `GET`으로 열고, 이어 쿠키 없는 다른 브라우저에서 fragment를 열어 본다. | 미리보기/링크 열기만으로 proof가 소비되거나 세션이 생기지 않는다. callback은 proof를 history에서 즉시 지우고 확인 화면을 보인다. `Continue` 전 consume 요청이 0건이다. |
| EMAIL-03 | `Continue`가 보낸 `POST /v1/auth/email/consume {token}`을 실행해 `/v1/auth/session`, reload, `POST /v1/auth/logout`을 호출한다. 별도 합성 주소로 `POST /v1/auth/email/start {email}`+`POST /v1/auth/email/verify {code}`도 성공시킨다. | 두 경로 모두 검증 성공 때만 계정·30일 세션을 만든다. 링크 경로는 `HttpOnly; SameSite=Lax; Path=/` 쿠키와 CSRF를 주고 HTTPS는 `Secure`; reload 후 같은 계정이며 logout 뒤 `/v1/auth/session`은 세션을 거부한다. 기존 6자리 OTP API도 호환 유지된다. |
| EMAIL-04 | 같은 정규화 이메일로 `t=0` 발송, `t=59s` 재요청, 이어 `t=60s,120s,180s,240s`에 성공하고 `t=300s` 새 브라우저에서 여섯 번째를 시도한다. | 60초 전과 시간당 5건 초과는 `429 rate_limited`, 정수 `retry_after_seconds` 및 `Retry-After`; 초과 요청은 메일·계정·세션을 만들지 않는다. 새 브라우저로 이메일 한도를 우회하지 못한다. |
| EMAIL-05 | 첫 proof를 `t=599s`와 `t=600s`에 각각 consume한다. | 599초에는 유효하고 600초에는 만료로 실패한다. 만료 proof는 세션을 만들지 않으며 새 challenge로만 다시 시작할 수 있다. |
| EMAIL-06 | 같은 미소비 proof로 두 개의 동시 `POST /v1/auth/email/consume`을 격리 저장소에 보낸 뒤 순차 재사용한다. | 원자적 소비 결과 성공은 정확히 한 번이다. 경쟁 요청과 재사용은 인증 실패, 계정 binding과 유효 세션은 중복 생성되지 않는다. |
| EMAIL-07 | proof 한 글자를 바꾸고, 존재하지 않는 challenge를 보내며, Resend fixture를 timeout/5xx로 실패시킨다. | 잘못된 proof는 실패하고 세션·계정이 생기지 않는다. 발송 실패는 성공으로 표시되지 않고 challenge를 소비할 수 없으며, 오류에 주소·proof·provider body가 반사되지 않는다. |
| EMAIL-08 | link 및 consume에 누락/외부 Origin, 잘못된 JSON, 설정 body 상한 초과를 보낸다. | 허용 Origin만 통과한다. 거부 요청은 메일·세션을 만들지 않고 정제된 오류와 `no-store`를 반환한다. |
| EMAIL-09 | 합성 이메일·proof를 challenge 저장소, 공개 DTO, 응답, 로그에서 검색한다. | challenge/verifier는 keyed hash만 저장되고 proof 원문은 응답·로그·영속 자료에 없다. 이메일 식별은 keyed hash로 저장하며 public 응답에 이메일이 없다. |
| EMAIL-10 | 로그인 전 브라우저에 공격자가 정한 임의 session cookie를 심고 유효 링크를 consume한 뒤 두 cookie를 각각 조회한다. | 성공 시 새 무작위 session cookie로 회전하며 사전 cookie는 인증되지 않는다. 타인이 고른 session ID를 승격하지 않고 CSRF·HttpOnly·SameSite 및 HTTPS Secure 속성을 유지한다. |

## 2. 서버 호출 제한과 격리

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| RL-01 | 동일 합성 owner/IP로 주입 한도 `N`의 `doc_memory_recall`을 `N+1`회 호출하고 마지막 요청을 CLI로도 실행한다. | 앞 `N`회만 admission된다. 초과는 HTTP 429 `rate_limited`, 양의 정수 `retry_after_seconds`, CLI 종료 6이며 recall 저장소·receipt writer는 호출되지 않는다. |
| RL-02 | 동일 IP에서 공개 `doc_memory_search`를 주입 한도 `N+1`회 실행한다. | `N+1`회는 429와 재시각을 돌려준다. 거부 검색은 결과/검색 상태를 쓰지 않고 query 원문을 로그나 limiter 응답에 포함하지 않는다. |
| RL-03 | 유효한 소유 메모리 11개와 동의·라이선스를 준비해 1시간 내 서로 다른 publish 11건을 요청한다. | 첫 10건만 게시 admission되고 11번째는 `rate_limited`다(제안값, SHR-19). 거부 호출 후 visibility, review 상태와 catalog가 변하지 않는다. |
| RL-04 | 한 owner가 60초에 `web preview` 31회 요청한다. | `core.md` 8절 제안값 30회/분의 초과는 429와 `retry_after_seconds`; 거부 preview는 preview 레코드나 원격 fetch를 만들지 않는다. |
| RL-05 | 서로 다른 합성 URL을 `web import` 한 분 내 31회 요청한다. | 제안값 30회/분의 초과는 429와 재시각이다. 초과 import는 라이브러리·파일·색인을 바꾸지 않고 원격 fetch도 시작하지 않는다. |
| RL-06 | 유효 receipt를 준비해 동일 계정으로 `doc_memory_outcome`을 주입 한도 `N+1`회 보고한다. | 처음 `N`건만 허용된다. 초과는 공통 429 계약이며 새 outcome·점수·receipt 상태 변경이 없다. |
| RL-07 | 각 제한 작업을 `N`회 허용한 뒤 한도를 넘기고 HTTP JSON 및 CLI 출력/종료 상태를 검사한다. | 모든 표면이 고정 코드 `rate_limited`, HTTP 429, 정수 `retry_after_seconds`와 양의 대기 시간을 제공한다. CLI 종료 코드는 6이고 URL·본문·IP·토큰은 오류에 없다. |
| RL-08 | recall/search/publish/preview/import/outcome 각각에서 한도를 넘기기 직전과 직후 업무 DB snapshot을 비교한다. | 거부 호출은 도메인 상태 변화 0: memory·catalog·review·preview·receipt·outcome·점수와 성공 사용량 기록이 동일하고 handler 작업이 실행되지 않는다. |
| RL-09 | IP가 다른 계정 A의 quota를 소진한 뒤 계정 B로 같은 작업과 owner usage 조회를 수행한다. | A의 거부 횟수·quota 정보·비공개 데이터가 B 응답에 나타나지 않는다. B의 독립 quota와 요청은 A의 계정 한도 때문에 차단되지 않는다. |
| RL-10 | 결정적 시계를 `retry_after_seconds` 전후로 이동해 같은 제한 작업을 재요청한다. | 대기 전에는 거부되고, 만료 후에는 다시 admission되어 성공 상태 변화가 정확히 한 번 생긴다. 실제 sleep 없이 회복 시각을 판정한다. |
| RL-11 | 각각 preview와 import에 동시 5건을 보내고 4건을 점유한 뒤 한 slot을 해제한다. | 제안 동시 한도 4에서 다섯 번째 동시 작업은 429/재시각, 저장 변화와 원격 fetch가 0이다. slot 해제 후 재시도는 허용된다. |
| RL-12 | 두 서버 인스턴스에서 같은 owner의 한도 `N`에 `N+K` 동시 호출을 보낸다. | 공유 limiter에서 성공은 최대 `N`; 모든 초과는 공통 429이며 초과 handler의 업무 상태 변경은 0이다. 인스턴스별로 한도가 중복되지 않는다. |

## 3. 사용량 집계와 개인정보

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| USAGE-01 | 새 계정에서 recall/search/publish/preview/import/outcome를 각각 호출하고 telemetry/usage 동의를 켜지 않은 상태를 조회한다. | 기본 off에서는 사용량 분석을 외부로 보내거나 집계 저장하지 않는다. 필요한 보안·업무 저장과 선택형 사용량 집계가 구분된다. |
| USAGE-02 | 합성 계정에서 별도 사용량 동의 후 각 6개 작업을 한 번씩 실행하고 하루 집계와 저장 행을 확인한다. | UTC 날짜·작업 종류·집계 count 등 최소 필드만 남고 요청별 event ID, reader ID, 원 IP, 세부 URL은 없다. 동의는 공유 동의와 독립적이다. |
| USAGE-03 | 이메일 `synthetic@example.test`, 문서 본문 `BODY_SENTINEL_91`, URL query `?token=QUERY_SENTINEL_82`를 넣은 작업 후 aggregate, 로그, telemetry payload를 검색한다. | 이메일·본문·원 URL/query·token sentinel은 사용량 집계/로그/telemetry에 0건이다. 공유 전용 동의·검사는 별도로 유지된다. |
| USAGE-04 | 고정 시계에서 집계 row를 89일·90일 경계 양쪽에 만들고 만료 작업을 실행한다. | 계정 연결 사용량은 최대 90일 보관되고 만료분은 제거된다. 새 집계는 유지되며 보관 만료가 score·memory 데이터를 바꾸지 않는다. |
| USAGE-05 | 계정에서 사용량 동의를 켜 한 건 집계한 뒤 opt-out하고 추가 작업 및 queue flush를 수행한다. | opt-out은 즉시 반영되어 이후 작업과 대기 queue는 수집·전송되지 않는다. 공유 `share-v1` 동의와 계정 인증 설정은 바뀌지 않는다. |
| USAGE-06 | 계정 A의 연결 집계를 만든 뒤 확인된 계정 삭제(`manage:account`, `confirmation=DELETE`)를 실행하고 A/B 집계를 다시 조회한다. | A 연결 사용량과 대기 telemetry가 제거되고 복구되지 않는다. B 자료와 정책상 비식별 coarse totals는 영향이 없으며, 이메일·계정 식별자로 A 집계를 찾을 수 없다. |
