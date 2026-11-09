# Arise 다중 문서 데모 실측 — 2026-11-09

**결과: 공개 Arise MCP 연결을 유지하면 Slides 10장, Docs 1페이지, 네이버 미발행 초안의 작성·저장·새 탭 재열기가 모두 동작한다. MeshCode 중계 호출 사이의 탭 제어 권한은 별도 차단 이슈 #395다.**

명세: [multi-app-browser-demo-v1.md](../spec/multi-app-browser-demo-v1.md).

후속 수정: [블로커 수정·적용 기록](arise-mcp-blockers-v1.md). #395와 #396의 관련 테스트 192개가 통과했고, 사용자 승인 후 로컬 설치본·MCP 설정·새 공용 데몬에 반영하여 실제 중계 경로까지 재검증했다. 아래 내용은 최초 데모 당시의 관측이다. 최종 적용 확인 때 Slides 59·네이버 63은 유지했고, 닫혀 있던 Docs 요약문은 저장본을 다시 열어 탭 126에 두었다.

이번 검증은 Codex가 Arise의 실제 브라우저 도구로 세 편집기를 조작한 스모크다. Arise 내장 AI에 단일 프롬프트를 입력하고 Document Memory 검색부터 세 결과물 완성까지 자동 진행하는 흐름은 실행하지 않았다. 브라우저 조작 성공을 제품의 Google/Naver 직접 API 연동 완료로 해석하지 않는다. 결과물은 기능 확인용 기본 텍스트 구성이다.

## 실제 결과물

