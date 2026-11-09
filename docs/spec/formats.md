# FMT: 표준 문서 구조, provider 어댑터, 내보내기

상태: 설계 초안(문서 우선, 구현 없음). WAM에는 대응 문서가 없는 신규 명세다. 제품 범위는 [`overview.md`](overview.md) v0.3(문서·슬라이드 우선, 시트는 후속)을 따른다.
영역 / 테스트 ID 접두사: `FMT` (케이스: [`../test/functional-tests.md`](../test/functional-tests.md))
기반: [`form.md`](form.md)(provider·family), [`memory.md`](memory.md)(L2 구조), [`web-import.md`](web-import.md)(가져오기 보안)

## 1. 목적

Google Docs, Google Slides, Notion, Word, PowerPoint 등은 구조와 스타일 모델이 서로 다르다. 서비스는 원본 파일을 보존하면서 **표준 구조(StandardDoc)** 로 변환해 색인·미리보기·복사·내보내기를 한다. 변환이 손실되는 곳은 조용히 버리지 않고 `warnings`로 보고한다. 변환 결과를 원본과 같은 모양이라고 주장하지 않는다.

## 2. 표준 구조 (StandardDoc)

JSON 스키마 원본: [`../../contracts/memory.v1.json`](../../contracts/memory.v1.json)의 `$defs.StandardDoc`. `schema: "stddoc/1"`이고 `type`이 `document`, `deck`, `sheet` 중 하나다.

### document

| 요소 | 규칙 |
|---|---|
| `blocks[]` | `heading`(level 1~6), `paragraph`, `list`(ordered, 같은 종류로 중첩 가능; 항목 문자열 앞 공백 2칸이 1단계 — 순서 있는 목록 안의 글머리표처럼 **종류가 섞인 중첩은 표현하지 못해** 바깥 목록의 종류로 평탄화된다), `table`(header, rows, 병합 셀 표시), `quote`, `callout`(tone: `note`, `tip`, `important`, `warning`, `caution`), `image`(alt, `ref`는 자산 해시) |
| 인라인 | 문단과 항목은 `text` 또는 `runs[]`(`text`, `bold`, `italic`, `code`, `href`) |
| `page` | `size`, `orientation`, `margins_mm`, 머리말·꼬리말 존재 여부, 페이지 번호 |
| `styles` | 이름 있는 스타일(`heading1`~`heading3`, `body`, `table`, `callout`)의 글꼴·크기·굵기·색·정렬·간격 |
| `slots[]` | 작성 시 채울 항목 `name`, `type`(`text`, `date`, `number`, `money`, `list`), `required`, `hint` |
| `rules[]` | 필수·선택 섹션, 순서, 최대 분량, 인용 방식([`memory.md`](memory.md) 4절) |

### deck (슬라이드)

| 요소 | 규칙 |
|---|---|
| `theme` | `aspect`(`16:9`, `4:3`, `custom`), `fonts`(heading, body), `colors`(primary, secondary, accent, background, text) |
| `slides[]` | 순서가 있는 페이지. `index`, `role`, `layout`, `title`, `blocks[]`, `components[]`, `notes` |
| `role` | `cover`, `agenda`, `problem`, `solution`, `product`, `market`, `traction`, `business_model`, `competition`, `team`, `financials`, `ask`, `closing`, `section`, `content` |
| `layout` | `title`, `title_body`, `two_column`, `image_left`, `image_right`, `blank` 등 이름. provider 레이아웃 이름은 가장 가까운 값으로 옮기고 `layout_inferred` 경고를 붙인다 |
| `components[]` | `type`(`text`, `image`, `chart`, `table`, `icon_list`, `quote`, `metric`, `shape`)과 최소 속성. 차트는 데이터 없이 종류·제목만 구조로 보존한다 |

### sheet (후속)

v1은 메타데이터만 다룬다: `sheets[]`(`name`), 열 `header`·`type`·`format`. 수식·검증·차트는 후속이다. Google Sheets와 XLSX의 구조 추출은 provider 감지와 `warnings: sheet_support_deferred`까지만 보장한다.

## 3. provider 어댑터 매트릭스

