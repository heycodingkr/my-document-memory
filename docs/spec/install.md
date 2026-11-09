# INST: 설치와 호스트 등록

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. 명령은 [`cli.md`](cli.md) 3절과 일치한다. Claude Code·Codex 상세는 WAM 승계(재확인 필요); Arise의 dmem 등록은 이 저장소에서 미확인이다.
영역 / 테스트 ID 접두사: `INST` ([케이스](../test/functional-install.md))
기반: [`../design/wam-port-map.md`](../design/wam-port-map.md) 7절, [`../test/tool-forms/snippet-form.md`](../test/tool-forms/snippet-form.md), [`../test/hosts/README.md`](../test/hosts/README.md)

## 1. 목적과 명령

`dmem install`은 사용자 선택 호스트에 원격 MCP 또는 로컬 stdio MCP를 등록한다. `uninstall`은 지정 호스트의 dmem 등록만 해제한다. 명령 표면과 종료 코드는 [`cli.md`](cli.md) 2·3절이 원본이다.

| 명령 | 계약 |
|---|---|
| `dmem install <host> [--local] [--scope <s>] [--dry-run]` | `claude-code`, `codex`, `arise` 등록. 기본은 원격 MCP, `--local`은 로컬 stdio MCP |
| `dmem uninstall <host>` | 지정 호스트의 dmem 등록 제거. 자격 증명·캐시는 별도 보존 |
| `dmem doctor [--json]` | 연결·TLS·인증·동의·캐시·호스트 등록·vocab 점검. 상세는 [`diagnostics.md`](diagnostics.md) |

등록 완료는 호스트 설정 반영을 뜻한다. 서버 연결, 사용자 인증, 동의, 실제 도구 호출 성공을 뜻하지 않는다. 지원하지 않는 scope나 미확인 어댑터는 상태 변경 없이 실패한다.

## 2. 바이너리와 설치 스크립트

배포용 설치 스크립트는 OS·아키텍처에 맞는 버전 고정 `dmem` 및 `dmem-mcp`를 HTTPS로 받고 체크섬을 확인한다. 검증 전 파일은 실행하지 않는다. 사용자 전용 실행 경로에 임시 파일로 설치한 뒤 원자 교체하고, 실패 시 기존 바이너리를 보존한다. sudo를 요구하지 않는다. 서명 릴리스·패키지 매니저·지원 OS 목록은 아직 확인된 배포 사실이 아니며 구현·수용 검증이 필요하다.

`--local` 등록은 호스트가 실행할 `dmem-mcp`의 절대 경로와 필요한 비밀 없는 설정만 둔다. MCP 프로세스는 runtime-v1의 단일 소유자 API `http://127.0.0.1:3847`에 연결한다. 해당 서버는 loopback에만 바인딩하고 `DMEM_TOKEN`을 요구한다. 설치기는 서버를 중복 기동하거나 토큰을 생성·저장·출력하지 않는다. 토큰 공급 위치는 runtime-v1과 CLI 설정의 정합성 과제로 남긴다.

## 3. 호스트별 등록 근거

| 호스트 | 등록 방식·범위 | 확인 상태 |
|---|---|---|
| `claude-code` | WAM 승계: 원격 `claude mcp add --transport http dmem <URL>`; 로컬 `claude mcp add dmem -- <절대경로> [인자]`. WAM 확인 scope는 `local`(기본), `user`, `project`; 경로는 각각 `~/.claude.json` 또는 프로젝트 `.mcp.json`. | WAM 승계(재확인 필요). DMEM 호스트 문서 미실행 |
| `codex` | WAM 승계: 원격 `codex mcp add dmem --url <URL>`; 로컬 `codex mcp add dmem -- <절대경로> [인자]`. WAM 확인 범위는 사용자 `~/.codex/config.toml`이며 `CODEX_HOME`으로 분리 가능. 프로젝트 등록은 확인되지 않음. | WAM 승계(재확인 필요). DMEM 호스트 문서 미실행 |
| `arise` | 이 저장소에서 확인한 것은 내장 공개 MCP `agent_browser --mcp-server`뿐이다. `dmem-mcp` 허브 등록 방식·scope는 확인되지 않았다. | [호스트 기록](../test/hosts/arise.md): 이 포팅에서 제품 허브 등록 미실행. 어댑터 검증 전 등록 성공으로 판정하지 않음 |

