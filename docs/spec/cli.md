# CLI: `dmem` 명령 표면과 자동화 계약

상태: 전체 목표 계약(문서 우선). 실제 Rust CLI 부분집합은 [`runtime-v1.md`](runtime-v1.md)·[`recall-v1.md`](recall-v1.md)·[`memory-community-smoke-v1.md`](memory-community-smoke-v1.md)와 별도 제품 스모크로 검증한다. WAM `cli.md`의 종료 코드·출력 계약·설정 규칙을 승계하고 명령을 문서 메모리 용도로 다시 정의했다. 로컬 stdio MCP 서버는 별도 바이너리 `dmem-mcp`다.
영역 / 테스트 ID 접두사: `CLI` (시나리오 원본: [`../test/tool-forms/cli-form.md`](../test/tool-forms/cli-form.md))
기반: [`core.md`](core.md), [`recall.md`](recall.md), [`library.md`](library.md), [`sharing.md`](sharing.md), [`web-import.md`](web-import.md), [`mcp.md`](mcp.md), [`install.md`](install.md), [`link.md`](link.md)

## 1. 범위

`dmem`은 사람이 직접 쓰거나 에이전트가 셸 도구로 호출하는 명령줄 도구다. MCP 도구와 1:1로 대응하는 명령은 **같은 입력·출력 스키마**를 쓴다(`--json`). 로컬 모드(기본)에서는 계정 없이 내 라이브러리를 쓰고, `DMEM_ENDPOINT`(또는 `--endpoint`)가 있으면 서버 모드다. 로컬 모드는 임베디드 라이브러리 또는 `127.0.0.1` loopback 서버(`DMEM_TOKEN` 필수, [`runtime-v1.md`](runtime-v1.md))로 구현할 수 있다. 사용자에게 보이는 명령·출력·종료 코드는 같다.

## 2. 명령 표면

| 명령 | 역할 | 대응 도구 | 인증 |
|---|---|---|---|
| `dmem recall <url> [keywords…] [--doc-type <id>] [--locale <bcp47>] [--provider <id>] [--kind <k>] [--scope mine\|team\|public\|all] [--limit 1..3] [--json]` 또는 `--stdin` | URL + 양식으로 L1 힌트 ≤3. `--stdin`은 같은 입력 필드의 JSON 객체 하나를 읽는다 | `doc_memory_recall` | 익명 가능 |
| `dmem search [query] [--scope …] [--kind …] [--doc-type …] [--locale …] [--provider …] [--license <id>] [--limit ≤20] [--cursor <c>] [--json]` | 내 라이브러리·팀·공개 카탈로그 탐색 | `doc_memory_search` | 익명 가능(공개) |
| `dmem list [필터…]` | `search --scope mine`의 별칭 | `doc_memory_search` | 로컬 |
| `dmem expand <memory_id> [--version <n>] [--level 1\|2] [--cursor <c>] [--json]` | 미리보기: L1 또는 L2 | `doc_memory_expand` | 보이는 범위 |
| `dmem save --kind <k> --title <t> --doc-type <id> --locale <bcp47> [--provider <id>] [--variant <v>] [--url-pattern <p>]… [--keyword <w>]… [--summary <텍스트>] [--key-point <텍스트>]… (--file <경로> \| --stdin --format markdown\|text\|html\|stddoc \| --from-preview <id>) [--memory <id> --base-version <n>] [--dry-run] [--yes] [--json]` | 내 라이브러리에 저장·수정 | `doc_memory_save` | 로컬/계정 |
| `dmem web search <query> [--locale …] [--doc-type …] [--provider …] [--limit ≤10] [--json]` | 웹 후보 검색 | `doc_memory_web_search` | 익명 |
| `dmem web preview <url> [--json]` | 저장 없이 미리보기 | `doc_memory_web_preview` | 익명 |
| `dmem import (<url> \| --preview <id>) --as template\|reference [--title <t>] [--doc-type …] [--locale …] [--provider …] [--copy-mode structure_only\|quote_limited\|full] [--license <id>] [--keyword <w>]… [--json]` | 웹 문서를 내 라이브러리로 가져오기 | `doc_memory_import` | 로컬/계정 |
| `dmem copy <memory_id> [--version <n>] [--title <t>] [--copy-mode …] [--json]` | 다른 사람(또는 내) 메모리를 내 라이브러리로 복사 | `doc_memory_copy` | 로컬/계정 |
| `dmem publish <memory_id> --visibility team\|public\|private [--version <n>] [--license <id>] [--consent] [--json]` | 게시·게시 취소 | `doc_memory_publish` | 연결 + 동의 |
| `dmem delete <memory_id> --yes [--json]` | 삭제 | `doc_memory_delete` | 소유자 |
| `dmem outcome <receipt_id> success\|partial\|failed [--used <memory_id>@<n>]… [--json]` | 사용 결과 보고 | `doc_memory_outcome` | 연결 + receipt 소유 |
| `dmem export <memory_id> --format md\|html\|docx\|pptx\|json --out <절대경로>` | 파일로 내보내기(CLI 전용) | 없음 | 로컬 |
| `dmem status [--json]` | 모드, endpoint, auth, 동의, vocab 버전, 검색 provider, 데이터 디렉터리 | `doc_memory_status` | 익명 |
| `dmem vocab [--json]` | doc_types·locales·providers·licenses·keywords 어휘 | 없음 | 익명 |
| `dmem leaderboard`, `dmem rank`, `dmem usage` | 공개 순위, 내 점수, 내 quota·사용량 | HTTP API | 익명 / 연결 |
| `dmem link [--no-browser]`, `dmem unlink [--local-only]` | 기기 연결(device flow)과 해지 | `/v1/link/*` ([`link.md`](link.md)) | 웹 계정 승인 |
| `dmem cache status`, `dmem cache clear` | 익명 recall 캐시 | 로컬 | 로컬 |
| `dmem doctor [--json]` | 연결·TLS·인증·동의·캐시·호스트 등록·vocab 점검 | 없음 | 익명 |
| `dmem install <host> [--local] [--scope <s>] [--dry-run]`, `dmem uninstall <host>` | `claude-code`, `codex`, `arise` 등록·제거 | 호스트 CLI/설정 ([`install.md`](install.md)) | 없음 |
| `dmem guide print [--host codex\|claude-code\|arise] [--write]` | 에이전트 지침 스니펫. `--write`는 마커 블록만 갱신 | 없음 | 없음 |
| `dmem browser-mcp --browser-mcp <절대경로> --browser-arg=--mcp-server` | 호스트 브라우저 어댑터 | `doc_memory_clip_current_tab` + browser 도구 | 로컬 |
| `dmem --version`, `dmem --help` | 버전, 도움말 | 없음 | 없음 |

