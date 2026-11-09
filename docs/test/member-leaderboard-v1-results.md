# 회원·리더보드 v1 검증 기록

2026-11-09. 계약: [기능 명세](../spec/member-leaderboard-v1.md), [입력과 기대 결과](member-leaderboard-v1.md), [설계와 검토](../design/member-leaderboard-v1-review.md). 이 기록은 아래 release와 당시 작업 트리의 검증 결과다.

## 재현과 구현

첫 focused Router 테스트에서 익명 GET /v1/leaderboard는404로 실패했다. profile 저장소/경로/순위 구현 후 같은 입력이200, 빈 items, points_per_approval=20으로 통과했다. 실제 SQLite와 이메일 capture를 사용하며 점수 테스트는 진짜 기여 승인/철회 경로를 거친다.

| 검증 | 결과 |
|---|---|
| `cargo test --workspace --locked` | 85 passed, 0 failed |
| 새 `member_leaderboard.rs` | 6 passed: 비공개 기본값·read 무쓰기·handle/동시 선점·인증/CSRF·실제 승인/철회·전체/공개 순위·동점/페이지·privacy·재시작 |
| `cargo build --workspace --locked` 및 accounts_fixture build | 성공 |
| `pnpm --dir web check` | 0 errors, 0 warnings |
| `pnpm --dir web build` | 성공 |
| `python3 tests/smoke/runtime-v1.py --browser` | HTTP/CLI/MCP/내보내기/불변 버전/재시작 통과, 일반 브라우저29 passed |
| `python3 tests/smoke/accounts-v1.py` | 이메일/계정3 + 회원3 + contribution review2 = 8 passed |
| 실제 승인 데이터의1440/390/320px | 가로 넘침 없음, leaderboard/본인 점수/공개 profile/철회와 opt-out 검증, 이미지 직접 검사 |

일반 브라우저 실행의9 skipped 중8개는 별도 이메일 capture fixture를 요구하는 계정/회원/검수 테스트로 전용 실행에서 통과했다. 나머지 실제 메일 배달 테스트는 일반 fixture에 Resend 자격 증명을 넣지 않아 실행하지 않았다. 기존 운영 Resend 연동/이메일 링크의 배달·명시 확인 검증은 [계정 운영 기록](accounts-community-v1-results.md)을 따른다. 이번 운영 확인에서는 사용자에게 새 인증 메일을 보내지 않고 기존 실제 세션을 확인했다.

전체 회귀에서 확인한 기존 기대값도 고쳤다. 추가 starter catalog로 전체18/영문9개라는 고정 개수가 더 이상 맞지 않아 실제 JSON 입력+기존 seed와20개 한도를 검증한다. 영어 본문 검증은 한국어 전환 버튼의 자국어 이름을 제외하며, Slides 링크는 현재 접근성 이름을 검증한다. 문서 v3를 열고 새로고침하면 #documents 목록을 유지하고 같은 v3를 다시 열어 내용이 보존되는지 확인한다.

로컬 증거: `target/e2e-logs/member-final/{rust,build,check,web-build,browser,accounts}.log`, `production.json`. 전용 브라우저 이미지: `target/e2e-logs/accounts-1794194916124699000/leaderboard-{1440,390,320}.png`, `member-mypage.png`. 임시 DB/합성 계정을 사용했으며 운영에 순위 데이터를 넣지 않았다.

## 운영 배포와 직접 확인

- release: `20261109T033037Z-80119`, source archive `.artifacts/deploy/20261109T033037Z-80119.tar.gz`.
- 기존 `scripts/deploy-production.sh jason-4090`의 flock 안에서 build/cutover, service healthy. env/Resend key/세션 secret을 덮어쓰지 않았다.
- 배포 전 SQLite backup API로 `/var/lib/my-document-memory/backups/before-members-20261109T033031Z.sqlite3` 생성,0600. 배포 후 백업의32개 records 각각 id/owner/kind/version/payload가 동일한지 읽기 전용 SQL 대조로 확인했고 accounts도 보존됐다. additive starter catalog는 기존 행을 덮어쓰지 않는다.
- 실제 `https://mydocumentmemory.com/v1/leaderboard`200: items=[], total=0, next_offset=null, points_per_approval=20. 공개 opt-in/승인 기여가 없으므로 빈 결과가 정상이다.
- 미존재 `/v1/profiles/no-such-member-20261109`404, 무인증 `/v1/me/profile`401, `/v1/auth/config`200+email_enabled=true, `/healthz`200. 모두 no-store 확인.
- HTTPS root HTML과 JS/CSS2개를 release archive 바이트와 대조해 일치 확인. 이후 다른 세션이 만든 로컬 bundle은 이 배포 증거와 구분한다.
- 실제 Arise의 세션 소유 window42/tab108에서 #leaderboard와 #me 확인. 기존 사용자 세션이 유지되고 본인 metrics는0/Not ranked/Not ranked, handle은 빈 값, 공개 체크는false였다. 공개 설정이나 실제 기여를 변경하지 않았다.
- Arise 스냅샷 captcha=false. 실제 화면의 empty state와 가로 넘침 없음 확인, `.artifacts/production-leaderboard.png`, `.artifacts/production-leaderboard-empty.png`를 이미지 도구로 직접 검사했다.
- private credentials0600, git ignored, 실제 key/secret byte가 web bundle에 없음을 값 출력 없이 검사했다.

공개 리더보드: <https://mydocumentmemory.com/#leaderboard>. My page에서 닉네임과 공개 여부를 선택하고 승인·공개된 기여가 생기면 순위에 표시된다. 현재 점수는 승인·공개 기여당20점이며 철회 시 빠진다. 성공 사용 보상·기간별 점수·점수 이력 ledger는 이 v1에 포함하지 않는다.
