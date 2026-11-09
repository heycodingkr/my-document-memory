# FORM: 양식(Form) 객체, 국가·provider 변형, 관습 경고

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM의 `task_category` 폐쇄 어휘를 **문서 종류 + 로케일 + provider** 세 축으로 확장한 신규 명세다.
영역 / 테스트 ID 접두사: `FORM` (케이스: [`../test/functional-tests.md`](../test/functional-tests.md))
기반: [`core.md`](core.md) 5절(정규화 순서), [`formats.md`](formats.md)(provider별 가져오기·내보내기), [`overview.md`](overview.md) v0.3

## 1. 왜 양식이 URL과 따로 필요한가

URL은 "어디서"를 말하고 양식은 "어떤 모양인가"를 말한다. `docs.google.com/document/d/:id/edit`에서 한국어 이력서와 미국식 resume, 일본의 履歴書는 서로 다른 구조를 쓴다. 같은 이력서도 용지(A4/Letter), 날짜 순서, 이름 순서, 필수 항목이 다르다. 같은 사이트의 Docs와 Slides는 같은 호스트지만 편집 모델이 전혀 다르다. 그래서 recall은 항상 **URL + 양식** 쌍으로 조회하고, 저장도 두 키를 함께 받는다.

## 2. 양식 객체

| 필드 | 필수 | 규칙 |
|---|---|---|
| `provider` | 예(저장), 아니오(recall) | 닫힌 어휘: `google_docs`, `google_slides`, `google_sheets`, `notion`, `docx`, `pptx`, `xlsx`, `pdf`, `markdown`, `txt`, `html`, `other` |
| `doc_type` | 예(저장), 아니오(recall) | 닫힌 어휘(3절). 별칭을 canonical id로 바꾼다 |
| `locale` | 예(저장), 아니오(recall) | 어휘의 BCP 47 값(4절). 언어만도 허용 |
| `region` | 아니오 | ISO 3166-1 alpha-2. 기본은 `locale`의 region이고 명시하면 덮어쓴다(미국 법인의 한국어 문서처럼 언어와 관습 지역이 다를 때) |
| `family` | 파생 | `document` / `deck` / `sheet`. provider에서 정한다([`core.md`](core.md) 3절) |
| `page` | 아니오 | `size`: `A4`, `A3`, `A5`, `Letter`, `Legal` 또는 슬라이드 비율 `16:9`, `4:3`, `custom`. `orientation`: `portrait`, `landscape`. `margins_mm`: 4개 정수 0~100 |
| `variant` | 아니오 | `[a-z0-9_]{1,32}`. 같은 doc_type 안의 국가·관행별 표준형을 구분한다(`jp_rirekisho`, `us_chronological`, `kr_tax_invoice`). 어휘로 닫지 않는다 |

저장된 메모리의 양식은 변경하면 새 버전이다([`memory.md`](memory.md)).

## 3. 문서 종류 어휘 v1

`doc_types` 어휘는 [`../../contracts/vocab/doc_types.json`](../../contracts/vocab/doc_types.json)이 원본이다. 항목은 `id`, `family`, 다국어 `labels`, `aliases[]`(`value`, 필요하면 `variant`)를 가진다. 초기 목록은 제품 양식 목록(`template-library.md`, 작성 중인 별도 문서)과 맞춰 확장한다.

| family | id |
|---|---|
| document | `resume`, `cover_letter`, `invoice`, `quote`, `contract`, `nda`, `report`, `proposal`, `meeting_minutes`, `business_plan`, `press_release`, `memo`, `official_letter`, `lesson_plan` |
| deck | `pitch_deck`, `report_deck`, `proposal_deck`, `lesson_deck` |
| sheet(후속, 메타데이터만) | `budget_sheet`, `invoice_sheet` |
| 공통 | `other` |

별칭 예: `이력서`·`resume`·`cv` → `resume`(`cv`는 variant `cv`), `履歴書` → `resume` + `jp_rirekisho`, `세금계산서` → `invoice` + `kr_tax_invoice`, `適格請求書` → `invoice` + `jp_qualified`, `견적서`·`見積書`·`angebot` → `quote`, `회의록`·`議事録` → `meeting_minutes`, `사업계획서` → `business_plan`, `수업지도안`·`교안` → `lesson_plan`.

어휘 밖 값은 `invalid_form: doc_type_unknown`이다. 새 종류는 어휘 버전을 올려 추가한다(`status`의 `vocab.doc_types`).

## 4. 로케일과 국가 관습

