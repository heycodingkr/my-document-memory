# 일반 개인 가입·익명 열람·회원 기여 검증

검증일: 2026-11-09. 계약: [계정·공개 기여](../spec/accounts-community-v1.md).

- 개인 이메일 최초 인증으로 계정을 만들 수 있으며 조직·관리자 이메일 허용 목록은 적용되지 않는다.
- 공개 메모리 목록·검색·전체 구조 미리보기는 로그인 없이 접근한다. 공개 응답에는 계정 이메일이나 owner 필드가 없다.
- 익명, 잘못된 인증, 관리자 전용 토큰, 가입되지 않은 local owner는 내 기여 조회·제출·검수 조회·철회에 401을 받는다. 회원 세션의 쓰기에는 Origin·CSRF도 필요하다.
- 회원에 매핑된 Bearer는 CLI/MCP 기여와 출처 보존 동작을 유지한다. 브라우저의 로컬 라이브러리 연결에서도 개인 가입과 이메일 로그인 진입이 가능하다.
- 로그인 전 기여 요청 진입은 이메일 인증 후 내 기여 화면으로 돌아온다. `pending`, `approved`, `rejected`, `withdrawn` 상태와 요청/갱신 시각을 저장하고 새로고침 후에도 유지한다. 공개 목록에는 승인된 요청만 노출한다.
- 내 기여 상태 필터·건수·명시적 갱신과 모바일 화면을 검증한다. 공개 화면은 1440/390/320px에서 가로 넘침을 확인한다.

실행 명령:

```sh
cargo test -p dmem-server --tests
cd web && pnpm check && pnpm build
cd ..
cargo build -p dmem-server --example accounts_fixture
python3 tests/smoke/accounts-v1.py
DMEM_E2E_TESTS='workspace.spec.ts' python3 tests/smoke/accounts-v1.py
cargo build -p dmem-cli -p dmem-mcp
python3 tests/smoke/community-v1.py
```

이메일 인증은 격리된 임시 SQLite DB와 합성 메일 캡처를 사용한다. 실제 개인 이메일 발송은 검증하지 않았으며, 운영 배포 결과는 아래에 별도로 기록한다. 브라우저 스크린샷은 각 실행의 `target/e2e-logs/accounts-*`에 저장한다.

편집기 회귀는 새 fixture로 따로 실행한다. 대량 검수 큐 fixture와 공개 기여가 누적된 DB에서 함께 실행하면 기본 목록의 20개 제한 때문에 편집기 테스트가 기대하는 seed 양식이 첫 페이지에서 밀려난다.

원본 작업 폴더 검증: 서버 테스트 64개 통과, 계정·공개 열람·기여·검수 브라우저 테스트 15개 통과, 별도 편집기 회귀 3개 통과. Svelte 검사 오류/경고 0개, 웹 빌드와 CLI/MCP community smoke 통과. 기여 내역의 모바일 스크린샷을 직접 확인하고 날짜와 동작 버튼이 한 줄의 좁은 영역을 나눠 쓰지 않도록 배치를 조정했다.


## 배포본 검증 (2026-11-09)

현재 운영 중인 `20261109T034500Z-admin-starters` 릴리스의 기준 커밋 `2a693b5`에서 별도 작업 트리를 만들고 가입·익명 열람·회원 기여 권한 및 상태 화면 변경을 반영했다. 운영 소스와 커밋 사이의 차이 8개를 확인해 관리자 allowlist 설정의 중복 선언과 호출 형식을 운영 코드에 맞췄다. 기존 관리자 회귀 테스트도 새 설정 입력 형식으로 유지했다.

배포본 검증 결과: `cargo test --workspace --locked` 94개 통과, `pnpm --dir web check` 오류/경고 0개, 웹 빌드 통과. 격리된 계정·공개 열람·기여·관리자 브라우저 테스트 14개 및 별도 문서 편집 회귀 3개가 통과했다. 원본 작업 폴더에서 검증한 별도 진행 기능은 이 배포본의 테스트 수에 포함하지 않는다. 운영 개인 이메일 발송은 검증 요청을 하지 않았다.


## 운영 배포 결과 (2026-11-09)

- 소스 커밋: `b0a27e51a654e17c7c514255c438c3907edf2be6`, GitHub `main` 푸시 확인.
- 운영 릴리스: `/srv/my-document-memory/releases/20261109T050859Z-18544`. 기존 배포 스크립트의 호스트 배포 잠금 아래 Rust 1.95.0 release 빌드와 서비스 전환을 완료했다.
- SQLite 백업: `/var/backups/my-document-memory/20261109T050848Z-personal-public.sqlite3`, 권한 0600, 무결성 검사 통과. 이전 릴리스는 `20261109T034500Z-admin-starters`다.
- HTTPS 웹·API 양쪽에서 익명 공개 목록·상세·리더보드를 확인했다. 이메일 가입 기능이 켜져 있으며, 익명 및 가입되지 않은 local Bearer의 기여 조회·제출·검수 조회·철회는 모두 401이다.
- 운영 HTML과 연결된 JS/CSS 세 파일의 SHA-256이 로컬에서 브라우저 검증한 배포 빌드와 일치한다.
- `public-api-v1.py` 9개 그룹 및 `deployed-v1.py` 4개 그룹 통과. 서비스 active, DB quick_check 통과. 기존 56개 record의 owner/kind/version/payload 해시가 모두 일치하고 계정 1개·기여 0개도 유지됐다. 비공개 서버 설정 파일 해시도 동일하다.
- 배포·권한 검증 증거: 원본 작업 폴더의 `.artifacts/deploy/personal-public-{api,web,policy}-live.json`. 운영에서 개인에게 인증 메일을 보내거나 기여 데이터를 생성하지 않았다.
