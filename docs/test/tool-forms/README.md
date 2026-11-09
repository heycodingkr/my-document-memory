# 도구 형태별 시나리오

상태: 분류 정의(문서 우선). 사용자가 `dmem`을 쓰는 **형태**(명령줄, MCP 서버, 지침 스니펫)와 **호스트**(Claude Code, Codex, Arise, 범용 MCP 클라이언트)별 시나리오를 모은다. 형태가 다르면 설치·인증·실패 모드가 달라지므로 기능 테스트(`../functional-tests.md`)와 따로 둔다.

| 문서 | 형태 | ID |
|---|---|---|
| [`cli-form.md`](cli-form.md) | `dmem` 명령줄 | `CLI-01~33` |
| [`mcp-form.md`](mcp-form.md) | `dmem-mcp`(stdio·원격) | `MCPF-01~27` |
| [`snippet-form.md`](snippet-form.md) | 에이전트 지침 스니펫 | `SNIP-01~04` |

호스트 등록(`dmem install`)과 서버 연결은 [`../functional-install.md`](../functional-install.md)(`INST`), [`../functional-connect.md`](../functional-connect.md)(`LINK`)가 정의한다.

## 분류 칸

각 시나리오의 `분류`는 `형태 · 호스트 · 계층 자동화 · 우선`이다.

| 칸 | 값 |
|---|---|
| 형태 | `CLI`, `MCPL`(로컬 stdio), `MCPR`(원격 HTTP), `SNIP` |
| 호스트 | `CC`(Claude Code), `CX`(Codex), `AR`(Arise), `GEN`(범용 클라이언트), `-`(무관) |
| 계층 자동화 | `L2 자동`(하네스가 블랙박스로), `L4 자동`/`L4 반자동`(실제 호스트), `L5 자동`(보안) |
| 우선 | `P0`(필수), `P1`, `P2`, `M`(측정값, 합격 조건 아님) |

## 실행 가능 범위

구현이 없는 동안 `L2 자동` 시나리오는 테스트 더블에 대해 실행하고, `L4`는 Arise 스모크([`../hosts/arise.md`](../hosts/arise.md))만 실제 호스트에서 실행한다. Claude Code·Codex 시나리오는 해당 호스트의 현재 설치·등록 방법을 확인한 뒤 같은 형식으로 `hosts/`에 기록한다.
