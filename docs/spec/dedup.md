# DEDUP: 게시 중복 판정과 재게시 차단

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. 게시 카탈로그 중복 검수는 runtime-v1 이후 단계이며, WAM의 중복 판정·takedown 지문 흐름을 문서 메모리 게시에 맞춘다.
영역 / 테스트 ID 접두사: `DEDUP` (케이스: [`../test/functional-connect.md`](../test/functional-connect.md))
기반: [`core.md`](core.md), [`library.md`](library.md), [`sharing.md`](sharing.md)

## 1. 목적

중복 검수는 같은 문서 메모리의 반복 게시, 실질적으로 같은 내용의 별도 게시, takedown 된 내용을 재게시하는 일을 막는다. 같은 범위의 서로 다른 유효한 양식은 공존할 수 있으며, 중복 키만으로 자동 병합하거나 덮어쓰지 않는다.

## 2. 게시 비교 범위와 정확 중복

게시 후보의 `scope_key = (site_host, canonical_url_patterns, kind, doc_type, locale)`다. `canonical_url_patterns`는 core.md 규칙으로 정규화해 정렬·중복 제거한 패턴 집합이다. 이는 공개 카탈로그의 비교 버킷이지 고유 키나 자동 병합 조건이 아니다. core.md의 `provider`, `region`, `variant`가 다른 후보는 같은 버킷이어도 자동 중복 거절하지 않고 구분 검수한다. 개인 라이브러리의 owner-scoped scope와 버전 계보는 core.md 6절 및 library.md 3절을 따른다.

각 게시 버전의 정규화된 공유 payload에서 `content_hash = SHA-256(canonical_payload)`를 계산한다. 동일 `scope_key`와 `content_hash`가 이미 있으면 정확 중복 후보로 판정하고 새 게시 대신 기존 항목을 검토자에게 연결한다. 해시 입력에는 원본 URL, 토큰, 소유자 식별자를 포함하지 않는다.

정확 중복 후보 판정은 콘텐츠의 자동 upsert 권한을 주지 않는다. 소유자 라이브러리의 변경은 명시적 `memory_id`와 `base_version`을 사용해 library.md의 upsert/version 규칙을 따른다.

## 3. 근접 중복과 검수

정확 해시가 다르더라도 같은 게시 범위에서 문서 구조가 거의 같으면 근접 중복 후보를 검수 큐에 표시한다. 비교는 비개인 슬롯과 문서 구조를 정규화한 뒤 shingle 유사도 또는 정규화 구조 유사도로 수행한다.

근접 중복 제안 임계값은 유사도 `≥ 0.90`(제안)이다. 점수는 자동 거절 근거가 아니라 검수 우선순위와 비교 설명에만 쓴다. 검수자는 기존 항목의 개선·변형·독립 양식 여부를 판정하며, 지역·언어·provider 차이는 적절한 키 필드로 구분한다.

## 4. 게시 남용 및 takedown 지문

사용자별 게시 요청은 시간당 10건을 초기 제한으로 둔다(제안; SHR-19 시험과 운영 측정으로 조정). 한도 초과는 공통 `rate_limited` 오류와 `retry_after_seconds`로 응답하며 요청 원문이나 본문을 에코하지 않는다.

운영자 takedown 시 공개 조회에서 즉시 숨기고, 정규화된 공유 콘텐츠에서 재게시 차단용 `takedown_fingerprint`를 만든다. 같은 지문으로 제출된 후보는 재검수/게시를 차단하고 기존 takedown 상태를 검토자에게 보인다. 지문은 원문이나 개인 정보 복원이 불가능한 서버 내부 값이며 공개·클라이언트 응답에 노출하지 않는다.

## 5. 저장·버전 상호작용

정확 중복, 근접 중복, takedown 판정은 게시 검수 상태에만 영향을 준다. 내 라이브러리의 생성·수정은 [`library.md`](library.md) 3절의 소유자 범위 upsert, 멱등 키, `base_version` 충돌 규칙을 따른다. 같은 범위의 수정은 기존 버전을 바꾸지 않고 새 불변 버전을 만든다.

runtime-v1에는 공개 사용자 게시와 검수 큐가 없으므로 이 절의 카탈로그 검수·게시 차단은 후속 단계 계약이다.

## 6. 개인정보·보안

URL 능력 ID, query, 개인 슬롯, 계정·기기 식별자를 해시 입력이나 검수 로그에 넣지 않는다. 해시 충돌이 의심되거나 정규화가 실패하면 자동으로 중복 확정하지 않고 검수 보류한다. 오류는 고정 코드만 반환한다.

## 7. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-DEDUP-01 | 게시 범위 정규화 | 같은 canonical URL 패턴 집합의 순서·중복 차이가 동일 scope가 된다 | DEDUP-01 |
| F-DEDUP-02 | 정확 중복 감지 | 동일 scope와 content_hash의 재게시가 중복 후보로 연결된다 | DEDUP-02 |
| F-DEDUP-03 | 범위 분리 | kind, doc_type, locale 또는 host가 다르면 자동 중복 처리하지 않는다 | DEDUP-03 |
| F-DEDUP-04 | 근접 중복 후보 | 제안 임계값 이상은 검수 큐 후보로 표시되고 자동 병합하지 않는다 | DEDUP-04, DEDUP-05 |
| F-DEDUP-05 | 게시 한도 | 사용자별 시간당 10건 초과는 rate_limited이며 재시도 시각을 제공한다 | DEDUP-06 |
| F-DEDUP-06 | takedown 재게시 차단 | takedown fingerprint와 일치하는 후보는 게시되지 않는다 | DEDUP-07 |
| F-DEDUP-07 | upsert·버전 보존과 비밀 비노출 | 같은 소유자 변경은 library.md 3절의 upsert/version 충돌을 따르고 오류·로그·공개 결과에 원문 URL, 본문, token이 없다 | DEDUP-08 |