| 서비스 | 저장 결과 | 남겨 둔 전용 창 / 탭 |
|---|---|---|
| Google Slides | [MDM Demo QA — My Document Memory Deck](https://docs.google.com/presentation/d/1ABtGK92zcRBSrwsO5zE2yNeI1gONSZcWg5qyg6NoEG4/edit): 서로 다른 제목과 본문이 있는 10장 | 창 12 / 탭 59 |
| Google Docs | [MDM Demo QA — One-page Overview](https://docs.google.com/document/d/1xX8gl534tE4N_oCUgdNCSRi99gUcqGV4HtS68PiSL8E/edit): Letter 세로, 실제 1페이지 | 창 16 / 탭 61 |
| Naver Blog | `MDM Demo QA — One brief, three documents`: 제목과 영문 본문을 임시저장하고 새 편집기에서 다시 불러옴. [글쓰기](https://blog.naver.com/GoBlogWrite.naver)의 임시저장 1개 목록에서 찾을 수 있다 | 창 14 / 탭 63 |

Google 결과물은 나에게만 공개인 상태에서 작성했다. 네이버 발행 버튼은 누르지 않았다. 기존 사용자 문서를 편집하지 않았다.

## 테스트 결과

| ID | 판정 | 직접 확인 |
|---|---|---|
| MAB-01 | PASS | 세 서비스가 별도의 소유 창에 열리고 실제 서비스 URL까지 이동함 |
| MAB-02 | PASS, 네이버 사전 로그인 필요 | Google은 기존 로그인으로 편집 가능. 네이버는 저장 계정 로그인 → 영수증 보안 확인 → 사이트가 요청한 재로그인 후 편집기에 진입 |
| MAB-03 | PASS | 제목·본문 입력 후 Drive 저장 표시 확인. 새 탭에서 다시 열고 탐색 영역의 슬라이드 번호 1~10과 서로 다른 제목 10개를 재확인 |
| MAB-04 | PASS | 초기 페이지 없음 형식을 페이지 형식으로 전환. 새 탭 재열기에서도 `.kix-page-paginated` 1개와 Drive 저장 표시 확인. 본문 상단·하단 스크린샷을 직접 검사 |
| MAB-05 | PASS | 실제 저장 후 임시저장 개수 0 → 1. 새 글쓰기 탭에서 해당 제목의 저장 항목을 선택하고 전체 본문 끝 문장까지 재조회·이미지 검사 |
| MAB-06 | PASS, 연결·프레임 우회 적용 | Slides → Naver → Docs → Slides의 탭 선택이 모두 `selection_verified=true`. Slides 10장·Docs 1페이지·네이버 제목/본문 표식이 모두 남아 있음 |
| MAB-07 | PASS | 각각 새로 만든 탭에서 서버 저장본을 다시 열었음. 동일 편집기에서 입력값만 읽은 결과와 구분 |
| MAB-08 | PASS, 미수정 문제 등록 | 연결 권한 #395와 iframe 경로 #396을 재현하고 동작하는 대안을 독립적으로 확인. 제품/Arise 소스 수정은 하지 않음 |

최종 합성 검증은 `.artifacts/multi-app-browser-demo/verification-summary.json`의 `allPass=true`다. 슬라이드 전체의 텍스트는 DOM으로 검사했고, 화면은 표지·2장·6장·10장 등 대표 장면을 직접 보았다. 전체 슬라이드의 디자인 완성도를 검수한 결과는 아니다.

## 블로킹 지점과 원인 경계

### #395 — 중계 호출 사이에 탭 제어 권한이 이어지지 않음

올바른 인자로 다시 재현했다.

1. MeshCode `call_tool`을 통해 `browser_new_window(session_id=dmem-host-qa-7138, url=about:blank)` 호출. 창 21 / 탭 67과 lease 반환.
2. 다음 호출에서 같은 session_id, tab_id로 `browser_select_tab` 실행.
3. `This MCP connection has no valid lease token for this tab` 오류. 초기 테스트 창에서도 같은 경계를 관측했다.

같은 공개 세션 이름은 연결의 비공개 lease 증명을 대신하지 못한다. 중계 경로에서 증명이 유지되지 않는 것은 관측했으나, 호스트 내부 구현 원인은 읽지 않았다.

**검증된 우회:** 설치된 `/Applications/Arise.app/Contents/MacOS/agent_browser --mcp-server`의 공개 stdio 연결 하나를 유지한다. 같은 연결과 고유 session_id로 전용 창을 만들고, 입력 전에 정확한 탭을 선택한다. private socket이나 CDP는 사용하지 않았다. 이 경로로 세 결과물과 최종 창 전환 검증을 완료했다.

### #396 — 네이버 `browser_eval(frame=f0)`가 바깥 문서를 읽음

새로 불러온 동일 초안에서 `browser_snapshot`은 편집 요소를 `frame=f0`로 표시하고 `browser_read(frame=f0)`는 본문을 읽었다. 그러나 `browser_eval(frame=f0)`의 location은 바깥 블로그 URL이고 body는 빈 문자열이었다. 단순 표식 검사는 이 경우 초안이 없다고 잘못 판단한다.

**검증된 우회:** `browser_frames`에서 이름이 `mainFrame`인 프레임을 찾고, 반환된 현재 `cef:` 식별자를 `browser_eval`에 전달한다. `PostWriteForm.naver` URL에서 제목과 본문 표식이 모두 true였다. 프레임 식별자는 이동·재열기 후 다시 찾는다. 초안 손실은 없었다.

### 촬영 전 준비 사항

- **네이버 로그인:** 이번에는 영수증 보안 확인을 이미지로 읽어 지원 도구로 통과했다. 이후 사이트가 다시 로그인을 요청했고, 저장 계정을 채운 다음 정상 진입했다. 이 구간은 본 촬영 전에 끝내 두는 편이 좋다. 보안 설정은 변경하지 않았다.
- **긴 본문 입력:** 실제 키보드 입력은 수십 초 이상 걸릴 수 있다. 이번 진단 클라이언트의 25초·45초 응답 제한을 넘긴 호출도 있었지만, 나중에 본문 전체와 저장본이 확인됐다. 타임아웃만 보고 같은 글을 다시 입력하면 중복될 수 있다. 먼저 현재 내용과 저장 상태를 읽는다.
- **문서 제목:** 처음 입력 필드의 값만 바꿨을 때는 새 탭에서 제목 없는 문서로 열렸다. 실제 키보드 입력과 TAB으로 제목 변경을 마친 뒤 재열기에서 유지됨을 확인했다. 보이는 입력값만으로 저장을 판단하지 않는다.
- **Docs 1페이지:** 기본 페이지 없음 형식에서는 1페이지라는 조건을 확인할 수 없다. 페이지 설정을 적용하고 저장본에서 페이지 수를 확인한다. 이번 UI의 페이지 클래스는 `.kix-page-paginated`였다.
- **브라우저 동기화:** 이동·클릭·저장은 입력 전송 응답 직후 완료되지 않을 수 있다. 대상 URL, 실제 편집 요소, 저장 표시·임시저장 개수를 확인한 뒤 다음 창으로 이동한다. `browser_script`의 각 단계 인자 키는 `params`다.

## 증거와 정리

증거 경로: `.artifacts/multi-app-browser-demo/` (각 도구 응답 JSON과 실제 Arise 스크린샷).

- `verification-summary.json`: 최종 10장 / 1페이지 / 네이버 제목·본문 / 창 선택 4회 검증.
- `host-lease-reproduction.json`: 올바른 인자로 재현한 중계 연결 오류.
- `v2-236-browser_eval.json`, `v2-238-browser_eval.json`: 네이버 f0와 native mainFrame 읽기의 차이.
- `v2-207-browser_screenshot.png`: 새 탭에서 다시 연 Slides.
- `v2-211-browser_screenshot.png`, `v2-213-browser_screenshot.png`: 새 탭에서 다시 연 Docs 상단·하단.
- `v2-225-browser_screenshot.png`, `v2-233-browser_screenshot.png`: 새 네이버 편집기의 임시저장 목록과 불러온 초안.
- `cleanup-results.json`: 이 작업이 만든 중복·빈 탭만 정리한 기록. 세 결과물 창은 유지한다.

이번 작업은 명세·결과 기록과 브라우저 테스트만 수행했다. 제품 코드를 바꾸지 않아 빌드·단위 테스트는 실행하지 않았다. 다른 세션이 동시에 수정·커밋하던 파일과 기존 이슈의 담당 상태는 변경하지 않았다. 브라우저 조작과 판단, 재조회·이미지 확인은 모두 이 세션에서 직접 수행했다.
