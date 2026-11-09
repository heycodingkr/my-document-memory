# CACHE: 클라이언트 익명 공개 recall 캐시

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM의 제한된 CLI/MCP cache 계약을 문서 메모리에 적용한다. 실제 recall v1은 별도 구현되어 있으며 이 파일의 영속 캐시·offline 동작은 후속 단계다.
영역 / 테스트 ID 접두사: `CACHE` (케이스: [`../test/functional-connect.md`](../test/functional-connect.md))
기반: [`recall.md`](recall.md), [`web-import.md`](web-import.md), [`mcp.md`](mcp.md), [`cli.md`](cli.md)

## 1. 범위

클라이언트는 서버가 명시적으로 cache 가능하다고 표시한 **익명 공개 recall 응답**만 저장한다. Cache는 온라인 결과 전송 비용을 줄이는 파생 데이터다. 사용자의 로컬 라이브러리는 primary store이며 cache 조회·만료·clear로 삭제하거나 대체하지 않는다.

미리보기는 별도 임시 산출물이다. `web-import.md` 5절에 따라 preview 내용은 15분 TTL로만 보관하고 기한 후 삭제한다. preview를 공개 recall cache로 저장하지 않는다.

## 2. 저장·호출 규칙

- 기본 freshness는 5분, 네트워크 오류 시 stale 사용 가능 기간은 생성 시각부터 최대 15분이다.
- 익명 공개 recall의 성공 응답만 저장하며, 서버의 명시적 cache opt-in이 없으면 저장하지 않는다.
- 인증된 모든 요청은 항상 서버에 도달한다. 인증 응답, 개인 라이브러리, receipt, 오류 응답은 캐시하지 않는다.
- 캐시 결과는 local hit임을 표시하고 server usage나 receipt를 생성하지 않는다. stale 결과로 receipt/outcome을 만들 수 없다.
- `401`, `403`, `429`, schema/origin 불일치, 명시적 무효화에서는 stale 데이터를 제공하지 않는다.
- key는 endpoint, schema/cache version, canonical request digest, anonymous scope를 포함한다. 원 URL, query, token, keyword 원문을 key·진단에 보관하지 않는다.
- 캐시는 크기와 entry 수를 제한하고 손상 시 캐시만 재생성한다. credential, 설정, 라이브러리 데이터는 건드리지 않는다.

## 3. 상태와 사용자 명령

MCP cache 응답의 `cache.state`는 `none | fresh | stale` 중 하나다([계약 스키마](../../contracts/mcp-tools.v1.json)). `none`은 cache 미사용/비활성, `fresh`는 5분 내 유효 항목, `stale`은 네트워크 오류 시 허용된 최대 15분의 오래된 항목이다. 상태에는 안전한 나이 정보만 덧붙이고 route·본문 조각은 노출하지 않는다.

CLI는 `dmem cache status`와 `dmem cache clear`를 제공한다. status는 사용 여부, 항목 수·크기·나이 범위만 보여 준다. clear는 클라이언트 cache만 비우며 token, 계정 연결, 로컬 라이브러리를 지우지 않는다.

## 4. 구현 경계와 오류

runtime-v1은 아직 원격 공개 recall/cache를 제공하지 않는다. 익명 공개 recall cache와 오프라인 stale fallback은 runtime-v1 이후 단계다. preview TTL은 web-import 미리보기 보관 정책으로 별도 적용한다.

로컬 파일 권한은 OS 사용자만 읽고 쓰게 제한한다. 캐시 key·payload·오류에서 인증 헤더, token, 능력 URL 원 ID, 개인 URL·검색어를 복원할 수 없어야 한다. 부적격 응답이나 cache 파싱 오류는 miss로 처리하고 서버 결과에 따라 진행한다.

## 5. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-CACHE-01 | 캐시 대상 제한 | 익명·공개·명시 opt-in recall만 저장된다 | CACHE-01 |
| F-CACHE-02 | fresh/stale TTL | 5분 내 fresh, network error 때만 15분까지 stale로 표시된다 | CACHE-02 |
| F-CACHE-03 | 인증 우회 | linked 요청은 cache read/write 없이 매번 server에 도달한다 | CACHE-03 |
| F-CACHE-04 | receipt 무생성 | cache hit/stale은 새 receipt·outcome·usage를 만들지 않는다 | CACHE-04 |
| F-CACHE-05 | cache state 계약 | 응답 값은 none, fresh, stale 중 하나다 | CACHE-05 |
| F-CACHE-06 | preview TTL 분리 | preview는 15분 후 만료되고 recall cache에 들어가지 않는다 | CACHE-06 |
| F-CACHE-07 | primary store 보호 | cache clear/손상이 로컬 library·credential에 영향을 주지 않는다 | CACHE-07 |
| F-CACHE-08 | 사용자 제어·개인정보 | status는 안전한 집계만, clear는 cache만 제거하고 민감 값은 미보관한다 | CACHE-08 |