WAM 호스트 CLI는 2026-10-29 당시 버전에서 확인됐으며 현재 버전의 보증이 아니다. Arise의 브라우저 MCP는 dmem 등록을 대신하지 않는다. `install`은 확인된 호스트 등록 명령/파일 형식만 사용하며 임의 설정 키, 자동 주입, 승인 우회는 금지한다. 스니펫 내용은 [`snippet-form.md`](../test/tool-forms/snippet-form.md) SNIP-01~03을 따른다. 호출 규칙·untrusted 처리·확인 필요 placeholder·명시 동의는 SNIP-01, `guide print --write`의 `AGENTS.md`/`CLAUDE.md` 마커 갱신은 SNIP-03이다. 설치가 지침 파일을 자동 변경하지 않는다.

## 4. 설정 파일 변경

파일을 다루는 어댑터는 현재 형식을 파싱하고 dmem 항목만 바꾼다. 잠금 후 같은 디렉터리에 새 파일을 완성하고 권한·인코딩·줄바꿈을 보존한다. 기존 파일은 `.dmem.bak`으로 먼저 백업한 뒤 임시 파일을 원자적으로 교체하고 재읽기 검증한다. 백업 또는 교체 실패면 원본을 보존·복구하고 임시 파일을 지운다.

잘못된 형식, 심볼릭 링크, 쓰기 권한 없음, 잠금 거부, 이름 충돌은 임의 복구나 덮어쓰기를 하지 않는다. 호스트 CLI 어댑터도 설정을 사전·사후 확인하고 실패 후 원본 복구를 보장해야 한다. 호스트 CLI가 이 보장을 제공할 수 없으면 변경하지 않고 실패한다.

## 5. 멱등성·업그레이드·제거

같은 호스트·scope·전송·endpoint의 재설치는 설정을 추가 복제하지 않고 성공한다. 같은 이름의 다른 endpoint/command가 이미 있으면 충돌로 보고 원본을 보존한다. 업그레이드는 검증한 바이너리와 dmem 등록만 교체한다. 설정·토큰·캐시는 유지하고 교체 실패는 이전 바이너리·설정으로 돌아간다.

`uninstall`은 지정 호스트의 dmem 등록과 설치기가 소유한 바이너리만 제거한다. 다른 서버, 다른 호스트, 사용자 작성 지침, 서버 데이터, `DMEM_TOKEN`, 인증 정보, 캐시는 건드리지 않는다. 등록이 없으면 변경 없는 성공으로 끝난다.

## 6. 계획 모드와 요구사항 추적

`--dry-run`은 검사 후 계획한 생성·교체·백업·삭제, 대상 경로, 호스트 명령을 출력한다. 바이너리 다운로드·파일 쓰기·호스트 CLI 호출·프로세스 시작은 하지 않는다. 출력은 적용 때와 같은 충돌 판정을 사용한다.

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-INST-01 | 검증된 사용자 설치 | 체크섬·권한 실패가 기존 바이너리를 보존한다 | INST-01~07 |
| F-INST-02 | 호스트별 원격·로컬 등록 | 확인된 호스트만 등록하며 비밀을 설정에 넣지 않는다 | INST-08~13 |
| F-INST-03 | 원자 설정 갱신 | 백업·원자 교체·실패 복구, 비 dmem 항목 보존 | INST-14~18 |
| F-INST-04 | 반복 설치·업그레이드 | 단일 등록 유지, 충돌 보존, 실패 시 롤백 | INST-19~23 |
| F-INST-05 | 계획·제거 범위 | dry-run 무변경, 지정 호스트의 소유 항목만 제거 | INST-24~30 |

