# 브라우저 호스트 통합과 Arise 테스트 환경

상태: 설계 초안(문서 우선). WAM `docs/design/browser-host-integration.md`, `docs/test/hosts/arise.md`와 과거 검증 기록을 승계한다. **WAM에서 확인된 사실은 "승계(재확인 필요)"로 표시**하고, 이 저장소에서 직접 실행해 확인한 것은 [`../test/hosts/arise.md`](../test/hosts/arise.md)에 날짜와 함께 적는다.
기반: [`../spec/mcp.md`](../spec/mcp.md) 6절, [`../spec/web-import.md`](../spec/web-import.md) 6절, 테스트 [`../test/host-smoke.md`](../test/host-smoke.md)

## 1. 왜 Arise인가

테스트 환경은 **Arise 브라우저**다. 같은 호스트에서 (1) 로컬 fixture 사이트를 열어 문서·양식 페이지를 렌더링해 보고, (2) 에이전트가 browser 도구와 `doc_memory_*`를 함께 쓰고, (3) 사용자가 지시한 현재 탭을 클립하는 흐름을 모두 시험할 수 있다. Arise는 자체 browser MCP(`agent_browser --mcp-server`)와 외부 MCP 허브를 제공한다.

## 2. 통합 경로

| 경로 | 방식 | 보장하는 것 | 보장하지 않는 것 |
|---|---|---|---|
| A. MCP 허브 | `dmem-mcp`(local stdio 또는 remote)를 Arise 설정의 MCP 허브에 등록. 같은 agent session에서 browser 도구와 `doc_memory_*`를 사용 | 도구 공존, 이름 충돌 없음 | 모델이 조립한 URL의 query가 기기 밖으로 안 나간다는 보장(canonical pattern을 넘기도록 안내만) |
| B. `dmem browser-mcp` | 공개 stdio browser MCP child를 host session 동안 하나 유지하면서 도구를 전달하고 `doc_memory_clip_current_tab`을 추가 | 같은 연결에서 browser 작업과 클립, URL 기기 내 정규화, 캡처 전후 target 재확인 | Arise 내부 socket·CDP 직접 접속은 지원 계약이 아니다 |
| C. 하네스 CDP | 격리 테스트가 fixture 브라우저를 직접 구동 | 테스트 전용 | **제품 연동이 아니다** |

Arise 계정·쿠키·브라우저 control socket은 `dmem` 인증이 아니다. `dmem` 연결은 별도로 명시해야 한다.

## 3. 클립 계약 (경로 B)

- 입력에 URL 필드가 없다. 선택된 automation target(session·client·tab/window·lease 만료·ready)을 검증하고 **기기에서** URL을 정규화한다.
- 읽는 것은 화면에 보이는 문서 텍스트·구조뿐이다. 쿠키·localStorage·폼 값·자격증명은 읽지 않는다. 비밀번호·결제 필드가 있는 페이지는 거부한다.
- 캡처 전후에 같은 target인지 확인하고 달라졌으면 저장하지 않는다. 다른 target을 대신 잡지 않는다.
- 저장은 `provenance: captured`. 모델이 `doc_memory_save`로 준 출처는 `claimed`다.
- 사용자 탭·다른 세션 탭·만료된 lease는 거부한다. 백그라운드 자동 클립은 없다.

## 4. 테스트 운용 규칙 (WAM 승계, 재확인 대상)