전역 옵션: `--endpoint <url>`, `--home <dir>`(`DMEM_HOME`과 동일), `--json`, `--yes`. `dmem-mcp`는 로컬 stdio MCP 서버(도구 12개)이며 `DMEM_*` 설정을 `dmem`과 공유한다.

## 3. 종료 코드

| 코드 | 의미 | 대표 오류 코드 |
|---|---|---|
| 0 | 성공(빈 결과·`created:false` 포함) | — |
| 1 | 예기치 않은 오류 | `internal` |
| 2 | 사용법·입력 오류 | `invalid_input`, `url_rejected`, `invalid_form`, `secret_detected`, `payload_too_large`, `unsupported_format`, `extract_empty`, `fetch_blocked` |
| 3 | 인증 필요 | `auth_required` |
| 4 | 권한·동의·상태 충돌 | `consent_required`, `scope_required`, `license_forbids`, `version_conflict` |
| 5 | 네트워크·서버·검색 provider 불가 | `server_unavailable`, `fetch_failed`, `search_unavailable` |
| 6 | 호출 제한 | `rate_limited` |
| 7 | 없음 또는 접근 불가(존재 여부를 숨긴다) | `not_found` |

오류 코드와 종료 코드의 대응은 [`core.md`](core.md) 7절이 원본이다.

## 4. 출력 계약

- 사람용 출력은 stdout, 진행·진단은 stderr다. `--json`이면 성공과 실패 모두 stdout에 `schema_version: 1`인 JSON 문서 **하나**를 낸다. 실패는 `error {code, message, reason?, trace_id?, retry_after_seconds?, allowed_modes?}`다.
- 성공 JSON은 대응 MCP 도구의 `structuredContent`와 같은 스키마다(`CLI-05`).
- recall·search·expand·web 결과는 `untrusted: true`와 고정 `framing`을 가진다.
- 출력·오류·로그에 토큰, 키, 센티널, 원본 URL의 쿼리, 입력 본문이 없다(입력 에코 금지).
- `NO_COLOR`가 있거나 TTY가 아니면 ANSI 색을 쓰지 않는다.
- TTY가 아니면 프롬프트를 띄우지 않는다. 확인이 필요한 동작(`save`의 덮어쓰기성 갱신, `delete`)은 `--yes`가 없으면 종료 코드 2다.

## 5. 입력 규칙

- **`recall`**: URL은 클라이언트가 canonical pattern으로 바꾼 뒤에만 쓴다([`core.md`](core.md)). 키워드는 NFKC·소문자 정규화 후 중복 제거한다. 원격 범위(`team`, `public`)가 있으면 공개 어휘에 있는 것만 보내고 어휘 밖 항목은 서버로 보내지 않고 stderr로 알린다. 로컬 전용(`--scope mine`)은 어휘 제한이 없다. 자유 텍스트 `task_hint`는 옵션이 아니다.
- **민감한 URL**은 `dmem recall --stdin --json`을 쓴다. stdin은 `url`, `doc_type`, `locale`, `provider`, `keywords`, `kind`, `scope`, `limit`만 허용하는 JSON 객체 하나다. 잘못된 JSON·알 수 없는 필드·크기 초과는 종료 코드 2이며 본문을 echo하지 않는다. 원 URL과 stdin 본문은 process args, stdout/stderr, 로그, 캐시, 텔레메트리에 복사하지 않는다.
- **`save --stdin`**은 본문 바이트를 `--format`으로 해석한다(`stddoc`는 StandardDoc JSON). `--file`은 CLI 전용이며 MCP에는 대응 입력이 없다.
- **`import`·`web preview`**의 URL은 사용자가 직접 입력한 값이다. query는 요청에만 쓰고 저장·로그하지 않는다([`core.md`](core.md) 4절).
- 허용되지 않는 `--level`·`--visibility`·`outcome` 값은 종료 코드 2이며 API 요청을 보내지 않는다. `receipt_id`는 128자 이하다.

