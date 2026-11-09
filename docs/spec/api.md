# API: HTTP v1 인증·라이브러리·공유 계약

상태: 설계 초안(문서 우선, 구현 없음). WAM endpoint·receipt 멱등성 규칙을 문서 메모리 도메인에 적응했다. 외부 WAM 호스트·배포 사실은 승계하지 않는다.
영역 / 테스트 ID 접두사: `API` (케이스: [`../test/functional-api.md`](../test/functional-api.md))
기반: [`core.md`](core.md), [`runtime-v1.md`](runtime-v1.md), [`recall.md`](recall.md), [`library.md`](library.md), [`sharing.md`](sharing.md), [`web-import.md`](web-import.md), [`mcp.md`](mcp.md), [`cli.md`](cli.md), [`privacy.md`](privacy.md)

## 1. 범위와 runtime-v1 프로필

HTTP API의 경로 접두사는 `/v1`이다. 요청·응답은 schema-versioned JSON이며 닫힌 입력 스키마를 검증한다. 일반 서비스는 public read에 익명을 허용하고 private/write에는 Bearer를 요구한다. `GET /healthz`는 인증 없는 무데이터 준비 확인이다.

### runtime-v1 프로필

`127.0.0.1:3847` loopback 서버는 `DMEM_TOKEN`을 요구하며 모든 `/v1` 호출에서 `Authorization: Bearer <token>`을 검사한다. 토큰 하나는 로컬 소유자 하나에 대응한다. `/healthz`만 토큰 없이 쓸 수 있다. 타 소유자 비공개 리소스와 없는 ID·version은 같은 `not_found`다. 이 프로필의 저장 리소스 종류는 `template`, `source`, `document`이며, `source`는 메모리 `reference`에 해당한다. runtime-v1은 로컬 단일 소유자·SQLite 부분집합이고 아래 계정·팀·공개 서비스 기능은 runtime-v1 이후 단계다.

## 2. 인증과 공통 규칙

인증 티어는 `anonymous`(공개 읽기), `linked`(계정 라이브러리·공유), `local-owner-token`(loopback 소유자 라이브러리)다. 서버 토큰 scope는 `read:library`, `write:library`, `write:share`, `report:outcome`, `read:dashboard`, `manage:account`로 분리한다. 호출자의 소유자·workspace는 인증 세션에서만 얻고 body의 ID를 신뢰하지 않는다.

`recall`은 자동 경로라 canonical URL pattern, 양식 필드, 공개 키워드, kind·scope·limit만 받는다. 인증 결과에만 owner-bound receipt를 발급한다. 검색은 직접 탐색 경로이며 `query` ≤200자, 페이지당 최대 20개, opaque `cursor`로 이어 간다. `expand`는 `level=1|2`, 선택 `version`과 `cursor`를 받아 불변 버전을 반환한다. L2는 64 KiB 한도와 cursor 규칙을 따른다([core 8절](core.md)).

## 3. Endpoint 계약

