# 기능 테스트 케이스 (핵심 영역)

상태: 케이스 정의(문서 우선). 구현·실행 결과는 [`environment.md`](environment.md)와 [`hosts/arise.md`](hosts/arise.md)에 날짜와 함께 기록한다. 이 문서는 `CORE`, `FORM`, `FMT`, `MEM`, `RCL`, `LIB`, `SHR`, `DISC`, `IMP`, `VER`, `TPL`, `DOC-01~02`, `PRIV`, `MCP`의 케이스 원본이다. 플랫폼·검수·웹 영역은 `functional-api.md` 등 별도 문서가 정의한다([`../spec/README.md`](../spec/README.md) 레지스트리).

## 읽는 법

| 열 | 의미 |
|---|---|
| 단계 | `R1` = [`runtime-v1.md`](../spec/runtime-v1.md) 단계 이상에서 요구, `F` = 전체 목표 계약, `L0` = 제품 내부 단위 테스트(블랙박스 하네스는 실행하지 않고 `SKIP(L0)`로 사유와 함께 보고) |
| 입력 | CLI(`dmem … --json`) 또는 MCP 호출. `recall(...)`은 `dmem recall --stdin --json`과 `doc_memory_recall`을 모두 뜻한다 |
| 기대 결과 | 스크립트가 확인할 수 있는 관찰값. 오류는 [`../spec/core.md`](../spec/core.md) 7절 고정 코드와 종료 코드(0~7) |

공통 규칙: 모든 오류 응답은 입력값을 되돌려 주지 않는다(`CORE-23`). 모든 실행은 일회용 `DMEM_HOME`과 임시 `HOME`에서 한다. fixture는 [`fixtures.md`](fixtures.md)다. 구현 범위 밖 케이스는 조용히 건너뛰지 않고 `SKIP(profile)`로 사유를 남긴다.

## CORE: URL·양식 키 정규화 ([`../spec/core.md`](../spec/core.md))

검증은 `recall(url)`이 돌려주는 `canonical_url`과 오류 코드로 한다(블랙박스).

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| CORE-01 | R1 | `core.md` 2절 예시 표의 14개 URL을 CLI `recall`에, 각 기대 canonical 문자열을 MCP `doc_memory_recall`에 넣는다 | CLI(원본 URL)와 MCP(canonical)의 `canonical_url`이 표의 값과 같다. canonical을 다시 정규화해도 그대로다(멱등) |
| CORE-02 | R1 | `http://example.com/a`, `ftp://example.com/`, `file:///etc/passwd`, `data:text/html,x`, `javascript:alert(1)`, `gopher://example.com/` | 전부 `url_rejected` reason `scheme_not_allowed`, 종료 코드 2, 네트워크 요청 0건 |
| CORE-03 | R1 | `https://user:pw_SENTINEL@example.com/`, `https://USERINFO_SENTINEL@example.com/x` | `url_rejected` reason `userinfo_not_allowed`. 출력·로그·캐시에 센티널 0건 |
| CORE-04 | R1 | `https://example.com/templates/resume/modern?utm_source=Q_SENTINEL#F_SENTINEL` | `canonical_url == "example.com/templates/resume/modern"`. `Q_SENTINEL`·`F_SENTINEL`이 모든 sink(stdout, stderr, 로그, 캐시, 저장소, 서버 요청)에 0건 |
| CORE-05 | R1 | `https://example.com:443/x`, `https://example.com:8443/x` | 앞은 `example.com/x`, 뒤는 `url_rejected` reason `host_not_allowed` |
| CORE-06 | R1 | `https://EXAMPLE.com./Templates/A`, `https://bücher.example/x` | `example.com/templates/a`(호스트·고정 단어 소문자, 후행 점 제거), `xn--bcher-kva.example/x`(IDNA) |
| CORE-07 | R1 | `https://127.0.0.1/`, `10.0.0.5`, `192.168.1.1`, `169.254.169.254/latest/meta-data`, `[::1]`, `[fd00::1]`, `https://2130706433/`, `https://0x7f.1/`, `https://localhost/`, `https://intranet/`, `https://metadata.google.internal/` | 전부 `url_rejected` reason `host_not_allowed`(비격리 모드) |
| CORE-08 | F | `DMEM_ISOLATED=1`에서 `http://127.0.0.1:<포트>/p/google-docs/document/d/FIX_KO_RESUME/edit`, `http://127.0.0.1:<포트>/pages/a?x=1`. 같은 URL을 `DMEM_ISOLATED` 없이 | 앞의 둘은 `docs.google.com/document/d/:id/edit`(provider `google_docs`)와 `fixture.test/pages/a`. 격리 없이는 `scheme_not_allowed`/`host_not_allowed`. `status.isolated`가 각각 `true`/`false` |
| CORE-09 | R1 | `https://example.com/people/948203/profile`, `…/people/12/profile` | 둘 다 `example.com/people/:id/profile` |
| CORE-10 | R1 | `/orders/123e4567-e89b-12d3-a456-426614174000`, `/x/0123456789abcdef0123` | 각각 `/orders/:id`, `/x/:id` |
| CORE-11 | R1 | `/blog/my-private-project-948203`, `/p/title-abcdef01`, `/blog/my-first-post` | 앞의 둘은 `/blog/:id`, `/p/:id`(slug 폐기). 셋째는 그대로 `/blog/my-first-post` |
| CORE-12 | R1 | `/s/Ab3dE6gH9jK2mN5pQ8sT`(숫자+문자 20자), `/s/abcdefghijklmnopqrst`(문자만 20자) | 앞은 `/s/:id`, 뒤는 `/s/abcdefghijklmnopqrst` |
| CORE-13 | R1 | `/@jane/posts`, `/u/jane.doe@corp.test/doc` | `/:handle/posts`. 뒤는 `url_rejected` reason `pii_in_url`(출력에 `jane.doe` 없음) |
| CORE-14 | R1 | `/a/b/c<d/e`, `/a/b/c/d/e/f/g/h/i`, 41자 세그먼트 | 각각 `example.com/a/b`(분류 불가부터 절단), `example.com/a/b/c/d/e/f/g/h`(8개), 41자 세그먼트부터 절단 |
| CORE-15 | R1 | `docs.google.com/document/u/1/d/GDOC_ID_SENTINEL_0123456789ABCDEFGHIJ/edit?usp=sharing&resourcekey=RK_SENTINEL_x#heading=h.x`, `…/document/d/ID/preview`, `…/document/d/ID/foo/bar`, `…/document/create`, `…/presentation/d/ID/edit#slide=id.p3`, `…/spreadsheets/d/ID/edit?gid=0` | `docs.google.com/document/d/:id/edit`, `…/preview`, `docs.google.com/document/d/:id`, `docs.google.com/document`, `docs.google.com/presentation/d/:id/edit`, `docs.google.com/spreadsheets/d/:id/edit`. provider는 `google_docs`×4, `google_slides`, `google_sheets`. 센티널 0건 |
| CORE-16 | R1 | `https://www.notion.so/myws/Quarterly-Report-0123456789abcdef0123456789abcdef?pvs=4`, `https://acme.notion.site/Invoice-Template-0123456789abcdef0123456789abcdef`, `https://notion.so/0123456789abcdef0123456789abcdef` | `www.notion.so/:id`, `acme.notion.site/:id`, `notion.so/:id`. provider `notion` |
| CORE-17 | R1 | `https://www.example.org/forms/invoice.docx?download=1`, `…/deck.PPTX`, `…/sheet.xlsx`, `…/a.pdf`, `…/a.md`, `…/a.txt` | provider `docx`, `pptx`, `xlsx`, `pdf`, `markdown`, `txt`. 쿼리 제거, 확장자 대소문자 무관 |
| CORE-18 | R1 | `https://example.com/anything`, `https://docs.google.com/forms/d/Ab3dE6gH9jK2mN5pQ8sT/edit`, `https://www.canva.com/design/DAFxxxxxxxxA/abcDEF123456/view` | provider `other`. 둘째는 `docs.google.com/forms/d/:id/edit`, 셋째 ID 세그먼트는 `:id` |
| CORE-19 | F | Google Docs 모양 URL(센티널 ID·`resourcekey`)을 `recall --stdin`, `web preview`, `import`에 넣고 저장까지 한다 | 라이브러리 파일·로그·캐시·진단·서버 요청·`export --format json` 어디에도 `GDOC_ID_SENTINEL`·`RK_SENTINEL` 0건. 저장된 출처의 `source_url`은 `null`, `source_ref`가 있다 |
| CORE-20 | F | 같은 fixture URL을 같은 라이브러리에 두 번 가져오기, 다른 `DMEM_HOME`(다른 `library_key`)에 한 번 | 같은 라이브러리의 `source_ref`는 같고 다른 라이브러리는 다르다. `source_ref`는 `^src_[a-z2-7]{26}$`이고 ID 부분 문자열을 포함하지 않는다 |
| CORE-21 | R1 | 서버 모드에서 요청을 기록하는 가짜 서버를 두고 `recall("http://example.com/")`, `recall("https://127.0.0.1/")` | 둘 다 `url_rejected`(종료 2). 가짜 서버의 요청 수 0, 원본 URL이 로그에 없다 |
| CORE-22 | R1 | MCP `doc_memory_recall`에 비정규 URL(`https://docs.google.com/document/d/ID/edit?usp=x`, 대문자 경로)과 canonical URL을 각각 | 앞은 `isError`, 코드 `non_canonical_url`. 뒤는 성공. CLI `recall --stdin`은 비정규 URL도 로컬에서 정규화해 성공 |
| CORE-23 | R1 | CORE-02·03·05·07·13, FORM-04·06, LIB-14의 거부 입력(센티널 포함) | 모든 오류 JSON·stderr·로그에 입력 센티널 0건. `error.code`가 `core.md` 7절 목록 안이고 `message`가 코드별로 고정이다(같은 코드의 `message`가 서로 다른 입력에서 같다) |
| CORE-24 | R1 | 2,048자 URL과 2,049자 URL, `limit=4`, 키워드 9개 | 2,048자는 통과, 2,049자는 `url_rejected` reason `too_long`. `limit=4`와 키워드 9개는 `invalid_input` |