## 6. 설정, 데이터, 환경 변수

| 항목 | 규칙 |
|---|---|
| 데이터 디렉터리 | `DMEM_HOME`(없으면 OS 설정 경로). `HOME`·`XDG_*`를 존중해 격리 테스트가 가능해야 한다. 구조는 [`library.md`](library.md) 7절 |
| 캐시 | macOS `~/Library/Caches/dmem`, Linux `$XDG_CACHE_HOME/dmem`, Windows `%LOCALAPPDATA%\dmem` |
| 환경 변수 | `DMEM_HOME`, `DMEM_ENDPOINT`, `DMEM_SEARCH_PROVIDER`(`none`\|`http:<url>`\|`fixture:<url>`), `DMEM_DISABLED=1`(메모리 호출 건너뜀), `DMEM_TELEMETRY=off`, `DMEM_ISOLATED=1`(테스트 전용, [`core.md`](core.md) 9절), `DMEM_TOKEN`(개발용 override) |
| 토큰 | OS 보안 저장소(macOS Keychain, Windows Credential Manager, Linux Secret Service)에만 둔다. 설정 파일에는 비밀이 아닌 값만 둔다. 프로세스 인자·환경변수·로그·평문 파일에 두지 않는다 |
| 파일 | 소유자만 읽고 쓴다(0700/0600). 심볼릭 링크를 따라가며 쓰지 않는다 |
| 테스트 전용 변수 | `DMEM_TEST_*`는 [`../test/environment.md`](../test/environment.md)에만 정의하며 제품 동작에는 필요 없다 |

## 7. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-CLI-01 | 명령 표면 | 2절의 명령이 도움말에 모두 나오고 알 수 없는 입력은 종료 코드 2 | CLI-04, CLI-06 |
| F-CLI-02 | MCP 도구와 동등 | 같은 입력·출력 스키마, recall은 같은 힌트를 같은 순서로 | CLI-05, CLI-31, MCPF-09, RCL-14 |
| F-CLI-03 | 저장·가져오기·복사 | 로컬 모드에서 계정 없이 동작하고 멱등이다 | CLI-07, CLI-13, CLI-17 |
| F-CLI-04 | 탐색 | recall·search·expand의 필터·범위·cursor | CLI-08~12 |
| F-CLI-05 | 익명과 연결 구분 | 익명 `publish`·`outcome`은 종료 코드 3, 쓰기 0건 | CLI-14~15, CLI-23 |
| F-CLI-06 | 삭제·내보내기 | `--yes` 필요, 덮어쓰기 거부 | CLI-16, CLI-22 |
| F-CLI-07 | 웹 검색·미리보기 | provider 없으면 종료 5, fixture에서 정상 | CLI-17~18 |
| F-CLI-08 | 입력 보호 | 민감 URL stdin, 비밀값 거부, 에코 금지 | CLI-19~20 |
| F-CLI-09 | 오프라인과 손상 복구 | 로컬은 계속 동작, 서버 필요 명령은 5 | CLI-21, CLI-24 |
| F-CLI-10 | 자동화 계약 | 종료 코드 0~7, `--json`, 비대화형, 색 규칙 | CLI-25~28 |
| F-CLI-11 | 에이전트의 셸 호출 | `recall --stdin --json`을 파싱하고 untrusted를 보존 | CLI-29 |
| F-CLI-12 | 진단 | `doctor`·`status`가 원인을 구분하고 비밀값이 없다 | CLI-30~31 |
| F-CLI-13 | 비밀값과 파일 권한 | 토큰·센티널이 인자·환경·로그에 없고 파일은 소유자만 접근 | CLI-32~33 |
| F-CLI-14 | 기기 연결 | device flow, OS 보안 저장소 | CLI-01~03 |
| F-CLI-15 | instruction 스니펫 | `guide print`가 호출 시점 규칙을 담고 `--write`는 마커 블록만 갱신 | SNIP-01~04 |

## 8. 열린 질문

1. 단일 바이너리(`dmem`에 `mcp` 서브커맨드) 배포 여부. 이 문서는 별도 `dmem-mcp`를 기준으로 쓴다.
2. 헤드리스 Linux·컨테이너처럼 Secret Service가 없을 때 토큰 저장 방식. 평문 파일을 조용히 만들지 않는다는 원칙만 정했다.
3. `dmem update` 명령을 둘지 여부.
4. 로컬 라이브러리의 저장 형식(SQLite 또는 JSON 스냅샷)은 구현 선택이며 계약은 파일 권한·원자성·잠금만 요구한다.
