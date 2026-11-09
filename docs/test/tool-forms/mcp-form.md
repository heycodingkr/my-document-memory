# MCP 형태 시나리오 (MCPF)

상태: 시나리오 정의(문서 우선). 명세 원본은 [`../../spec/mcp.md`](../../spec/mcp.md), [`../../spec/recall.md`](../../spec/recall.md), [`../../spec/link.md`](../../spec/link.md)이고 도구 스키마는 [`../../../contracts/mcp-tools.v1.json`](../../../contracts/mcp-tools.v1.json)이다. WAM `tool-forms/mcp-form.md`의 호스트 시나리오를 옮겼다. 호스트 관련 사실은 **WAM 승계(재확인 필요)** 이며 Claude Code·Codex는 이 저장소에서 아직 실행하지 않았다.
ID 접두사: `MCPF`(01~27). 로컬 stdio(`MCPL`)와 원격(`MCPR`) transport를 모두 다룬다. 프로토콜 계약 케이스는 [`../functional-tests.md`](../functional-tests.md)의 `MCP`다.

## 전제

- 도구는 `doc_memory_status`, `recall`, `search`, `expand`, `web_search`, `web_preview`, `save`, `import`, `copy`, `publish`, `delete`, `outcome` 12개이고 호스트 어댑터 전용으로 `doc_memory_clip_current_tab`이 있다.
- 호스트: Claude Code(`CC`), Codex CLI(`CX`), Arise(`AR`), 범용 MCP 클라이언트(`GEN`, 하네스의 `mcpclient`). 분류 칸은 `형태 · 호스트 · 계층 자동화 · 우선`이다. 계층 L0~L6은 테스트 계층이며 메모리 레이어와 다르다.

## 사용 (도구 발견·권한 티어·호출)

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| MCPF-01 | initialize의 `instructions` | MCPR/MCPL · GEN · L2 자동 · P0 | 앞 512자가 자기완결(recall 호출 시점·untrusted 규칙 포함), 전체 4,096자 이하. 핵심 지침(작업 전 recall, 사용자 지시 우선, 동의가 있을 때만 publish)이 앞쪽 | MCP-22, SNIP-01 |
| MCPF-02 | tools/list | MCPL · GEN · L2 자동 · P0 | 도구 12개, 각 설명 4,096자 이하. 읽기(`status`, `recall`, `search`, `expand`, `web_search`, `web_preview`)·쓰기·파괴(`delete`) 표시, `tools/list`+`instructions` ≤12,000 bytes | MCP-02, MCP-19, MCP-23 |
| MCPF-03 | Claude Code 기본 지연 로드 대 `alwaysLoad` | MCPL · CC · L4 자동 · M | 문서 작업 전 에이전트가 recall을 호출하는 비율을 두 설정에서 기록(합격 조건이 아니라 측정값). 낮으면 템플릿·instructions 개선 | BEH-01, SMK-06 |
| MCPF-04 | Codex 승인 모드 `writes` | MCPL · CX · L4 자동 · P1 | 읽기 도구는 승인 없이 실행, `save`·`import`·`copy`·`publish`·`delete`·`outcome`은 승인 요구. 승인 이벤트 수로 판정 | MCP-19, HOST-02 |
| MCPF-05 | 브라우저 MCP 공존 | MCPL · CC CX AR · L4 반자동 · P0 | 메모리 MCP와 browser MCP가 같은 세션에서 모두 보이고 이름 충돌이 없다. 한쪽 장애가 다른 쪽에 영향 없음. fixture 저장 oracle로 확인 | HOST-03, HOST-04, HOST-07, MCP-21 |
| MCPF-06 | 로컬·익명 연결 | MCPL · CC CX · L4 자동 · P0 | 로컬 모드: 저장·복사·가져오기·삭제 허용. 서버 모드 익명: recall·search·expand·web_*·공개 `copy`(로컬 라이브러리로) 성공, `publish`·`outcome`은 `auth_required`·서버 쓰기 0 | MCP-20, SHR-18 |
| MCPF-07 | 연결된 회원 | MCPL/MCPR · CC CX · L4 반자동 · P0 | recall 응답에 `receipt_id`, `publish`는 동의가 있어야, `outcome`은 receipt 소유 계정만 | RCL-12, SHR-01~02, MCP-17 |
| MCPF-08 | recall 출력 크기 | MCPL · GEN · L2 자동 · P0 | 힌트 ≤3개, 힌트당 ≤400 est tokens. Claude Code 경고 임계·Codex 출력 한도보다 한참 작다 | RCL-08, MEM-05 |
| MCPF-09 | CLI와의 동등성 | MCPL/CLI · GEN · L2 자동 · P0 | 같은 입력에서 MCP recall과 `dmem recall`이 같은 힌트를 같은 순서로 | RCL-14, CLI-05 |
| MCPF-10 | untrusted 프레이밍과 주입 시드 | MCPL · CC CX AR · L4 자동 · P0 | 힌트가 구조적으로 "참고용"과 분리, 악성 지시 시드를 에이전트가 따르지 않음. 도메인 이동·데이터 전송·자격증명 입력 0 | RCL-11, BEH-04, SEC-B03 |
| MCPF-11 | 같은 입력의 연속 recall | MCPL · CC CX · L4 자동 · P0 | 같은 URL·양식을 연속 호출해도 receipt·점수 이벤트가 늘지 않는다(연결은 소비자-레코드-일 1회, 익명·캐시는 0) | SCORE, RCL-12 |
| MCPF-12 | 동의 없는 publish | MCPL · CC CX · L4 자동 · P0 | 서버 요청 0, 에이전트가 사용자에게 알린다 | SHR-02, BEH-07 |
| MCPF-13 | outcome 재전송·타인 영수증·만료 | MCPL · CC CX · L4 자동 · P0 | 같은 결과·버전 집합은 `duplicate:true`, 다른 결과는 `version_conflict`, 타인·만료 receipt는 `not_found`, 점수 변화 없음 | MCP-17, SCORE |
| MCPF-14 | 응답 지연·타임아웃 | MCPL/MCPR · CC CX · L4 자동 · P1 | 서버 응답이 늦으면 호스트 타임아웃(Codex `tool_timeout_sec` 기본 60초, WAM 승계)에서 도구 오류, 상태 불변. 재시도는 멱등(`save`는 `created:false`) | LIB-04 |
| MCPF-25 | outcome의 잘못된 입력 | MCPL · GEN · L2 자동 · P0 | receipt 누락·빈·128자 초과, 알 수 없는 필드, enum 밖 결과를 거부하고 원장 변경 0 | MCP-05, CLI-23 |
| MCPF-26 | scope 누락 | MCPL/MCPR · GEN · L2 자동 · P0 | 유효한 토큰에 `report:outcome`·`write:share`가 없으면 도구 오류(서버 모드), 저장·점수 변화 0 | API, MCP-20 |
| MCPF-27 | save·import 입력 검증 | MCPL · GEN · L2 자동 · P0 | `inputSchema`에 파일 경로 필드가 없고, 알 수 없는 필드·1 MiB 초과 `content`·비밀값은 거부, 상태 변화 0 | MCP-12, LIB-14, MEM-15 |