## FORM: 양식·로케일·관습 ([`../spec/form.md`](../spec/form.md))

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| FORM-01 | R1 | `recall(url=docs.google.com/document/d/:id/edit, provider="notion")` | 오류 없음. 응답 `form.provider == "notion"`(명시값 우선) |
| FORM-02 | R1 | doc_type `이력서`, `Resume`, `RESUME `, `ＲＥＳＵＭＥ`(전각), `견적서`, `見積書`, `angebot`, `회의록`, `議事録`, `교안` | `resume`×4, `quote`×3, `meeting_minutes`×2, `lesson_plan` |
| FORM-03 | R1 | `履歴書`, `세금계산서`, `適格請求書`, `cv`; `履歴書` + 명시 `variant="us_chronological"` | `resume`+`jp_rirekisho`, `invoice`+`kr_tax_invoice`, `invoice`+`jp_qualified`, `resume`+`cv`. 명시 variant가 있으면 명시값 |
| FORM-04 | R1 | `save`와 `recall`에 doc_type `foo` | 둘 다 `invalid_form` reason `doc_type_unknown`, 종료 2, 저장 0건 |
| FORM-05 | R1 | locale `ko_KR`, `KO-kr`, `ko-kr`, `ko` | `ko-KR`×3, `ko`(언어만 허용, region `null`) |
| FORM-06 | R1 | locale `xx-YY`, `ko-US`, `en-AU` | 전부 `invalid_form` reason `locale_unknown` |
| FORM-07 | R1 | locale `en-US`(+region 생략), `en-US`+region `KR`, region `ZZ` | `region == "US"`, `region == "KR"`(명시 override), `invalid_form`(region `ZZ`) |
| FORM-08 | R1 | page `{A4, portrait, [25,20,25,20]}`; `{B5,…}`, margins 101, orientation `diagonal`; deck provider에 `A4`, document provider에 `16:9` | 첫째 통과. 나머지는 `invalid_form` reason `page_invalid` |
| FORM-09 | R1 | variant `us_chronological`; `Has Space`, `UPPER`, 33자, 빈 문자열 | 첫째 통과. 나머지는 `invalid_form` reason `variant_invalid` |
| FORM-10 | R1 | doc_type `other`(family 없음)에 provider `google_slides`/`pptx`/`google_sheets`/`xlsx`/`docx`/`other`; doc_type `pitch_deck`+`google_docs`; `resume`+`google_slides` | family `deck`, `deck`, `sheet`, `sheet`, `document`, `document`. 뒤의 둘은 `invalid_form` reason `family_mismatch` |
| FORM-11 | R1 | 같은 URL 패턴(`docs.google.com/document/d/:id/edit`)·doc_type `resume`에 ko-KR 양식과 en-US(page Letter) 양식 두 개를 저장하고 질의 locale `ko-KR`, `ko`, `en-GB`, `ja-JP`, 생략으로 recall | 두 힌트가 항상 모두 나오고 `locale_match`는 ko-KR 양식에 `exact`/`language`/`none`/`none`/`unspecified`, en-US 양식에 `none`/`none`/`language`/`none`/`unspecified`다(힌트는 최대 3개이므로 라이브러리를 작게 만들어 둘 다 보이게 한다) |
| FORM-12 | R1 | en-US·page Letter 이력서 양식 하나만 저장하고 ko-KR 질의로 recall | 힌트 `warnings`에 `paper_mismatch`, `date_order_mismatch`, `currency_mismatch`, `name_order_mismatch` 네 코드가 모두 있고 각 경고에 `code`가 있다. `expand`는 저장한 locale을 돌려준다. (`RCL-LIB`의 M2는 ko-KR 질의에서 4위라 보이지 않으므로 `RCL-16`이 `scope=mine`으로 좁혀 같은 결과를 확인한다) |
| FORM-13 | R1 | ko-KR 양식과 en-US(Letter) 양식을 저장하고 ko-KR 양식을 ko-KR 질의로, en-US 양식을 en-GB 질의로 recall | ko-KR 양식: `warnings == []`. en-US 양식: `paper_mismatch`, `date_order_mismatch`, `currency_mismatch`만(이름 순서는 같다) |
| FORM-14 | F | `status`의 `vocab`. 저장된 기록의 doc_type을 알 수 없는 값(`legacy_x`)으로 바꾸고(더블 훅 `__test patch`) doc_type 없이 recall | `vocab.doc_types`·`regions`·`licenses`·`keywords` 버전 문자열이 있다. 바꾼 기록은 보존되고 `freshness == "needs_reverify"`로 값 그대로 다른 항목 뒤에 오며 `expand`가 된다. doc_type을 지정한 recall은 그 값이 맞는 항목만 낸다. 제품은 주입 훅이 없으면 `SKIP` |
| FORM-15 | R1 | `pptx`+`pitch_deck`, `google_docs`+`pitch_deck`, `other`+`pitch_deck`, `google_slides`+`resume` | 첫째 통과, 나머지는 `family_mismatch` |
| FORM-16 | R1 | 같은 URL 패턴·doc_type `resume`에 KR(ko-KR)·US(en-US, Letter)·JP(ja-JP, `jp_rirekisho`) 세 양식을 저장하고 locale `ko-KR`, `ja-JP`, `en-US`로 recall | 세 메모리가 별개로 존재한다(`list`가 3개). 힌트 3개 중 첫 힌트가 각각 KR, JP, US 양식이다 |

