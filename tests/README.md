# tests: 계약 테스트·스모크·하네스

상태: 구현됨. `run_all.py`의 기본 대상은 참조 구현인 **테스트 더블**이다. 실제 Rust 제품과 `runtime-v1.py`·`recall-v1.py`·`community-v1.py` 전용 스모크도 있으며 [포팅 완료 검증](../docs/test/wam-port-completion-v1.md)에 결과를 구분해 기록한다. 하네스는 Python 3 표준 라이브러리만 쓴다(설치 단계 없음). 현재 규모: 케이스 238개(R1·F 행 203개 전부 구현 또는 사유와 함께 `coverage.json`), 하네스 자체 검사 138개, 변이 18개. 케이스 ID와 입력·기대 결과의 원본은 [`../docs/test/`](../docs/test/README.md)이고 **테스트는 새 ID를 만들지 않는다.** 이 디렉터리의 코드는 구현 언어와 무관한 **블랙박스**(CLI·stdio MCP·HTTP·브라우저)로만 대상을 다룬다.

## 실행

```
python3 -B -m unittest discover -s tests/lib/selftest -p "test_*.py"      # 하네스 자체 검사(HARN-01,03,04,05,07,08,09,12,14,15,16,17; 브라우저·네트워크 없음, 수십 초)
python3 -B tests/smoke/run_all.py --suite smoke                            # CLI·MCP 스모크(SMK-*, CLI-04, 로컬 스모크): docs/test/local-smoke.md
python3 -B tests/smoke/run_all.py --suite contract                         # 계약 케이스 전량(CORE·FORM·FMT·MEM·RCL·LIB·SHR·DISC·IMP·VER·TPL·PRIV·MCP·CLI·SEC-A04)
python3 -B tests/smoke/run_all.py --ids 'RCL-*,SHR-*' --suite contract     # 일부만
python3 -B tests/env/mutation_check.py                                     # 변이 검사(HARN-02): 일부러 깨진 더블 18종을 지정 케이스가 잡는지. --repeat 2: 재현성(HARN-13)
python3 -B tests/smoke/arise_smoke.py                                      # Arise 브라우저 환경 스모크(설치된 Arise 필요)
PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all                   # 명세→테스트 ID 추적(HARN-11)
PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace --list                 # 코드→문서 추적과 R1·F 행의 구현·사유 확인(HARN-10)
PYTHONPATH=tests/lib python3 -B -m dmtest.porttrace --require-upstream    # WAM 원본 전체 처분·대상 존재(HARN-17; 상위 WAM 필요)
cargo test --workspace
cargo build --workspace --examples
python3 -B tests/smoke/runtime-v1.py                                    # 실제 Rust CLI/MCP·HTTP·영속성
python3 -I tests/smoke/recall-v1.py                                     # 실제 Rust recall CLI/MCP/HTTP
python3 -B tests/smoke/community-v1.py                                  # 실제 비공개 저장·공개 복사·기여·검수
python3 -B tests/smoke/web-memory-v1.py --browser --arise                 # 실제 URL intake·CLI/MCP·소유 Arise 탭·웹 입력
```

러너는 케이스마다 새 일회용 세계(`HOME`·`XDG_*`·`DMEM_HOME`)를 만들고 `DMEM_CASE_TIMEOUT`초(기본 90) 안에 끝나지 않으면 자식 프로세스 그룹을 종료하고 `FAIL(timeout)`으로 기록한다. 판정을 한 번도 평가하지 않은 케이스는 `FAIL(vacuous)`다. 새 케이스 작성법은 [`smoke/cases/README.md`](smoke/cases/README.md).

`run_all.py --target product` 어댑터는 전체 `doc_memory_*` 계약을 구현하는 대상을 위한 것이다. 현재 Rust 제품의 `document_*`·CLI 명령에 직접 연결하는 예제가 아니다. 현재 제품은 위의 전용 스모크를 실행한다. 상위 WAM이 없는 checkout에서 `porttrace`의 원본 대조는 명시적으로 미실행이며 `--require-upstream`은 실패한다.

