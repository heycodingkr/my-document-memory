# 계정·마이페이지·공개 기여 — 실행 결과

2026-11-09. 구현 계약 [accounts-community-v1](../spec/accounts-community-v1.md), 테스트 입력/기대 결과 [명세](accounts-community-v1.md), 설계/원인/리뷰 [기록](../design/accounts-community-v1-review.md), 비밀을 포함하지 않는 [운영 안내](../spec/accounts-operations-v1.md).

## 제품 검증

- `cargo test --workspace --locked`: 33개 통과. OTP 6자리·브라우저 바인딩·시도/재발송/시간당 제한·만료·1회성, 영속 계정/세션, Origin/CSRF, 사용자 격리, 이메일 링크의 이동성/재사용/실패 처리, 기여 검수/복사/철회, 공개 출처의 private ID 제거·최초 저작자 보존·16개 계보 한도 포함.
- `pnpm --dir web check`, `pnpm --dir web build`: 0 오류/0 경고, 빌드 성공.
- `python3 tests/smoke/accounts-v1.py`: 실제 Rust API + 임시 SQLite + synthetic mailer + Playwright 3개 통과. 다른 브라우저에서 이메일 링크 확인, 같은 페이지 hash 이동, proof 제거와 명시적 계속 버튼, 재사용 거부, 마이페이지, 새 양식, 기여 제출→관리자 승인→익명 공개→private 복사→철회, 새로고침, 로그아웃, 401 개인 화면 초기화, 390px overflow 검사.
- `python3 tests/smoke/runtime-v1.py --browser --browser-spec workspace.spec.ts --browser-spec agent-handoff.spec.ts`: 기존 HTTP/CLI/MCP·저장 충돌·출처·버전·재시작 영속성 스모크 및 웹 8개 통과.
- 실제 Resend API key를 문자열로 검사한 소스/문서/프런트 빌드 120개 파일에서 0건. credentials/는 Git 제외, 디렉터리 0700 / 파일 0600 확인.

계정 테스트는 다른 실행이 결과 디렉터리를 지우지 않도록 `DMEM_E2E_OUTPUT_DIR`을 실행별 `target/e2e-logs/accounts-*`로 지정한다. 단독 계정 스모크만 실제 이메일 링크를 synthetic mailbox에 캡처하고, 다른 runtime 스모크에서는 이 세 케이스를 사유와 함께 skip한다.

## 실제 외부 서비스

사용자가 help@mydocumentmemory.com으로 가입한 Resend에 sending-only API key를 생성하고 `credentials/resend-api-key`에 저장했다. key 원문은 이 보고서에 없다. Resend의 mydocumentmemory.com 도메인 Verified와 실제 로그인 메일 Delivered를 확인했다. Arise에서 그 코드로 실제 help 계정 로그인을 완료하고 My page 화면을 이미지로 확인했다. 기존 Cloudflare 수신 라우팅은 변경하지 않았다.

운영 jason-4090의 /etc/my-document-memory/server.env에는 메일 key/HMAC secret/관리자 secret/발신자를 추가했다. 기존 DMEM_TOKEN, DB, Origin은 보존했다. SQLite의 일관된 백업 `before-accounts-20261109T021234Z.sqlite3`을 /var/lib/my-document-memory에 만들었다. 이 설정 작업은 서비스를 재시작하거나 release를 전환하지 않았다.

## 유지 중인 로컬 프리뷰

최신 서버 프리뷰: http://127.0.0.1:3849/#me (PID 10105). 로그: /var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794190902283.log. 이 작업이 시작한 이전 PID 92640만 종료하고 최신 binary로 교체했다. 기존 다른 개발 서버는 유지했다. healthz 200, auth/config email_enabled=true, 익명 공개 양식 18개 응답을 다시 확인했다. detached 프로세스이므로 현재 턴 종료 후에도 유지된다.

## 범위와 현재 배포 상태

마지막 직접 확인 시 운영 current는 /srv/my-document-memory/releases/20261109T011532Z이고 /v1/auth/config는 404였다. 계정 기능과 설정 준비는 완료됐지만, 운영 공개 반영은 같은 저장소의 영문 랜딩/이메일 링크 배포 작업 #392와 함께 진행해야 한다. 그 작업의 release 전환 결과를 확인하기 전 운영 로그인이 배포됐다고 표시하지 않는다.

전체 웹 suite에는 별도 진행 중인 landing-demo.spec.ts 케이스가 추가됐다. 합친 전체 runtime 브라우저 실행은 이 데모 suite의 미완료 케이스에서 120초 상한에 도달했다. 위 계정·편집기·에이전트 11개와 Rust 33개는 독립 실행에서 통과했으며, 전체 신규 데모 suite 통과로 대체해 주장하지 않는다.

점수·리더보드·자동 개인정보/중복 검수·팀 공유는 구현 범위 밖이다. 공개 기여는 구조만 제출하고 별도 관리자 검수 후 공개된다. 기존 local 소유자의 자료를 새 이메일 계정에 자동 이전하지 않는다.
