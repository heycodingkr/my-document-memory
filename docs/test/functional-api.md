# Functional API·DB 테스트 스펙

상태: 설계 인수 케이스(문서 우선, 실행 미구현). API 응답과 저장 상태를 함께 판정한다.
영역 / 테스트 ID 접두사: `API`, `DB` (상세 명세: [`../spec/api.md`](../spec/api.md), [`../spec/database.md`](../spec/database.md))
기반: [`../spec/core.md`](../spec/core.md), [`../spec/runtime-v1.md`](../spec/runtime-v1.md), [`../spec/privacy.md`](../spec/privacy.md), WAM `docs/test/functional-tests.md` API 및 `docs/test/database.md`의 격리 fixture·SQL oracle 방식을 적응

## 1. 공통 fixture와 판정

합성 계정 `user_a`, `user_b`, 토큰 `token_a`, `token_b`, 공개 `memory_pub@1`, A의 private `memory_private@1`, receipt `receipt_a`를 준비한다. 문서 입력은 `stddoc/1` JSON이며 URL·키·개인정보에는 합성 값만 쓴다. API는 loopback test server와 두 사용자 auth fixture, DB는 새 임시 SQLite 및 disposable PostgreSQL schema에서 실행한다. DB 합격은 응답만 보지 않고 row·제약·transaction 전후 상태를 조회한다. 동시성 순서는 barrier/lock 상태로 관찰한다.

## 2. HTTP API 케이스

| ID | 입력 / 시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| API-01 | `GET /healthz`; 이어 `GET /v1/status` 무토큰, `Bearer token_a` | healthz는 무데이터 200, 무토큰은 401 `auth_required`, 유효 토큰 status는 mode/auth만 반환하고 token은 없음 |
| API-02 | A가 private `mem_a` 저장; B가 `GET /v1/memories/mem_a/expand?level=1`와 `mem_missing` 조회 | 두 응답은 동일 404 `not_found`; B의 목록·검색·오류에 A의 메타데이터 0건 |
| API-03 | linked A가 `POST /v1/recall`에 canonical URL, `doc_type=resume`, `locale=ko-KR`, `limit=3`; anonymous로 반복 | 최대 3 L1 hint와 untrusted framing; linked에만 A 소유 receipt, 익명에는 receipt 없음 |
| API-04 | `GET /v1/search?query=resume&scope=public&limit=1` 후 cursor; 이어 201자 query | page는 공개 결과만 1개와 다음 cursor, 두 페이지 중복 없음; 초과 query는 400, 저장·검색 기록 변화 없음 |
| API-05 | `GET /v1/memories/memory_pub/expand?level=2&version=1`에 작은 cursor 사용, 없는 version 99 조회 | v1의 StandardDoc·license·source가 cursor로 이어짐; version 99는 404이며 head로 대체하지 않음 |
| API-06 | client가 fetch guard로 HTTPS fixture 문서를 추출해 `POST /v1/import`에 `StandardDoc`; 별도 `http://127.0.0.1/admin` preview/import | 정상 문서는 private source/template 저장; 사설 목적지는 클라이언트·서버 fetch 양쪽에서 `fetch_blocked: private_address`, outbound request·저장 0건 |
| API-07 | `POST /v1/library/memories`로 template 및 reference 저장 후 동일 scope/hash 재전송 | `template`·`source` 매핑과 정화 결과가 보존되고 재전송은 같은 id/version, `created:false` |
| API-08 | `POST /v1/documents`에 `{title,template_id,source_ids,outline_approved:true}`; v1 저장 후 `PUT`에 base 1 두 번 | document는 template/source의 불변 version을 고정; 첫 저장 v2, 두 번째 stale 저장은 409 `version_conflict`, v1·v2 모두 보존 |
| API-09 | A가 library 목록 cursor 조회·`DELETE /v1/library/memories/mem_a`에 confirm; B가 동일 delete | A의 목록만 반환되고 삭제 후 A 조회는 404; 미확인 삭제는 무효, B 응답은 없는 ID와 같은 404 |
| API-10 | `POST /v1/copies`에 공개 `CC-BY-4.0` v1 full 복사; `unknown`에 full 요청 | 첫 요청은 새 private id와 최초 author/license/version 귀속; 두 번째는 403 `license_forbids`, `allowed_modes=[structure_only]` |
| API-11 | `POST /v1/library/memories/{id}/publish`에 share consent 누락, 이어 `consent_version=share-v1`; `DELETE /v1/library/memories/{id}/publish` | 누락 요청은 403 `consent_required`와 DB 변화 0; 동의 요청은 publication/review 생성; unpublish는 동의 없이 공개 검색 즉시 제외 |
| API-12 | A의 receipt에 `{outcome:success,used:[{memory_id:"memory_pub",version:1}]}`; B가 같은 receipt, A가 동일/다른 결과 재전송 | B는 404, A 같은 결과는 멱등, 다른 결과는 409; 허용된 성공 outcome만 정책에 따라 ledger 반영 |
| API-13 | `GET /v1/vocab/doc_types`, `locales`, `providers`, `licenses`, `keywords` | 각 endpoint는 닫힌 어휘와 version을 반환하고 임의 vocab 이름은 404; 계정·사용 문서 내용 없음 |
| API-14 | `GET /v1/status`, `GET/PUT /v1/me/consent`에 `share_enabled=true` | mode·vocab·consent 상태가 맞고 저장; 계정 허용 스위치만으로 다음 publish 동의가 충족되지는 않음 |
| API-15 | `DELETE /v1/me/account`에 `confirmation=DELETE`, `manage:account`; 삭제 옵션 `public=remove` | 세션·device·private 데이터가 폐기되고 선택된 게시물이 사라짐; 이미 생성한 타인의 copy는 유지 |
| API-16 | 익명 `GET /v1/leaderboard`; A가 `GET /v1/me/usage`로 다른 계정 ID를 지정 | 공개 opt-in handle·합계만 반환; usage는 인증된 A의 quota만 반환하고 요청자가 고른 owner ID는 무시 |
| API-17 | `POST /v1/link/start` → 승인된 `/poll` → `GET /status` → `POST /revoke` | 최소 scope 기기 토큰이 발급되고 status는 현재 기기만 표시; revoke 후 같은 token은 401 |
| API-18 | 잘못된 form, 초과 payload, 차단 license 입력에 sentinel `SENTINEL_X7` 포함 | 고정 오류 JSON과 해당 status/reason/allowed_modes만 반환; response·log에 sentinel/body/URL query 0건 |
| API-19 | A 토큰에서 `read:library`로 GET 후 `write:library`, `write:share`, `report:outcome`, `read:dashboard`, `manage:account`별 쓰기 호출 | 허용 scope는 동작하고 누락 scope는 403 `scope_required`; private foreign row는 scope 오류로 존재를 드러내지 않음 |
| API-20 | 동일 canonical recall/search/save 요청을 HTTP, 대응 MCP tool, `dmem --json`으로 호출 | 정규화 입력·성공 JSON schema·결과 정렬이 동등하며 API 오류 코드는 CLI 종료 코드 표와 매핑됨 |

