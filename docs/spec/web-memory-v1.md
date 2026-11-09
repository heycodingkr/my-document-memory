# Web memory v1: 실제 URL 검색·미리보기·가져오기·Arise 클립

상태: 2026-11-09 로컬 구현. 편집 전에 고정한 이 계약은 `web-import.md` 전체 목표의 부분집합을 실제 Rust `document_*`·CLI·Svelte 제품에 연결한다. 입력·기대 결과와 실행 범위는 [`../test/web-memory-v1.md`](../test/web-memory-v1.md), 설계/검증은 [`../design/web-memory-v1-review.md`](../design/web-memory-v1-review.md).

## 사용자 동작과 계약

- 내 라이브러리의 웹 가져오기 화면에서 URL을 미리보고 문서 종류·국가/언어·provider를 확인한 후 비공개 양식 또는 참고자료로 저장한다. 원본 출처·라이선스·가져온 시각·내용 hash를 재조회할 수 있다.
- 검색은 설정된 Brave Search API를 사용한다. 키가 없으면 검색 미설정 상태를 명시하고 URL 붙여넣기는 계속 동작한다. 검색은 후보만 반환하고 자동 크롤링·저장하지 않는다. 키는 서버 환경에만 둔다.
- 실제 HTTP는 `/v1/web/search`, `/v1/web/preview`, `/v1/web/import`, `/v1/web/clip`, `/v1/web/origins/{id}`다. 기존 Bearer/세션·CSRF 소유자 경계를 그대로 적용한다.
- 실제 stdio MCP는 `document_web_search`, `document_web_preview`, `document_web_import`, `document_web_origin`을 추가한다. CLI는 `dmem web search|preview|import|origin`과 `dmem browser-mcp --browser-mcp <path>`를 제공한다. 기존 파일 `import`는 보존한다.
- URL fetch는 HTTPS/443, 공개 DNS의 모든 주소 확인·연결 pinning·프록시 비활성화·hop별 재검사, redirect 최대3·전체10초·본문5MiB를 적용한다. 사용자 Cookie/Authorization·원문 URL을 로그로 보내지 않는다. loopback 테스트 예외는 명시적으로 주입한 주소 하나에만 적용하며 기본 제품에서는 꺼져 있다.
- HTML은 html5ever 기반 파서로 제목·헤딩·표 머리글·본문을 추출한다. 스크립트·스타일·폼·숨김·제로폭·주입 지시와 비밀값은 저장에서 제외/거부한다. 비밀번호·결제 폼과 noai는 거부한다. 파싱·네트워크 실패는 고정 오류/이유만 반환한다.
- URL 콘텐츠는 HTML·plain text·Markdown과 아래 Google export를 지원한다. 참고자료는 헤딩과 본문의 원래 순서를 유지한다. HTML은 원격 JavaScript를 실행하지 않으며 완전한 CSS 레이아웃을 재구성하지 않는다. 동적 페이지의 현재 보이는 내용은 소유 Arise 탭 클립을 사용한다.
- 공개 Google Docs는 DOCX, Slides는 PPTX export로 가져오고 기존 추출기를 재사용한다. URL의 파일 ID·query·fragment는 출처에 저장하지 않는다. 로그인 필수 문서는 파일 업로드나 소유 Arise 탭 클립을 안내한다. OAuth 계정 동기화·Sheets 전체 편집·OCR은 이 intake 계약에 포함하지 않는다.
- preview는 소유자별 임시 메모리(15분·개수/bytes 상한)에만 보관하고 item을 저장하지 않는다. import는 같은 preview 스냅샷을 사용하며 만료·타 소유자 ID는 동일 not_found다. 같은 owner·source·form·content·copy mode 재요청은 같은 항목을 반환한다.
- 선택한 정규화 form은 template뿐 아니라 reference의 출처에도 영속 저장한다. 웹 reference에서 양식을 추출할 때 그 form과 외부 권리를 이어받는다. 기존 recall v1의 대상은 양식이며 reference는 별도 검색·읽기를 사용한다.
- 라이선스 기본값은 unknown. 검출된 CC0/CC-BY/MIT/Apache의 허용 범위에서만 full copy를 허용한다. 그 외는 structure_only이며 본문·목록·표 본문은 저장하지 않는다. 가져온 외부 양식은 provenance가 검수에서 보존되어 임의 재라이선스로 게시되지 않는다.
- 기존 recall v1 순위는 유지한다. 웹 출처가 있는 힌트는 출처 원장의 license/copy policy를 반환하고, 사용자 직접 작성물의 기본 `full` 정책을 적용하지 않는다. 직접 가져온 항목의 source origin은 `imported`, 개인 복사본은 `copied`다.
- browser 어댑터는 공개 stdio MCP child 한 연결을 유지한다. 캡처 전후 context의 client/session/window/tab/URL/lease 소유권을 확인한다. 입력에 URL/HTML을 받지 않는다. 화면에 보이는 문서만 캡처하며 폼 값·cookie/storage는 읽지 않는다. 교체·만료·사용자/타 세션 탭은 저장 전에 거부한다.
- 임의 HTTP HTML 입력은 claimed provenance다. 어댑터가 `DMEM_CAPTURE_SECRET`으로 본문·시각에 서명한 요청만 captured로 기록한다. 서버와 어댑터에 같은 비밀을 설정하며 MCP 도구 인수·로그에는 노출하지 않는다. 미설정이면 캡처를 명시적으로 거부한다.

## 의존 순서 원자 목표

| 단계 / route | 출력 | 독립 확인 | 선행 |
|---|---|---|---|
| W0 / 직접 | 현재 git·코드·테스트·이슈와 이 계약·입력/기대 결과 | 실제 소스 읽기 | 없음 |
| W1 / 직접 | DTO·HTML 추출/복사 정책·공개 주소 판정, 먼저 실패하는 테스트 | 정상·적대 fixture red→green | W0 |
| WG / `codex:gpt-6-luna` background 읽기 | 기존 더블/fixture의 재사용 지점 15줄 이내 file:line | 인용 파일 직접 열기; 요약은 증거가 아님 | W0; W1과 독립 |
| W2 / 직접 | 제한 fetch·preview 캐시·소유자별 원자 저장/출처 | 임시 HTTP/DB·DNS/redirect·멱등/격리 테스트 | W1, WG |
| W3 / 직접 | API·CLI/MCP·웹 가져오기 화면 | 실제 바이너리와 웹 입력/기대 결과 | W2 |
| W4 / 직접 | 보존 연결의 browser-MCP 어댑터와 소유 탭 클립 | 가짜 MCP 음성 대조, 실제 Arise 캡처/저장/재조회 | W2; W3과 순차 통합 |
| W5 / 직접 | 전체 Rust·기존 제품 회귀·신규 스모크·웹 check/build·Arise | 부모 실행 로그와 이미지 검사, 최종 diff/원인/리뷰 | W3, W4 |

배포와 사용자 설정 교체는 이 구현에 포함하지 않는다. 기존 동시 작업을 보존한다.
