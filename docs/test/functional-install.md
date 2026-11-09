# 기능 설치·진단 시나리오

상태: 전체 목표의 테스트 설계(문서 우선). 실제 제품 부분집합의 실행 결과는 [포팅 검증](wam-port-completion-v1.md)과 구분한다. Claude Code·Codex 등록 세부는 WAM 승계(재확인 필요)이며 Arise의 dmem 어댑터는 미확인이다. 아래 호스트 시험은 일회용 설정과 가짜 CLI/네트워크 fixture만 쓰며 실제 호스트 지원을 증명하지 않는다.
영역 / 테스트 ID 접두사: 설치·호스트 수명주기 `INST-01~30`, 진단 `DIAG-01~08`.
기반: [설치 명세](../spec/install.md), [진단 명세](../spec/diagnostics.md), [CLI 명세](../spec/cli.md) 3절, [지침 스니펫 형태](tool-forms/snippet-form.md), [호스트별 실행 문서](hosts/README.md), WAM [설치 시나리오](../../../web-agentic-memory/docs/test/tool-forms/install.md), [CLI 기기 연결·호스트 등록 검증](../../../web-agentic-memory/docs/test/cli-link.md).

## 1. 격리 전제

각 행은 새 `TEST_ROOT=$(mktemp -d)`에서 `HOME=$TEST_ROOT/home`, `XDG_CONFIG_HOME=$TEST_ROOT/xdg`, `DMEM_HOME=$TEST_ROOT/dmem`, `CODEX_HOME=$TEST_ROOT/codex`를 지정한다. Claude 설정은 격리 HOME의 `~/.claude.json`, Codex 설정은 격리 `CODEX_HOME/config.toml`에 둔다(호스트별 위치·명령은 WAM 승계(재확인 필요)). 가짜 `claude`·`codex` 실행 파일은 `$TEST_ROOT/bin`에서만 찾는다. 각 fixture는 원격 endpoint `https://mcp.example.test/mcp`, 로컬 실행 파일 `$TEST_ROOT/bin/dmem-mcp`, 비밀 아닌 기존 서버 `other-browser`, 설정 sentinel `KEEP-OUTSIDE-DMEM`을 사용한다. Arise 설정은 형식을 가정하지 않고 테스트 어댑터에 임시 파일 `$TEST_ROOT/arise-host-config`로 전달한다. 실제 사용자 설정·네트워크·인증은 사용하지 않는다.

