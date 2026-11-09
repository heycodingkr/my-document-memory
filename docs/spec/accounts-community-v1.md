# 계정·내 공간·공개 기여 v1

상태: 구현 및 검증 진행 (2026-11-09). 기본 웹 이메일 로그인은 동시 작업 [이메일 링크 명세](landing-email-links-v1.md)로 확장됐으며, 본 명세의 OTP API도 호환 유지한다. 기존 runtime-v1의 Rust/Axum/SQLite/Svelte와 Bearer 기반 CLI/MCP 호환성을 유지한다. 테스트 정의: [accounts-community-v1](../test/accounts-community-v1.md).

## 의존 순서와 원자 목표

| 순서/경로·담당 | 산출물 | 부모의 독립 검증 | 선행 |
|---|---|---|---|
| 0 WAM 참고 수집 / codex:gpt-6-luna, 읽기 전용 | 로그인·기여·공개 목록 관련 file:line 최대 10개, 코드 복사·수정 없음 | 인용 위치를 직접 열어 계약 비교 | 없음 |
| 1 docs/spec, docs/test / 부모 | 경계·라우트·입력/기대 결과 | 현재 코드/테스트와 대조 | 없음 |
| 2 server identity 저장·HTTP / 부모 | 이메일 OTP, 계정/세션, Resend adapter | 임시 DB + 캡처 mailer를 통한 실제 Router 테스트 | 1 |
| 3 server community 저장·HTTP / 부모 | 공개 목록, 내 통계, 기여 제출/철회/관리자 검수 | 소유자 A/B·익명·관리자의 실제 Router 및 영속성 테스트 | 2 |
| 4 web / 부모 | 이메일 로그인, 내 공간/기여, 익명 공개 탐색, 기존 편집기 | Svelte check/build 및 실제 서버 E2E | 3 |
| 4a 새 Svelte 컴포넌트 3개 문구 / codex:gpt-6-luna | AuthPanel·MyPage·PublicLibrary의 영문 사용자 문구(기존 landing 용어와 일치), 로직 수정 없음 | 부모가 코드 직접 확인 후 check/build/E2E | 4 컴포넌트 골격 |
| 5 설정·운영 문서 / 부모 | Resend/Cloudflare/DNS·관리자 설정, 검증과 한계 기록 | workspace tests, 기존 smoke, 실제 브라우저 확인, diff 리뷰 | 4 |

현재 작업 트리의 다른 작업은 보존한다. 디자인·원인 분석·빌드·테스트·통합·최종 리뷰는 부모가 수행한다. 외부 서비스 가입은 사용자 이메일을 확인한 뒤 수행하며 비밀은 출력/소스에 저장하지 않는다.

## 계정 계약

- POST /v1/auth/email/start {email}: 이메일 정규화/검증, 10분 유효한 6자리 코드. 브라우저 challenge 쿠키에 바인딩. 60초 재발송 제한과 시간당 이메일/브라우저 제한. 코드·토큰·이메일을 로그/오류에 출력하지 않는다. 미설정 mailer는 503이며 발송 성공으로 표시하지 않는다.
- POST /v1/auth/email/verify {code}: 같은 challenge 쿠키, 최대 5회 시도, 1회 사용. 성공 시 영속 계정과 30일 세션. 쿠키 HttpOnly/SameSite=Lax/Path=/, HTTPS 운영에서는 Secure. 저장소에는 코드와 세션 원문 대신 keyed hash를 저장한다. 재발송은 이전 코드를 무효화한다.
- GET /v1/auth/session: 현재 계정·이메일·csrf token. POST /v1/auth/logout: 세션 폐기와 쿠키 제거. 브라우저 쓰기는 정확한 허용 Origin 및 X-CSRF-Token을 검증한다. 로그인 start/verify도 허용 Origin을 필수 검증해 login CSRF를 방지한다.
- 기존 Bearer는 CLI/MCP용이며 local 소유자 데이터를 이메일 계정으로 자동 이전하지 않는다. 브라우저 세션 만료는 화면의 개인 데이터를 즉시 비우며 재로그인 안내를 제공한다.
- Resend endpoint는 https://api.resend.com/emails, timeout·성공 상태 검사. DMEM_RESEND_API_KEY, DMEM_EMAIL_FROM, DMEM_AUTH_SECRET, DMEM_WEB_ORIGIN 설정. 운영 도메인 mydocumentmemory.com, DNS Cloudflare. Resend 도메인 검증과 실제 수신은 외부 검증 항목이다.

## 내 공간·공개 기여 계약

- GET /v1/me: 사용자별 양식/자료/문서/기여 수. 개인 자료는 기존 owner 경계로 격리한다. 웹의 내 메모리는 내 양식·자료·작성 문서로 구성한다.
- GET /v1/public/templates 및 /{id}: 로그인 없이 공개 승인 양식과 기존 seed만 조회. 비공개 ID는 404. q/family 필터와 기존 최대 20개 제한. 원문 자료·작성 문서·이메일·소유자 ID는 포함하지 않는다.
- POST /v1/me/contributions {template_id,author,license,rights_confirmed}: 자기 소유 private 양식만, 공개될 구조 미리보기 후 권리 확인, CC0-1.0 또는 CC-BY-4.0. source 원문·작성 문서·비공개 provenance를 포함하지 않는 불변 snapshot을 pending으로 제출. 같은 양식의 활성 중복 제출은 409. 다른 소유자의 동일 구조는 독립 기여다.
- GET /v1/me/contributions: 자신의 기여만. POST /v1/me/contributions/{id}/withdraw: 자신의 pending/approved 기여 철회. 철회된 공개 원본은 탐색/복사에서 사라지고 기존 복사본의 고정 출처는 유지된다.
- GET /v1/admin/contributions, POST /v1/admin/contributions/{id}/decision {decision}: 별도 DMEM_ADMIN_TOKEN만 허용. 일반 사용자/Bearer local에 관리자 권한 없음. pending만 approve/reject 가능. approve는 불변 snapshot을 공개 catalog 새 ID로 원자적으로 저장. 철회와 동시 검수는 하나만 성공. 자동 게시·자동 개인정보 검수를 구현했다고 표시하지 않는다.
- 공개 양식을 내 라이브러리로 복사하면 새 private ID와 원본 id/version/author/license를 보존한다. 복사본에서 재기여할 때 원 라이선스·저작자 attribution을 보존하며 CC-BY를 CC0로 바꾸지 못한다. 공개 ID로 검증된 attributions 계보를 최대 16개 보존하며, 한도를 넘으면 일부를 버리지 않고 license_forbids로 거절한다. 비공개 ancestor ID는 공개 snapshot의 origin/attributions에서 제거한다.

## 요구사항 추적

| 요구사항 | 테스트 |
|---|---|
| 발송·코드/세션·재로그인·로그아웃 | AC-01~06 |
| Origin·CSRF·시도/재발송 제한·실패 처리 | AC-07~10 |
| 사용자별 데이터와 내 공간 | AC-11 |
| 비공개 snapshot 기여/검수/철회/복사·라이선스 | AC-12~17 |
| 실제 웹 흐름과 기존 편집기 회귀 | AC-18~20 |

외부 운영 설정이 미완료면 로컬 구현/테스트와 분리해 보고한다. OAuth/기여 점수/리더보드/자동 큐·LLM 검수는 이번 범위에 없다.