증거는 `target/e2e-logs/<suite>/<run-id>/`(git 무시)에 `meta.json`, `cases.jsonl`, `trace.jsonl`, `sinks/`, `summary.md`로 남는다([`../docs/test/README.md`](../docs/test/README.md) 5절).

## 구성

| 경로 | 역할 |
|---|---|
| `lib/dmtest/` | 하네스 라이브러리(아래 API). 구현에 의존하지 않는다 |
| `lib/selftest/` | 하네스 라이브러리와 더블 구성요소의 단위 테스트 138개(스키마 검증기, 센티널, 8-sink 스윕, 러너·프로필 게이트·타임아웃, 프로세스, 대상 어댑터, 빌더, 계약 정적 검사, 포팅 목록, 더블의 URL·양식·순위·형식·fetch) |
| `env/fixture-sites/` | loopback fixture 웹 서버([`../docs/test/fixtures.md`](../docs/test/fixtures.md) 4절) |
| `env/dmem-double/` | **테스트 더블**: 계약을 실행 가능하게 만든 참조 구현. 제품이 아니다(`dmem`, `dmem-mcp` 실행 파일 포함) |
| `fixtures/` | 라이브러리·공유 카탈로그 데이터, 파일 빌더, 골든 파일 |
| `smoke/` | `run_all.py`(러너), `cases/`(케이스 구현: `core form fmt mem recall lib shr disc imp ver tpl priv mcp mcp_b cli cli_b cli_exit sec smoke`), `arise_smoke.py`(Arise 환경 21개 점검) |
| `sentinels.json` | 센티널 말뭉치(시드 `dmem-sentinels-v1`, 한 곳에서만 정의) |
| `coverage.json` | 구현하지 않은 케이스의 상태와 사유: `skip`(이 하네스로 자동화 불가), `product-only`, `L0`, `external`(다른 하네스가 검증), `covered`(구현된 기능 케이스와 같은 점검). 조용한 누락 금지(`dmtest.codetrace`) |
| `env/mutation_check.py` | 변이 18종 × 지정 케이스 검사(HARN-02, HARN-13) |

## 대상 어댑터

하네스는 환경 변수로 대상을 고른다. 같은 케이스가 더블과 제품에서 돌아야 한다.

| 변수 | 의미 |
|---|---|
| `DMEM_TARGET` | `double`(기본) 또는 `product` |
| `DMEM_BIN`, `DMEM_MCP_BIN` | `product`일 때 `dmem`·`dmem-mcp` 절대 경로. `double`이면 `env/dmem-double/dmem`, `dmem-mcp` |
| `DMEM_SERVER_CMD` | (선택) 서버가 필요한 제품을 띄우는 명령 템플릿. 자리표시자 `{port}`, `{data_dir}`, `{token}`. 하네스가 임의 빈 포트로 띄우고 `DMEM_ENDPOINT`·`DMEM_TOKEN`을 자식에게 준다 |
| `DMEM_PROFILE` | `full`(기본) 또는 `runtime-v1`. `runtime-v1`이면 `단계 F` 케이스는 `SKIP(profile)` + 사유 |

하네스가 실행마다 자식 프로세스에 주는 환경: 일회용 `HOME`·`XDG_CONFIG_HOME`·`XDG_CACHE_HOME`·`XDG_DATA_HOME`·`TMPDIR`(짧은 `/tmp/dmem-*`), `DMEM_HOME`, `DMEM_ISOLATED=1`, 필요 시 `DMEM_SEARCH_PROVIDER`, `DMEM_ENDPOINT`·`DMEM_TOKEN`, `DMEM_TELEMETRY=off`.

**더블 전용 테스트 변수**(제품에는 필요 없다): `DMEM_TEST_IDENTITY`(`local`\|`anon`\|`alice`\|`bob`\|`carol`), `DMEM_TEST_SERVER_STATE`(다중 사용자 서버 상태 파일 경로. 있으면 더블은 서버 모드로 동작), `DMEM_TEST_SHARED`(초기 공유 카탈로그 JSON), `DMEM_TEST_REQUEST_LOG`(원격 연산 로그 JSONL 경로: `{op, write, body_keys}`), `DMEM_TEST_RESOLVE`(`host=ip1,ip2;…` 가짜 DNS), `DMEM_TEST_CLOCK_OFFSET`(초), `DMEM_TEST_SERVER_DOWN`(1이면 서버 필요 연산이 `server_unavailable`, 로컬 연산은 계속), `DMEM_DOUBLE_MUTATION`(변이 이름, 아래). 하네스 변수: `DMEM_CASE_TIMEOUT`(케이스 제한 시간, 초).