| 규칙 | 근거 |
|---|---|
| 모든 테스트는 **고유 `session_id`** 를 쓰고 **자기 소유 background 탭만** 연다(`browser_new_tab`/`browser_open`). 사용자 탭은 읽지도 닫지도 않는다 | WAM 검증 2026-10-29 |
| 끝나면 자기 탭만 `browser_close_tab`으로 닫고 `browser_release`를 호출한다. **`browser_close`는 호출하지 않는다**(앱 전체를 닫는 전역 동작) | WAM 검증 |
| `ready: true`만으로는 탐색 완료가 아니다. 요청한 **대상 URL**까지 기다린다 | WAM 검증 |
| browser MCP child는 host session 동안 **하나**만 유지한다. 일회성 child로는 기존 lease proof를 재사용할 수 없다 | WAM 검증 |
| 창이 없으면 Arise를 활성화하고 현재 AX 메뉴 File → New Window를 새로 관찰해 눌러 창을 만든 뒤 `browser_new_tab(window_id)`을 쓴다. 옛 AX 경로를 하드코딩하지 않는다 | WAM 검증 2026-10-27 |
| 비동기 레이아웃 검사는 `browser_eval`에서 `window.__result`에 저장하고 후속 호출에서 읽는다. 상대 import는 `arise://renderer-eval` 기준이라 `location.origin`을 쓴다 | WAM 기록 |
| 스크롤 직후 좌표 클릭은 geometry를 재측정(≤1px 차이)한 뒤 한다 | WAM 기록 |
| 앱이 보내는 **JS dialog**(`alert`·`confirm`·`prompt`·`beforeunload`)는 페이지 JS를 멈추고 다른 모든 도구를 `javascript_dialog_pending`으로 거부한다. 자동 승인되지 않는다. `browser_dialog(inspect)`로 untrusted 메시지를 읽고 작업 의도에 맞게 `dismiss`/`accept`한다. beforeunload 수락은 초안을 버릴 수 있어 승인 없이 하지 않는다 | 이 저장소 실측 2026-11-09 |
| 같은 앱을 **다른 에이전트 세션도 동시에 쓴다**. `browser_tabs`의 `is_mine`·`owner.session_id`로 구분하고, 소유자 없는 탭은 사용자 탭이다. 정리 검증은 "소유자 없는 탭의 id·URL·제목이 전후 같다"로 한다(다른 세션의 탭은 스스로 바뀔 수 있다) | 이 저장소 실측 2026-11-09 |
| `innerText`는 `display:none` 텍스트만 뺀다. 크기 0·배경색 동일 텍스트는 그대로 노출되므로 현재 탭을 텍스트로 읽는 어댑터는 반드시 살균한다 | 이 저장소 실측 2026-11-09 |
| lease는 120초 TTL이다. 긴 실행은 `browser_heartbeat`로 갱신한다 | 이 저장소 실측 2026-11-09 |
| 서명된 릴리스 바이너리를 번들 밖으로 복사하면 시작 직후 종료한다. 설치된 앱을 제자리에서 쓴다 | WAM 기록 |
| MCP child의 `TMPDIR`을 앱과 다르게 고정하면 실행 중인 앱을 못 찾고 두 번째 인스턴스를 띄울 수 있다. child는 앱과 같은 환경을 상속한다 | WAM 기록 |

## 5. fixture 사이트 (loopback)

`tests/env/fixture-sites/`의 서버는 임의 빈 포트에 바인딩하고(포트를 하드코딩하지 않는다), `DMEM_ISOLATED=1` 규칙([`../spec/core.md`](../spec/core.md) 9절)에 맞춰 provider 모양의 경로를 제공한다.

| 경로 | 목적 |
|---|---|
| `/p/google-docs/document/d/<FIXTURE_ID>/edit` | Docs 모양 문서 페이지(국가별 변형: KR/US/JP 이력서·청구서) |
| `/p/google-docs/document/d/<FIXTURE_ID>/export?format=md\|html\|docx\|txt` | 내보내기 경로 모사(미검증 경로 — [`formats.md`](../spec/formats.md) 3절) |
| `/p/google-slides/presentation/d/<FIXTURE_ID>/export?format=pptx` | Slides 모양 PPTX 내보내기 |
| `/p/notion/<slug>-<hex32>` | Notion 모양 공개 페이지 |
| `/pages/license-*.html` | 라이선스 변형(CC-BY, CC0, MIT, 없음, NC) |
| `/pages/hostile-*.html` | 주입 문구, 숨김 텍스트, 제로폭, 거대 응답, 느린 응답, 로그인 리다이렉트, 사설 주소 리다이렉트 |
| `/search?q=…` | `fixture` 검색 provider의 고정 결과 |

센티널은 합성 값이며 실제 사이트·계정·개인 문서를 쓰지 않는다([`../test/README.md`](../test/README.md) 4절).

## 6. 수용 테스트

호스트 여정은 `HOST-01~12`, 고객 경로는 `CUST-01~06`, 스모크는 `SMK-01~16`([`../test/host-smoke.md`](../test/host-smoke.md))이 정한다. Arise 실행 기록 양식은 [`../test/hosts/arise.md`](../test/hosts/arise.md)다.