## 2. 설치·등록·파일 변경

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| INST-01 | 격리 HOME/XDG와 빈 사용자 bin; 테스트 릴리스 fixture가 버전 `1.0.0` 바이너리와 일치하는 checksum 제공; `dmem install` | 검증된 파일만 사용자 경로에 설치되고 `dmem --version`이 `1.0.0`; 종료 0, sudo 요청·부분 파일 없음(install.md §2). |
| INST-02 | INST-01과 같되 checksum을 한 바이트 변경 | 설치 실패, 다운로드 임시 파일 제거, 기존 바이너리와 호스트 설정 바이트 동일; 오류에 비밀값 없음. |
| INST-03 | 기존 `dmem` v1과 임시 설정을 만든 뒤 다운로드 fixture를 DNS 실패로 설정 | 재시도 가능한 실패 상태; v1·설정·토큰 sentinel·캐시 그대로이며 부분 설치 없음. |
| INST-04 | 사용자 설치 디렉터리를 쓰기 불가로 만들고 설치 실행 | 비영(非零) 종료, sudo 요구 없이 대안 경로 안내, 디렉터리와 기존 파일 변경 없음. |
| INST-05 | 같은 릴리스로 두 번 설치; `DMEM_HOME`에 토큰·캐시 sentinel, 호스트 파일에 dmem와 `other-browser` seed | 두 실행 모두 성공하고 설치 파일·설정 diff 없음; 토큰·캐시·다른 서버 보존(멱등). |
| INST-06 | v1 바이너리 존재, v2 교체 중 rename 실패를 파일시스템 fault fixture로 주입 | 기존 v1 실행 파일과 설정이 그대로고 임시 v2 제거; 실패 진단 출력. |
| INST-07 | `AGENTS.md`·`CLAUDE.md`에 사용자 본문만 둔 뒤 각 호스트 `dmem install` | 두 문서의 바이트가 그대로다. 설치는 지침 파일을 자동 수정하지 않는다(install.md §3). |
| INST-08 | `HOME/.claude.json`에 빈 격리 설정, 가짜 `claude`; `dmem install claude-code`와 endpoint fixture | 원격 MCP 등록 항목 하나만 생기고 endpoint·선택 scope가 조회된다; 연결·인증 성공이라고 출력하지 않는다. 명령/파일 형식은 WAM 승계(재확인 필요). |
| INST-09 | 같은 격리 Claude 설정에서 `dmem install claude-code --local --scope user`; 절대경로 `$TEST_ROOT/bin/dmem-mcp` | dmem 항목은 local stdio 절대경로를 가리키고 설정에 토큰이 없다; 선택한 user scope 외 설정 불변. Scope/CLI 사실은 WAM 승계(재확인 필요). |
| INST-10 | `CODEX_HOME/config.toml`이 없는 격리 디렉터리와 가짜 `codex`; `dmem install codex` | 해당 임시 config에 dmem 원격 URL 하나가 생기며 HOME의 실제 Codex 설정은 접근되지 않는다. 형식은 WAM 승계(재확인 필요). |
| INST-11 | 격리 Codex 설정에서 `dmem install codex --local` 및 임시 절대경로 | dmem 명령/인자만 등록되고 endpoint 전달에 필요한 비밀 아닌 환경만 남는다; 토큰 값·다른 서버 값은 설정되지 않는다. 형식은 WAM 승계(재확인 필요). |
| INST-12 | Arise 어댑터 fixture에 임시 설정 파일과 기존 항목 제공; `dmem install arise` | 미지원/unsupported로 비영 종료하고 등록 성공을 주장하지 않으며 임시 파일 hash가 같다. Arise 등록 키·scope는 미확인이라 이 시험에서 추측하지 않는다. |
| INST-13 | 격리 HOME과 Claude/Codex 임시 설정; 지원하지 않는 `--scope unknown` 또는 PATH에서 host CLI 제거 | 입력/어댑터 오류로 비영 종료; 설정 원본 hash와 다른 서버가 보존되고, 설정 파일을 직접 고쳐 우회하지 않는다. |
| INST-14 | Claude JSON 및 Codex TOML 임시 설정 각각에 `other-browser`와 임의 사용자 키를 seed하고 dmem 등록 | 파싱 후 dmem 항목만 추가된다; 다른 항목의 구조·값은 보존되고 설정 원문/비밀은 stdout에 나오지 않는다. |
| INST-15 | 기존 Claude/Codex 임시 파일의 mode, 인코딩, CRLF 기록 후 등록; 원본 hash 기록 | 교체 전에 같은 디렉터리의 `.dmem.bak`이 이전 파일과 바이트 동일하며 권한·인코딩·줄바꿈 보존(install.md §4). |
| INST-16 | 유효한 임시 host 설정과 등록 요청; write 추적 fixture로 임시 파일·rename 순서 기록 | 완성된 임시 파일만 원자 교체되고 재읽기 파싱에서 dmem 항목 확인; 최종 파일은 하나이며 unrelated 설정 동일. |
| INST-17 | `.dmem.bak` 생성에 실패하도록 임시 디렉터리 fault 주입 후 등록 | 원본 설정 hash 동일, host CLI/rename 미호출, 임시 파일 제거 및 비영 종료. |
| INST-18 | 백업은 성공시키고 원자 rename 또는 재읽기 검증을 실패시키도록 주입 | 원본 설정이 복구되고 dmem 변경이 남지 않음; 백업·복구 실패 여부를 안전한 고정 진단으로 반환하고 임시 파일 정리. |

