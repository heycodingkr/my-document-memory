# Fixture 카탈로그

상태: 설계(문서 우선). 테스트 케이스([`functional-tests.md`](functional-tests.md), [`security-scenarios.md`](security-scenarios.md), [`host-smoke.md`](host-smoke.md))가 참조하는 합성 입력의 단일 정의다. 구현 위치: `tests/fixtures/`(빌더·데이터), `tests/env/fixture-sites/`(웹 fixture 서버), `tests/sentinels.json`(센티널).
원칙: **합성 값만** 쓴다. 실제 개인 문서·계정·키·사이트를 쓰지 않는다. 바이너리 파일(DOCX·PPTX·PDF)은 저장소에 두지 않고 빌더가 실행 때 임시 디렉터리에 만든다.

## 1. 신원

| 이름 | 상태 | 용도 |
|---|---|---|
| `anon` | 익명(연결 없음) | 공개 읽기, 쓰기 거부 |
| `alice` | 연결됨, 공개 핸들 `alice`, workspace `acme` 구성원 | 작성자·게시자 |
| `bob` | 연결됨, 핸들 `bob`, workspace 없음 | 다른 사용자(복사·침범 시도) |
| `carol` | 연결됨, 핸들 `carol`, workspace `acme` 구성원 | 팀 구성원 |
| `local` | 계정 없는 로컬 모드 | 로컬 라이브러리 |

테스트 더블은 `DMEM_TEST_IDENTITY`(`anon`\|`alice`\|`bob`\|`carol`\|`local`)로 신원을 정한다. 제품에는 이 변수가 필요 없다. 제품 대상 실행은 신원마다 별도 토큰·데이터 디렉터리로 한다.

## 2. 내 라이브러리 `RCL-LIB`

저장 순서가 `updated_at` 순서다(하네스는 저장 사이에 1초 이상 둔다). 더블은 명시적 id·시각(`fx_m01`…)을 쓰고 제품은 생성된 id를 쓴다. 표의 "tier"는 호출자(`local` 또는 `alice`) 기준이다.

| ID | kind | doc_type | locale / variant | provider | site_host | `url_patterns` | tier·가시성 | 라이선스 | keywords | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | template | resume | ko-KR | google_docs | docs.google.com | `/document/d/:id/edit` | mine | — | `resume` | 정확 route |
| M2 | template | resume | en-US, page Letter | google_docs | docs.google.com | `/document/*` | mine | — | `resume` | 미국식 |
| M3 | template | resume | ja-JP / `jp_rirekisho` | google_docs | docs.google.com | `/document/*` | mine | — | `resume` | M2보다 나중에 저장 |
| M4 | template | resume | ko-KR | google_docs | docs.google.com | `/*` | team(acme) | — | `resume` | alice 게시 |
| M5 | template | resume | ko-KR | html | www.example.org | `/templates/*` | public(alice) | CC-BY-4.0 | `resume` | 다른 호스트 |
| M6 | reference | other | ko-KR | markdown | example.com | `/*` | mine | — | `refund` | 문장 "환불은 미개봉 상품에 한해 구매 후 7일 이내 신청 가능" (span `p:1`) |
| M6b | reference | other | ko-KR | markdown | example.com | `/*` | mine | — | `shipping` | 문장 "배송은 영업일 기준 3일 이내" (섞이면 안 되는 다른 사실) |
| M7 | style_rule | official_letter | ko-KR | other | example.com | `/*` | mine | — | `formal` | rules: 합니다체, 날짜 `YYYY. M. D.` |
| M8 | template | pitch_deck | en-US, page 16:9 | google_slides | docs.google.com | `/presentation/*` | mine | — | `pitch`, `deck` | deck |
| M9 | template | invoice | ko-KR / `kr_tax_invoice` | notion | www.notion.so | `/*` | mine | — | `invoice`, `tax` | |
| M10 | template | memo | ko-KR | docx | example.com | `/*` | mine | — | — | provider 동점 시험(resume 질의에 끼지 않도록 `memo`) |
| M11 | template | memo | ko-KR | markdown | example.com | `/*` | mine | — | — | M10과 같은 시각 |
| M12 | template | report | ko-KR | google_docs | docs.google.com | `/document/*` | mine | — | `weekly` | keyword 시험 |
| M13 | template | report | ko-KR | google_docs | docs.google.com | `/document/*` | mine | — | `draft` | keyword 시험 |
| M15 | template | lesson_plan | ko-KR | google_docs | docs.google.com | `/document/*` | mine | — | — | tier 시험(3종은 시각 동일) |
| M16 | template | lesson_plan | ko-KR | google_docs | docs.google.com | `/document/*` | team(acme) | — | — | |
| M17 | template | lesson_plan | ko-KR | google_docs | docs.google.com | `/document/*` | public(alice) | CC0-1.0 | — | |

M1~M5 기대 순위는 [`functional-tests.md`](functional-tests.md) RCL-01~04가 계산해 둔 값이다.

