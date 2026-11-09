# 계정 운영 설정

계약: [계정·공개 기여](accounts-community-v1.md). 웹은 Svelte, API는 Rust/Axum, 상태는 SQLite다. Resend는 로그인 메일 전송에만 사용한다.

## 로컬 자격 증명

실제 값은 Git에서 제외한 `credentials/`에 저장한다. 디렉터리 0700, 파일 0600.

| 파일 | 용도 | 환경 변수 우선값 |
|---|---|---|
| credentials/resend-api-key | Resend sending-only API key | DMEM_RESEND_API_KEY |
| credentials/auth-secret | 영속 HMAC key; 교체하면 기존 인증 challenge/세션 무효 | DMEM_AUTH_SECRET |
| credentials/admin-token | 기여 검수 전용 Bearer, 일반 계정/CLI와 분리 | DMEM_ADMIN_TOKEN |

서버는 위 파일을 기본 경로로 읽는다. 키가 없으면 이메일 로그인은 비활성화되고 발송 요청은 503을 반환한다. API key가 있는데 auth secret이 없거나 짧으면 시작을 거부한다. `DMEM_EMAIL_FROM` 기본값은 `My Document Memory <help@mydocumentmemory.com>`. 실서비스 `DMEM_WEB_ORIGIN=https://mydocumentmemory.com`을 사용해 Secure 쿠키를 켠다. 기존 `.env`의 DMEM_TOKEN은 local 소유자의 CLI/MCP 연결용이다.

`node scripts/dev.mjs`는 .env를 읽어 개발 API와 Vite를 시작한다. 이미 실행 중인 서버를 재시작할 때는 그 서버의 소유자를 확인한다. 서비스가 유지되어야 하는 프리뷰는 detached 프로세스로 실행한다.

## Resend / Cloudflare

사용자가 가입한 Resend 계정은 help@mydocumentmemory.com. 도메인은 Cloudflare DNS의 mydocumentmemory.com이며, Resend UI에서 Verified를 확인했다. 발송 인증은 resend._domainkey TXT와 rsend/send CNAME을 사용한다. 레코드 값은 Resend UI의 실제 안내를 따른다. Cloudflare의 기존 수신 MX, support/help → Gmail 전달은 별도 기능이므로 교체하지 않는다.

실제 메일 발송과 수신 상태는 Resend UI에서 확인한다. 로그인 메일 내용·OTP·링크 proof·API key는 터미널이나 보고서에 출력하지 않는다.

## 기존 Linux 배포

호스트 jason-4090, 서비스 my-document-memory.service, loopback :3848, persistent DB /var/lib/my-document-memory/library.sqlite3, release /srv/my-document-memory/releases, current symlink, 환경 파일 /etc/my-document-memory/server.env. 기존 서비스와 DB를 보존하며, 계정 migration 전에 SQLite backup API로 일관된 백업을 만든다. 빌드/검증된 새 release만 원자적으로 전환하고 이상 시 이전 current로 복귀한다.

운영 키는 서버의 root 전용 환경 파일이나 dmem만 읽는 별도 파일로 전달한다. 소스 archive/web build에 credentials/를 포함하지 않는다. 환경 파일 값을 표시하지 않으며, 기존 DMEM_TOKEN/DB/Origin을 지우지 않는다. 이메일 링크 기본 UI를 추가하는 작업 #392와 합쳐 release 20261109T022729Z-13901을 배포했다. `/v1/auth/config`는 email_enabled=true이며, 전체 일반 웹21개 + 계정3개 검증 후 전환했다. 같은 호스트 동시 배포는 scripts/deploy-production.sh의 flock으로 직렬화한다.

## 검수

브라우저에서는 https://mydocumentmemory.com/#review 에서 관리자 이메일 링크를 요청한다. 운영 환경의 DMEM_ADMIN_EMAILS에 쉼표로 구분한 명시적 이메일만 허용한다. 주소는 공백 제거·소문자화 후 정확히 비교하며 와일드카드나 잘못된 주소는 거부한다. 빈 목록이면 관리자 로그인이 비활성화된다. 발신자 주소나 일반 회원을 자동으로 관리자로 승격하지 않는다.

로그인 링크는 10분간 1회 사용하며 명시적인 POST 확인 후 일반 회원과 별개인 HttpOnly 관리자 쿠키를 발급한다. 관리자 세션은 2시간이며 매 요청마다 허용 목록을 다시 확인한다. 허용 이메일 제거 후 서비스 설정을 반영하면 기존 세션도 거부한다. 모든 관리자 응답은 no-store이며 승인·반려·로그아웃에는 허용 Origin과 관리자 CSRF가 필요하다.

GET /v1/admin/contributions, GET /v1/admin/contributions/{id}/review, POST /v1/admin/contributions/{id}/decision으로 검토한다. decision은 approve/reject다. 별도의 DMEM_ADMIN_TOKEN은 API/CLI 운영 호환용으로 남고 브라우저에 입력하거나 저장하지 않는다. 일반 회원 세션과 DMEM_TOKEN은 관리자 권한이 없다. 승인·반려는 현재 검토 결과를 같은 DB 트랜잭션에서 다시 확인하며 가명화한 관리자 식별자와 결정을 기록한다. 실제 관리자 이메일은 사용자에게 확인한 값만 운영 환경 파일에 반영한다. 사양과 검증은 admin-email-starters-v1.md를 참조한다.