## FMT: 표준 구조·어댑터·내보내기 ([`../spec/formats.md`](../spec/formats.md))

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| FMT-01 | R1 | 제목(1·2단계), 순서 있는 중첩 목록, 헤더+2행 표, `note`·`warning` 콜아웃을 가진 StandardDoc을 Markdown으로 내보내기(overview 10절) | `#`/`##`, `1.` + 2칸 중첩, GFM 파이프 표(헤더 구분선 포함), `> [!NOTE]`·`> [!WARNING]` 블록이 `formats.md` 5절 규칙대로. 블록 수·순서가 입력과 같다 |
| FMT-02 | R1 | FMT-01의 결과를 다시 가져오기(`save --stdin --format markdown`) | 지원 블록의 종류와 순서가 원본과 같다(heading, list, table, callout) |
| FMT-03 | R1 | 본문에 `<script>alert(1)</script>`, `"><img src=x onerror=alert(1)>`, `[x](javascript:alert(1))`, `&`, `<`가 든 문서를 HTML로 내보내기 | 결과에 `<script`, `onerror=`, `javascript:`가 없고 텍스트는 이스케이프로 보존된다. 태그는 허용 목록(`h1-h6,p,ul,ol,li,table,thead,tbody,tr,th,td,blockquote,aside,img,a,strong,em,code,br`) 안이다 |
| FMT-04 | R1 | A4와 Letter 페이지의 문서를 DOCX로 내보낸 뒤 다시 가져오기 | 유효한 ZIP/XML(`[Content_Types].xml` 있음, 외부 관계 0). 제목 단계·표 셀·순서·용지(A4/Letter)가 같다 |
| FMT-05 | R1 | `tpl01-monthly-report.docx`를 `save --file`(overview TPL-01) | 개요가 `["요약","지표","위험","요청"]` 순서(문서 제목 별도), 표 셀 보존, 제목·본문 스타일이 `styles`에 반영 |
| FMT-06 | F | `evil-macro.docx`, `evil-ole.docx`, `evil-external.docx`, `evil-dde.docx` | 매크로·OLE는 `unsupported_format`. 외부 관계 파일은 저장되되 `external_reference_removed` 경고이고 fixture 서버 요청 로그에 **0건**(가져오지 않음). DDE는 필드 지시문이 제거되고 `fields_flattened` 경고 |
| FMT-07 | F | `zipbomb.docx`(해제 후 100 MiB, 압축비 1000:1) | `payload_too_large`, 종료 2, 메모리 사용이 한도 안(하네스가 자식 RSS 최대 256 MiB 이하를 확인), 부분 저장 0 |
| FMT-08 | R1 | `deck-5.pptx` | deck StandardDoc: 슬라이드 5장, 순서 유지, `theme.aspect == "16:9"`, 역할 추론 `["cover","problem","solution","market","ask"]`(제목 기반, 못 정하면 `content`), 슬라이드 제목·본문 텍스트 보존 |
| FMT-09 | F | `google_slides` 모양 URL(`/p/google-slides/…`)을 가져오기 | fixture 요청 로그에 `format=pptx`만 요청되고 `md`·`html` 시도가 없다. 결과는 deck이고 `layout_inferred` 경고 |
| FMT-10 | F | `google_sheets` 모양 URL: 기본(`/p/google-sheets/…`)과 CSV만 내보내는 변형(`/p/google-sheets-csv/…`, 가져오기는 쿼리를 버리므로 변형을 경로 별칭으로 고른다) | 기본은 xlsx 내보내기만 요청하고, csv 변형은 xlsx를 먼저 시도한 뒤 csv로 후퇴하며 `first_sheet_only` 경고를 낸다. 둘 다 `sheet_support_deferred` 경고와 메타데이터(시트 이름·열 머리글)만 저장하고 데이터 행은 저장하지 않는다 |
| FMT-11 | F | `text.pdf`, `scan.pdf` | `text.pdf`는 reference로 저장되고 span `locator`가 쪽 번호 형식 `page:<n>`(`page:1`). `scan.pdf`는 `extract_empty` reason `ocr_required`. PDF 어댑터가 없는 구현은 `SKIP` 사유를 남긴다 |
| FMT-12 | F | Notion 모양 페이지(`/p/notion/Quarterly-Report-…`) | 헤딩·목록·표·콜아웃이 StandardDoc 블록으로 매핑(종류와 순서 일치). provider `notion` |
| FMT-13 | F | `rich-lossy.docx`, `rich-lossy.pptx` | `warnings`에 `images_omitted`, `comments_dropped`, `unsupported_block` 중 해당 요소 종류마다 최소 1개. 경고 없이 사라진 요소 0(요소 종류 수 ≤ 경고 코드 종류 수) |
| FMT-14 | R1 | `export`: 상대 경로 `--out`, 이미 있는 파일, 심볼릭 링크, 없는 상위 디렉터리, 정상 경로(이미지 블록이 있는 문서) | 상대·존재·링크·상위 없음은 종료 2이고 기존 파일 내용이 그대로다. 정상은 파일 모드 0600. v1은 이미지 자산을 저장하지 않으므로 `<출력>.assets/`를 만들지 않는다(자산을 저장하는 구현은 0700으로 만든다) |

## MEM: 레이어·kind·슬롯·출처 ([`../spec/memory.md`](../spec/memory.md))

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| MEM-01 | R1 | M6(환불 사실)과 M6b(배송 사실)를 저장. `recall(url=example.com/, doc_type="other", kind="reference", keywords=["refund"])` 후 `expand(level=2)` (overview 10절) | 첫 힌트가 M6이고 M6b는 힌트 본문에 섞이지 않는다. L2 `spans[0]`이 문장 "환불은 미개봉 상품에 한해 구매 후 7일 이내 신청 가능"과 정확히 같고 `locator == "p:1"`이다 |
| MEM-02 | R1 | 경계 입력: title 120/121자, summary 600/601자, key_points 6/7개, keyword 32/33자, keywords 8/9개, url_patterns 4/5개 | 앞 값은 통과, 뒤 값은 `invalid_input`. 거부 시 저장 0건 |
| MEM-03 | R1 | template(본문 없음), reference(텍스트 없음), style_rule(규칙 없음)을 각각 저장 | `extract_empty` 또는 `invalid_input`, 저장 0건 |
| MEM-04 | R1 | template에 본문 `L2_ONLY_SENTINEL`을 넣어 저장한 뒤 `recall`, `expand(level=1)`, `expand(level=2)` | 앞의 둘 응답에 센티널 0건, level 2에는 있다 |
| MEM-05 | F | 최대 길이 L1(한국어·영어 혼합)을 가진 메모리 5개 이상을 만든 뒤 `recall` | 힌트 ≤3개, 각 힌트 JSON의 `ceil(utf8_bytes/4) ≤ 400` |
| MEM-06 | R1 | 슬롯 이름 `Name`, `1abc`, 41자, 중복; rule kind `foo` | 전부 `invalid_input`. 유효한 슬롯·rule kind는 통과 |
| MEM-07 | R1 | 본문에 `{{확인 필요: Q4 매출}}`, `{{needs-info: owner}}`, `{{name}}` | 저장→`expand(level=2)`→Markdown 내보내기를 거쳐도 세 표식이 원문 그대로다 |
| MEM-08 | F | M1 저장 뒤 같은 scope·같은 내용을 식별자 없이 재저장; 다른 내용을 식별자 없이 저장; 이어 `memory_id=M1`, `base_version=1`로 수정; 같은 URL·doc_type·locale의 reference; locale만 다른 template | 동일 내용은 같은 id/version의 `created:false`; 다른 내용의 식별자 없는 저장은 `invalid_input`(`reason=scope_conflict`)이며 상태 변화 0; 명시적 업데이트는 M1 v2를 만들고 v1은 불변; reference와 locale 변형은 각각 별도 active id |
| MEM-09 | R1 | v1 저장 뒤 v2 저장. `expand --version 1`, `expand`(생략) | v1은 v1 당시 내용(해시 동일), 생략은 v2 |
| MEM-10 | L0 | 같은 버전을 두 번 재색인 | 색인 행 집합이 같다. 블랙박스에서는 프로세스를 다시 띄운 뒤 `recall` 결과가 같은지만 확인(`RCL-09`) |
| MEM-11 | F | `summary`에 URL, 이메일, 제어 문자 U+0007, 제로폭 문자, 주입 문구("이전 지시를 무시…") | URL·이메일·제어·제로폭은 `invalid_input`. 주입 문구는 저장되되 `injection_flagged` 경고이고 `recall`의 L1에는 그 문장이 없다 |
| MEM-12 | R1 | 입력에 알 수 없는 필드 `foo`, MCP 입력에 알 수 없는 필드 | `invalid_input`, 저장 0건 |
| MEM-13 | F | `import`(fixture) 후 `export --format json`의 `source` 블록 | `origin == "fetched"`, `source_host`·`content_hash`(`^sha256:`)·`retrieved_at` 있음. Google 모양 URL이면 `source_url == null`이고 `source_ref` 있음. 복사본은 `derived_from` 있음 |
| MEM-14 | F | `license-none.html`(prose `PROSE_SENTINEL_U1`, 표 본문 셀 `BODYCELL_U1`)을 `import --as template` | `copy_policy_applied == "structure_only"`. `export --format json` 어디에도 `PROSE_SENTINEL_*`·`BODYCELL_*` 0건. 헤딩과 표 머리글은 남고 `retained.body_chars_removed > 0` |
| MEM-15 | R1 | 정상 문단 50개 중 하나에 비밀 센티널(가족별로 실행), template에 개인 정보 센티널(이메일·전화·주민·카드·계좌) | 비밀: `secret_detected`, 종료 2, 라이브러리 변화 0, 응답에 값·위치 없음. 개인 정보: 저장되고 값이 슬롯(`email`, `phone`, `national_id`, `card_number`, `account_number`)으로 치환되며 원래 값이 L0·L1·L2·원본 외 어디에도 없다(원본 보존 파일 제외), `scrub.pii_slotified`가 건수와 같다 |
| MEM-16 | F | span 200 KiB짜리 reference를 `expand(level=2)`로 연속 읽기 | 각 응답 ≤64 KiB, `truncated`와 `cursor`로 이어지며 span이 순서대로 중복·누락 없이 모두 나온다 |