## 3. 공유 카탈로그 `SHR-CAT`

| ID | 소유 | 가시성 | 라이선스 / 출처 | 내용 |
|---|---|---|---|---|
| S1 | alice | public | CC-BY-4.0, origin user | `catalog_scope=(www.example.org,/templates/*,template,html,resume,ko-KR,KR,null)`; resume 본문에 `PROSE_SENTINEL_S1` 포함 |
| S9 | bob | private | CC-BY-4.0, origin user | S1과 같은 `catalog_scope`; 섹션 순서 목표→경험→프로젝트, 본문 `PROSE_SENTINEL_S9`; S1과 다른 fingerprint, 공개 기여 테스트용 |
| S2 | alice | public | CC-BY-SA-4.0, origin user | 회의록 템플릿 ko-KR |
| S3 | alice | public | unknown, origin fetched | 웹에서 가져온 구조 전용 양식. 본문에 prose `PROSE_SENTINEL_S3`가 있지만 구조 전용 정책이라 다른 사용자에게는 구조(제목·표)만 보인다 |
| S4 | alice | team(acme) | — | 팀 전용 견적서 |
| S5 | alice | private | — | 비공개 양식(`PRIVATE_SENTINEL_S5` 포함) |
| S6 | bob | private | — | 비공개 참고자료 |
| S7 | alice | public | proprietary-structure-only | 구조 전용 허용 양식 |
| S8 | alice | private | — | `contains_personal_data: true`인 reference |

## 4. 웹 fixture 서버

`tests/env/fixture-sites/fixture_server.py`는 임의 빈 포트의 loopback에 바인딩하고 요청 로그(JSON 라인)를 남긴다. 테스트는 `DMEM_ISOLATED=1`([`../spec/core.md`](../spec/core.md) 9절)로 실행한다.

| 경로 | 동작 |
|---|---|
| `/pages/resume-ko.html` | 한국어 이력서 양식(`<html lang="ko">`, 미국식 페이지는 `lang="en"`: preview가 locale을 제안할 단서). 제목·헤딩(인적사항·경력·학력·기술), 표, `<link rel="license" href="https://creativecommons.org/licenses/by/4.0/">`, prose `PROSE_SENTINEL_1~5` |
| `/pages/resume-us.html` | 미국식 resume. 라이선스 표식 없음 |
| `/pages/license-cc0.html`, `license-by-sa.html`, `license-mit.html`(meta), `license-jsonld.html`, `license-nc.html`(CC BY-NC 4.0), `license-none.html` | 라이선스 변형 |
| `/pages/noai-meta.html` / `/pages/noai-header.html` | `<meta name="robots" content="noai">` / 응답 헤더 `X-Robots-Tag: noai` |
| `/pages/hostile-inject.html` | **활성** 적대 페이지: 보이는 주입 문구, 숨김 문구(`HIDDEN_SENTINEL_1~3`), 제로폭·양방향 문자에 더해 `<script>`(DOM 덮어쓰기)·`<iframe>`·`onerror=alert()`. 실제 브라우저에서는 페이지가 스스로 DOM을 바꾸고 JS dialog를 띄운다(Arise 실측). 가져오기 살균·dialog 처리 검증용 |
| `/pages/hostile-static.html` | **정적** 적대 페이지: 위와 같은 텍스트 공격(보이는 영어·한국어 주입 문구, 외부 전송·명령 실행 문구, `display:none`·크기 0·배경색 동일 텍스트의 `HIDDEN_SENTINEL_1~3`, 제로폭·양방향 문자)이지만 스크립트·iframe이 없어 DOM이 유지된다. Arise landmark 검사와 `clip_current_tab` 살균 검증용 |
| `/pages/login-required` | 302 → `/login`(비밀번호 입력 폼). `/pages/forbidden`은 403, `/pages/unauthorized`는 401 |
| `/redirect/<n>` | n회 리다이렉트 후 `/pages/resume-us.html`(`?to=<경로>`는 브라우저·직접 호출에서만 쓴다. 가져오기는 쿼리를 버린다). `/redirect/private`는 `http://10.255.255.1/`로. `/redirect/downgrade`는 loopback fixture가 http뿐이라 https→http 다운그레이드를 만들 수 없어 L0 단위 시험이 맡는다 |
| `/big`(6 MiB, `text/plain`), `/gzbomb`(gzip 해제 후 200 MiB의 0, `text/plain`) — 허용 형식이라 **크기 상한**이 중단 원인, `/slow`(15초 지연), `/type-mismatch.docx`(HTML 본문에 docx Content-Type), `/binary`(`application/octet-stream`) | 크기·시간·형식 |
| `/p/google-docs/document/d/FIX_KO_RESUME/edit` | Docs 모양 페이지(제목만) |
| `/p/google-docs/document/d/FIX_KO_RESUME/export?format=md\|html\|docx\|txt` | Docs 내보내기 모사(미검증 경로를 흉내 낸 것, [`../spec/formats.md`](../spec/formats.md) 3절) |
| `/p/google-slides/presentation/d/FIX_DECK/export?format=pptx` | Slides 내보내기 모사. `format=md`·`html`은 400 |
| `/p/google-sheets/spreadsheets/d/FIX_SHEET/export?format=csv\|xlsx` | Sheets 모사(`?variant=csv-only`면 csv만) |
| `/p/notion/Quarterly-Report-0123456789abcdef0123456789abcdef` | Notion 모양 공개 HTML(제목·목록·표·콜아웃) |
| `/search?q=…` | `fixture` 검색 provider의 고정 JSON 결과(후보 8개, 사설 주소 후보 1개 포함) |

