# Web memory v1 설계·원인·리뷰

2026-11-09. 계약: [`../spec/web-memory-v1.md`](../spec/web-memory-v1.md), 입력/기대 결과: [`../test/web-memory-v1.md`](../test/web-memory-v1.md).

기존 제품에는 파일 업로드·양식/자료/작성 문서·공개 기여·recall이 있었지만 URL fetch/search/preview와 현재 탭 clip은 명세/더블에만 있었다. 이제 실제 Rust API·CLI·MCP·Svelte 화면에 intake v1을 연결했다. 배포나 사용자 설정 변경은 하지 않았다.

## 설계와 경계

`dmem-contracts/src/web.rs`가 공통 DTO다. `dmem-core/src/web.rs`는 네트워크 없이 HTML 파싱·본문 순서·복사 정책·주소 판정을 맡는다. `dmem-server/src/web.rs`가 DNS pinning·hop별 검사·상한·Brave 검색·소유자별 preview snapshot을 관리하고, `web_store.rs`가 항목·출처·멱등 키를 한 트랜잭션으로 저장한다. preview는 15분/owner 16개/global 64개이며 각 추출물은 1MiB 이하로 제한한다. URL 응답은 5MiB/전체 10초/동시 4개다. loopback 예외는 테스트에서 주입한 정확한 socket address 하나다. 제품 환경 변수로 SSRF 검사를 끌 수 없다.

출처 원장은 canonical URL·정규화 form·license·copy policy·hash·시각·provenance를 보존한다. 비공개 복사·참고자료→양식 추출·불변 기여 snapshot·승인된 공개 항목에도 권리가 이어진다. 공개 출처 조회는 `@catalog` 항목에만 허용한다. 외부 unknown/제약 있는 출처의 CC0 게시와 CC-BY의 CC0 변경은 거부한다. recall의 사용자 직접 작성물 기본 정책도 외부 원장보다 우선할 수 없다.

`dmem-mcp/src/bridge.rs`는 공개 browser stdio child 한 개를 유지하고, browser 도구와 메모리 21개 도구·clip 별칭 2개를 함께 제공한다. child에 라이브러리·캡처·관리자 비밀을 넘기지 않는다. 이름이 같은 public session만으로 clip을 허용하지 않는다. native 평가에 필요한 private lease가 보존된 연결에서만 캡처가 성공해야 하고, 전후 client/session/window/tab/URL/만료 검사를 모두 통과해야 저장한다. 설치된 Arise 0.1.77은 `has_local_lease` 필드를 생략하므로 native 평가 성공과 전후 일치도 필수 근거다. 명시적으로 false인 lease는 즉시 거부한다.

모델 입력에는 URL/HTML을 받지 않는다. 정적 캡처 함수는 보이는 문서 구조만 읽으며 폼 값·Cookie·storage를 읽지 않는다. 서버는 본문과 시각에 대한 HMAC을 검증한 경우만 captured로 기록한다. 일반 HTTP 입력은 claimed이며 native browser 캡처를 사칭할 수 없다. 사용자가 직접 서명 비밀을 가진 환경에서의 운영자 신뢰까지 browser attestation으로 증명하는 기능은 아니다.

## 실패 재현과 수정

| 원인 | 수정 | 독립 재검증 |
|---|---|---|
| 한국어 preview에서 영어로 바꿀 때 이전 KR region이 남음 | locale select의 실제 선택값으로 region 갱신 | Playwright red `20261109-134725-7276/web.log`의 Expected US/Received KR → WI-18 두 케이스 통과 |
| public 필터/다른 언어 때문에 저장한 양식이 목록에 안 보임 | 가져오기 후 해당 언어·private·전체 종류로 목록 갱신 | red `20261109-135126-9552/web.log`의 Expected private/Received public → 목록 버튼과 HTTP form 확인 |
| en-GB가 en-US로 일반화됨 | 알려진 전체 locale를 먼저 보존한 뒤 언어 fallback | `wi11_detected_british_locale_keeps_its_region`: en-GB/GB 통과 |
| 정상 `password: {{password}}`를 JSON 전체에서 검사해 비밀로 오인 | 실제 필드 문자열 검사, 기존 검수와 같은 placeholder 판정 재사용 | 정상 placeholder 허용/실제 합성 비밀 거부 red→green |
| heading 배열과 body 배열을 순서대로 합쳐 참고문서 순서가 바뀜 | HTML DOM·문서 block·slide 순서의 `WebPart`를 별도로 보존 | `wi12_reference_text_keeps_headings_with_their_original_paragraphs` red→green |
| reference의 form이 멱등 키에만 있고 DB에 남지 않음 | 출처 원장에 form 저장, 양식 추출 시 계승 | `wi11_reference_form_survives_reload_and_template_extraction`: origin locale Null→ja-JP, DB 재열기 뒤 Google Docs/resume/JP/variant 일치 |
| private 외부 항목을 recall에서 직접 작성물로 취급해 full로 표시 | 외부 원장의 정책으로 보정하고 같은 토큰 예산 재적용 | `wi13_recall_does_not_upgrade_external_copy_rights`: full→structure_only, unknown/imported 확인 |
| 저장 알림과 목록 loading status가 동시에 나타나 테스트 locator가 모호함 | 가져오기 panel 안의 status를 검증 | strict locator 실패 재현 뒤 Playwright 두 케이스 통과 |
| native 탭 닫기 응답 뒤 잠시 탭이 남고, 이동 중 평가가 일시 실패함 | 실제 탭 제거와 기대 DOM/입력 상태를 확인한 뒤 다음 단계로 진행 | 닫기 직후 남음·0.15초 뒤 제거 재현, 사용자 탭 전후 동등성은 그대로 유지 |
| 제목 입력 뒤 Save 버튼이 viewport 아래에 있어 native click 거부 | 설치본 도구 계약의 visible-target 조건을 확인하고 실제 geometry→`browser_scroll`→표시/활성 상태 검사→native click | top 904.95/bottom 943.45, viewport 651을 기록한 뒤 실제 저장·재조회·완료 PNG까지 33/33 통과 |

## 최종 리뷰와 제약

부모가 구현 파일·마이그레이션·관련 기존 코드와 실패/성공 결과를 직접 읽고 검증했다. 읽기 전용 위임 #170은 timeout/PARTIAL로 끝났고, 인용한 fixture 위치만 직접 열어 활용했다. 그 요약을 구현/검증 증거로 세지 않았다. 빌드·테스트·실제 Arise 입력은 모두 부모가 실행했다.

실행 명령·결과와 evidence 경로는 [테스트 문서](../test/web-memory-v1.md)에 있다. Arise 원본·웹 화면 PNG를 이미지 도구로 직접 검사했다. 사용자 탭은 전후 동일하고 생성한 탭과 임시 서버/DB만 정리한다. 다른 세션의 계정·관리자·데모 변경은 보존한다.

실제 Google 로그인·Brave 운영 키는 사용하지 않았다. Google export와 검색 응답은 결정적인 fixture로 검증한 범위다. OAuth 동기화, Sheets 편집/수식, PDF/OCR, 복잡한 Office/CSS 레이아웃 복원, reference recall 확장은 후속 범위다. HTML fetch는 원격 JavaScript를 실행하지 않으며 CSS 숨김 규칙은 보수적으로 처리한다. 동적인 화면은 소유 Arise 탭 캡처를 사용한다. 전체 WAM 목표 계약·더블의 성공을 이 부분집합의 제품 성공으로 합산하지 않는다.