## 하네스 라이브러리 API (`lib/dmtest/`)

| 모듈 | 공개 API(시그니처 고정) |
|---|---|
| `evidence` | `RunDir(suite, run_id=None)`: `.path`, `.write_meta(dict)`, `.case(id, verdict, **fields)`(`cases.jsonl`), `.trace(event, **fields)`, `.sink(name, bytes)`, `.write_summary()` |
| `procs` | `isolated_env(tmp, **extra) -> dict`, `Owned(cmd, env, cwd=None, stdin=None)`: `.start()`, `.stop(timeout)`(프로세스 그룹만), `.wait(timeout)`, `.stdout`, `.stderr`. `free_port() -> int`, `leftover_check(before, after)` |
| `sentinels` | `generate(seed="dmem-sentinels-v1") -> dict`, `load() -> Sentinels`(`.value(family, n)`, `.ids()`), `scan(paths_or_bytes, sentinels, variants=True) -> [Finding(sentinel_id, path, variant)]`(값은 반환·출력하지 않는다) |
| `schema` | `ContractStore(contracts_dir)`: `.schema(file, pointer)`, `.tool(name)`; `validate(instance, schema, store) -> [str]`(지원: `type`(배열 포함), `enum`, `const`, `properties`, `required`, `additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`, `maxLength`, `minimum`, `maximum`, `pattern`, `oneOf`, `anyOf`, `$ref`(`#/…`와 `file.json#/…`)). 오류 문자열에 인스턴스 값을 넣지 않는다 |
| `cli` | `Cli(argv0, env)`: `.run(args, stdin=None, timeout=30) -> Result(exit, stdout, stderr, json, seconds)`. `--json` 출력이 JSON 문서 하나가 아니면 `json=None` |
| `mcpclient` | `McpSession(cmd, env)`: `.initialize(version="2025-11-25")`, `.list_tools()`, `.call(name, args) -> McpResult(is_error, text, structured, raw)`, `.send_raw(bytes)`, `.stdout_extra_bytes`, `.close()`. 프레임 한도·취소·ping 도우미 |
| `fixture_http` | `FixtureServer(log_dir)`: `.start() -> base_url`, `.stop()`, `.log() -> [dict]`, `.reset()` |
| `builders` | `docx(...)`, `pptx(...)`, `pdf(...)`, `evil_docx(kind)`, `zipbomb_docx()`, `tpl01()`, `deck5()` → bytes. 같은 입력이면 같은 bytes |
| `target` | `Target.from_env()`: `.cli(identity="local")`, `.mcp(identity="local")`, `.profile`, `.is_double`, `.server_state_path`, `.request_log()`, `.load_fixture_library(name)`(더블: 직접 로드, 제품: 공개 CLI로 저장) |
| `runner` | `@case(id, profile="R1"\|"F", layer="L2", needs=())` 데코레이터, `Ctx`(아래), `run(ids, profile, suite, strict)` |
| `doctrace` | (구현됨) 명세→테스트 ID 추적. `codetrace.py`: 코드가 쓰는 ID가 문서에 정의됐는지(`HARN-10`) |

`Ctx`(케이스 인자): `.cli(args, stdin=None, identity="local", env=None)`, `.mcp(identity="local")`, `.fixtures`(웹 fixture 서버 `.url`, `.log()`), `.load_library("rcl-lib"|"shr-cat")`, `.home`(이번 케이스의 `DMEM_HOME`), `.sentinels`, `.scan_sinks(extra_paths=())`(홈·로그·캐시·요청 로그·산출물), `.request_log()`, `.expect(cond, msg)`(실패 누적), `.skip(reason)`(명시적 건너뛰기, 사유 필수), `.schema_ok(instance, ref)`, `.profile`, `.is_double`.

