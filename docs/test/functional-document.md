# DOC: 문서 편집기와 작성 흐름 기능 테스트

상태: 문서 우선 테스트 스펙(구현 전).
영역 / 테스트 ID 접두사: `DOC` (케이스: [`../spec/document.md`](../spec/document.md))
기반: [`../spec/formats.md`](../spec/formats.md), [`../spec/memory.md`](../spec/memory.md), [`../spec/library.md`](../spec/library.md), [`../spec/sharing.md`](../spec/sharing.md), [`../spec/privacy.md`](../spec/privacy.md), [`../spec/runtime-v1.md`](../spec/runtime-v1.md)

이 파일은 테스트 ID `DOC-03`~`DOC-12`를 정의한다. `DOC-01`~`DOC-02`는 [`functional-tests.md`](functional-tests.md)에 정의되어 있다. 이 표의 DOC ID는 테스트 케이스이며 `template-library.md`의 DOC/SLIDE/SHEET 번호는 시드 카탈로그 항목 ID다.

## 1. 편집과 작성

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| DOC-03 | `stddoc/1`, `type=document`에 heading("개요"), paragraph("초안"), list, table 블록을 넣고 heading을 "요약"으로 편집해 저장 후 다시 연다. | 블록 타입과 순서는 heading→paragraph→list→table로 유지되고 제목만 "요약"으로 바뀐다. 미지원 블록을 추가하면 조용히 삭제하지 않고 `warnings`에 `unsupported_block`이 나온다. |
| DOC-04 | 문서에 `{{project_name}}`(필수 text), `{{due_date}}`(date)를 두고 각각 "결제 API 이전", `2026-12-01`을 입력해 저장한다. | 입력 UI의 필드명·종류가 슬롯 정의와 같고 저장 본문에서 두 표식이 입력값으로 치환된다. |
| DOC-05 | 양식의 본문에 `{{확인 필요: 월 매출}}`을 두고 월 매출 수치나 참고자료 없이 초안을 생성한다. | 초안과 Markdown 내보내기에 표식이 그대로 남고 월 매출 수치를 새로 만들지 않는다. |
| DOC-06 | `type=deck`의 표지·문제·트랙션 3장 outline과 `template_id/version=seed-pitch/2`, 참고자료 `report-8/4`를 선택한다. 승인 전 생성 요청 후 승인한다. | 승인 전 문서 생성이 0건이다. 승인 후 장 순서가 유지되며 산출물에 두 입력 버전이 기록되고, 제공하지 않은 트랙션 수치는 확인 필요로 남는다. |

## 2. 출처, 버전, 내보내기

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| DOC-07 | 복사한 양식의 `derived_from={memory_id:"seed-42", version:3, author_handle:"hana", license:"CC-BY-4.0"}`로 문서를 만들고 편집기에서 확인한 뒤 Markdown으로 내보낸다. | 출처 패널과 내보낸 결과 모두 원 저작자 `hana`, 라이선스 `CC-BY-4.0`, 원본 버전 3을 표시한다. 원본 ID·버전은 편집 중 바뀌지 않는다. |
| DOC-08 | 기존 문서 `doc-9`의 현재 version 1을 `base_version=1`로 열어 본문을 "초안 B"로 바꾸고 저장한다. | 응답은 version 2이며 현재 본문은 "초안 B"다. version 1을 조회하면 이전 본문이 그대로 남는다. |
| DOC-09 | `doc-9`의 version 2가 저장된 뒤, 오래된 `base_version=1` 화면에서 본문 "오래된 저장"을 제출한다. | 응답 오류는 `version_conflict`; head는 version 2와 "초안 B" 그대로이고 서버의 추가 버전은 0건이다. 편집 화면의 "오래된 저장" 초안은 지워지지 않는다. |
| DOC-10 | 문서 fixture를 `md`, `html`, `docx`, `json`으로, 덱 fixture를 `md`, `html`, `pptx`, `json`으로 내보낸다. 같은 요청에서 `sheet`의 `.xlsx` 및 Google Docs/Slides/Sheets 직접 생성도 선택한다. | 문서·덱은 formats 명세의 지원 형식만 만든다. 지원 블록과 순서는 보존되고 HTML 실행 스크립트는 0개다. 시트 XLSX와 직접 Google 생성은 성공으로 보고하거나 결과 파일을 만들지 않으며 미지원/후속으로 표시한다. |

## 3. 개인 정보 경계

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| DOC-11 | 문서에 합성 개인정보 `윤가람`, `garam-doc-test@example.invalid`와 고유 문구 `DOC-SENTINEL-781`을 슬롯으로 입력한 뒤 저장하고 공개 카탈로그에서 고유 문구를 검색한다. | 문서 visibility는 `private`이고 일반 공개 결과에 문서와 sentinel이 각각 0건이다. 템플릿 공개 카탈로그에 개인 입력이 자동 복사된 쓰기도 0건이다. |
| DOC-12 | 위 비공개 문서로 게시를 요청한다. 먼저 `consent=false`, 다음으로 `consent=true`를 보내고 개인 정보 검수를 확인한다. | 동의 없는 요청은 서버 게시 요청·쓰기 0건이다. 동의 후에도 개인 정보 검수 결과는 `rejected`/`personal_data`, 공개 레코드 0건이며 비공개 문서와 입력 초안은 그대로 남는다. |

## 4. 판정 범위

표의 버전·출처·형식 값은 fixture 입력이다. 실행 시 UI 표시만 보지 않고 저장된 `StandardDoc`, 응답의 version/error/warnings, 내보낸 파일, 공개 검색 결과를 확인한다.

개인 정보 탐지는 휴리스틱이므로 테스트에는 합성 주소·이메일·식별값만 사용한다. 게시 단계에서는 자동 탐지 통과를 안전 판정으로 간주하지 않고 사용자 동의와 별도 검수를 확인한다.

## 5. 단계별 실행 조건

`DOC-03`~`DOC-10`은 편집기 구현 단계에서 실행한다. `DOC-11`~`DOC-12`는 게시 기능이 runtime-v1 이후 단계에 추가될 때 실행한다.

이 문서는 예상 동작을 고정하며, 테스트 케이스 정의 자체가 현재 구현 지원을 뜻하지 않는다.