## 3. 반복 설치·업그레이드·계획·제거·스니펫

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| INST-19 | 동일 host/scope/transport/endpoint를 같은 격리 설정에 연속 두 번 등록 | 등록 항목 수 1개, 두 번째 실행의 설정 diff 0, 성공 종료; unrelated 서버 보존. |
| INST-20 | 격리 설정에 이름 `dmem`으로 다른 HTTPS endpoint 등록 후 새 endpoint 설치 | 충돌로 중단, 원래 endpoint와 파일 hash 보존; 덮어쓰기 명령 안내만 출력. |
| INST-21 | 격리 설정에 이름 `dmem`으로 다른 local command/args 등록 후 `--local` 설치 | 충돌 상태와 비영 종료; 기존 command·args 및 다른 설정 불변. |
| INST-22 | 설치 바이너리 v1, 등록이 그 절대경로를 가리킴; `DMEM_HOME`에 토큰·캐시 sentinel; 검증된 v2 fixture로 업그레이드 | 바이너리만 v2로 교체되고 등록 절대경로·토큰·캐시·host 설정 유지; schema 변경 안내가 있으면 버전 식별자만 출력. |
| INST-23 | INST-22에서 v2 checksum 또는 교체 단계를 실패시킴 | v1 바이너리와 모든 설정·토큰·캐시가 그대로며 부분 v2 삭제; 오류 종료. |
| INST-24 | 미등록 Claude 임시 설정에서 `dmem install claude-code --dry-run`; 실행 전후 파일 hash와 shim 호출 횟수 기록 | stdout에 생성·백업 대상 경로와 실행할 host 명령만 계획으로 출력; 모든 hash 동일, 다운로드·쓰기·host CLI 호출·프로세스 시작 0회. |
| INST-25 | 임시 설정을 한 번은 같은 dmem 등록, 한 번은 충돌 endpoint로 준비하고 각각 `--dry-run` | 계획이 각각 no-op 또는 conflict로 판정되며 실제 두 파일 hash와 shim 호출 횟수 불변; conflict를 덮어쓰기 계획으로 내지 않는다. |
| INST-26 | Claude 임시 설정에 dmem·`other-browser`, 사용자 지침 sentinel을 두고 `dmem uninstall claude-code` | dmem 등록만 제거; 다른 MCP·지침·DMEM 토큰·캐시·서버 데이터 그대로. 제거 범위는 install.md §5 기준. |
| INST-27 | Codex 임시 `config.toml`에 dmem과 별도 서버/임의 TOML 값을 둔 뒤 `dmem uninstall codex` | dmem 등록만 빠지고 나머지 TOML 값과 항목이 보존된다; 실제 Codex 설정은 건드리지 않는다. 호스트 파일 사실은 WAM 승계(재확인 필요). |
| INST-28 | dmem 항목이 없는 새 격리 Claude 설정에서 `dmem uninstall claude-code` | 변경 없는 성공(종료 0), 파일 hash 동일; host CLI가 다른 항목을 제거하지 않는다. |
| INST-29 | 임시 `AGENTS.md`에 앞·뒤 사용자 sentinel 본문, Claude용 `CLAUDE.md`에도 별도 본문을 두고 `dmem guide print --write --host codex` 및 `--host claude-code` 실행 | 각 파일에는 dmem 마커 블록이 추가되고 마커 밖 바이트는 그대로다; stdout에는 지침 본문/비밀이 아닌 변경 요약만 나온다(SNIP-03). |
| INST-30 | INST-29 결과에 동일 두 명령을 다시 실행한 뒤 블록 안 문자열만 이전 버전으로 바꾸고 재실행 | 두 번째 실행은 전체 파일 hash 불변; 갱신 실행은 dmem 마커 블록만 최신 출력으로 교체하고 앞·뒤 사용자 sentinel을 보존한다. |

