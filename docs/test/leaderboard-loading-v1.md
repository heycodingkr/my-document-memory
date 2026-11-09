# 리더보드 로딩 입력과 기대 결과

계약: [leaderboard-loading-v1](../spec/leaderboard-loading-v1.md). 이슈 #408.
운영 회원 데이터를 변경하지 않고 Playwright에서 session/leaderboard 응답을
제어한다. 페이지의 가상 시계를 진행해 네트워크가 멈춘 경우를 재현한다.

| ID | 입력 | 기대 결과 |
|---|---|---|
| LL-01 | session=401, leaderboard 응답 헤더가 오지 않음 | 9초에는 로딩, 10초 이후 시간 초과 오류와 Retry, 빈 순위 안내 없음 |
| LL-02 | LL-01 이후 Retry에 공개 회원 한 명 응답 | 새 요청 1회, 실제 handle/40점/순위 표시, 로딩·오류 사라짐 |
| LL-03 | session 응답이 멈춤, direct #leaderboard, leaderboard=정상 빈 응답 | 10초 이후 초기 화면 대기가 끝나고 공개 리더보드/0명 안내 표시; 로그인 성공 표시 없음 |
| LL-04 | session=401, leaderboard=정상 빈 응답 | 즉시 0 contributors 및 빈 순위 안내; 오류/로딩 없음 |
| LL-05 | leaderboard=503, Retry=정상 빈 응답 | 기존 서버 오류와 Retry, 재시도 성공 후 빈 상태 |
| LL-06 | leaderboard 응답 헤더 후 JSON body가 멈춤 | 응답 JSON 읽기도 같은 10초 제한을 적용해 오류/Retry 표시 |
| LL-07 | 읽기 성공 후 10초 이상 경과 | 이미 표시된 정상 순위가 유지되고 오류가 새로 나타나지 않음 |
| LL-08 | 실제 임시 SQLite+합성 이메일 회원 흐름 | 가입/로그인/공개 선택/실제 승인·철회/40·20점과 순위/공개 개인정보 경계 유지 |

LL-06은 브라우저의 fetch 응답 스트림에 abort를 연결한 합성 지연 body를 사용한다.
실제 fetch/페이지 흐름을 사용하는 LL-01~05와 함께 헤더만 제한하는 오류를 막는다.
기존 Playwright `members.spec.ts`는 실제 API/DB를 사용하는 LL-08의 oracle이다.

## 실행 기록

- 수정 전 LL-01과 LL-06은 가상 10.1초 이후에도 `Loading public ranks…`가
  유지되고 alert가 없어 실패했다. LL-04/05 정상 빈 상태와 503 복구는 통과했다.
  trace 및 DOM: `target/e2e-logs/leaderboard-loading-red/`.
- LL-03의 첫 기대 문구를 실제 초기 화면과 대조해 수정했다. 최초 직접 진입 시
  session 조회 전에는 landing이 표시되며, 조회 중 sidebar로 이동하면 Opening
  your space가 표시된다. 사용자에게 보일 공개 순위가 10초 이후에도 없는지로
  다시 실행했고 수정 전 실패했다. `target/e2e-logs/leaderboard-loading-session-red/`.
- 수정 후 같은 5개 focused 브라우저 테스트가 모두 통과했다. LL-01은 실제
  fetch의 `net::ERR_ABORTED`도 확인한다. `target/e2e-logs/leaderboard-loading-green/`.
- `pnpm --dir web check`: 0 errors, 0 warnings.
- `pnpm --dir web build`: 성공. JS `index-CMRkVlAT.js`.
- `cargo test --locked -p dmem-server --test member_leaderboard`: 6 passed.

