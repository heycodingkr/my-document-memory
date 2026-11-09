# 호스트별 실행 문서

상태: 호스트별 확인된 설치·설정·실행 사실만 기록한다(추측으로 적지 않는다). 형식은 [`../host-smoke.md`](../host-smoke.md) 4절 템플릿이다.

| 호스트 | 문서 | 환경 스모크 | `dmem-mcp` 등록·호출 | 마지막 확인 |
|---|---|---|---|---|
| **Arise 브라우저** | [`arise.md`](arise.md) | **통과**(21/21, Arise 0.1.77) | 이 포팅에서는 제품 허브 등록·clip·자발적 recall 미실행 | 2026-11-09 |
| Claude Code | [`matrix.md`](matrix.md) | 미실행 | 현재 설정·버전 재확인 후 실행 | — |
| Codex CLI | [`matrix.md`](matrix.md) | 미실행 | 현재 설정·버전 재확인 후 실행 | — |
| Chrome + browser MCP | [`matrix.md`](matrix.md) | 미실행 | 미실행 | — |
| 범용 stdio MCP 클라이언트 | [`../local-smoke.md`](../local-smoke.md), [`../wam-port-completion-v1.md`](../wam-port-completion-v1.md) | 더블 계약과 실제 Rust 제품을 각각 실행 | 실제 제품 initialize/list/call·저장·복사·recall·기여 검증 | 2026-11-09 |

Claude Code·Codex·Chrome·Meta 항목은 WAM 문서의 구조를 [`matrix.md`](matrix.md)에 적응했다. 호스트 CLI는 자주 바뀌므로 **현재 버전으로 다시 확인한 뒤** 실행 결과와 설치 명령을 기록한다. 이 매트릭스는 미검증 호스트가 통과했다는 기록이 아니다.
