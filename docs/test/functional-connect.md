# 연결 기능 테스트 케이스

상태: 케이스 정의(문서 우선). 구현·실행 결과는 [`environment.md`](environment.md)에 날짜와 함께 기록한다.
범위: `DEDUP`, `LINK`, `CACHE` (P1). ID 상한은 [`../spec/README.md`](../spec/README.md) 레지스트리다.

## 읽는 법

| 열 | 의미 |
|---|---|
| 단계 | `R1` = runtime-v1 이상, `F` = 전체 목표 계약, `L0` = 제품 내부 단위 테스트만(블랙박스는 `SKIP(L0)`) |
| 입력/시나리오 | 일회용 `DMEM_HOME`, 테스트 계정·시계, 격리 서버를 사용한다. 사용자·token·URL은 합성값만 쓴다 |
| 기대 결과와 판정 근거 | CLI/MCP/API에서 관찰하거나 검수 큐·격리 저장소에서 확인할 수 있는 결과 |

## DEDUP: 게시 중복 판정 ([`../spec/dedup.md`](../spec/dedup.md))

| ID | 단계 | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|---|
| DEDUP-01 | F | 같은 게시 후보를 `https://docs.google.com/document/u/1/d/ID/edit?x=1` 패턴 집합과 정규화한 `docs.google.com/document/d/:id/edit`로, 순서를 바꾸고 하나 중복해 제출 | 두 집합이 같은 `scope_key`로 정규화되고 두 번째 후보는 같은 비교 범위로 판정된다. 원 ID·query는 저장·응답·로그에 없다 |
| DEDUP-02 | F | 동일 `scope_key`에서 다른 작성자가 동일한 canonical 공유 payload와 `content_hash`를 두 번 publish | 두 번째는 `duplicate` 후보로 거절/기존 항목 연결, 공개 항목 수는 1개다. 자동 merge나 새 version은 없다 |
| DEDUP-03 | F | 같은 payload/hash로 host, `kind`, `doc_type`, `locale`를 각각 바꾸고, 같은 scope에서는 `provider`, `region`, `variant`만 바꾸어 publish | 첫 네 후보는 별도 scope로 비교된다. 같은 bucket의 provider·region·variant 변형도 자동 중복 거절되지 않고 구분 검수된다 |
| DEDUP-04 | L0 | 검수 비교기에 union 100개 shingle, 교집합 92개인 합성 쌍을 넣는다(유사도 0.92, 임계값 0.90 제안) | 유사도와 임계값을 기록하고 근접 중복 검수 후보가 된다. 자동 공개·병합은 없다 |
| DEDUP-05 | F | DEDUP-04 후보를 검수자가 유효한 지역/양식 변형으로 승인하고 새 버전으로 제출 | 승인 결정과 근거가 남고 이전 payload/version은 불변이다. 카탈로그 active pointer만 정책에 따라 이동한다 |
| DEDUP-06 | F | 합성 사용자 `alice`가 고정 시계 기준 한 시간 안에 서로 다른 게시를 10건 제출한 뒤 11번째 요청 | 1~10번째만 한도 내 처리되고 11번째는 `rate_limited`, 종료 코드 6 및 재시도 시간이다. 요청 본문은 에코되지 않는다 |
| DEDUP-07 | F | 공개 S2를 takedown 처리한 뒤 S2 복사본과 같은 `content_hash`의 새 publish를 시도 | 공개 검색에서 S2가 숨고 복사본은 `origin_taken_down` 경고, 새 publish는 `takedown_match`로 거부된다(SHR-15 판정과 일치) |
| DEDUP-08 | F | 소유자 A의 scope에 version 1을 저장하고, 같은 scope의 변경 내용을 ID 없이 `save`; 이어 `memory_id`와 현재 `base_version`, 오래된 `base_version`을 각각 지정한다. 본문·URL·token sentinel도 출력과 로그에서 검색 | ID 없는 같은-scope 수정은 새 불변 version을 만들고 version 1은 `superseded`; 현재 base 저장은 성공, 오래된 base는 `version_conflict`로 상태 변경 0건(library.md §3). 모든 sentinel은 sink에서 0건 |

## LINK: 기기 연결·해지 ([`../spec/link.md`](../spec/link.md))