| 메서드·경로 | 접근 | 입력·성공 응답 |
|---|---|---|
| `GET /healthz` | 익명 | 데이터 없는 준비 상태 |
| `POST /v1/recall` | public 익명; private `read:library` | recall 필터 → 최대 3개 L1 hint, untrusted framing, linked 결과에만 `receipt_id` |
| `GET /v1/search` | public 익명; mine/team `read:library` | `query,scope,kind,doc_type,locale,provider,license,limit,cursor` → 보이는 결과, `next_cursor` |
| `GET /v1/memories/{id}/expand` | 공개 또는 `read:library` | `level,version,cursor` → L1 또는 L2·출처·라이선스 |
| `POST /v1/library/memories` | `write:library` | `kind,title,form,content` 또는 `from_preview_id`, 패턴·키워드·`dry_run` → id/version/created/scrub |
| `PUT /v1/library/memories/{id}` | `write:library` | 저장 입력 + 필수 `base_version` → 새 정수 version; stale base는 `version_conflict` |
| `POST /v1/documents` | `write:library` | `CreateDocument{title,template_id,source_ids,outline_approved}` → 선택 버전을 고정한 document |
| `GET /v1/documents/{id}` | `read:library` | owner 문서와 참조 version만 |
| `PUT, DELETE /v1/documents/{id}` | `write:library` | `SaveDocument{base_version,title,content}`로 version 갱신; confirm 삭제 |
| `GET /v1/library/memories` | `read:library` | 소유자 필터와 cursor → 내 목록만 |
| `DELETE /v1/library/memories/{id}` | `write:library` | `confirm=true` → 버전·색인·원본 삭제 및 필요 시 비공개 전환 |
| `POST /v1/import` | `write:library` | `preview_id` 또는 `StandardDoc` + `as,title,form,copy_mode,license` → 비공개 저장 결과 |
| `POST /v1/copies` | `write:library` | `memory_id,version,title,copy_mode` → 새 비공개 id와 `derived_from` |
| `POST /v1/library/memories/{id}/publish` | `write:share` | `version,visibility,license,consent,consent_version` → visibility/review_state/reasons |
| `DELETE /v1/library/memories/{id}/publish` | `write:share` | 소유자 게시 취소 → 즉시 공개 검색 제외; 동의 불필요 |
| `POST /v1/receipts/{id}/outcome` | `report:outcome` | `outcome,used[{memory_id,version}]`(최대 3) → recorded/duplicate |
| `GET /v1/vocab/{doc_types\|locales\|providers\|licenses\|keywords}` | 익명 | 닫힌 어휘와 버전 |
| `GET /v1/status` | 익명 또는 Bearer | mode, endpoint, auth, consent, vocab/catalog version, provider, isolated |
| `GET /v1/me/consent` | linked, `write:share` | 현재 공유 동의 상태 |
| `PUT /v1/me/consent` | linked, `write:share` | `{share_enabled,consent_version}`; 게시 동의는 별도 매 요청 필요 |
| `DELETE /v1/me/account` | `manage:account` + CSRF | `confirmation=DELETE` → 계정 정책에 따른 연결·데이터 삭제 |
| `GET /v1/leaderboard` | 익명 | opt-in 공개 handle·집계만 반환 |
| `GET /v1/me/usage` | `read:dashboard` | 본인 quota·사용량만 반환 |
| `POST /v1/link/start`, `/poll` | device flow | 승인 뒤 최소 scope device token 반환 |
| `GET /v1/link/status`; `POST /v1/link/revoke` | 현재 device bearer | 현재 기기만 조회·해지; token은 응답하지 않음 |

HTTP web import에서 클라이언트는 [fetch guard](web-import.md) 2절을 적용해 추출한 `StandardDoc`을 `POST /v1/import`로 보낸다. 웹 앱의 서버측 fetch도 동일 guard를 사용한다. 서버는 URL 쿼리·원문 응답을 저장하거나 오류에 싣지 않는다.

## 4. 동의, 가시성, 오류

공개 게시마다 `consent=true`와 현재 `consent_version=share-v1`이 필요하다. 동의 누락·버전 불일치는 `consent_required`; publish에서 `visibility=private`은 unpublish다. 라이선스 복사 한도를 넘으면 `license_forbids`와 고정 enum `allowed_modes[]`를 반환한다. receipt는 소유자·만료를 확인하고 같은 결과 및 사용 버전 집합의 재전송만 멱등이다.

오류 JSON은 `{code,message,reason?,trace_id?,retry_after_seconds?,allowed_modes?}`다. `code`와 HTTP status는 [core 7절](core.md)의 고정 대응을 사용하고, 응답·로그에 입력·token·URL 쿼리·본문을 echo하지 않는다. 없는 리소스와 접근 불가 private row는 동일 404 `not_found`; 인증 실패 401, scope 부족 403, 충돌 409, 한도 초과 413/429다. 개인·비공개 쿼리와 계정 응답은 `Cache-Control: no-store`다.

## 5. 채널 동등성

recall/search/expand/save/import/copy/publish/delete/outcome의 필드와 JSON 출력은 [MCP](mcp.md) 도구 및 [CLI](cli.md) 대응 명령과 같은 계약을 쓴다. vocab·consent·account·leaderboard·usage·link는 HTTP endpoint이며 CLI가 이를 호출할 수 있다. MCP/CLI의 이름·입력 규칙을 임의로 변경하지 않는다.

## 6. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-API-01 | runtime 인증과 상태 | 모든 `/v1`에 token, healthz 무데이터, foreign private 은폐 | API-01, API-02 |
| F-API-02 | recall·search·expand | 한도, cursor, 불변 version, 가시성 적용 | API-03~05 |
| F-API-03 | 웹 가져오기 | 클라이언트·서버가 같은 fetch guard를 거치고 StandardDoc 저장 | API-06 |
| F-API-04 | 내 라이브러리 | 저장·버전 충돌·목록·삭제·멱등성 | API-07~09 |
| F-API-05 | 복사·게시·결과 | license 상한, share-v1 동의, owner receipt 멱등성 | API-10~12 |
| F-API-06 | 어휘·운영 endpoint | status/consent/account/leaderboard/usage/link 소유권 적용 | API-13~17 |
| F-API-07 | 오류·인증 경계 | 고정 오류 객체와 scope 행렬, 민감 입력 비노출 | API-18~19 |
| F-API-08 | 채널 동등성 | MCP/CLI와 입력·출력 스키마가 일치 | API-20 |
