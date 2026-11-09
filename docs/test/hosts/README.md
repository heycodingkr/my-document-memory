# 호스트별 실행 문서

상태: 호스트별 확인된 설치·설정·실행 사실만 기록한다(추측으로 적지 않는다). 형식은 [`../host-smoke.md`](../host-smoke.md) 4절 템플릿이다.

| 호스트 | 문서 | 환경 스모크 | `dmem-mcp` 등록·호출 | 마지막 확인 |
|---|---|---|---|---|
| **Arise 브라우저** | [`arise.md`](arise.md) | **통과**(21/21, Arise 0.1.77) | 미실행(제품 없음) | 2026-11-09 |
| Claude Code | 없음 | 미실행 | 미실행 | — |
| Codex CLI | 없음 | 미실행 | 미실행 | — |
| Chrome + browser MCP | 없음 | 미실행 | 미실행 | — |
| 범용 MCP 클라이언트(하네스 `mcpclient`) | [`../local-smoke.md`](../local-smoke.md) | 테스트 더블 대상 | 테스트 더블 대상 | 진행 중 |

Claude Code·Codex·Chrome 항목은 WAM 문서의 확인 사실(`../web-agentic-memory/docs/test/hosts/*.md`)을 참고할 수 있으나, 호스트 CLI는 자주 바뀌므로 이 저장소에서 **현재 버전으로 다시 확인한 뒤** 문서를 만든다. 확인 전에는 파일을 만들지 않는다.
