# Runtime v1 — 실행 가능한 로컬 문서 메모리

기준: 2026-11-09. overview/core/form/template-library 설계를 구현 단계로 나누는 계약이다. 기존 설계 파일과 데모 작업은 보존한다. 개발/실행 범위는 이 저장소이며 배포는 포함하지 않는다.

범위 주의: 아래는 **최초 로컬 단계의 계약**이다. 이후 [`recall-v1.md`](recall-v1.md), [`accounts-community-v1.md`](accounts-community-v1.md), [`memory-community-smoke-v1.md`](memory-community-smoke-v1.md)가 URL+양식 recall·계정 인증·익명 공개 조회·기여·검수·CLI/MCP를 확장한다. "모든 /v1 요청은 Bearer 필수", "공개 기여 없음"은 최초 단계에만 해당한다. 현재 검증 범위는 [`../test/wam-port-completion-v1.md`](../test/wam-port-completion-v1.md)에 구분해 기록한다. 웹 URL fetch·현재 탭 clip은 아직 목표 계약이다.

## 설계와 참고 근거

형제 저장소 web-agentic-memory의 Cargo workspace, core/contracts/server/client/cli/mcp 경계, Axum 어댑터와 Svelte 웹 구성을 참고한다. WAM의 브라우저 작업 지식, 기여 점수, curator, OAuth 운영 코드를 그대로 복사하지 않는다. 이 제품의 핵심은 개인 양식, 근거 자료와 작성 결과의 분리다.

Rust 2024 workspace + Axum 0.8 + SQLite(rusqlite), Svelte 5 + TypeScript + Vite를 사용한다. SQLite는 추가 서비스 없이 로컬 실행/검증하는 첫 저장 어댑터다. overview의 PostgreSQL·객체저장소·worker는 다중 사용자 운영 단계이며 이 구현이 지원한다고 표시하지 않는다.

## 의존 순서와 원자 목표

| 순서/경로 | 산출물 | 부모 독립 검증 | 선행 |
|---|---|---|---|
| 1 contracts/ + crates/dmem-contracts | 닫힌 어휘, HTTP/CLI 공유 DTO, 고정 오류 | serde 계약·한도·잘못된 필드 테스트 | 없음 |
| 2 crates/dmem-core | URL/양식 정규화, 원본에서 블록 추출, 안전한 내보내기 | 입력/기대값 테이블 + 실제 ZIP/XML 확인 | 1 |
| 3 crates/dmem-server | SQLite migration, 소유자 격리, 라이브러리/자료/문서 API, 충돌 검사 | 실제 Router·임시 SQLite 통합 테스트, 재열기 영속성 | 1,2 |
| 4 crates/dmem-client → cli/mcp | 공통 HTTP client, dmem CLI, stdio JSON-RPC tools | 실제 API smoke와 JSON-RPC 오류/도구 계약 | 3 |
| 5 web | 라이브러리/자료/최근 문서, 블록/슬라이드 편집, 저장/내보내기 | TypeScript/Svelte check, build, 실제 API 연결 브라우저 smoke | 3 |
| 6 README/.env.example/scripts | 실행 방법, 기능/제한 표, 통합 smoke | clean command 기준 직접 실행, 최종 diff 리뷰 | 4,5 |

설계·구현 판단·파일 수정 전 해당 코드 읽기·빌드·테스트·통합·최종 리뷰는 부모가 수행한다. 반복적인 crate manifest 골격만 읽기 범위를 명시해 위임할 수 있다. 위임 결과 요약은 증거로 쓰지 않고 파일을 직접 읽는다.

## 동작 계약

