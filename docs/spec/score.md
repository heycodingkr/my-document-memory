# SCORE: 영수증, 사용 결과와 작성자 점수

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM의 기여 승인 점수와 작업 분야 점수를 제거하고 공개 문서 메모리의 성공 사용만 반영한다. receipt와 score ledger는 runtime-v1 이후 단계다.

현재 구현과 구분: [`member-leaderboard-v1.md`](member-leaderboard-v1.md)의 회원 리더보드는 승인되어 공개 중인 기여당 20점을 계산한다. 이 파일은 receipt에 기반한 성공 사용 점수의 별도 목표 계약이며 현재 리더보드 구현을 설명하지 않는다.
영역 / 테스트 ID 접두사: `SCORE` (케이스: [`../test/functional-review.md`](../test/functional-review.md))
기반: [`sharing.md`](sharing.md) 7절, [`privacy.md`](privacy.md) 6절, [`mcp.md`](mcp.md) outcome 계약

현재 구현된 [member-leaderboard-v1](member-leaderboard-v1.md)의 **기여 점수(contribution points)**는 승인·공개 중인 양식당20점이며, 이 문서의 **성공 사용/impact 점수**와 구분한다. 이 문서의 receipt/outcome과 impact ledger는 여전히 후속 설계이며 현재 공개 리더보드에 합산하지 않는다.

## 1. 원칙

점수는 다른 연결 계정이 공개 메모리 버전을 실제로 사용해 성공했다고 보고한 경우에만 작성자에게 생긴다. 게시 승인, 단순 recall, 익명 사용, 본인 사용, 캐시 조회는 점수를 만들지 않는다. 점수량은 버전이 지정된 서버 정책으로 정하고 client가 지정할 수 없다.

## 2. Receipt 발급

연결된 계정의 실제 서버 recall은 최대 3개의 scoreable한 `public` 버전에 묶인 `receipt_id`를 받을 수 있다. 영수증은 서버가 인증 계정, 만료 시각, 공개된 `(memory_id, version)` 집합과 각 버전의 작성자 귀속을 고정한다. 연결되지 않은 익명 요청과 캐시 결과에는 receipt가 없다. 보관 기간은 [`privacy.md`](privacy.md) 5절에 따라 30일이다.

`team`·`private` 메모리는 성공 사용 점수 대상이 아니다. 클라이언트가 작성자·소비자 ID나 점수 값을 보낸 경우 신뢰하지 않는다. 인증 identity와 귀속은 서버가 정한다.

## 3. Outcome 계약

`doc_memory_outcome`은 receipt 소유자의 연결된 계정만 보고한다. 요청은 `receipt_id`, `outcome`(`success`, `partial`, `failed`), 선택 필드 `used: [{memory_id, version}]`(최대 3개)를 받는다. 각 쌍은 receipt에 포함된 공개 버전이어야 하며 중복은 허용하지 않는다.

성공 사용은 `outcome=success`이고 해당 버전이 `used`에 포함된 경우다. 생략·빈 목록, `partial`, `failed`는 점수 0이다. receipt 밖의 버전, 만료 receipt, 다른 계정 receipt는 거부하고 점수 원장을 바꾸지 않는다.

## 4. 멱등성·회수

Outcome의 비교 키는 receipt 내 `(memory_id, version)` 집합을 정렬한 값이다. 동일 결과와 동일 집합을 순서만 바꿔 재보고하면 `duplicate=true`로 멱등 응답하고 추가 event는 없다. 이미 소비된 receipt에 결과나 집합이 달라진 보고는 `version_conflict`이며 원장 변화가 없다.

성공 사용은 서버 원장에 작성자와 공개 memory version에 귀속된 event로 추가한다. unpublish 또는 takedown은 기존 지급을 삭제·수정하지 않고 해당 버전 지급을 상쇄하는 reversal event를 한 번 추가한다. 재처리해도 reversal은 중복되지 않는다.

## 5. 리더보드와 개인정보

공개 leaderboard는 사용자가 opt-in한 경우에만 선택한 `author_handle`과 집계 점수를 공개한다. opt-out은 공개 결과에서 즉시 제외한다. 이메일, account/device ID, receipt ID, 개별 소비자 정체, 공개되지 않은 메모리별 활동은 응답에 넣지 않는다([`privacy.md`](privacy.md) 6절).

## 6. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-SCORE-01 | 공개 사용 영수증 | linked 서버 recall만 계정·공개 버전 묶음 receipt를 받고 익명·캐시는 받지 않음 | SCORE-01, SCORE-03, SCORE-06 |
| F-SCORE-02 | 성공 사용 귀속 | 다른 연결 계정의 실제 공개 버전 success만 작성자 event를 만듦 | SCORE-02, SCORE-04~05 |
| F-SCORE-03 | Outcome 검증 | receipt 소유·만료·공개 버전·used 최대 3개를 검증 | SCORE-07 |
| F-SCORE-04 | 재전송 멱등성 | 결과와 version 집합 동일 재전송은 중복; 변경은 version_conflict | SCORE-08 |
| F-SCORE-05 | unpublish/takedown 회수 | 원 event를 보존하고 버전별 reversal을 정확히 한 번 추가 | SCORE-09 |
| F-SCORE-06 | opt-in leaderboard | opt-in handle과 집계만 공개하고 opt-out 및 식별자를 숨김 | SCORE-10 |

receipt/outcome 원문과 소비자 신원은 공개하지 않는다. 이 명세는 점수 정책의 숫자나 운영상 어뷰즈 탐지 임계치를 정하지 않는다.
