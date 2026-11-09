# 지침 스니펫 형태 시나리오 (SNIP)

상태: 시나리오 정의(문서 우선). 명세 원본은 [`../../spec/mcp.md`](../../spec/mcp.md) 5절(`instructions`)과 [`../../spec/cli.md`](../../spec/cli.md)의 `dmem guide print`다. 에이전트가 MCP 없이 셸로 `dmem`을 쓸 때 읽는 지침(`AGENTS.md`·`CLAUDE.md` 마커 블록)을 시험한다.
ID 접두사: `SNIP`(01~04).

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| SNIP-01 | `dmem guide print`의 내용 | CLI · - · L2 자동 · P0 | 호출 시점 규칙(문서·슬라이드·페이지 작업 전 recall, 문서 종류·로케일이 바뀔 때·다른 route로 이동할 때, 같은 route·doc_type·locale은 5분 안에 반복하지 않음, 사용자가 거부하면 호출 안 함), untrusted 우선 규칙, 슬롯 값을 지어내지 않고 `{{확인 필요: 항목}}`, `expand`는 필요할 때만, 공유·게시는 명시적 동의 후에만을 모두 담는다. `mcp.md` 5절 `instructions` 문구와 의미가 일치(정규본 파일과 문자열 비교) | MCP-22, MCPF-01 |
| SNIP-02 | 스니펫의 안전 | CLI · - · L5 자동 · P0 | 토큰·키·개인 ID가 없다. "쿼리·fragment·자격증명·비공개 ID를 뺀 canonical 패턴을 쓰고 민감한 URL은 `recall --stdin`으로 넘긴다"는 안내가 있다 | SEC-F02 |
| SNIP-03 | `guide print --write` | CLI · - · L2 자동 · P0 | 현재 디렉터리의 `AGENTS.md`(기본 Codex) 또는 `CLAUDE.md`에 `dmem` 마커 블록만 만들거나 갱신한다. 사용자가 쓴 나머지 내용은 바이트 단위로 보존, 두 번 실행해도 같은 결과(멱등), 마커가 없는 파일에는 끝에 추가, 쓰기 전 `--dry-run`이 차이를 보여 준다 | SEC-F03 |
| SNIP-04 | 에이전트의 스니펫 사용 | CLI · CC CX · L4 자동 · M | 스니펫만 보고 에이전트가 문서 작업 전에 `dmem recall --stdin --json`을 호출하고 출력을 파싱한다. 호출률과 파싱 성공률은 **측정값**이다 | CLI-29, SMK-06 |