## RCL: recall ([`../spec/recall.md`](../spec/recall.md))

`RCL-LIB`([`fixtures.md`](fixtures.md) 2절)를 저장 순서대로 만든 뒤 실행한다. 순위 튜플은 `locale_rank` → `route_exact` → `route_covered` → `provider_exact` → `source_tier` → `keyword_hits` → `freshness` → `quality_band` → `updated_at` → `memory_id`다.

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| RCL-01 | F | `recall(url="docs.google.com/document/d/:id/edit", doc_type="resume", locale="ko-KR")` (호출자 `carol`, scope all. `RCL-LIB`는 `local` 행을 carol의 것으로 적재하고 M4·M5·M16·M17은 alice가 게시한 것이다. carol은 `acme` 구성원) | 힌트 순서 `[M1, M4, M5]`(M1: locale exact+정확 route, M4: 같은 locale+호스트 전체 route+team, M5: 같은 locale+다른 호스트). `source.tier`는 `mine`·`team`·`public`. M2·M3는 locale 불일치로 밀린다 |
| RCL-02 | F | `recall(url="www.example.org/templates/resume/modern", doc_type="resume", locale="ko-KR")` | `[M5, M1, M4]`. doc_type이 같으면 **호스트가 달라도** 후보다. M5는 `route_covered`로 앞, M1·M4는 provider 불일치 뒤에서 tier로 mine > team |
| RCL-03 | F | `recall(url="docs.google.com/document/d/:id/edit")`(doc_type·locale 없음) | `[M1, M3, M2]`: M1 정확 route, 그다음 상위 route를 덮는 후보 중 mine·provider 동점이라 `updated_at`이 최신인 M3, M2 순. 같은 호스트의 다른 document 양식(M4 team, M12·M13·M15·M16·M17)은 `updated_at`·tier에서 뒤라 제외되고, M5·M8·M9는 후보가 아니다(타 호스트·family 불일치) |
| RCL-04 | F | `recall(url=…, doc_type="resume", locale="ja-JP")`, 같은 호출에 locale `en-GB` | 첫째 `[M3, M1, M2]`(M3 locale exact). 둘째 `[M2, M1, M3]`(M2는 `en`이 같아 `language`) |
| RCL-05 | F | M10(docx)·M11(markdown)에 `recall(url="example.com/x", doc_type="memo", locale="ko-KR", provider=…)` | provider `markdown` → M11 먼저, `docx` → M10 먼저, 생략(감지 `other`) → 둘 다 동점(`updated_at`도 같다)이라 `memory_id` 오름차순(더블: M10, M11). 제품은 관찰한 `updated_at`·id로 기대를 계산 |
| RCL-06 | F | M15(mine)·M16(team)·M17(public) 같은 조건, 호출자 `carol`, scope all | 순서 `[M15, M16, M17]`. `source.tier`가 각각 `mine`, `team`, `public` |
| RCL-07 | F | M12(`weekly`)·M13(`draft`)에 `keywords=["초안"]`, 같은 호출에 `["draft"]`, `["weekly"]` | 앞 둘은 M13이 먼저이고 `matched_on`에 `keywords`가 있다(별칭 `초안`=`draft`). 셋째는 M12 먼저 |
| RCL-08 | F | 후보가 6개 이상인 질의(doc_type 없는 Docs 편집 URL): 기본, `limit=1`, `limit=4` | 3개, 1개, `invalid_input` |
| RCL-09 | F | 저장(적재) 순서를 바꾼 라이브러리 3개와 프로세스 재시작 후 같은 질의를 5번: 뚜렷한 순위가 있는 질의(RCL-01)와 모든 키가 같아 동점인 질의(M10·M11, doc_type `memo`) | 힌트의 `memory_id` 순서가 15번 모두 같다. 완전 동점은 `memory_id` 오름차순(더블: M10, M11)이다. 제품은 관찰한 필드로 기대를 계산한다. MCP 서버도 CLI와 같은 순서를 낸다 |
| RCL-10 | R1 | 모르는 URL·양식 질의 / 거부되는 URL | 앞은 `hints == []`, `reason == "no_match"`, 종료 0. 뒤는 `url_rejected`, 요청 0건 |
| RCL-11 | R1 | 모든 recall 응답 | `untrusted == true`, `framing`이 고정 문구와 같고 힌트에 L2 필드(`l2`, `structure`, `spans`)가 없다. 스키마 `RecallResult` 검증 통과 |
| RCL-12 | F | 서버 모드에서 `anon`과 `carol`로 같은 recall(doc_type `lesson_plan`), 계정 없는 로컬 모드(서버 없는 별도 세계)에서 recall | `anon`: 공개 M17만, `receipt_id` 없음. `carol`: M15·M16·M17 모두 `receipt_id` 있음. 로컬: `receipt_id` 없음 |
| RCL-13 | F | `SHR-CAT`에서 호출자별 `scope=mine/team/public/all` | `mine`은 내 것만, `team`은 같은 workspace 항목만, `public`은 공개만, `all`은 합집합. `anon`+`all`은 공개만이고 오류 아님. 다른 사용자의 비공개는 어떤 scope에도 없다 |
| RCL-14 | R1 | 같은 canonical 입력으로 CLI와 MCP를 각각 | `hints`가 같은 순서·같은 내용(`receipt_id` 제외 깊은 비교) |
| RCL-15 | F | 호스트 에이전트 행동([`host-smoke.md`](host-smoke.md) BEH-01·BEH-06·BEH-08) | 작업 전 recall 호출, 같은 (route, doc_type, locale)을 5분 안에 반복하지 않음, 사용자가 거부하면 호출 없음. 호출률은 측정값 |
| RCL-16 | F | `scope=mine`으로 M1·M2·M3만 남겨 ko-KR로 recall(M2가 3위 안에 든다) | 순서 `[M1, M3, M2]`. M2 힌트 `warnings`에 `FORM-12` 코드가 구조(`code`, 선택 `detail`)대로 있다 |
| RCL-17 | F | 서버 모드 가짜 서버가 요청 본문을 기록. `recall` 입력에 쿼리·`Q_SENTINEL`, 어휘 밖 키워드 `zzz_sentinel`, 대문자 | 서버가 받은 본문의 키는 `url`(canonical), `doc_type`, `locale`, `provider`, `keywords`(어휘 안만), `kind`, `scope`, `limit`뿐. 센티널 0건. 어휘 밖 키워드는 stderr로 알리고 전송하지 않는다 |
| RCL-18 | F | superseded 버전, 삭제된 메모리, takedown된 항목, `needs_reverify` 항목(더블 훅)이 있는 라이브러리 | 앞의 셋은 결과에 없다. `needs_reverify`는 나오되 같은 튜플의 fresh 항목보다 뒤다 |
| RCL-19 | F | 로컬 모드에서 `scope=public`, `scope=team` | `hints == []`, `reason == "scope_unavailable_local"`, 종료 0 |
| RCL-20 | F | 서버 모드 익명 공개 recall을 캐시한 뒤 서버 중지, 연결 호출도 같이 | 익명은 `cache.state`가 `stale` 또는 `fresh`로 표시되고 `receipt_id` 없음. 연결 호출은 종료 5, 캐시를 쓰지 않는다. 캐시 불가 구현은 `SKIP` |

