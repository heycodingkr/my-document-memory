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

운영 키는 서버의 root 전용 환경 파일이나 dmem만 읽는 별도 파일로 전달한다. 소스 archive/web build에 credentials/를 포함하지 않는다. 환경 파일 값을 표시하지 않으며, 기존 DMEM_TOKEN/DB/Origin을 지우지 않는다. 이메일 링크 기본 UI를 추가하는 동시 작업 #392의 배포와 조율한다.

## 검수

GET /v1/admin/contributions와 POST /v1/admin/contributions/{id}/decision은 별도 관리자 Bearer와 허용 Origin이 필요하다. decision은 approve/reject다. 공개할 제목·요약·섹션·태그·저작자·라이선스를 확인한 뒤 승인한다. 일반 계정 세션은 관리자 권한이 없다. 비밀/개인 정보 자동 탐지·중복 검수·점수·리더보드·팀 공간은 후속 범위다.