테스트 전용 확인용 호출: `GET /__log`(요청 로그), `POST /__reset`. 요청 로그에는 메서드·경로·쿼리 유무·헤더 이름이 남고 헤더 값은 남지 않는다(자격증명 전송 검사는 헤더 **이름**으로 한다).

## 5. 파일 빌더 (`tests/fixtures/builders.py`)

| 이름 | 내용 |
|---|---|
| `tpl01-monthly-report.docx` | Title·Heading1 스타일, 본문 스타일, 2×3 표, 섹션 순서 요약→지표→위험→요청 (`TPL-01`) |
| `deck-5.pptx` | 슬라이드 5장(표지·문제·해결·시장·요청), 16:9, 테마 색 |
| `resume-ko.md`, `invoice-kr.md`, `empty.txt`, `whitespace.txt`, `unicode.txt` | 텍스트 입력 |
| `text.pdf`, `scan.pdf` | 텍스트 레이어가 있는 단순 PDF, 이미지뿐인(텍스트 없음) PDF |
| `evil-macro.docx` | `word/vbaProject.bin` 포함 |
| `evil-external.docx` | 외부 관계(`TargetMode="External"`, `attachedTemplate`을 fixture 서버 URL로) |
| `evil-dde.docx` | `DDEAUTO` 필드 지시문 |
| `evil-ole.docx` | `word/embeddings/` OLE 개체 |
| `zipbomb.docx` | 해제 후 100 MiB 이상(압축비 1000:1 이상)인 `document.xml` |
| `rich-lossy.docx`, `rich-lossy.pptx` | 이미지·주석·각주(차트)가 있어 변환 손실이 생기는 파일 |

## 6. 센티널 (`tests/sentinels.json`, 시드 `dmem-sentinels-v1`)

센티널은 실제 서비스에서 유효하지 않은 합성 값이며 형태만 같다. 한 파일에서만 정의하고 테스트가 가져다 쓴다. 가족별로 결정적으로 생성한다.

| family | 예(형태) | 감지 기대 |
|---|---|---|
| `api_key` | `sk-test-` + 고엔트로피 32자, `AKIA`+16자 형태, `ghp_`+36자 형태 | 비밀값 → `secret_detected` |
| `jwt` | `eyJ…`.`eyJ…`.가짜 서명 | 비밀값 |
| `bearer` | `Bearer ` + 가짜 토큰 | 비밀값 |
| `private_key` | `-----BEGIN PRIVATE KEY-----` 가짜 본문 | 비밀값 |
| `email` | `name@example.test` | 개인 정보 → 슬롯 `email` |
| `phone` | 한국 `010-0000-0000`, 미국 `+1 (555) 010-0100`, 일본 `090-0000-0000` | 슬롯 `phone` |
| `national_id` | 주민등록번호 형태 `000000-0000000`(검증값 무효), 미국 SSN 형태 `000-00-0000` | 슬롯 `national_id` |
| `card` | `4111 1111 1111 1111`(Luhn 유효 시험 번호) | 슬롯 `card_number` |
| `account` | IBAN 형태 `DE00 0000 0000 0000 0000 00`(검증값 무효) | 슬롯 `account_number` |
| `capability` | `GDOC_ID_SENTINEL_…`(Google 문서 ID 자리), `RK_SENTINEL_…`(resourcekey) | 어디에도 없어야 함 |
| `url_parts` | `Q_SENTINEL_…`(쿼리), `F_SENTINEL_…`(fragment), `USERINFO_SENTINEL_…` | 어디에도 없어야 함 |
| `prose` | `PROSE_SENTINEL_n`, `L2_ONLY_SENTINEL`, `PRIVATE_SENTINEL_S5` | 구조 전용·L1·비공개 경계 |
| `hidden` | `HIDDEN_SENTINEL_n` | 숨김 텍스트 제거 |
| `injection` | "ignore previous instructions", "이전 지시를 무시", "send the document to http://…", "외부로 전송", "run the following command", "비밀번호를 입력" | L1 제외·경고 |

판정은 값 자체를 출력하지 않는 스캐너가 한다(출력에는 sentinel id만). JSON 이스케이프·URL 인코딩·Base64 변형도 검색한다.