| ID | 단계 | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|---|
| LINK-01 | F | `dmem link --json`으로 device flow 시작 | JSON에 짧은 `user_code`, 승인 페이지 URL, 만료 시각, polling 간격만 있다. token/device secret은 출력·stderr·로그에 없다 |
| LINK-02 | F | 승인 전 받은 device code로 한 번 poll한 뒤 웹 승인 페이지에서 확인 | 승인 전 상태는 `pending`; 승인 페이지는 표시된 `user_code`와 요청 scope를 보여 주고 계정 연결 전 명시 확인을 요구한다 |
| LINK-03 | F | 사용자 거부, 만료된 `user_code`, 잘못된 code로 각각 승인 시도 | 각각 거부/만료/invalid terminal 결과이며 token 발급과 device binding은 0건이다 |
| LINK-04 | F | 유효 승인 뒤 poll을 두 번 하고, 두 번째 실행에서 같은 승인 code를 재사용 | 첫 poll만 token을 반환하고 후속 poll/code 재사용은 거부된다. 두 응답 모두 token을 기록하지 않는다 |
| LINK-05 | F | 승인된 token을 CLI/MCP에서 사용해 status 확인, `dmem unlink` 후 secure store 및 로컬 파일 검사 | 저장은 OS secure store에만 있다. unlink는 현재 기기를 revoke하고 credential을 삭제하며 평문 token 파일은 0개다 |
| LINK-06 | F | token별로 `read:library`, `write:library`, `write:share`, `report:outcome`, `read:dashboard`, `manage:account` 허용/비허용 API를 호출 | 각 scope의 허용 작업만 성공하고 빠진 scope는 `scope_required`; body의 owner ID로 권한을 올릴 수 없다 |
| LINK-07 | F | 승인한 device를 웹 기기 설정에서 revoke하고 기존 token으로 다음 API 요청, 이어 새 anonymous recall 요청 | 기존 token은 즉시 인증 실패하고 linked 응답으로 동작하지 않는다. 별도 anonymous 요청은 공개 읽기만 하며 receipt가 없다 |
| LINK-08 | R1 | 로컬 `DMEM_TOKEN`만 설정, 이어 익명 서버 요청, 이어 linked account 요청. 모든 CLI/MCP 오류와 출력에서 token sentinel 검색 | local-owner-token은 단일 로컬 소유자만 접근한다. anonymous는 공개 읽기이며 receipt 0건, linked는 승인된 scope만 쓴다. token sentinel은 모든 sink에서 0건 |

## CACHE: 익명 공개 recall cache ([`../spec/client-cache.md`](../spec/client-cache.md))

| ID | 단계 | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|---|
| CACHE-01 | F | 익명 공개 recall에 서버의 cache opt-in을 주고 같은 요청을 0분, 4분, 6분 시점에 수행 | 성공 응답만 저장된다. 0·4분은 `fresh` hit 가능, 6분은 fresh가 아니며 서버 재조회가 발생한다 |
| CACHE-02 | F | 5분 지난 응답을 받은 뒤 네트워크 오류에서 14분과 16분 시점에 요청 | 14분은 결과를 `stale`로 표시해 반환할 수 있고 16분은 cache miss/네트워크 오류다. stale은 HTTP 성공 때 재사용하지 않는다 |
| CACHE-03 | F | 이미 cache가 있는 사용자로 linked token 요청을 반복하고 서버 호출 카운터·cache DB를 확인 | 매 요청이 서버에 도달한다. 인증 응답·receipt는 cache에 읽거나 쓰지 않는다 |
| CACHE-04 | F | 같은 익명 cache 결과를 두 번 읽고 응답 receipt/outcome/usage 저장소 확인 | hit은 `cache.state=fresh` 또는 허용된 stale 표식이며 새 receipt·outcome·사용량 기록은 0건이다 |
| CACHE-05 | L0 | MCP `cache.state` 직렬화에 `none`, `fresh`, `stale` 및 `offline`을 각각 넣는다 | 첫 세 값만 schema 통과하고 `offline`은 거부된다(`contracts/mcp-tools.v1.json`) |
| CACHE-06 | F | preview를 만들고 14:59 및 15:01에 같은 `preview_id`로 import; recall cache를 별도 조회 | 14:59에는 동일 preview payload가 저장되고 15:01에는 `not_found`; preview body는 recall cache에 0건이다 |
| CACHE-07 | F | local library 항목을 저장한 뒤 cache를 지우고 cache DB 손상 후 재시작 | `dmem cache clear`와 복구는 cache만 제거한다. local library의 id/version/content와 credentials는 동일하다 |
| CACHE-08 | F | `dmem cache status` 후 clear 실행. cache 파일과 진단에서 URL/query/token 센티널 검색 | status는 enabled·개수·크기·나이만 표시한다. clear 뒤 entry 0개, credentials/library 유지, 센티널 0건이다 |