`locales` 어휘 v1: `ko-KR`, `en-US`, `en-GB`, `ja-JP`, `zh-CN`, `de-DE`, `fr-FR`. 원본은 [`../../contracts/vocab/regions.json`](../../contracts/vocab/regions.json)(`locales`, `regions`)이고, 지역 관습 프로필의 원본은 [`../../contracts/vocab/region_profiles.json`](../../contracts/vocab/region_profiles.json)이다.

### 로케일 일치 단계 (`locale_match`)

| 값 | 의미 |
|---|---|
| `exact` | 언어와 region이 모두 같다 |
| `language` | 언어는 같고 region이 다르거나 한쪽이 언어만 가졌다 (`en-GB` ↔ `en-US`, `ko` ↔ `ko-KR`) |
| `none` | 언어가 다르다 |
| `unspecified` | 질의에 locale이 없다 |

### 지역 관습 프로필 (경고용 힌트)

recall은 메모리의 지역 관습과 질의 대상의 관습이 다르면 `warnings[]`를 붙인다. 값은 용지(ISO 216 / 북미 Letter), 날짜 표기 순서, ISO 4217 통화 소수 자릿수, 이름 순서의 **관습 힌트**이며 법적 요건이 아니다. 검증과 강제가 아니라 "확인하세요" 신호다.

| region | 기본 용지 | 날짜 순서 | 통화(소수) | 이름 순서 |
|---|---|---|---|---|
| KR | A4 | YMD | KRW(0) | family_given |
| US | Letter | MDY | USD(2) | given_family |
| GB | A4 | DMY | GBP(2) | given_family |
| JP | A4 | YMD | JPY(0) | family_given |
| CN | A4 | YMD | CNY(2) | family_given |
| DE | A4 | DMY | EUR(2) | given_family |
| FR | A4 | DMY | EUR(2) | given_family |

| 경고 코드 | 조건 |
|---|---|
| `paper_mismatch` | 메모리 `page.size`(또는 지역 기본 용지)와 질의 지역 기본 용지가 다르다 |
| `date_order_mismatch` | 날짜 순서가 다르다(특히 MDY↔DMY는 일자 오해 위험) |
| `currency_mismatch` | 통화 또는 소수 자릿수가 다르다 |
| `name_order_mismatch` | 이름 순서가 다르다 |
| `provider_mismatch` | 질의 provider와 메모리 provider가 다르다(변환 가능 여부는 [`formats.md`](formats.md)) |

국가별 **필수 항목**(예: 사업자등록번호, 적격청구서 등록번호, VAT ID)은 어휘가 아니라 양식의 `slots`와 `rules`로 표현한다([`memory.md`](memory.md)). 합성 fixture는 형태만 흉내 내고 실제 번호를 쓰지 않는다.

## 5. 변형 공존

같은 `(url pattern, kind, doc_type)`에서 locale·variant가 다르면 서로 다른 메모리로 공존한다([`core.md`](core.md) 6절). recall에 locale이 있으면 `locale_match` 순으로 정렬된다. 한 사용자가 한국어·영어·일본어 이력서를 따로 두고 목적지 국가에 맞게 가져오는 흐름이 기본이다.

## 6. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-FORM-01 | 별칭 해석 | 다국어 별칭이 canonical `doc_type`(+variant)이 되고 어휘 밖은 거부된다 | FORM-02~04 |
| F-FORM-02 | 로케일 정규화와 일치 단계 | `ko_KR`→`ko-KR`, 언어만 허용, `locale_match` 4단계 | FORM-05~06, FORM-11 |
| F-FORM-03 | provider·family 일관성 | 명시값 우선, family 불일치는 거부 | FORM-01, FORM-10, FORM-15 |
| F-FORM-04 | region 유도와 override | locale에서 파생, 명시값이 우선 | FORM-07 |
| F-FORM-05 | page·variant 검증 | 형식 위반은 `invalid_form` | FORM-08~09 |
| F-FORM-06 | 지역 관습 경고 | 용지·날짜·통화·이름 순서 불일치 경고, 같은 지역은 0건 | FORM-12~13 |
| F-FORM-07 | 어휘 버전 | `status`가 버전을 보고하고 알 수 없는 버전의 데이터는 보존되며 재확인 표시 | FORM-14 |
| F-FORM-08 | 국가별 변형 공존 | KR·US·JP 이력서가 별개로 저장되고 locale 지정 시 정확한 변형이 1순위 | FORM-16, TPL-04~05 |