접근 경로는 세 가지뿐이다. (a) 공개 URL(링크 공유·공개 웹), (b) 사용자가 직접 내려받아 준 파일, (c) Arise 같은 호스트 브라우저에서 사용자가 명시적으로 지시한 현재 탭 가져오기([`browser-host-integration.md`](../design/browser-host-integration.md)). 계정 연동(OAuth) 커넥터는 후속이며 `dmem`은 provider 자격증명을 다루지 않는다.

| provider | 구조 추출에 쓰는 경로(우선순위) | 충실도 | 알려진 한계 |
|---|---|---|---|
| `google_docs` | ① DOCX 내보내기 ② Markdown 내보내기 ③ HTML 내보내기 | ①`structural` ②③`text_only`+구조 | 멀티 탭 문서는 탭별로 따로 가져오거나 평탄화하고 `tabs_flattened` 경고 |
| `google_slides` | ① PPTX 내보내기 | `structural` | **Markdown·HTML 내보내기가 없다.** 레이아웃·역할은 추론(`layout_inferred`) |
| `google_sheets` | ① XLSX 내보내기 ② CSV/TSV | ①`structural` ②`text_only` | **CSV/TSV는 첫 시트만** → `first_sheet_only` 경고. v1은 메타데이터까지 |
| `notion` | ① 공개 페이지 HTML ② 사용자가 내려받은 HTML/Markdown | `structural` | 비공개 페이지는 로그인이 필요해 `fetch_blocked: login_required`. 하위 페이지·DB는 별개 항목 |
| `docx` / `pptx` / `xlsx` | OOXML 직접 파싱 | `structural` | 매크로·외부 관계·DDE·OLE는 거부([`security-scenarios.md`](../test/security-scenarios.md) SEC-C) |
| `pdf` | 텍스트 레이어 추출 | `text_only` | 스캔 PDF는 `extract_empty: ocr_required`. 레이아웃 재현 주장 금지 |
| `markdown` / `txt` / `html` | 직접 파싱(HTML은 살균 후) | `structural`(md)/`text_only`(txt) | HTML의 스크립트·이벤트 핸들러·숨김 텍스트는 제거하고 경고 |
| HWP/HWPX | 후속 | — | 변환 품질 평가 후 순서 결정([`overview.md`](overview.md) 12절) |

### 검증 상태 (2026-11-09)

| 사실 | 상태 | 근거 |
|---|---|---|
| Google Docs 내보내기 MIME: docx, odt, rtf, pdf, txt, html, html(zip), epub, markdown(`text/markdown`) | **확인** | Google Drive API 문서 "Export MIME types for Google Workspace documents"(최종 갱신 2026-09-03) |
| Google Slides 내보내기: pptx, odp, pdf, txt (Markdown·HTML 없음) | **확인** | 같은 문서 |
| Google Sheets 내보내기: xlsx, ods, pdf, html(zip), csv·tsv(첫 시트만) | **확인** | 같은 문서 |
| Notion 내보내기: PDF, HTML, Markdown & CSV (PDF는 Letter/A4/Legal) | **확인(2차)** | Notion Help "Export your content" 검색 결과와 가이드 요약. 공식 페이지 본문은 직접 읽지 못했다 |
| Google 웹 UI 내보내기 URL 형태(`/export?format=…`), "복사" 링크(`/copy`) | **미검증** | 공식 문서로 확인하지 못했다. 어댑터 구현 시 확인하고, 그 전까지 fixture는 이 경로를 **모사**할 뿐이다 |
| Google Docs API의 탭 구조와 Slides API의 레이아웃 모델 | **미검증** | 커넥터 단계(후속)에서 확인 |

미검증 항목에 의존하는 구현은 기능 플래그로 가두고, 확인 후 이 표를 갱신한다.

## 4. 충실도와 경고

| 충실도 | 의미 |
|---|---|
| `exact` | 구조와 스타일이 원본과 같다고 검증됨(자체 편집기 문서) |
| `structural` | 블록 순서·제목 단계·표·슬롯은 보존, 스타일은 근사 |
| `text_only` | 텍스트와 위치 출처만 보존 |
| `unsupported` | 가져오지 않음 |

