# CLI 형태 시나리오 (CLI)

상태: 시나리오 정의(문서 우선). 명세 원본은 [`../../spec/cli.md`](../../spec/cli.md)이고 분류 체계는 [`README.md`](README.md)에 있다. 구현과 실행 결과는 없다. 자동 실행은 [`../../../tests/`](../../../tests/README.md)의 하네스가 더블과 제품 대상으로 한다(`CLI-01~03`, `CLI-29~30`의 일부는 호스트·서버가 필요).
ID 접두사: `CLI`(01~33). 호스트 등록 도우미(`dmem install`, `guide`)는 [`../functional-install.md`](../functional-install.md)(`INST`)와 `SNIP`이 다룬다.

## 전제

- 명령 표면·종료 코드·출력 계약은 [`../../spec/cli.md`](../../spec/cli.md) 2~4절이다. 명세가 바뀌면 명세를 먼저 고치고 이 표를 따라 고친다.
- 종료 코드: 0 성공(빈 결과·`created:false` 포함), 1 예기치 않은 오류, 2 사용법·입력 오류, 3 인증 필요, 4 권한·동의·상태 충돌, 5 네트워크·서버·검색 provider 불가, 6 호출 제한, 7 없음·접근 불가.
- 분류 칸은 `형태 · 호스트 · 계층 자동화 · 우선`이다(`-`는 호스트 무관). 모든 실행은 일회용 `HOME`·`XDG_*`·`DMEM_HOME`에서 한다.
- 단계(`R1`·`F`)는 [`../functional-tests.md`](../functional-tests.md) 읽는 법과 같다. 같은 입력의 상세는 추적 칸의 케이스가 가진다.

## 연결

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| CLI-01 | `dmem link` 정상(device flow) | CLI · - · L4 반자동 · P0 | `user_code`와 승인 URL이 출력되고 `--no-browser`가 동작한다. 승인 뒤 토큰은 OS 보안 저장소에만 저장되고 출력·로그에 토큰이 없다 | LINK, SMK-12 |
| CLI-02 | `dmem link` 거부·만료·Ctrl-C | CLI · - · L4 반자동 · P0 | 토큰이 만들어지지 않고 종료 코드가 구분되며 다시 시도할 수 있다 | LINK |
| CLI-03 | `dmem unlink` | CLI · - · L4 자동 · P0 | 로컬 토큰이 지워지고 서버 기기 해지가 요청된다. 이후 `publish`·`outcome`은 종료 3 | LINK, SMK-12 |

## 사용

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| CLI-04 | `--version`, `--help` | CLI · - · L2 자동 · P1 | `cli.md` 2절의 모든 명령 이름이 도움말에 있고 종료 0, 비밀값 없음 | F-CLI-01, SMK-01 |
| CLI-05 | MCP 도구와 1:1 | CLI · - · L2 자동 · P0 | `status`, `recall`, `search`, `expand`, `save`, `import`, `copy`, `publish`, `delete`, `outcome`, `web search`, `web preview`의 `--json` 출력이 대응 MCP 도구의 `structuredContent`와 같은 스키마(`contracts/mcp-tools.v1.json` `result`)를 통과한다 | MCP-03, F-CLI-02 |
| CLI-06 | 잘못된 인자·알 수 없는 서브커맨드 | CLI · - · L2 자동 · P1 | 종료 2와 사용법, API·서버 요청 0 | F-CLI-01 |
| CLI-07 | `dmem save --file`(md, docx) 저장·`--dry-run`·재저장 | CLI · - · L2 자동 · P0 | 비공개 저장, `dry_run`은 변화 0, 재저장은 `created:false`, `--memory`+`--base-version` 충돌은 종료 4 | LIB-01, LIB-03~05 |
| CLI-08 | 익명·로컬 `dmem recall` | CLI · - · L2 자동 · P0 | 힌트 ≤3, 각 항목에 `matched_on`·범위·버전·`locale_match`, `receipt_id` 없음, `untrusted` 프레이밍, 종료 0 | RCL-01~06, RCL-11, SMK-03 |
| CLI-09 | 모르는 URL·양식 | CLI · - · L2 자동 · P0 | 빈 결과와 `reason: no_match`, 종료 0(오류 아님) | RCL-10, SMK-04 |
| CLI-10 | 키워드 어휘 | CLI · - · L2 자동 · P1 | 원격 범위에서는 어휘 밖 키워드를 서버로 보내지 않고 stderr로 알린다. 로컬 `--scope mine`은 어휘 제한이 없다. 목록은 `dmem vocab`으로 확인 | RCL-07, RCL-17 |
| CLI-11 | `dmem expand <id> --level 1\|2 [--version n]` | CLI · - · L2 자동 · P1 | level 1은 L1, level 2는 L2와 같은 `expand` 결과. 허용되지 않는 level은 종료 2, 없는 버전은 종료 7 | MEM-04, LIB-06, VER-02 |
| CLI-12 | `dmem search`·`list` 범위·필터·cursor | CLI · - · L2 자동 · P0 | 결과 필드(`author_handle`·`license`·`version`), `remote` 표시, 로컬 `scope=public`은 `scope_unavailable_local` | SHR-07~08, LIB-07 |
| CLI-13 | `dmem copy`(공개 항목 → 내 라이브러리) | CLI · - · L2 자동 · P0 | 새 비공개 메모리, `derived_from`, 원본 불변, `--copy-mode`가 상한을 넘으면 종료 4(`allowed_modes`) | SHR-11~12, SMK-08 |
| CLI-14 | `dmem publish` 동의 없음·있음 | CLI · - · L2 자동 · P0 | 동의 없음: 종료 4·서버 쓰기 0. 동의 있음: 검수 큐. `--visibility private`은 동의 없이 통과 | SHR-01~03, SMK-11 |
| CLI-15 | 익명 `publish`·`outcome` | CLI · - · L2 자동 · P0 | 종료 3, 서버 쓰기 0. 익명 `copy`는 로컬 라이브러리로 허용 | SHR-18, MCP-20 |
| CLI-16 | `dmem delete` | CLI · - · L2 자동 · P0 | `--yes` 없이 비대화형이면 종료 2, 있으면 삭제 후 `expand`가 종료 7 | LIB-11 |
| CLI-17 | `dmem import`·`web preview` | CLI · - · L2 자동 · P0 | 라이선스별 `copy_policy`, 구조 전용 저장, preview는 저장 없음, `--preview <id>`는 preview 시점 내용 | IMP-01~06, SMK-09 |
| CLI-18 | `dmem web search` | CLI · - · L2 자동 · P1 | provider 없음: 종료 5. fixture provider: 후보 canonical URL, 비밀 질의는 종료 2 | DISC-01~04 |
| CLI-19 | 입력 검증과 민감 URL의 stdin 입력 | CLI · - · L2 자동 · P0 | 쿼리·fragment가 붙은 URL을 positional로 줘도 서버로 쿼리가 나가지 않는다. `recall --stdin --json`은 허용 필드·크기를 검증하고 원 URL·쿼리를 argv·로그·캐시에 남기지 않는다. 잘못된 JSON·알 수 없는 필드는 종료 2이며 입력을 echo하지 않는다 | CORE-04, CORE-19, CORE-22, RCL-17 |
| CLI-20 | 비밀값·센티널 입력 | CLI · - · L5 자동 · P0 | `save`·`search`·`web search`가 종료 2(`secret_detected`)로 거부하고 서버·저장 sink에 0건 | MEM-15, LIB-08, SEC-A01~02 |
| CLI-21 | 오프라인 | CLI · - · L2 자동 · P0 | 로컬 `list`·`recall --scope mine`·`save`는 동작, 서버가 필요한 명령은 종료 5, 익명 공개 recall은 캐시 표시 | RCL-20, SMK-13 |
| CLI-22 | `dmem export` | CLI · - · L2 자동 · P1 | md·html·docx·pptx·json 생성, 상대 경로·기존 파일·링크는 종료 2·불변, 파일 0600 | FMT-14, LIB-12 |
| CLI-23 | `dmem outcome` 인자·멱등 | CLI · - · L2 자동 · P0 | enum 밖 결과, 128자 초과 `receipt_id`, receipt에 없는 `--used`는 종료 2. 같은 결과 재전송은 `duplicate:true`, 타인·만료 receipt는 종료 7 | MCP-17, VER-06 |
| CLI-24 | 저장소·캐시 손상 | CLI · - · L2 자동 · P1 | 크래시 없이 고정 문구로 종료 1(또는 복구), 스택·경로·입력 echo 없음 | LIB-13 |

