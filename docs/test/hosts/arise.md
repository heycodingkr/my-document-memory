# 호스트: Arise 브라우저

형식은 [`../host-smoke.md`](../host-smoke.md) 4절 템플릿이다. **직접 실행해 확인한 사실**과 **WAM 승계(재확인 필요)** 를 구분해 적고, 확인하지 못한 항목은 비워 둔다. 하네스는 Arise의 공개 stdio MCP(`agent_browser --mcp-server`)만 쓴다. CDP나 앱의 내부 제어 소켓에 접속하지 않는다.

```
호스트: Arise (/Applications/Arise.app, 번들 ID ai.meshcode.agent-browser)
  실행 시점 설치본 Info.plist 버전: 0.1.77 (2026-11-09 10:12 KST, 스모크 meta.json)
  같은 날 작업 초반에 읽은 값: 0.1.76 → 작업 중에 앱이 갱신됨. 환경이 움직이므로 실행마다 버전을 기록한다
설치/등록 명령: browser MCP는 앱에 내장. `dmem-mcp`의 허브 등록과 `dmem browser-mcp`는 구현이 없어 미확인
설정 파일 경로와 형식: 이 저장소에서 읽지 않음. WAM 승계(재확인 필요): $XDG_CONFIG_HOME/agent-browser/settings.toml
환경변수 상속 여부: 스모크는 자식 MCP에 부모 환경을 그대로 상속(앱과 같은 TMPDIR) — 정상 동작을 확인
비대화형 실행 방법: python3 -B tests/smoke/arise_smoke.py
SMK 결과(환경 스모크): 2026-11-09 21/21 통과, 실행 증거 target/e2e-logs/arise/20261109-101257-0323/ (git 무시)
  SMK-14 일부(자기 소유 탭만 닫기) ✓. SMK-10(현재 탭 클립)·SMK-02/HOST-05·HOST-10(허브 등록)은 제품 없음 → 미실행
BEH 결과: 미실행
알려진 이슈: 아래
```

## 확인한 사실 (2026-11-09, 이 저장소에서 직접 실행)

| 항목 | 관찰 | 근거 |
|---|---|---|
| MCP 연결 | `agent_browser --mcp-server`를 부모 환경으로 띄우면 `initialize`(protocolVersion `2025-11-25`)와 `tools/list`가 성공. 도구 62개 노출(WAM 문서 시점의 39개보다 많다) | `meta.json` `tools_exposed` |
| 세션 소유 탭 | `browser_new_tab(session_id, window_id, activate=false)`이 **백그라운드 탭을 만들고 lease를 준다**(ttl 120초). `browser_tabs`가 `is_mine`·`owner`를 구분해 준다 | 수동 실행, 스모크 |
| 다른 세션과 공존 | 같은 앱을 **다른 에이전트 세션이 동시에 쓴다**(다른 `session_id`의 탭 2개가 보였다). 소유권 표시로 구분되어 서로 건드리지 않는다 | 수동 `browser_tabs` |
| 정리 | `browser_close_tab`으로 **자기 탭만** 닫고 `browser_release` 뒤 사용자 탭(소유자 없음)의 id·URL·제목이 전후 같다. `browser_close`(전역)는 호출하지 않는다 | 스모크 HARN-05 5건 |
| 탐색 완료 판정 | `ready`만으로는 부족하다. 스모크는 `location.pathname`이 **대상 경로가 될 때까지** 기다린다 | 스모크 |
| fixture 렌더링 | resume-ko(제목·헤딩 4·CC-BY 링크·표 1·prose 센티널 5·`lang=ko`), 라이선스 변형 4, provider 모양 2, 정적 적대 페이지가 기대 landmark대로 읽힘 | 스모크 HARN-06, 스크린샷 `shots/resume-ko.png`를 직접 열어 확인 |
| 브라우저는 원 URL을 보존 | `location.href`에 쿼리·fragment가 그대로 있다. 정규화는 브라우저가 아니라 `dmem`의 책임이다 | 스모크 |
| **JS dialog** | 활성 적대 페이지(`hostile-inject.html`)의 `alert`가 페이지 JS를 멈추고, Arise는 **모든 도구를 `javascript_dialog_pending`으로 거부하며 자동 승인하지 않는다.** `browser_dialog(inspect → dismiss, dialog_id)`로 명시 응답해야 재개된다. 메시지는 untrusted 페이지 내용이다 | 수동 + 스모크 |
| **숨김 텍스트 노출** | `display:none` 텍스트는 `innerText`에 없지만 **크기 0·배경색 동일 텍스트는 `innerText`에 그대로 나온다.** `innerText`로 현재 탭을 읽는 클립 어댑터는 사람 눈에 안 보이는 문구를 가져오므로 정화가 필수다 | 스모크 HARN-06(적대 정적 페이지) |
| 활성 적대 페이지의 DOM 파괴 | `hostile-inject.html`의 스크립트가 `document.body.innerHTML`을 덮어쓴다. landmark 검사에는 **스크립트 없는 `hostile-static.html`**을 쓰고 활성 페이지는 dialog 처리 검증에만 쓴다 | 수동 |

## WAM 승계 (재확인 필요)

[`../../design/browser-host-integration.md`](../../design/browser-host-integration.md) 4절의 표를 따른다. 위 확인 사실 중 세션 소유 탭·정리·`ready` 한계는 이 실행에서 다시 확인되었다. 아직 확인하지 못한 것: 창이 0개일 때의 복구 절차(File → New Window), 비동기 레이아웃 검사의 `window.__result` 패턴, 스크롤 직후 좌표 클릭, 서명된 바이너리 복사 금지, 앱과 다른 `TMPDIR`를 쓰는 MCP 자식의 실패 모드.

## 격리 실행 레시피

하네스 스모크는 **설치된 앱을 제자리에서** 쓰고 자기 세션의 탭만 연다(사용자 프로필·설정을 읽거나 바꾸지 않는다). 사용자 앱과 완전히 분리된 인스턴스가 필요하면 WAM의 격리 레시피(`HOME`·`XDG_*`·`ARRISE_CEF_CACHE`·`AGENT_BROWSER_*`를 일회용 루트로, 설치본을 제자리 실행)를 쓰되 이 저장소에서는 아직 구현·검증하지 않았다.

## 실행

```
python3 -B tests/smoke/arise_smoke.py [--browser-mcp PATH] [--out DIR] [--no-shots]
```

종료 코드: 0 전부 통과, 1 검사 실패, 2 환경 문제(Arise 없음, 창 없음). 창이 없으면 Arise를 활성화하고 File → New Window를 새로 관찰해 연 뒤 다시 실행한다(옛 AX 경로를 하드코딩하지 않는다).

## 아직 없는 것

- `dmem browser-mcp`·`doc_memory_clip_current_tab`(`IMP-19`, `SMK-10`, `HOST-09`): 제품 구현이 필요하다. 스모크 케이스 정의는 [`../host-smoke.md`](../host-smoke.md), 계약은 [`../../spec/web-import.md`](../../spec/web-import.md) 6절.
- Arise MCP 허브에 `dmem-mcp` 등록(`HOST-05`, `HOST-10`): 설정 절차를 Arise의 현재 UI로 확인해야 한다.
- 에이전트 행동(`BEH-*`), 연결 계정(`CUST-06`).
