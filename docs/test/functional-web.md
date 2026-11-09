# 기능 테스트: 웹 화면

상태: L3 웹 E2E 케이스 설계(실행 결과 아님). 테스트 대상은 [`../spec/web.md`](../spec/web.md)다.
영역 / 테스트 ID 접두사: `WEB` (예약 범위 01~30)
기반: [`../spec/runtime-v1.md`](../spec/runtime-v1.md), [`../spec/web.md`](../spec/web.md), [`fixtures.md`](fixtures.md), [`functional-tests.md`](functional-tests.md), [`hosts/arise.md`](hosts/arise.md)

## 1. 환경과 판정

모든 케이스는 Arise의 공개 stdio MCP(`agent_browser --mcp-server`)로 실행한다. run마다 고유 `session_id`를 쓰고 `browser_new_tab(..., activate=false)`로 자기 소유 background 탭에서 앱을 연다. `ready=true`만 믿지 않고 대상 경로가 될 때까지 기다린다. 사용자·다른 세션 탭은 읽거나 닫지 않으며 종료 때 자기 탭만 `browser_close_tab`하고 `browser_release`한다. 전역 `browser_close`는 쓰지 않는다([`hosts/arise.md`](hosts/arise.md), 직접 확인 2026-11-09).

`R1`은 runtime-v1 로컬 기능, `F`는 runtime-v1 이후 전체 범위다([`../README.md`](README.md) 2절). 화면 문구·포커스는 해당 탭의 접근성 트리/DOM으로, 네트워크와 저장 변화는 fixture 요청 로그·테스트 저장소 oracle로 판정한다. 임의 포트의 loopback fixture와 `DMEM_ISOLATED=1`을 쓰고 모든 신원·자료는 [`fixtures.md`](fixtures.md)의 합성 입력이다.