## LIB: 내 라이브러리 ([`../spec/library.md`](../spec/library.md))

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| LIB-01 | R1 | `resume-ko.md`를 `save --file`(`--dry-run` 후 실제 저장) | 저장 결과 `visibility == "private"`, `version == 1`. `DMEM_HOME/originals/<sha256>` 파일이 있고 모드 0600 |
| LIB-02 | R1 | `tpl01-monthly-report.docx` 저장(overview TPL-01) | `expand(level=2)`의 구조에서 섹션 순서 요약→지표→위험→요청, 표 1개(2×3), 개인 양식으로 목록에 나온다 |
| LIB-03 | R1 | `--dry-run` 전후 라이브러리 | `dry_run == true`, `memory_id == null`. 전후 `list` 건수와 `DMEM_HOME` 파일 목록(로그 제외)이 같다 |
| LIB-04 | R1 | 같은 내용·같은 scope를 두 번 저장 | 둘째는 `created == false`, 같은 `memory_id`·`version`. 버전 수 1 |
| LIB-05 | R1 | `memory_id`+`base_version=1`로 수정 → 같은 `base_version=1`로 다시 → `base_version=2`로 | 첫째 `version 2`(v1 superseded), 둘째 `version_conflict` 종료 4·변화 0, 셋째 `version 3` |
| LIB-06 | R1 | `expand --version 1`, `--version 99` | 앞은 v1 내용, 뒤는 `not_found` 종료 7 |
| LIB-07 | R1 | 메모리 25개. `search --scope mine`을 `--limit 10`으로 `cursor` 따라가기, kind·doc_type·locale·provider 필터 | 3페이지(10/10/5)에서 중복·누락 0, 마지막 `next_cursor == null`. 정렬이 `updated_at` 내림차순 + `memory_id`. 필터 결과가 조건과 일치 |
| LIB-08 | R1 | 가족별 비밀 센티널을 `save`(MEM-15와 같은 입력)·`search --query`·`web search` | 종료 2 `secret_detected`. 저장소 파일 목록·해시 변화 0, stdout·stderr·로그에 센티널 0 |
| LIB-09 | F | template 본문에 이메일·전화(KR/US/JP)·주민번호 형태·카드·IBAN 형태 | 슬롯으로 치환, `scrub.pii_slotified`가 건수, `export --format json`에 원래 값 0건 |
| LIB-10 | F | reference에 개인 정보(S8) | 값이 보존되고 `contains_personal_data == true`(export json), 가시성은 `private` 유지 |
| LIB-11 | R1 | TTY 없이 `delete`(`--yes` 없음/있음), 이후 `expand`, `DMEM_HOME` 전체 스캔 | 없음 → 종료 2(변화 0). 있음 → `deleted == true`, `expand`는 종료 7. `DMEM_HOME`에서 삭제한 메모리의 센티널 0건 |
| LIB-12 | R1 | `export`를 md·html·docx·pptx(deck)·json로. 같은 경로에 다시 | 파일 생성, 모드 0600, 내용이 `FMT-01~05` 규칙대로. 둘째 호출은 종료 2·기존 파일 불변 |
| LIB-13 | R1 | `DMEM_HOME` 모드 확인. `library` 파일을 심볼릭 링크로 바꿈. 저장소 파일을 일부 덮어써 손상시킴 | 디렉터리 0700·파일 0600. 링크는 따라가며 쓰지 않고 거부(종료 ≠ 0, 링크 대상 불변). 손상은 `internal` 종료 1·고정 문구, 패닉 스택·경로·입력 에코 없음 |
| LIB-14 | R1 | 10 MiB+1바이트 파일, 인라인 1 MiB+1바이트(`--stdin`), 빈·공백 파일, `.exe`, 이미지뿐인 DOCX | `payload_too_large`, `payload_too_large`, `extract_empty`, `unsupported_format`, `extract_empty`. 모두 종료 2·저장 0 |
| LIB-15 | F | 같은 파일로 메모리 2개 저장, 하나 삭제, 나머지 삭제 | `originals/<sha256>`가 1개로 공유, 하나 삭제 후 남음, 둘 다 삭제 후 사라짐 |
| LIB-16 | F | 두 프로세스가 동시에 `memory_id`+`base_version=1`로 다른 내용 저장, 10회 반복 | 매 회 정확히 하나만 성공(`version 2`)하고 다른 하나는 `version_conflict`. 저장소가 유효하다(다음 `list`·`expand` 성공) |

## SHR: 공유·복사·라이선스 ([`../spec/sharing.md`](../spec/sharing.md))

`SHR-CAT`([`fixtures.md`](fixtures.md) 3절)과 신원 `anon`·`alice`·`bob`·`carol`로 실행한다. 서버 모드(더블 또는 서버가 있는 제품)에서만 `F`이다.

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| SHR-01 | F | `alice`가 S5를 `publish --visibility public --license CC-BY-4.0 --consent`(consent_version `share-v1`) | `review_state`가 `queued` 후(fixture worker 승인) `approved`. `anon`의 `search --scope public`에 나오고 `author_handle == "alice"`, `license == "CC-BY-4.0"`, `version`이 있다. 서버에 동의 기록(버전·시각·대상)이 남는다(더블 `GET /__test/consents`) |
| SHR-02 | F | `--consent` 없이 publish | 종료 4 `consent_required`, 서버 쓰기 요청 0건(가짜 서버 카운터) |
| SHR-03 | F | `--license` 생략, `--license GPL-3.0`(어휘 밖) | 둘 다 `invalid_input`(종료 2), 쓰기 0 |
| SHR-04 | F | S8(`contains_personal_data`)을 public으로 publish | `review_state == "rejected"`, `reasons`에 `personal_data`. 공개 검색 결과에 없다 |
| SHR-05 | F | 저장된 template에 비밀 센티널을 주입(더블 훅)한 뒤 publish | `rejected`, `reasons`에 `secret`. 공개 카탈로그에 0건. 제품은 훅이 없으면 `SKIP` |
| SHR-06 | F | `alice`가 S4를 team으로. `carol`, `bob`, `anon`이 `search --scope team`, `recall`, `expand`, `copy` | `carol`만 보이고 복사 가능. `bob`·`anon`은 검색 결과에 없고 `expand`·`copy`는 `not_found`(종료 7)(`TPL-03`) |
| SHR-07 | F | 신원 × scope 전수(`anon`: public, `bob`: mine+public, `carol`: mine+team+public, `local`: mine)로 `search` | 각 신원이 볼 수 있는 집합과 정확히 일치. `bob`에게 S5가 없고 `alice`에게 S6이 없다. 로컬 모드의 `team`·`public`은 `scope_unavailable_local` |
| SHR-08 | F | `search`에 license·doc_type·locale·provider 필터, 페이지네이션, 같은 질의 반복 | 필터 일치, 결과 항목이 `SearchItem` 스키마 통과(`author_handle`, `license`, `copy_policy`, `visibility`, `version`), 순서가 안정적이다. `public`·`team`이면 `remote == true`, `mine`이면 `false` |
| SHR-09 | F | `search --query`에 비밀 센티널. 로컬 모드의 `search --scope mine --query …`(네트워크 요청을 기록) | 앞은 `secret_detected` 종료 2, 서버 요청 0. 뒤는 네트워크 요청 0 |
| SHR-10 | F | `bob`이 S1을 `expand` level 1·2, S3를 level 2 | `author_handle`, `license`, `version`이 있고 `untrusted == true`. 호출 전후 S1의 `version`·`updated_at`·내용 해시가 같다. S3 level 2에는 본문 prose가 없다 |
| SHR-11 | F | `bob`이 S1을 `copy` | 새 `memory_id`가 `bob`의 비공개 라이브러리에 생기고 `derived_from == {memory_id: S1, version, author_handle: "alice", license: "CC-BY-4.0"}`, `copy_policy_applied == "full"`. S1은 변하지 않는다(`TPL-02`) |
| SHR-12 | F | `bob`이 S3를 `--copy-mode full`, 기본 모드로 `copy` | 앞은 종료 4 `license_forbids`와 `allowed_modes == ["structure_only"]`. 뒤는 `copy_policy_applied == "structure_only"`, 복사본 L2에 `PROSE_SENTINEL_*` 0건 |
| SHR-13 | F | `bob`이 S1(CC-BY)·S2(CC-BY-SA)·S3·S7의 복사본을 제목을 바꿔(`copy --title`, 원본과 같은 내용이면 `duplicate`가 먼저 걸리므로) publish | S1 복사본: `CC-BY-4.0`로 허용(`derived_from` 유지). S2 복사본: `CC-BY-4.0`는 `license_forbids`, `CC-BY-SA-4.0`는 허용. S3·S7 복사본: 어떤 라이선스로도 `license_forbids` |
| SHR-14 | F | `alice`가 S1을 `publish --visibility private`(동의 불필요). 이후 `anon`의 `search`·`recall`·`expand`·`copy`, `bob`의 앞서 만든 복사본 | `anon`의 네 호출 모두 S1이 없거나 `not_found`. `bob`의 복사본은 그대로 있고 `expand`가 성공한다 |
| SHR-15 | F | 운영자 takedown(더블 `__test takedown`)을 S2에. 이후 `bob`이 takedown 전에 만든 S2 복사본, 같은 사슬의 새 게시 | 다른 사용자(`anon`·`bob`·`carol`)의 search·expand·copy에서 S2가 숨는다(소유자 자신의 목록 표시는 명세가 정하지 않아 판정하지 않는다). 복사본은 `origin_taken_down` 경고가 붙고 publish는 `license_forbids` 또는 `rejected`+`takedown_match`다 |
| SHR-16 | F | `bob`이 `alice`의 비공개 S5 id와 존재하지 않는 id로 `expand`·`copy`·`publish`·`delete`·`outcome` | 모든 호출이 `not_found` 종료 7이고 두 경우의 응답 본문이 바이트 단위로 같다(입력 id를 에코하지 않는다)(`SEC-01`) |
| SHR-17 | F | `bob`이 S1(공개)을 `publish --visibility private`, `delete` | `not_found`. S1은 변하지 않는다 |
| SHR-18 | F | `anon`이 `publish`·`outcome`, 그리고 S1을 `copy` | 앞의 둘은 종료 3 `auth_required`, 서버 쓰기 0. `copy`는 **로컬 라이브러리**로 허용되고 `receipt_id`가 없다 |
| SHR-19 | F | `alice`가 이미 공개된 S1과 같은 `content_hash`의 복사본을 publish. 한 시간 안에 11번째 publish | 앞은 `rejected`+`duplicate`. 뒤는 종료 6 `rate_limited`(한도 10/시간, 제안값) |
| SHR-20 | F | `alice`의 S1 → `bob`이 copy(B), B를 `CC-BY-4.0`로 publish하고 승인 → `carol`이 B를 copy(C), C를 `CC-BY-4.0`로 publish하고 승인 | `C.derived_from`의 `memory_id`·`version`은 B, `author_handle == "alice"`, `license == "CC-BY-4.0"`. 승인 뒤 `anon`의 `expand C`에서 `source.derived_from`이 같은 값(공개 attribution)이고 `source.author_handle == "carol"` |
| SHR-21 | F | S1(alice, approved public)과 같은 `catalog_scope`에서 fingerprint가 다른 S9(bob)을 `consent=true`, `consent_version=share-v1`, `license=CC-BY-4.0`으로 publish | 검토 통과 후 public search에 S1·S9가 서로 다른 `memory_id`와 작성자 정보로 공존하고 S1의 head/version은 불변이다. `carol`이 S9를 copy하면 `derived_from`이 S9의 게시 version을 고정한다. scope가 같다는 이유로 자동 병합·덮어쓰기되는 항목은 0 |