`warnings[]` 코드(고정 enum): `styles_approximated`, `layout_inferred`, `tabs_flattened`, `first_sheet_only`, `sheet_support_deferred`, `images_omitted`, `comments_dropped`, `fields_flattened`, `table_html_fallback`, `unsupported_block`, `hidden_text_removed`, `external_reference_removed`. 지원하지 않는 블록이나 속성이 있으면 반드시 `unsupported_block`이나 해당 경고가 남는다.

## 5. 내보내기

| 대상 | document | deck | 비고 |
|---|---|---|---|
| Markdown(`md`) | 지원 | 지원(슬라이드마다 `---` 구분, 손실) | CLI `dmem export` |
| HTML(`html`) | 지원 | 지원 | 허용 태그 목록만, 스크립트·이벤트 핸들러 없음 |
| DOCX(`docx`) | 지원 | — | 페이지 설정·스타일 반영 |
| PPTX(`pptx`) | — | 지원 | 웹 편집기 경로가 우선, CLI는 구조 템플릿만 |
| JSON(`json`) | 지원 | 지원 | StandardDoc 그대로 |
| PDF | 웹 앱 렌더링 경로(후속) | 웹 앱 렌더링 경로(후속) | CLI는 지원하지 않는다 |

### Markdown 변환 규칙 (document)

| 블록 | 변환 |
|---|---|
| `heading` level n | `#` × n |
| `paragraph` | 텍스트. 인라인은 `**굵게**`, `*기울임*`, `` `코드` ``, `[텍스트](href)` |
| `list` | 순서 없음 `- `, 순서 있음 `1. `, 중첩은 2칸 들여쓰기 |
| `table` | GFM 파이프 표. 병합 셀이나 셀 내 줄바꿈이 있으면 HTML `<table>`로 대체하고 `table_html_fallback` 경고 |
| `quote` | `> ` |
| `callout` | GFM 경고 블록: `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`(tone에 대응) 다음 줄부터 `> ` 본문 |
| `image` | `![alt](assets/<해시>.<확장자>)`, 자산 파일은 `<출력>.assets/`에 쓴다 |
| 슬롯 | `{{name}}` 그대로 |
| 확인 필요 표식 | `{{확인 필요: 항목}}` 그대로 |

내보내기 후 다시 가져온 Markdown은 지원 블록의 종류와 순서가 같아야 한다(FMT-02).

### 내보내기 파일 안전

`--out`은 절대 경로여야 하고 기존 파일을 덮어쓰지 않는다. 심볼릭 링크를 따라가며 쓰지 않는다. 파일은 소유자만 읽고 쓴다(0600). 내보낸 HTML은 허용 태그 밖의 요소를 포함하지 않는다.

## 6. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-FMT-01 | Markdown 변환 규칙 | 5절 규칙대로 내보내고 구조가 사라지지 않는다 | FMT-01~02 |
| F-FMT-02 | HTML·DOCX 내보내기 | 허용 태그만, 재가져오기 시 제목 단계·표·순서·용지 보존 | FMT-03~04 |
| F-FMT-03 | DOCX 가져오기 | 섹션 순서·표·제목/본문 스타일을 추출 | FMT-05 |
| F-FMT-04 | OOXML 보안 | 매크로·외부 관계·DDE·OLE·압축 폭탄을 거부하거나 제거하고 경고 | FMT-06~07 |
| F-FMT-05 | deck 가져오기 | PPTX의 슬라이드 순서·텍스트·테마·역할 추론 | FMT-08~09 |
| F-FMT-06 | provider 제약 반영 | Slides에 Markdown 경로 없음, Sheets CSV 첫 시트 경고 | FMT-09~10 |
| F-FMT-07 | PDF | 텍스트 PDF는 페이지 출처, 스캔은 `ocr_required` | FMT-11 |
| F-FMT-08 | Notion 공개 페이지 | HTML 블록 매핑 | FMT-12 |
| F-FMT-09 | 손실 보고 | 지원하지 않는 요소가 `warnings`에 나타난다 | FMT-13 |
| F-FMT-10 | 내보내기 파일 안전 | 덮어쓰기·상대 경로·심볼릭 링크 거부, 0600 | FMT-14 |