## 2. 케이스

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| WEB-01 | `R1`; `RCL-LIB`의 M1·M2를 seed하고 `/library`를 연다 | 두 항목의 L1 제목·`resume`·locale이 목록에 보이고 L2 본문은 없다; 화면 항목 수와 seed 2건이 일치한다 |
| WEB-02 | `R1`; 빈 `DMEM_HOME`에서 `/library`를 연다 | `empty` 상태와 새 메모리 행동이 보이고 오류 코드·목록 행은 0건이다 |
| WEB-03 | `R1`; M6·M6b seed 후 라이브러리의 kind=`reference`, provider=`markdown`, 검색어 `환불` 선택 | 결과는 M6만 포함하고 배송 문장 M6b는 없다; loopback 요청 로그는 0건이다 |
| WEB-04 | `R1`; M1 상세를 열고 L2 펼침 버튼을 키보드로 작동한다 | 초기 `aria-expanded=false`에서 `true`로 바뀌고 해당 항목의 L2만 나타난다; 다른 목록 항목은 확장되지 않는다 |
| WEB-05 | `R1`; M1 v1을 `base_version=1`로 v2 저장한 뒤 상세를 다시 연다 | 현재 버전은 v2, 이전 버전 선택은 v1로 표시되고 v1·v2 L2 내용이 서로 섞이지 않는다 |
| WEB-06 | `F`; recall에 `https://docs.google.com/document/d/GDOC_ID_SENTINEL_0123456789ABCDEFGHIJ/edit?token=Q_SENTINEL&resourcekey=RK_SENTINEL_x#heading=F_SENTINEL` 입력, `resume/ko-KR/google_docs` 선택 | 제출 후 입력칸·결과는 `docs.google.com/document/d/:id/edit`만 보이고 요청에도 query·fragment·원 ID가 없다; RCL-LIB M1이 후보에 든다 |
| WEB-07 | `F`; 같은 Docs 경로에 `resume/en-US/google_docs` 선택 후 recall | 결과에는 같은 호스트의 resume 후보만 있고 M2가 M3보다 앞선다; 화면의 선택 locale은 `en-US`다 |
| WEB-08 | `F`; recall에서 provider=`dropbox`, doc_type=`resume` 입력 후 제출 | 요청 전 `invalid_form`/`provider_unknown` 코드가 보이고 recall 요청은 0건이며 입력 수정이 가능하다 |
| WEB-09 | `F`; `https://example.org/other`와 `memo/ko-KR/markdown`으로 recall | 성공한 빈 결과 `no_match` 상태이며 `not_found` 오류나 메모리 행은 없다 |
| WEB-10 | `F`; fixture 검색 provider에 `이력서 양식`, locale=`ko-KR`, doc_type=`resume`으로 `/web-search` 제출 | 검색 목록에 `한국어 이력서`가 나오고 URL은 `fixture.test/pages/resume-ko.html`로 표시된다; 후보는 최대 10건이고 저장 변화는 0이다 |
| WEB-11 | `F`; fixture 검색어 `__mode:hostile` 제출 | `<script>`·제어 문자·HTML 태그가 실행/마크업 되지 않고 안전한 텍스트로만 보인다; 페이지 제목·버튼이 주입 문구로 바뀌지 않는다 |
| WEB-12 | `F`; `DMEM_SEARCH_PROVIDER=none`, 검색어 `회의록` 제출 | `search_unavailable` 코드와 재시도/직접 URL 행동이 보이고 fixture 요청·저장은 0건이다 |
| WEB-13 | `F`; 기본 fixture 검색에서 첫 `한국어 이력서` 후보 선택 | `web_search` 1회 후 `web_preview` 1회, 미리보기는 헤딩·`CC-BY-4.0`·만료 시각을 표시하고 `import` 호출과 라이브러리 변경은 0건이다 |
| WEB-14 | `F`; 시험 검색 provider가 `http://10.0.0.5/private` 후보를 돌려주는 응답으로 검색 화면을 연다 | 비허용 후보가 목록·링크에 없고 선택 가능한 preview가 없다; 해당 주소에 대한 fixture/외부 요청은 0건이다 |
| WEB-15 | `F`; WEB-13의 미리보기에서 가져오기 확인을 한 번 누른다 | `import(preview_id)` 1회, 저장 항목 1건; `origin=fetched`, 라이선스·`content_hash`가 미리보기와 같고 성공 상태에 새 항목 링크가 보인다 |
| WEB-16 | `F`; 미리보기를 만든 뒤 시계를 16분 전진해 같은 preview 화면을 연다 | `not_found` 코드와 다시 검색 행동이 보이고 가져오기·저장 변화는 0건이다 |
| WEB-17 | `F`; 공개 카탈로그에 S1, S9를 준비하고 `/community`에서 `resume` 검색 | 공개 S1만 보이고 비공개 S9는 목록·결과 수·페이지 이동 어디에도 없다; S1에 `CC-BY-4.0` 출처가 보인다 |
| WEB-18 | `F`; 공개 S1 상세를 열고 L2를 펼친다 | L1이 먼저 보이고 확장 후 L2와 `alice`·버전·`CC-BY-4.0` attribution이 함께 보인다; `source_ref`·원본 파일은 없다 |
| WEB-19 | `F`; `/community/:memory_id`에서 비공개 S5와 임의 없는 ID `mem_missing`을 각각 연다 | 두 응답의 화면 heading·안내·고정 `not_found` 코드가 같다; 어느 쪽도 공개 여부나 소유자를 드러내지 않는다 |
| WEB-20 | `F`; 공개 S1에서 copy 확인을 누른다 | 새 private 메모리 1건이 보이고 `derived_from`은 S1의 version·`alice`·`CC-BY-4.0`; S1 내용과 version은 불변이다 |
| WEB-21 | `F`; unknown 라이선스 구조 전용 S3 상세에서 본문 보기 및 `copy_mode=full` 요청 | L2 prose `PROSE_SENTINEL_S3`는 없고 full 복사는 `license_forbids`/허용 모드 `structure_only`; 저장은 0건이다 |
| WEB-22 | `F`; 내 S5 게시 화면을 연다 | `share-v1` 동의는 기본 해제, 라이선스는 미선택, 게시 버튼은 비활성이고 화면 열기만으로 publish 요청은 0건이다 |
| WEB-23 | `F`; 게시 라이선스 선택지를 연다 | 선택지는 `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `MIT`, `Apache-2.0`; `unknown`과 `proprietary-structure-only`는 게시 선택지에 없다 |
| WEB-24 | `F`; S5 게시에서 `share-v1` 동의와 `CC-BY-4.0` 선택 후 한 번 제출 | 요청에 `consent=true`, `consent_version=share-v1`, 선택 라이선스가 있고 1건만 접수된다; 화면은 `queued`/검수 중이며 승인 전 `published`라고 하지 않는다 |
| WEB-25 | `F`; `license-none.html`을 먼저 가져와 생성한 `unknown` 라이선스 메모리에 `CC0-1.0`으로 게시를 시도한다 | `license_forbids` 고정 코드가 보이고 공개 카탈로그·동의 기록 변화는 0건이다; 서버 원문이나 입력 URL은 표시되지 않는다 |
| WEB-26 | `R1`; `/forms/select`에서 country=`KR`, provider=`google_docs`, doc_type=`resume` 선택 | 선택 요약은 `region=KR`, `locale=ko-KR`, provider `google_docs`, family `document`; 지원 양식만 결과에 보인다 |
| WEB-27 | `R1`; country=`US`, provider=`google_docs`, doc_type=`resume` 선택 | 선택 요약은 `locale=en-US`, region `US`, 페이지 `Letter`; KR 선택을 바꾸면 이전 locale이 남지 않는다 |
| WEB-28 | `F`; 양식 선택에서 provider=`dropbox`와 `resume` 제출 시도 | `invalid_form`/`provider_unknown`이 표시되고 저장·recall 요청은 0건; 유효한 provider로 수정할 수 있다 |
| WEB-29 | `R1`; recall 요청을 지연 2초로 설정해 제출 두 번 누른 뒤 첫 응답을 `server_unavailable`로 완료 | 즉시 `loading`과 비활성 버튼이 보이고 요청은 1건; 오류 뒤 입력은 남고 고정 코드·재시도 행동이 보인다 |
| WEB-30 | `F`; WEB-06 URL과 `Q_SENTINEL`, `F_SENTINEL`, `GDOC_ID_SENTINEL_0123456789ABCDEFGHIJ`로 키보드만 사용해 recall 완료 | label·초점·live 오류가 접근성 트리에서 확인되고 제출 후 화면/앱 URL/오류/저장/요청에 세 센티널·secret이 0건; tab 순서로 요청을 끝낼 수 있다 |
