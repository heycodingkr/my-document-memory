# 케이스 모듈 작성 안내

`tests/smoke/cases/*.py`는 [`docs/test/functional-tests.md`](../../../docs/test/functional-tests.md)(와 `tool-forms/`·`host-smoke.md` 등)의 표 행 하나를 함수 하나로 옮긴 블랙박스 케이스다. 모듈 이름은 아무거나 되고(`util.py` 제외) 러너가 `cases/` 아래를 모두 불러온다. 케이스는 대상(더블 또는 제품)의 **CLI·stdio MCP 바이너리만** 거친다. 더블 내부 모듈을 import하지 않는다.

## 1. 뼈대

```python
from dmtest.runner import case
from .util import recall, reject, save_md

@case("RCL-01", "R1", needs=())          # 단계: R1 | F | L0, needs: "server" | "hooks" | "fixtures"
def rcl_01(ctx):
    r = recall(ctx, "docs.google.com/document/d/:id/edit", doc_type="resume")
    ctx.expect(r.exit == 0 and r.json["hints"] == [], "empty library must return no hints")
```

- 케이스 ID는 `docs/test`에 정의된 ID뿐이다(`dmtest.codetrace`가 검사). 단계(R1/F/L0)는 표의 `단계` 열을 따른다.
- `ctx.expect(조건, 실패 메시지)`는 모든 판정에 쓴다. **모든 판정은 항상 평가되어야 한다.** `if x in hints: expect(...)`처럼 대상이 없을 때 조용히 건너뛰는 형태는 쓰지 않는다. 대상이 없으면 그것이 실패다: `ctx.expect(x is not None, "…")`. 판정이 한 번도 평가되지 않은 케이스는 러너가 `FAIL(vacuous)`로 처리한다.
- `ctx.skip("사유")`는 사유와 함께 건너뛴다. `needs=("hooks",)` 케이스는 제품 대상에서 자동으로 `SKIP(needs)`다.
- 비밀·센티널 값은 메시지에 쓰지 않는다. 메시지는 증거 파일에 남는다.

## 2. 도구

| API | 용도 |
|---|---|
| `ctx.cli(identity="local").json(args, stdin=None)` | CLI를 `--json`으로 실행한다. `Result.exit`·`.json`·`.code`(고정 오류 코드)·`.stdout`·`.stderr`. `.run(args)`는 `--json` 없이 |
| `ctx.mcp(identity="local")` | stdio MCP 세션(초기화됨). `with ctx.mcp() as m: r = m.call("doc_memory_save", {...})` → `McpResult.is_error`·`.structured`·`.code`·`.text`. `m.list_tools()`, `m.rpc(...)`, `m.send_raw(bytes)`, `m.noise_bytes` |
| `ctx.load_library("rcl-lib", identity="alice")` | 고정 라이브러리(`tests/fixtures/*.json`)를 저장소에 넣는다(더블 훅, `needs=("hooks",)`) |
| `ctx.cli().json(["__test", "patch", memory_id, json])` | 더블 훅: 기록 필드 수정(`{"record": {...}}`), `approve-all`, `takedown`, `consents` |
| `ctx.fx_url`, `ctx.search_provider("fixture")` | 루프백 fixture 웹 서버(`tests/env/fixture-sites/`)와 검색 공급자 |
| `ctx.scan_sinks(identities, extra)`, `ctx.scan_values([...])` | 센티널 sink 스캔(값은 출력하지 않고 id만 돌려준다) |
| `ctx.schema_ok(instance, "doc_memory_recall")` | 응답을 `contracts/`의 스키마로 검증 |
| `util.recall(ctx, url, identity, **fields)` | URL을 stdin으로 넘겨 recall(argv에 URL이 남지 않는다) |
| `util.save_md(ctx, text, kind, title, doc_type, locale, identity, extra, provider)` | markdown 저장 |
| `util.reject(ctx, result, code, reason, exit_code=2)` | 고정 오류 코드·reason·종료 코드 판정 |

`needs=("server",)`는 공유 서버 상태를 켠다. 서로 다른 `identity`(예: `alice`, `bob`)는 서버 상태만 공유하고 로컬 홈은 따로 가진다(게시·복사·가시성 케이스).

## 3. 알아 둘 규칙

- **같은 scope는 upsert다.** `(URL 패턴, kind, provider, doc_type, locale, region, variant)`가 같으면 저장은 새 메모리가 아니라 같은 메모리의 새 버전이다([`core.md`](../../../docs/spec/core.md) 6절). 같은 URL에 메모리 여러 개가 필요하면 `locale`·`variant`·`provider`를 달리한다.
- **recall은 힌트를 최대 3개만 준다.** 순위 4위 이하는 관찰되지 않는다. 대상 메모리가 3위 안에 들도록 라이브러리를 작게 만들거나 질의를 좁힌다.
- 정규 URL 패턴(`docs.google.com/document/d/:id/edit`)과 원본 URL 모두 입력으로 받는다. 능력 ID(문서 ID)는 저장·출력되지 않는다.
- 판정의 근거는 [`docs/spec`](../../../docs/spec)다. 더블이 명세와 다르면 더블이 틀린 것이므로 최종 보고에 파일·줄과 함께 적는다(더블 수정은 하네스 작성자가 한다).
- 케이스 하나는 `DMEM_CASE_TIMEOUT`(기본 90초) 안에 끝나야 하고, 초과하면 러너가 `FAIL(timeout)`으로 처리한다.

## 4. 실행

```bash
perl -e 'alarm 120; exec @ARGV' python3 -B tests/smoke/run_all.py --ids 'RCL-*' --suite contract
python3 -B tests/smoke/run_all.py --ids 'RCL-03' --suite contract      # 증거: target/e2e-logs/contract/<run-id>/
```

`--strict`는 범위 안 `SKIP`을 실패로 본다. `DMEM_TARGET=product DMEM_BIN=… DMEM_MCP_BIN=…`는 같은 케이스를 제품에 돌린다([`../../README.md`](../../README.md)).