## 케이스 구현 규약

- 케이스는 `smoke/cases/<영역>.py`에 `@case("CORE-02", profile="R1", layer="L2")`로 등록한다. ID는 [`../docs/test/`](../docs/test/README.md)에 정의된 것만 쓴다(`HARN-10`이 검사).
- 한 케이스는 일회용 `DMEM_HOME`과 새 프로세스에서 시작한다. 케이스 사이에 상태를 공유하지 않는다.
- 실패 메시지에 입력 센티널 값을 넣지 않는다(sentinel id만).
- **모든 판정은 항상 평가한다.** `if x in hints: expect(...)`처럼 대상이 없을 때 조용히 건너뛰는 형태, `or True` 같은 항진식, 죽은 `if False` 분기를 쓰지 않는다. 대상이 없으면 그것이 실패다(`ctx.expect(x is not None, …)`). 러너는 판정이 0번 평가된 케이스를 `FAIL(vacuous)`로 처리한다.
- 같은 scope(`URL 패턴·kind·provider·doc_type·locale·region·variant`)에 다른 내용을 `memory_id` 없이 저장하면 `invalid_input scope_conflict`다. 서로 다른 메모리가 필요하면 `locale`·`variant`를 달리한다. recall 힌트는 최대 3개이므로 대상이 3위 안에 들게 라이브러리를 작게 만든다.
- 자동화하지 않는 ID는 `coverage.json`에 상태 + 사유(`skip`, `product-only`, `L0`, `external`, `covered`)로 남긴다. 정의된 ID가 `coverage.json`에도 케이스에도 없으면 `HARN-10` 실패다.
- 판정 근거는 대상 응답과 **독립 oracle**(fixture 요청 로그, 파일 시스템, 센티널 스캔)이다. "대상이 성공했다고 말함"은 증거가 아니다.

## 변이 (HARN-02)

`env/mutation_check.py`는 `DMEM_DOUBLE_MUTATION=<이름>`으로 일부러 깨뜨린 더블에 케이스를 돌려 **지정한 케이스가 실패해야** 통과한다. 깨끗한 더블은 전부 통과해야 한다(양성·음성 대조).

| 변이 | 깨뜨리는 동작 | 반드시 실패해야 하는 케이스 |
|---|---|---|
| `leak_query` | 정규화가 쿼리를 남김 | CORE-04, SEC-A04 |
| `capability_leak` | Google 문서 ID를 저장 | CORE-19, SEC-A04 |
| `echo_input` | 오류가 입력을 되돌려 줌 | CORE-23, SEC-A04 |
| `four_hints` | recall이 4개 반환 | RCL-08, MCP-09 |
| `no_untrusted` | `untrusted`·`framing` 누락 | RCL-11 |
| `route_before_locale` | 순위 튜플에서 route가 locale보다 앞 | RCL-04 |
| `nondeterministic_rank` | 동점을 무작위로 정렬 | RCL-09 |
| `l2_in_recall` | recall 힌트에 L2 포함 | MEM-04, RCL-11 |
| `partial_secret_save` | 비밀값을 가려서 저장 | MEM-15, LIB-08, SEC-A04 |
| `structure_keeps_prose` | 구조 전용인데 본문 보존 | MEM-14, IMP-05 |
| `license_ignored` | 미확인 라이선스에 full 복사 허용 | SHR-12, IMP-06 |
| `copy_mutates_origin` | 복사가 원본 `updated_at`을 바꿈 | SHR-11 |
| `cross_tenant_leak` | 타인 비공개가 검색·조회됨 | SHR-16, RCL-13 |
| `no_consent_write` | 동의 없이 publish를 기록 | SHR-02 |
| `ssrf_no_guard` | 가져오기 방어(해석된 주소·리다이렉트 검사)가 사설 주소를 허용 | IMP-10, IMP-11 |
| `overwrite_export` | export가 기존 파일을 덮어씀 | FMT-14 |
| `stdout_noise` | MCP stdout에 배너 출력 | MCP-06 |
| `exit_code_wrong` | `not_found`의 종료 코드가 7이 아님 | CLI-26 |
