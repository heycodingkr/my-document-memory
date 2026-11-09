# DB: 저장 중립 계약과 SQLite·PostgreSQL 어댑터

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. runtime-v1의 SQLite `records/revisions/source_files` 골격을 확장한다. WAM의 원장·불변 버전 원칙을 적응하고 Gatekeeper queue 구현 세부는 승계하지 않는다.
영역 / 테스트 ID 접두사: `DB` (케이스: [`../test/functional-api.md`](../test/functional-api.md))
기반: [`core.md`](core.md), [`runtime-v1.md`](runtime-v1.md), [`memory.md`](memory.md), [`library.md`](library.md), [`sharing.md`](sharing.md), [`privacy.md`](privacy.md)

## 1. 저장 중립 계약

저장소는 owner 경계, 불변 버전, 게시 동의, 복사 출처, receipt·outcome, 감사 가능한 score ledger를 보장한다. 논리 엔티티는 `users`, `workspaces`, `workspace_members`, `devices`, `sessions`, `memories`, `memory_versions`, `memory_index`, `source_files`, `publications`, `reviews`, `takedowns`, `copies`, `consents`, `receipts`, `outcomes`, `score_ledger`다.

`memories`는 owner, kind, `scope_key`, current version, status를 갖는다. owner-scoped `scope_key=(owner_id, site_host, canonical_url_pattern, kind, provider, doc_type, locale, region, variant)`이며 한 owner·scope에 active lineage는 하나다. 서로 다른 owner는 나머지 scope 값이 같아도 독립 lineage를 가진다. 공개 카탈로그는 `owner_id`를 뺀 `catalog_scope`를 후보 검색에 쓰되 그 키로 고유성을 강제하거나 항목을 자동 병합·덮어쓰지 않는다. `memory_versions`는 1부터 증가하는 정수 `version`, schema version, 정화된 content JSON, SHA-256 fingerprint, 생성 시각을 가지며 update-in-place하지 않는다. 변경은 `base_version` 비교 후 새 버전과 head 이동을 한 transaction으로 commit한다.

`memory_index`는 해당 불변 버전에서 재생성 가능한 L0 투영이다: URL pattern, kind, form, keyword, title/summary 검색 필드. inactive 버전은 기본 recall/search에서 제외한다. `source_files`는 원본 bytes를 SHA-256 주소로 묶고 private 접근을 유지한다. 공개 데이터에는 원본, 능력 URL, `source_ref`, 사용자·device ID를 넣지 않는다.

가시성은 모든 목록·검색·expand SQL의 owner/workspace/publication predicate 안에서 적용한다. 결과를 가져온 뒤 숨기는 방식은 금지한다. foreign private row와 없는 row는 같은 `not_found`이며 전문 검색에서도 비공개 title·본문 존재를 노출하지 않는다. FTS는 visibility predicate와 함께 실행한다.

## 2. 공유·동의·결과 데이터

`publications`는 memory/version, `visibility`(`private|team|public`), `review_state`(`none|queued|approved|rejected`), license, consent reference를 기록한다. public 검색에는 승인된 현재 publication만 포함한다. 게시·`share-v1` consent·review 생성은 원자적이며, unpublish/takedown은 공개 조회에서 즉시 제외한다.

`reviews`는 version, 결정·고정 사유 코드, 시각을 연결한다. `takedowns`는 조치 사유와 삭제용 `content_fingerprint`를 기록해 일치 콘텐츠의 재게시를 막는다. `copies`는 새 private memory와 `derived_from(memory_id,version,author,license)`를 보존한다. `consents`는 목적·버전·시각·대상을 기록한다. `receipts`는 linked consumer, 선택 버전, 발급·만료 시각을 고정하고 `outcomes`는 owner의 단일 멱등 결과다. `score_ledger`는 receipt 유래의 append-only 지급·reversal만 저장한다. 익명·자기 사용은 점수를 만들지 않는다.

## 3. 저장 어댑터