## 3. 저장소 DB 케이스

| ID | 입력 / SQL 시나리오 | 기대 결과와 DB oracle |
|---|---|---|
| DB-01 | 빈 SQLite 파일에 migration; `records(owner_a,template,1,payload)`, `revisions`, `source_files` 생성 | runtime-v1 기본 컬럼과 확장 논리 엔티티·index가 적용됨; 잘못된 kind/version은 거부되고 일부 row가 남지 않음 |
| DB-02 | `users(a)`, workspace/member/device/session 삽입 후 없는 user/workspace FK로 device·memory 삽입 | 유효 참조만 commit; 없는 owner/workspace는 FK 거부, token 원문은 어떤 row에도 없음 |
| DB-03 | owner A의 private payload/title, owner B가 같은 scope의 FTS·ID query | B 검색 row 0개, ID API는 missing row와 동일 404; query plan이 visibility predicate를 후보 SQL에 적용 |
| DB-04 | `owner_a`가 동일 scope `(owner_a,example.org,example.org/forms/:id,template,html,resume,ko-KR,KR,null)`를 두 transaction에서 동시 삽입; `owner_b`는 나머지 필드가 같은 scope 삽입; `owner_a`에는 `provider=markdown`, `region=US`, `variant=cv`를 각각 단독 변경한 scope도 추가 | `owner_a`의 완전 동일 scope는 한 active lineage만 commit되고 실패 transaction의 부분 row는 0; `owner_b`의 동일 나머지 tuple은 독립 lineage로 공존; provider·region·variant 각 변경은 별도 active scope다 |
| DB-05 | memory v1 content/fingerprint 저장; base_version 1로 v2 추가; stale base 1 재시도 및 v1 UPDATE 시도 | 성공 transaction은 v2 head만 이동; stale 쓰기·v1 변경은 거부, v1 JSON/hash 그대로 |
| DB-06 | v1 L0 pattern·keywords 삽입, 같은 버전 재색인, v2 supersede 후 query | index tuple은 unique·재색인 멱등; 기본 검색은 active projection만 반환, FTS에 private/inactive row 없음 |
| DB-07 | `source_files`에 동일 bytes 두 번 저장 후 조회 권한 확인 | 동일 SHA-256은 한 content object로 정규화; bytes checksum 일치, 공개 사용자 조회 0건 |
| DB-08 | `share-v1` consent와 publication/review를 함께 commit; 동의 누락 rollback; fingerprint takedown 후 재게시 | 승인 없는 public row 노출 0; 동의 누락 transaction 변화 0; fingerprint 재게시가 차단되고 review·audit 참조 유지 |
| DB-09 | 공개 CC-BY v1 복사해 owner B의 private memory 생성; 원본 수정·takedown 수행 | copy의 새 id와 최초 `derived_from` attribution/license/version 유지; 원본 불변, taken-down origin 재게시 불가 |
| DB-10 | 로그인 receipt owner A에 success outcome 두 번, B의 receipt 사용, self-use·anonymous 사용, reversal | owner 외 처리는 0변경; 같은 outcome ledger 1회; anonymous/self 0점; reversal은 원 event를 지우지 않는 별도 반대 delta |
| DB-11 | preview 만료, 거절 publication payload 7일 경과, receipt 30일 경과, usage 90일 경과, 계정 삭제 | 각각 기한 뒤 purge; 요청 URL·IP 원문은 애초 0건; account 연결 삭제 뒤 승인된 타인 copy는 유지 |
| DB-12 | SQLite commit 후 재오픈; 트랜잭션 중 오류 rollback; 같은 저장 계약을 disposable PostgreSQL에서 재생 | 재오픈 후 id/version/hash 유지; 실패 transaction 일부 row 0; 두 adapter의 visibility·active-scope·outcome oracle 일치 |
