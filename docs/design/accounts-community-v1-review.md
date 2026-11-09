# 계정·내 공간·공개 기여 v1 — 설계 및 검증 기록

2026-11-09. 계약: [accounts-community-v1](../spec/accounts-community-v1.md), 입력/기대 결과: [테스트 명세](../test/accounts-community-v1.md).

## 설계 근거와 변경 경계

기존 runtime-v1은 설정된 Bearer 하나를 local owner로 해석했다. 이메일 로그인 화면만 추가하면 기존 소유자 하나를 여러 사람이 공유하게 되므로, SQLite의 계정·세션을 별도로 만들고 기존 owner 필터에 영속 account ID를 전달한다. CLI/MCP Bearer와 기존 local 데이터는 그대로 유지하며 새 이메일 계정으로 자동 귀속시키지 않는다.

WAM에서 직접 확인한 근거는 identity/email.rs:145/212, http/email_routes.rs, http/contribution_routes.rs:54/94, http/read_routes.rs:55, web/routes/dashboard/+page.svelte:90이다. 6자리 이메일 코드·브라우저 바인딩·별도 검수자 권한과 익명 공개 조회 경계를 참고했다. WAM의 점수·리더보드·사용량·LLM 검수를 구현했다고 표시하지 않는다.

계정과 세션은 SQLite에 보존된다. 이메일 challenge는 10분/5회/1회 사용이며 브라우저 쿠키와 결합된다. OTP와 세션은 영속 인증 secret을 사용하는 HMAC으로 저장한다. 운영 HTTPS의 HttpOnly/SameSite=Lax/Secure 쿠키, 엄격한 Origin, 세션 쓰기의 CSRF 검증, 이메일·브라우저별 재발송/시간당 제한 및 전역 200건/시간 상한을 사용한다. IP별 분산 rate limit은 후속 운영 항목이다. 401을 관찰하면 웹의 개인 데이터와 모달을 초기화한다.

기여는 원문 자료와 작성 문서가 아니라 양식의 불변 구조 snapshot이다. 명시적 권리 확인·공개 저작자·CC0/CC-BY 선택 후 pending으로 저장한다. 별도 관리자 secret으로 승인해야 새 공개 ID가 생성된다. 철회는 이후 공개 조회와 복사를 제거하며 이미 복사된 버전은 보존한다. 자동 PII 검수 대신 공개 미리보기와 사람의 검수를 제공한다.

공개 metadata에는 비공개 원본 ID가 들어가면 안 된다. 복사의 origin과 공개 저작자 표시 계보를 분리해, 공개로 확인된 attribution만 최대 16개 보존한다. 계보가 한도를 넘으면 일부를 조용히 버리지 않고 복사를 거절한다. CC-BY가 포함된 파생 기여는 CC0로 바꾸지 못한다.

## 재현 후 수정한 결함

- 익명 공개 조회가 없던 상태에서 실제 Router 테스트가 404로 실패한 것을 확인하고 공개 전용 경로를 추가했다.
- Svelte의 quoted pattern 속성에서 `{6}`이 표현식으로 처리되어 올바른 6자리 코드가 HTML form 검증을 통과하지 못했다. 실제 브라우저 로그인 테스트로 재현 후 literal expression으로 수정했다.
- 갱신되는 unkeyed 양식 목록에서 표시된 회의록을 클릭했지만 실제 copy 요청이 sales.quote.en으로 전송됐다. trace의 실제 HTTP 요청과 모달 제목 검사로 재현하고 template ID로 keyed each를 적용했다.
- 계정 메뉴 추가 및 두 개 언어/범위 필터가 좁은 화면을 넘었다. 계정 메뉴를 별도 반응형 영역으로 구성하고 검색 필터를 줄바꿈했다. viewport 390px에서 실제 요소 경계와 document scrollWidth를 검사한다.
- private copy의 private ancestor ID가 공개 snapshot에 남는 경우와 파생 양식을 다시 복사하면 최초 기여자 attribution이 사라지는 경우를 독립 실패 테스트 2개로 재현했다. 공개 ID 검증과 별도 attributions 계보를 추가한 뒤 두 테스트가 통과했다.

## 외부 설정

Resend 계정은 사용자 요청대로 help@mydocumentmemory.com. sending-only API key를 생성하여 credentials/resend-api-key에 저장했다. credentials/auth-secret과 admin-token도 준비했다. 디렉터리 0700, 파일 0600, credentials/ 전체 Git 제외를 실제 확인했다. 값은 소스·보고서에 포함하지 않는다.

Resend UI에서 mydocumentmemory.com 도메인 Verified와 로그인 메일 Delivered를 확인했다. 공개 DNS의 resend._domainkey TXT, rsend/send CNAME도 확인했다. 기존 Cloudflare Email Routing 수신 MX와 support/help 전달 설정은 변경하지 않았다. 실제 Arise에서 help 계정 OTP 로그인 후 My page 화면을 확인했다.

기존 호스트 브라우저 wrapper가 호출 사이 lease proof를 잃고 빈 탭을 선택하여, 이 저장소의 tests/smoke/arise_smoke.py McpChild를 재사용한 하나의 유지되는 공개 stdio MCP 연결로 Arise를 제어했다. private 제어 socket/CDP를 사용하지 않았다. 이미 검증된 최신 Arise MCP binary는 project-only 등록하며 기존 MCP 설정을 보존했다.

최종 전체 체크·배포 결과는 테스트 명세의 실행 기록에 갱신한다. 같은 작업 트리의 영문 랜딩/양식/이메일 링크 추가 작업과 합친 최신 상태를 검증해야 한다.