## 4. doctor 원인·출력 안전성

모든 행은 새 격리 `TEST_ROOT`와 임시 host/config/cache fixture를 사용한다. Doctor는 읽기 전용이며 완료된 JSON 보고는 [diagnostics.md](../spec/diagnostics.md) §2의 닫힌 상태·필드 규약을 따른다.

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| DIAG-01 | `DMEM_ENDPOINT=https://dns-fail.dmem.test/mcp?case=URL_QUERY_SENTINEL`; hermetic resolver가 DNS NXDOMAIN 반환; `dmem doctor --json` | `connection=unreachable`; TLS/인증/캐시/host/vocab 검사는 결과에 남아 독립 판정된다. stdout에 query sentinel이나 전체 URL 없음. |
| DIAG-02 | endpoint를 loopback 시험 HTTPS 서버의 self-signed 인증서로 연결하고 doctor 실행 | 원격 TLS 검사가 `tls_error`; 연결 불가와 구별되고 인증서·오류 원문은 출력하지 않는다. |
| DIAG-03 | 임시 인증 fixture가 잘못된 bearer에 HTTP 401 반환; `DMEM_TOKEN=INVALID_TOKEN_SENTINEL` | 인증 상태 `unauthorized`, 연결 성공 상태는 유지; token/header/401 body 미노출. |
| DIAG-04 | 임시 인증 fixture가 만료 credential 전용 응답(401 + expired 표식) 반환; `DMEM_TOKEN=EXPIRED_TOKEN_SENTINEL` | 현재 diagnostics.md 허용 계약상 auth는 `unauthorized`다. DIAG-03과 출력 상태가 같아 만료 원인을 구별할 수 없음을 명시적으로 기록한다; 만료 전용 표시는 명세 §2에 추가되기 전까지 미합격/열린 계약 간극이다(WAM의 `reauth_required`는 승계 사실이며 DMEM 상태값으로 가정하지 않음). |
| DIAG-05 | `DMEM_HOME`과 XDG cache 아래 캐시 경로를 만들지 않고 doctor 실행 | cache 상태 `missing`; doctor가 디렉터리·캐시 항목을 생성/열거하지 않고 다른 검사도 계속한다. |
| DIAG-06 | 임시 Claude·Codex 설정은 유효하되 dmem entry 없음; host 앱/CLI shim 호출을 감시 | 호스트 등록 상태 `missing`; 앱·MCP 프로세스 실행 0회, 설정 hash와 비 dmem 값 불변. 경로 가정은 WAM 승계(재확인 필요). |
| DIAG-07 | 임시 vocab 파일은 구조를 유지하되 설치 버전과 다른 `version`으로 seed | vocab 상태 `mismatch`; 설치/관찰 버전만 허용 범위에서 출력하고 vocab 항목 값·원문은 없음. |
| DIAG-08 | 임시 설정에 URL path/query/fragment sentinel, token·Authorization sentinel, 문서 title/body sentinel, raw error sentinel을 각각 두고 모든 검사 실행 | JSON은 `schema_version`·`checks`와 허용된 고정 필드만 포함; 토큰·URL 전체 및 path/query/fragment·문서/응답 본문·설정 원문·오류 원문이 0회 출현. 설정·캐시·문서·동의 상태 hash가 실행 전후 같다. |

## 5. 판정 한계

설치 명세가 요구하는 INST-01~30, 진단 명세가 요구하는 DIAG-01~08을 이 문서에서 정의한다. Claude Code·Codex의 실제 CLI·scope·설정 동작은 현 저장소에서 재확인되지 않아 각 행에 WAM 승계(재확인 필요)로 표시했다. Arise는 미검증이므로 install/uninstall 성공을 기대하지 않는다. 진단 명세의 `unauthorized` 단일 상태로는 일반 401과 토큰 만료를 구별할 수 없으며, DIAG-04는 이 계약 간극을 드러낸다.
