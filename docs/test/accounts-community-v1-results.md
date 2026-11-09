# 계정·마이페이지·공개 기여 — 실행 결과

2026-11-09. 구현 계약 [accounts-community-v1](../spec/accounts-community-v1.md), 테스트 입력/기대 결과 [명세](accounts-community-v1.md), 설계/원인/리뷰 [기록](../design/accounts-community-v1-review.md), 비밀을 포함하지 않는 [운영 안내](../spec/accounts-operations-v1.md).

## 제품 검증

- `cargo test --workspace --locked`: 33개 통과. OTP 6자리·브라우저 바인딩·시도/재발송/시간당 제한·만료·1회성, 영속 계정/세션, Origin/CSRF, 사용자 격리, 이메일 링크의 이동성/재사용/실패 처리, 기여 검수/복사/철회, 공개 출처의 private ID 제거·최초 저작자 보존·16개 계보 한도 포함.
- `pnpm --dir web check`, `pnpm --dir web build`: 0 오류/0 경고, 빌드 성공.
- `python3 tests/smoke/accounts-v1.py`: 실제 Rust API + 임시 SQLite + synthetic mailer + Playwright 3개 통과. 다른 브라우저에서 이메일 링크 확인, 같은 페이지 hash 이동, proof 제거와 명시적 계속 버튼, 재사용 거부, 마이페이지, 새 양식, 기여 제출→관리자 승인→익명 공개→private 복사→철회, 새로고침, 로그아웃, 401 개인 화면 초기화, 390px overflow 검사.
- 최종 `python3 tests/smoke/runtime-v1.py --browser`: 기존 HTTP/CLI/MCP·저장 충돌·출처·버전·재시작 영속성 스모크와 일반 웹 21개 통과. 계정 3개는 해당 프로필에서 사유와 함께 skip 후, 전용 계정 스모크에서 3개 모두 별도 통과. 최종 웹 검증은 합계 24개.
- 실제 Resend API key를 문자열로 검사한 소스/문서/프런트 빌드 120개 파일에서 0건. credentials/는 Git 제외, 디렉터리 0700 / 파일 0600 확인.

계정 테스트는 다른 실행이 결과 디렉터리를 지우지 않도록 `DMEM_E2E_OUTPUT_DIR`을 실행별 `target/e2e-logs/accounts-*`로 지정한다. 단독 계정 스모크만 실제 이메일 링크를 synthetic mailbox에 캡처하고, 다른 runtime 스모크에서는 이 세 케이스를 사유와 함께 skip한다.

## 실제 외부 서비스

사용자가 help@mydocumentmemory.com으로 가입한 Resend에 sending-only API key를 생성하고 `credentials/resend-api-key`에 저장했다. key 원문은 이 보고서에 없다. Resend의 mydocumentmemory.com 도메인 Verified와 실제 로그인 메일 Delivered를 확인했다. Arise에서 그 코드로 실제 help 계정 로그인을 완료하고 My page 화면을 이미지로 확인했다. 기존 Cloudflare 수신 라우팅은 변경하지 않았다.

운영 jason-4090의 /etc/my-document-memory/server.env에는 메일 key/HMAC secret/관리자 secret/발신자를 추가했다. 기존 DMEM_TOKEN, DB, Origin은 보존했다. SQLite의 일관된 백업 `before-accounts-20261109T021234Z.sqlite3`을 /var/lib/my-document-memory에 만들었다. 이 설정 작업은 서비스를 재시작하거나 release를 전환하지 않았다.

## 실제 운영 이메일 링크 로그인

배포 후 Arise에서 https://mydocumentmemory.com/#me로 help@mydocumentmemory.com의 로그인 링크를 요청했다. Resend에서 새 메일 Delivered를 확인하고, 공개 stdio MCP의 native cef iframe handle로 메일 링크를 읽되 proof는 출력하지 않았다. 실제 운영 URL에서 주소의 proof 제거를 확인한 뒤 Continue to my space를 눌러 My page를 열었다. 같은 URL 재방문 후 로그인 유지와 실제 화면을 재확인했다. 서버 SQLite를 별도로 조회해 help 계정 1개와 세션 1개가 생성된 것을 확인했다. 운영 화면 캡처는 .artifacts/production-mypage.png이며 직접 이미지로 확인했다.

## 유지 중인 로컬 프리뷰

최신 서버 프리뷰: http://127.0.0.1:3849/#me (PID 10105). 로그: /var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794190902283.log. 이 작업이 시작한 이전 PID 92640만 종료하고 최신 binary로 교체했다. 기존 다른 개발 서버는 유지했다. healthz 200, auth/config email_enabled=true, 익명 공개 양식 18개 응답을 다시 확인했다. detached 프로세스이므로 현재 턴 종료 후에도 유지된다.

## 범위와 현재 배포 상태

최종 검증 후 `scripts/deploy-production.sh jason-4090`으로 release `20261109T022729Z-13901`을 반영했다. 원격 flock으로 build/cutover를 직렬화하고 고유 release suffix를 사용한다. 실제 current symlink·service active, 공개 HTTPS health 200, auth/config `email_enabled=true`, 익명 공개 양식 18개를 독립 확인했다. 무인증 session/source/admin 접근은 401이다. 공개 영어 HTML과 두 asset의 bytes가 로컬 검증 빌드와 일치하며 실제 API key가 없다. 기존 local 자료는 source6/template6/document2로, pre-account backup과 일치한다.

중간 실행에서는 동시 작업의 미완료 landing-demo.spec.ts에서 120초 상한에 도달했다. 이후 최신 구현의 demo5개를 별도 검증하고, 전체 웹 suite21개와 전용 account3개를 다시 실행해 모두 통과한 뒤 배포했다.

점수·리더보드·자동 개인정보/중복 검수·팀 공유는 구현 범위 밖이다. 공개 기여는 구조만 제출하고 별도 관리자 검수 후 공개된다. 기존 local 소유자의 자료를 새 이메일 계정에 자동 이전하지 않는다.