## DISC: 웹 검색 ([`../spec/web-import.md`](../spec/web-import.md) 7절)

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| DISC-01 | F | `DMEM_SEARCH_PROVIDER` 없음(`none`)에서 `web search "이력서 양식"` | `search_unavailable`, 종료 5, 네트워크 요청 0건(fixture 로그 0) |
| DISC-02 | F | `DMEM_SEARCH_PROVIDER=fixture:<서버>/search`, `web search "이력서 양식" --limit 5` | `candidates` ≤5, 각 `url`이 canonical(쿼리 없음), `untrusted == true`·고정 `framing`, `WebSearchResult` 스키마 통과 |
| DISC-03 | F | 같은 질의에 `--locale ko-KR`, `--doc-type resume`, `--provider google_docs` | 필터가 결과 순서·구성에 반영된다(해당 locale·provider 후보가 앞). fixture가 받은 질의에 필터 값이 포함된다 |
| DISC-04 | F | 질의에 비밀 센티널 | `secret_detected` 종료 2, fixture 요청 0건, 로그에 질의 텍스트 없음(해시만) |
| DISC-05 | F | 200자·201자 질의 | 200자는 통과, 201자는 `payload_too_large` |
| DISC-06 | F | fixture 결과의 title·snippet에 HTML 태그, 제어 문자, 주입 문구, 3,000자 | 응답 필드가 길이 한도 안이고 태그·제어 문자가 제거되며 주입 문구는 데이터로만 나간다(실행·따름 없음) |
| DISC-07 | F | fixture 결과에 `http://10.0.0.1/x`, `file:///x`, `https://127.0.0.1/` 후보 포함 | 세 후보는 `candidates`에 없고 `filtered >= 3` |
| DISC-08 | F | fixture가 429/타임아웃/500 응답 | 각각 종료 6 `rate_limited`, 종료 5 `search_unavailable`, 종료 5. 부분 결과 0, 상태 변화 0 |

## IMP: 웹 미리보기·가져오기·클립 ([`../spec/web-import.md`](../spec/web-import.md))