- `cargo build --locked -p dmem-server --example accounts_fixture`: 성공.
- `DMEM_E2E_TESTS='leaderboard-loading.spec.ts accounts.spec.ts members.spec.ts'
  python3 tests/smoke/accounts-v1.py`: 빌드된 web/dist와 실제 임시 SQLite,
  합성 이메일 fixture에서 **11 passed**. 새 테스트5개와 실제 계정3개/회원3개다.
  기존 회원 테스트는 실제 승인/철회, 공개 선택 해제,40/20점, 개인정보 경계를 검사한다.
  결과: `target/e2e-logs/accounts-1794197864039175000/`.
- `git diff --check -- web/src/lib/api.ts`: 통과. 명세/테스트/설계 신규 파일도 공백 검사했다.

운영 API/DOM은 조사 시 정상 0명이었으며 로컬 변경을 운영에 배포하지 않았다.
원래 사용자 요청의 실제 네트워크 지연 원인은 확보된 증거만으로 확정할 수 없다.

## 사용자 승인 후 커밋·푸시·운영 배포

2026-11-09 06:09 UTC. 사용자가 커밋·푸시와 가능한 운영 배포를 요청했다.
[릴리스 명세와 검토](../spec/leaderboard-loading-release-v1.md).

- 최초 수정 코드는 이미 원격 main의 `92657d0`에, 원래 재현 테스트/문서는
  `82633bd`에 통합돼 있었다. 실제 `origin/main`의 파일과 커밋 포함 여부를 확인했다.
- 당시 운영은 `b11e064` / `20261109T055832Z-bugfix-b11e064`로, timeout이
  없었다. 그 소스의 변경 전 빌드를 실제 운영 index/JS/CSS SHA-256과 대조해
  모두 일치 확인했다. main에만 있는 다른 기능은 이 배포에 포함하지 않았다.
- 운영 소스에 api.ts의 timeout 메시지/helper와 session/leaderboard 호출만 적용했다.
  릴리스 커밋 **`0f24b781c953fd9c356a6223a01101a57a942c69`**를
  `release/leaderboard-loading-20261109`에 푸시하고 원격 ref 일치를 확인했다.
- 이 고정 소스에서 Svelte check 0 errors/0 warnings, production build 성공,
  실제 임시 SQLite/합성 이메일 회원·계정/로딩 브라우저 **11/11 통과**.
- 배포 release: **`20261109T060904Z-leaderboard-0f24b78`**. 공유 배포 lock 안에서
  예상 base/index/backend/config hash를 검사하고 새 frontend만 atomic 전환했다.
  서버 SHA-256과 PID **804357**, 설정 hash가 배포 전후 동일하다. 서버 재시작이나
  DB migration은 수행하지 않았다. 기존 static 파일과 실제 동영상도 보존했다.
- SQLite backup API로 `/var/backups/my-document-memory/20261109T060904Z-leaderboard-0f24b78.sqlite3`
  백업을 생성하고 integrity_check=ok,0600을 확인했다. rollback 대상은 기존
  `/srv/my-document-memory/releases/20261109T055832Z-bugfix-b11e064`다.
- 실제 HTTPS에서 candidate 공개 파일 **16개 전체 SHA-256 일치**(동영상 전체 포함),
  MP4 Range=206, 웹/API 양쪽 health=200. JS는 `index--tCSRMg5.js`다.
- 실제 도메인에서 배포 번들로 LL-01~07 focused 브라우저 **5/5 통과**.
  지연/오류 입력은 브라우저 안에서만 주입하며 운영 계정/기여 데이터를 변경하지 않았다.
- 주입 없는 실제 `/v1/leaderboard`는200, `items=[]`, `total=0`이고,
  세션 소유 Arise window65/tab156의 실제 DOM에서도 기존 로그인 상태와 빈 순위
  안내를 확인했다. captcha=false. 운영에 임의 회원·점수를 생성하지 않았다.

증거: `.artifacts/leaderboard-publication-20261109/`의 `baseline.json`,
`candidate-{check,build,browser}.log`, `publication-state.json`, `deploy.log`,
`frontend-manifest.json`, `public-verification.json`, `after-state.json`, `live-tests/`.
배포 완료: <https://mydocumentmemory.com/#leaderboard>.