## 자동화 계약

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| CLI-25 | 비대화형(TTY 없음) | CLI · - · L2 자동 · P0 | 프롬프트 없이 끝나고, 확인이 필요한 동작은 `--yes`가 없으면 종료 2 | F-CLI-10 |
| CLI-26 | 종료 코드 표 | CLI · - · L2 자동 · P0 | 0~7 각 코드를 유발하는 케이스가 표와 일치(빈 결과 0, 사용법 2, 익명 쓰기 3, 동의 없음 4, 서버 불가 5, 429 6, 없음 7) | cli.md 3절 |
| CLI-27 | `--json` | CLI · - · L2 자동 · P0 | stdout에는 JSON 문서 하나, 진행·로그는 stderr, `schema_version: 1`. 오류도 stdout에 `{schema_version, error}` | F-CLI-10 |
| CLI-28 | 색과 TTY | CLI · - · L2 자동 · P2 | `NO_COLOR`가 있거나 TTY가 아니면 ANSI 문자 없음 | F-CLI-10 |
| CLI-29 | 에이전트가 셸 도구로 호출 | CLI · CC CX · L4 자동 · M | 민감할 수 있는 현재 URL은 `recall --stdin --json`으로 전달해 원 URL이 argv·로그에 없고, 출력 JSON을 파싱해 힌트를 untrusted로 보존. 호출률·파싱 성공률 기록 | SNIP-04, RCL-14 |

## 진단·보안

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| CLI-30 | `dmem doctor` 정상·실패 유형 | CLI · CC CX · L4 자동 · P0 | 연결·TLS·인증·동의·캐시·호스트 등록·vocab 점검, 사람용과 `--json`. DNS·TLS·401·토큰 만료·캐시 없음·호스트 미등록·버전 불일치를 구분하고 비밀값이 없다 | INST, F-CLI-12 |
| CLI-31 | `dmem status` | CLI · - · L2 자동 · P0 | `doc_memory_status`와 같은 필드(mode·auth·consent·vocab·search_provider·isolated·data_dir). 웹 계정만 있고 host를 연결하지 않은 사용자는 `anonymous`, 이메일·내부 ID·토큰 없음 | MCP-18 |
| CLI-32 | 토큰·센티널 비노출 | CLI · - · L5 자동 · P0 | argv·환경·로그·크래시 출력에 토큰과 센티널 0 | SMK-16, SEC-H02 |
| CLI-33 | 파일 권한·심볼릭 링크 | CLI · - · L5 자동 · P1 | 설정·데이터·내보내기 파일은 소유자만 접근, 심볼릭 링크를 따라가며 쓰지 않음 | LIB-13, FMT-14 |