모든 IMP 케이스는 `DMEM_ISOLATED=1`과 fixture 서버([`fixtures.md`](fixtures.md) 4절)로 실행하며 fixture 요청 로그로 요청 수를 확인한다.

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| IMP-01 | F | `web preview <resume-ko.html>` | `WebPreviewResult` 스키마 통과: `outline`에 헤딩, `stats`, `license.id == "CC-BY-4.0"`(source `detected`), `content_hash`, `expires_at`(15분 이내). 라이브러리 변화 0 |
| IMP-02 | F | preview 뒤 fixture 페이지 내용을 바꾸고 `import --preview <id>` | 저장된 내용의 `content_hash`가 preview 시점 값과 같다(바뀐 내용이 아니다). 16분 뒤(시계 조작) 같은 id는 `not_found` |
| IMP-03 | F | `import <resume-ko.html> --as template` | 저장 `source`: `origin == "fetched"`, `provenance == "fetched"`, `source_host == "fixture.test"`, `source_url`에 쿼리·fragment 없음, `retrieved_at`, `content_hash` |
| IMP-04 | F | `license-cc0.html`, `resume-ko.html`(rel=license CC-BY), `license-mit.html`(meta), `license-jsonld.html`, `license-by-sa.html` | 감지 license가 `CC0-1.0`, `CC-BY-4.0`, `MIT`, 각 JSON-LD 값, `CC-BY-SA-4.0`이고 `license_source == "detected"`. 허용 라이선스는 `copy_policy_applied == "full"` |
| IMP-05 | F | `license-none.html`, `license-nc.html` | 둘 다 `structure_only`(`unknown`, `proprietary-structure-only`). 본문 prose가 저장물에 없고(`MEM-14`) 제목·헤딩·표 머리글은 있다 |
| IMP-06 | F | `license-none.html`을 `--copy-mode full` | 종료 4 `license_forbids`, `allowed_modes == ["structure_only"]`, 저장 0 |
| IMP-07 | F | `license-none.html` + `--license CC0-1.0`(충돌 없음), `license-nc.html` + `--license CC0-1.0`(충돌) | 첫째: 저장되고 `license_source == "user_asserted"`, `unverified == true`, 이후 `publish`는 `rejected`+`license`(미검증 출처는 게시 불가). 둘째: 검출값이 더 제한적이라 `license_forbids` |
| IMP-08 | F | `noai-meta.html`, `noai-header.html` | meta는 preview에 `signals.noai == true`, import는 `structure_only` 강제·게시 불가. 헤더는 `fetch_blocked` reason `signal_noai` |
| IMP-09 | F | `https://10.0.0.5/`, `https://169.254.169.254/`, `https://[fd00::1]/`, `https://2130706433/`, 비격리 모드의 loopback | 전부 `fetch_blocked`/`url_rejected`. fixture·네트워크 요청 0건 |
| IMP-10 | F | 테스트 resolver(`DMEM_TEST_RESOLVE`)로 `mixed.test` → `[203.0.113.10, 10.0.0.7]`, `loop.test` → `[127.0.0.1]`(fixture 호스트 아님) | 둘 다 `fetch_blocked` reason `private_address`(모든 A/AAAA를 검사). 해석 후 연결 대상 IP 재확인은 제품 단위 테스트(`L0`: "검사한 IP에 직접 연결, 재해석 없음") |
| IMP-11 | F | `/redirect/3`, `/redirect/4`(둘 다 끝은 `/pages/resume-us.html`. 가져오기는 쿼리를 버리므로 `to`를 쓰지 않는다), `/redirect/private`(Location `http://10.255.255.1/`) | 3회는 성공. 4회는 `redirect_limit`. `private`은 `private_address`. 사설 대상으로 요청이 나가지 않는다. https→http 다운그레이드(`scheme`)는 loopback fixture가 http뿐이라 `L0` 단위 테스트가 확인한다 |
| IMP-12 | F | `file:///etc/passwd`, `ftp://…`, `data:…`, `javascript:…`, `https://example.com:8443/` | 전부 거부(`scheme_not_allowed`/`host_not_allowed`), 요청 0 |
| IMP-13 | F | `/big`(6 MiB), `/gzbomb` | 둘 다 `fetch_blocked` reason `size`. 읽고 해제한 바이트가 한도(5 MiB) + 제한된 버퍼 안(클라이언트 최대 메모리 증가 < 40 MiB, 소요 시간 < 8초 — 서버 쪽 전송량은 loopback 소켓 버퍼링 때문에 증거가 못 된다), 부분 저장 0 |
| IMP-14 | F | `/slow`(15초 지연) | 10초 근처에서 `fetch_blocked` reason `timeout`, 저장 0 |
| IMP-15 | F | `/type-mismatch.docx`, `/binary` | `fetch_blocked` reason `content_type`, 저장 0 |
| IMP-16 | F | `/pages/login-required`, `/pages/unauthorized`, `/pages/forbidden` | `fetch_blocked` reason `login_required`와 안내(파일 내려받아 `--file`, Arise 현재 탭 클립). fixture 요청 로그에 `Cookie`·`Authorization` 헤더 **이름** 0건 |
| IMP-17 | F | `hostile-inject.html`(활성)과 `hostile-static.html`(정적) import | `hidden_text_removed`·`injection_flagged` 경고. 저장물에 `HIDDEN_SENTINEL_*`, `<script`, `<iframe`, `onerror`, 제로폭·양방향 문자 0건. L1에 주입 문구 없음 |
| IMP-18 | F | Docs 모양(`export?format=md`), Slides 모양(pptx), Notion 모양 URL | 각각 StandardDoc(document, deck, document), provider `google_docs`/`google_slides`/`notion`, doc_type·locale 제안이 있다. Slides에서 `format=md` 요청 0건(`FMT-09`) |
| IMP-19 | F | Arise에서 `hostile-static.html`·`resume-ko.html?Q_SENTINEL…#F_SENTINEL…` 탭을 열고 `doc_memory_clip_current_tab`([`host-smoke.md`](host-smoke.md) SMK-10) | `provenance == "captured"`, 탭 URL의 canonical과 일치, 쿼리·fragment 센티널 0. **`innerText`는 크기 0·배경색 동일 텍스트를 내보내므로**(Arise 실측, [`hosts/arise.md`](hosts/arise.md)) 저장물에 `HIDDEN_SENTINEL_*`·주입 문구가 0건이어야 한다. 비밀번호 입력이 있는 `/login` 탭은 `login_required`로 거부. 사용자 탭·다른 세션 탭은 거부. `dmem browser-mcp`가 없으면 `SKIP` |
| IMP-20 | F | 1분 안에 `web preview`/`import`를 한도 초과(제안: 분당 30회)·동시 호출 상한 초과 | 초과분은 종료 6 `rate_limited`, 상태 변화 0, 앞선 호출은 정상 |

## VER: 버전 ([`../spec/memory.md`](../spec/memory.md) 6절)

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| VER-01 | F | `bob`이 `alice`의 공개 양식 v1을 복사한 뒤 `alice`가 원본을 v2로 저장하고 `publish --version 2`로 공개해 승인(공개되지 않은 v2는 다른 사용자에게 head가 아니다, `VER-05`). `bob`이 다시 복사 | 기존 복사본의 `derived_from.version == 1`이 유지되고, 새 복사본은 공개된 head인 v2를 가리킨다. 웹 문서 수준(`RT-07`~`RT-08`)은 [`README.md`](README.md) 7절 |
| VER-02 | R1 | `expand --version n` 반복 | 같은 버전은 항상 같은 내용 해시를 돌려준다 |
| VER-03 | R1 | v2까지 저장한 뒤 `recall` | head인 v2만 힌트로 나오고 superseded v1은 나오지 않는다(`expand --version 1`은 가능) |
| VER-04 | F | 메모리를 삭제한 뒤 `expand --version 1` | `not_found`(현재 버전이나 다른 버전으로 대체하지 않는다) |
| VER-05 | F | v1을 publish한 뒤 v2를 저장 | 공개는 v1 그대로. `publish --version 2` 이후에 v2가 공개된다 |
| VER-06 | F | `outcome`의 `used`에 receipt에 없는 `(memory_id, version)` | `invalid_input`, 점수·기록 변화 0 |

## TPL: 양식 흐름 (overview 10절 + 국가·provider 변형)

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| TPL-01 | R1 | 제목/본문 스타일, 표, 요약→지표→위험→요청 순서의 DOCX 양식 업로드(overview 10절). 같은 내용으로 새 문서 시작 | 추출 미리보기에 구조·스타일이 보이고(`FMT-05`) 개인 양식으로 저장된다(`LIB-02`). 새 문서의 섹션 순서·주요 스타일이 같다(웹/API 수준, `RT-06`~`RT-07`) |
| TPL-02 | F | 다른 사용자가 공개한 양식을 검색→미리보기→새 문서 시작(overview 10절) | 작성자·라이선스·버전이 미리보기와 사용 기록에 있다(`SHR-10`). 원본은 바뀌지 않고 내 복사본이 생긴다(`SHR-11`) |
| TPL-03 | F | 팀 전용 양식을 비회원이 조회(overview 10절) | 메타데이터·본문이 보이지 않는다(`SHR-06`). 공개 여부만으로 권한을 우회하지 못한다 |
| TPL-04 | F | KR·US·JP 이력서 양식을 각각 저장(KR: A4·`name_ko`·`phone`·`address_kr` 슬롯, US: Letter·사진·나이 슬롯 없음, JP: `jp_rirekisho`·`furigana`·`birth_date` 슬롯) | 세 양식이 별개 메모리로 공존하고 `expand(level=2)`의 `slots`·`page`가 각 국가 관습을 반영한다. locale 지정 recall이 정확한 변형을 1순위로 준다(`FORM-16`) |
| TPL-05 | F | US Letter 양식을 ko-KR 작업에 recall | `paper_mismatch`·`date_order_mismatch`·`currency_mismatch`·`name_order_mismatch` 경고가 있고 `expand`의 `page.size == "Letter"`다. 양식 자체는 변경되지 않는다 |
| TPL-06 | F | 같은 `pitch_deck`을 `google_slides`와 `pptx`로 저장하고 `provider=google_slides`로 recall, 문서 family(resume)로 recall | `google_slides` 항목이 먼저(`provider_exact`). resume 질의에는 deck이 나오지 않는다(family 불일치) |
| TPL-07 | F | 필수 슬롯(`name`, `date`)이 있는 양식을 Markdown으로 내보내기 | `{{name}}`·`{{date}}` 표식이 그대로 남고 `expand(level=2)`의 `slots[].required`와 일치한다 |
| TPL-08 | F | `deck-5.pptx`를 template로 저장하고 `pptx`로 내보낸 뒤 다시 가져오기 | 유효한 PPTX(ZIP/XML), 슬라이드 5장, 제목 보존, 재가져오기 후 역할 `cover`·`problem`·`ask`가 같다 |

## DOC: 문서 작성 (overview 10절, 웹·API 수준)