| 어댑터 | 물리 계약 |
|---|---|
| SQLite — runtime-v1 우선 | 기존 `records(id,owner,kind,version,payload,updated_at)`를 head envelope로 유지한다. `kind`는 `template/source/document`; `payload`는 typed JSON이다. `revisions(document_id,owner,version,payload)`를 불변 이력으로 일반화하고, memory 버전/head를 같은 transaction으로 갱신한다. `source_files(source_id,original)`에 `sha256` unique 값을 추가한다. scope·publication·receipt 등은 정규화 테이블과 인덱스로 확장한다. |
| PostgreSQL — 다중 사용자 단계 | 위 논리 엔티티를 FK/unique 제약이 있는 관계형 테이블과 JSONB content로 저장한다. owner/workspace·membership·session/device를 분리하고, 활성 scope partial unique index, 버전 immutability, consent·receipt/outcome transaction을 강제한다. 객체 저장소 연결은 private SHA-256 key만 사용한다. |

SQLite는 한 로컬 owner의 loopback 라이브러리다. PostgreSQL 다중 사용자·workspace는 runtime-v1 이후 단계이며 아직 제공한다고 간주하지 않는다. 원본 bearer/device token, 원 URL·query, request body·페이지 내용은 DB·감사로그에 저장하지 않는다. token은 hash 또는 OS 보안 저장소 참조만 남긴다.

## 4. 색인·보관·삭제

SQLite는 FTS5, PostgreSQL은 `tsvector` + GIN을 사용해 title/summary/keywords를 검색한다. 검색 계획은 owner·visibility·active version을 먼저 제한한다. L0 튜플 unique 제약과 route/keyword 인덱스를 두고, FTS 결과도 같은 필터를 통과시킨다. 인덱스는 재생성 가능하며 source content와 독립한다.

보관은 [privacy 5절](privacy.md)을 따른다: preview 15분, 거절·취소 게시 검수 payload 7일, receipt 30일, 계정 사용량 집계 90일(제안). 요청 원문·IP·URL·질의 전문은 보관하지 않는다. 사용자 삭제는 모든 메모리 버전·색인·원본·캐시를 제거한다. 계정 삭제 시 private 데이터와 연결·세션을 삭제하고 공개 게시물은 사용자 선택에 따라 삭제 또는 작성자 정보 제거 후 유지한다. 타인이 적법하게 만든 복사본은 유지한다.

## 5. 무결성 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-DB-01 | 어댑터 schema와 FK | SQLite/PostgreSQL에 계약 엔티티·참조 무결성, 잘못된 owner 거부 | DB-01, DB-02 |
| F-DB-02 | 조회 격리 | private foreign row는 조회·FTS에서 0건이고 ID 응답은 not_found | DB-03 |
| F-DB-03 | active scope 유일성 | 같은 owner+scope 동시 쓰기에서 active 1개; 다른 key 공존 | DB-04 |
| F-DB-04 | 정수 불변 버전 | stale base_version rollback; 이전 JSON/fingerprint 보존 | DB-05 |
| F-DB-05 | L0/FTS projection | 재색인 멱등, inactive 제외, visibility predicate 유지 | DB-06 |
| F-DB-06 | 원본 파일 | 동일 SHA-256 공유, private bytes 보존·비공개 | DB-07 |
| F-DB-07 | publish·review·takedown | consent와 publication 원자성, fingerprint 차단 | DB-08 |
| F-DB-08 | 복사·provenance | 새 private id와 최초 author/license/version 유지 | DB-09 |
| F-DB-09 | receipt·outcome·ledger | owner·만료·멱등성, 익명/자기 사용 점수 0, reversal append | DB-10 |
| F-DB-10 | 삭제·보관 | 기한 전후 purge, 계정 선택, 복사본 유지 | DB-11 |
| F-DB-11 | 재시작·원자성 | SQLite reopen 및 PostgreSQL rollback/commit 결과 일치 | DB-12 |