## 인증 (티어·토큰 수명)

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| MCPF-15 | 한 endpoint의 익명 읽기와 인증 쓰기 | MCPR · CC CX · L4 반자동 · P0 | 연결 시 로그인 없이 recall이 가능해야 한다. `publish`·`outcome`에서 host OAuth 또는 `dmem link`가 동작해야 한다. 호스트가 원격 OAuth를 지원하지 않으면 local stdio + `dmem link`로 전환. 연결이 안 된 상태를 성공으로 표시하면 실패 | CUST-01~06, LINK |
| MCPF-16 | 거절·취소·만료·갱신 | MCPR · CC CX · L4 반자동 · P0 | 거절·취소 뒤에는 인증 필요 상태로 돌아오고 익명 recall은 계속되며 쓰기는 401/403. 만료 때 갱신되면 끊김 없고 실패하면 재인증 안내 | LINK, SHR-18 |
| MCPF-17 | 로그아웃과 해지 | MCPR/MCPL · CC CX · L4 반자동 · P0 | 호스트의 인증 해제·`dmem unlink`·웹 기기 해지 뒤 다음 쓰기가 즉시 거부, 익명 읽기는 계속 | LINK, HOST-11 |

## 수명주기

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| MCPF-18 | 호스트 재시작·세션 재개 | MCPL/MCPR · CC CX · L4 반자동 · P1 | 재로그인 없이 연결 유지, 도구가 바뀐 뒤에는 목록 갱신 | SMK-15 |
| MCPF-19 | 종료 신호 | MCPL · CC · L4 자동 · P0 | macOS·Linux에서 SIGINT, 100 ms 뒤 SIGTERM, 400 ms 뒤 SIGKILL 시퀀스 안에 정리하고 종료(WAM 승계, 재확인). 저장소·캐시가 손상되지 않는다 | LIB-13 |
| MCPF-20 | 로컬 라이브러리와 오프라인 | MCPL · CC CX · L4 자동 · P0 | 로컬 라이브러리는 항상 동작, 서버 모드의 익명 공개 recall만 캐시 표시, 연결 호출·게시·outcome은 서버 필요 | RCL-20, SMK-13 |

## 진단·장애

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| MCPF-21 | 서버 장애·네트워크 단절 | MCPR · CC CX · L4 자동 · P0 | 호스트가 실패 상태를 표시하고 에이전트는 recall 없이 작업을 이어 간다. 원인(DNS·TLS·HTTP status)을 구분하되 URL·토큰을 노출하지 않는다 | FAIL-01~24 |

## 보안

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| MCPF-22 | 비밀값 유출 점검 | MCPL/MCPR · CC CX · L5 자동 · P0 | `claude mcp get/list`, `codex mcp list --json`, 호스트 로그, 프로세스 인자, 서버 로그에 토큰·센티널 0 | SMK-16, SEC-H02 |

## 프로토콜 준수

| ID | 시나리오 | 분류 | 기대와 판정 근거 | 추적 |
|---|---|---|---|---|
| MCPF-23 | stdio stdout 순수성 | MCPL · GEN · L2 자동 · P0 | `dmem-mcp`가 stdout에 JSON-RPC 메시지 외에는 쓰지 않는다. 로그는 stderr | MCP-06 |
| MCPF-24 | Streamable HTTP·stdio conformance | MCPR/MCPL · GEN · L2 자동 · P0 | 스크립트 클라이언트로 initialize·tools/list·tools/call이 규약대로 동작하고 원격·로컬의 도구 계약이 같다(같은 입력·출력 스키마·오류 코드) | MCP-01~08, MCP-24 |