`DOC-03` 이후와 편집기·생성 계약은 [`functional-document.md`](functional-document.md)가 정의한다. 아래 둘은 overview의 원본 케이스이며 블랙박스 CLI/MCP 하네스는 실행하지 않고 제품의 API·웹 테스트가 실행한다(`SKIP(L3)`).

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| DOC-01 | R1 | 양식과 참고자료를 선택해 "월간 보고서" 작성 요청 | 편집기에 해당 섹션을 가진 초안이 만들어지고 자료를 인용한 문장을 원문 위치(span)에서 확인할 수 있다. 선택하지 않은 자료는 쓰이지 않는다(`RT-07`) |
| DOC-02 | R1 | Q4 매출 값이 없는 상태에서 Q4 실적 보고서 작성 요청 | `{{확인 필요: Q4 매출}}`이 남고 근거 없는 수치는 생성되지 않는다 |

## PRIV: 개인정보·동의·삭제 ([`../spec/privacy.md`](../spec/privacy.md))

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| PRIV-01 | R1 | 로컬 모드에서 저장·검색·복사·가져오기 흐름 전체를 네트워크 기록 아래 실행(`web preview` 제외) | 새 메모리 `visibility == "private"`, 로컬 라이브러리 동작 중 외부 요청 0건 |
| PRIV-02 | F | 서버 모드 `recall`의 요청 본문 기록 | `RCL-17`의 허용 필드만 있다 |
| PRIV-03 | F | 동의가 있는 publish | 서버가 `consent_version`, 시각, 대상(`memory_id`·`version`·`visibility`·`license`)을 기록한다. 동의 없는 publish는 쓰기 0건(`SHR-02`) |
| PRIV-04 | F | 검수 대기(`queued`) 중인 publish를 `visibility=private`로 | 대기 항목이 취소되고 공개 조회에서 즉시 제외된다 |
| PRIV-05 | F | 텔레메트리 설정 토글 후 `status` | 공유 동의(`consent.sharing`)가 바뀌지 않는다 |
| PRIV-06 | F | publish 확인 출력 | "자동 탐지는 완전하지 않으며 게시 책임은 소유자에게 있다"는 고지 문구가 사람용 출력에 있고 `--json`에는 `notice` 필드가 있다(문구는 고정 키 `privacy.detection_limit`) |
| PRIV-07 | F | 시계를 조작해 preview 16분, 거절된 publish payload 8일, receipt 31일 경과 | 각각 삭제되어 조회·재사용 불가. 감사 사실(사유 코드)은 남는다 |
| PRIV-08 | R1 | 센티널이 든 메모리 저장 후 `delete`, 전체 `DMEM_HOME`·캐시 스캔 | 센티널 0건(`LIB-11`과 같은 sink에 캐시·진단 포함) |
| PRIV-09 | F | 계정 삭제(`confirmation=DELETE`) | 세션·device·credential 해지, 비공개 라이브러리 삭제, 공개 게시물은 선택(삭제/작성자 제거 후 유지)대로 처리, 타인의 복사본은 유지 |
| PRIV-10 | F | opt-out 사용자의 공개 응답, 리더보드 | 이메일·계정 ID·기기 ID·`source_ref`가 공개 응답에 0건 |

## MCP: 프로토콜·도구 계약 ([`../spec/mcp.md`](../spec/mcp.md))

`dmem-mcp`를 stdio로 띄워 JSON-RPC를 직접 주고받는다.

| ID | 단계 | 입력 | 기대 결과와 판정 근거 |
|---|---|---|---|
| MCP-01 | R1 | `initialize`(protocolVersion `2024-11-05`, `2025-03-26`, `2025-11-25`) | 지원 버전에 응답하고 `serverInfo`, `capabilities.tools`, `instructions`가 있다. 지원하지 않는 버전은 협상된 버전으로 응답 |
| MCP-02 | R1 | `tools/list` | 도구 12개(이름이 [`../../contracts/mcp-tools.v1.json`](../../contracts/mcp-tools.v1.json)과 일치), 각 `inputSchema`가 카탈로그와 같다. 2025-03-26 이상에서만 `annotations`, `outputSchema`는 `delete`에만 있다 |
| MCP-03 | R1 | 각 도구의 성공 호출 | text JSON과 `structuredContent`가 같고 스키마 `result`(카탈로그)를 통과한다 |
| MCP-04 | R1 | 알 수 없는 method, 알 수 없는 tool 이름 | JSON-RPC 오류(-32601 / -32602), 상태 변화 0 |
| MCP-05 | R1 | 잘못된 인자(타입 위반, enum 밖, 알 수 없는 필드, `limit` 범위) | `isError == true`, `error.code == "invalid_input"`, 입력 에코 없음, 상태 변화 0 |
| MCP-06 | R1 | 모든 호출 동안 stdout 수집 | JSON-RPC 메시지 외의 바이트 0. 로그는 stderr로만 |
| MCP-07 | R1 | 64 KiB 초과 프레임, 잘못된 UTF-8, 잘못된 JSON | 원문 없이 parse error(-32700 등) 응답 후 같은 연결에서 다음 `ping` 성공 |
| MCP-08 | R1 | 진행 중 요청 취소(`notifications/cancelled`), 알 수 없는 id 취소, `ping` | 취소 가능한 요청은 중단, 알 수 없는 id는 무시, `ping`은 응답 |
| MCP-09 | R1 | `doc_memory_recall` 계약 | `RecallResult` 스키마, ≤3 힌트, `RCL-11`·`RCL-14` |
| MCP-10 | F | `doc_memory_search` 계약 | `SearchResult` 스키마, `limit ≤ 20`, `cursor` 왕복 |
| MCP-11 | R1 | `doc_memory_expand` 계약 | `level` 1·2, `version` 고정, 보이지 않으면 `not_found` |
| MCP-12 | R1 | `doc_memory_save` 계약 | 인라인 `content`만 받고 파일 경로 필드가 없다(`inputSchema`에 `file`·`path` 키 0). `dry_run`, `created`, `secret_detected` |
| MCP-13 | F | `doc_memory_web_search`·`web_preview`·`import` 계약 | 각 스키마 통과, 제한·오류 코드가 `DISC`·`IMP`와 같다 |
| MCP-14 | F | `doc_memory_copy` 계약 | `CopyResult` 스키마, `derived_from`, `license_forbids`+`allowed_modes` |
| MCP-15 | F | `doc_memory_publish` 계약 | `consent` 없으면 `consent_required`, `private`은 동의 없이 통과 |
| MCP-16 | R1 | `doc_memory_delete` 계약 | `confirm` 없으면 `invalid_input`, `confirm:true`면 `DeleteResult` |
| MCP-17 | F | `doc_memory_outcome` 계약 | 같은 결과·버전 집합(순서 무관)은 `duplicate:true`, 다른 결과는 `version_conflict`, 타인·만료 receipt는 `not_found` |
| MCP-18 | R1 | `doc_memory_status` | `StatusResult` 스키마. 토큰·이메일·계정 ID·device 이름이 응답에 없다 |
| MCP-19 | R1 | 도구 annotations | 읽기 전용 도구(`status`, `recall`, `search`, `expand`, `web_search`, `web_preview`)만 `readOnlyHint: true`, `delete`만 `destructiveHint: true`. 실제 동작(저장소 변화 여부)이 표시와 일치 |
| MCP-20 | F | 로컬·익명·연결 신원별 도구 허용·거부 | `SHR-18`·`CLI-15`와 같은 매트릭스(익명 `publish`·`outcome`은 `auth_required`, 로컬 쓰기는 허용) |
| MCP-21 | F | `dmem-mcp`와 WAM `wam-mcp`(`web_memory_*`)를 한 호스트에 등록 | 도구 이름 충돌 0, 서로의 `tools/list`에 영향 없음, 한쪽 제거가 다른 쪽 설정을 바꾸지 않는다. WAM 바이너리가 없으면 `SKIP`(이름 비교는 정적 검사로 수행) |
| MCP-22 | R1 | `instructions` | 앞 512자 안에 recall 호출 지시와 untrusted 규칙이 있고(자기완결), 전체 4,096자 이하, 각 도구 설명 4,096자 이하 |
| MCP-23 | R1 | `tools/list`+`instructions`의 UTF-8 크기 | 초기 상한 12,000 bytes 이하(est tokens ≈3,000). 측정값을 기록하고 초과하면 계약 재검토 |
| MCP-24 | L0 | 원격 Streamable HTTP(서버 모드): `POST`/`GET`, Origin allowlist, `Accept`, 401 `WWW-Authenticate`, 64 KiB | 제품 서버 통합 테스트가 확인한다(`SKIP(L0)`) |