- 서버는 기본 127.0.0.1:3847. DMEM_TOKEN 필수. 인증 실패는 auth_required, 리소스 부재와 타 소유자의 비공개 리소스는 모두 not_found. 로컬 웹은 사용자가 입력한 token을 세션에만 보관한다.
- 모든 /v1 요청은 Bearer token이 필요하다. /healthz는 데이터 없는 준비 확인이다. 설정 token 하나가 로컬 소유자 하나에 해당하며, 테스트용 인증자에서 복수 소유자를 검증한다. 브라우저 Origin은 설정한 로컬 웹 주소만 허용한다.
- 현재 runtime-v1의 공개 catalog는 읽기 전용 시드 양식이다. 사용자의 public contribution, review queue, URL importer는 구현 범위에 없다. 시드 복사는 private 새 양식이며 원본 id/version/author/license를 보존한다. 공개 조회는 양식 구조만 포함하며 타인 자료 본문은 포함하지 않는다.
- 자료는 TXT/Markdown 및 기본 DOCX/PPTX 텍스트/제목/표 추출을 지원한다. 원본 bytes와 체크섬을 보존하고 source span(문단/슬라이드 위치)을 붙인다. 크기·확장자·ZIP 해제 한도를 검사한다. PDF 가져오기/OCR, 복잡한 Office 레이아웃은 후속이며 지원으로 위장하지 않는다.
- 양식과 자료는 별도 endpoint와 검색 결과를 쓴다. 검색은 소유권/종류 필터를 먼저 적용하며 query 최대 200자, 결과 최대 20개다.
- 새 문서는 선택한 양식의 불변 버전과 선택한 자료 버전을 기록한다. 외부 LLM 없는 결정적 초안 작성: 각 섹션은 확인 필요 placeholder로 시작하고 선택한 자료 원문은 출처와 함께 별도 근거 블록으로만 추가한다. 양식 예시와 자료 내용을 임의의 사실로 합성하지 않는다.
- deck 생성은 순서가 있는 목차를 웹에서 확인하고 명시적으로 승인한 후 생성한다. sheet 편집은 후속이며 작성 버튼을 제공하지 않는다.
- 저장은 base_version을 요구하고 트랜잭션으로 비교한다. 오래된 저장은 version_conflict, 이전 내용은 revisions에서 읽을 수 있다. 근거 인용은 자료의 해당 불변 버전을 가리킨다.
- 기본 편집 블록은 heading/paragraph/list/table/quote. deck은 순서가 있는 slide(title/body) 모델이다. 내보내기: Markdown/HTML, 기본 DOCX(document)/PPTX(deck). PDF는 브라우저 인쇄를 이용하며 서버 PDF 엔진으로 표현하지 않는다. HTML/XML은 항상 escape한다.
- URL 투영은 core 규칙대로 provider ID/query/fragment를 보존하지 않는다. URL 원격 fetch와 URL provenance 저장은 이번 단계에 없으며 source_ref를 만들어냈다고 표시하지 않는다.
- 모든 입력은 길이/알 수 없는 필드/유효하지 않은 family/빈 제목을 검사하고 고정 오류만 반환한다. 사용자 입력·파일 내용·token을 오류나 로그에 되돌려 주지 않는다.

## 테스트 입력과 기대 결과

| ID | 입력 | 기대 결과 |
|---|---|---|
| RT-01 | Google Docs 두 개 ID + resourcekey/query | 같은 docs.google.com/document/d/:id/edit, 원본 ID와 query 없음 |
| RT-02 | http, userinfo, IP, localhost, 이메일 경로 | 고정 url_rejected reason, 입력 echo 없음 |
| RT-03 | 이력서 + KO_kr; 履歴書; google_slides + resume | resume/ko-KR, resume/jp_rirekisho, family_mismatch |
| RT-04 | 공개 회의록 양식 복사 | private 복사, 새 ID, 원본 버전/저작자/라이선스 보존 |
| RT-05 | A의 비공개 자료를 B가 목록·ID·검색·문서 생성으로 접근 | 노출 0건, ID 접근/생성은 not_found |
| RT-06 | UTF-8 Markdown 제목·문단, DOCX 표, PPTX slide | 추출 블록/위치와 원본 체크섬 보존, 빈/잘못된/대형 파일 거부 |
| RT-07 | 양식만 선택해 초안; 선택한 자료 하나 추가 | 확인 필요 텍스트, 선택 자료만 근거 블록/버전 링크 |
| RT-08 | v1 기반 저장 2회 + DB 재열기 | 첫 저장 v2, 두 번째 conflict, v1/v2 내용 보존 |
| RT-09 | <script>, &, 따옴표를 문서에 넣고 HTML/Office export | 실행 가능한 HTML 삽입 없음, 유효한 ZIP/XML, 텍스트 보존 |
| RT-10 | API 연결 실패/401/빈 검색/저장 충돌 | 웹에서 복구 가능한 오류, 미저장 내용 보존 |
| RT-11 | MCP initialize/list/call + 잘못된 JSON/unknown tool | JSON-RPC 규격 응답, stdout에 로그 없음 |
| RT-12 | 웹에서 양식 검색→복사→자료 업로드→문서 작성→편집→저장→export | 실제 API/DB에 반영, 새로고침 후 재조회 |
