# 회원·프로필·리더보드 v1 설계와 검토

2026-11-09. 계약: [member-leaderboard-v1](../spec/member-leaderboard-v1.md), [입력/기대 결과](../test/member-leaderboard-v1.md).

## 문제와 근거

이메일 계정·마이페이지·기여 검수는 있었지만 로그인/가입의 별도 안내, 공개 닉네임/선택 공개, 회원 점수/순위, 공개 리더보드 경로는 없었다. 빈 leaderboard를 요구하는 첫 실제 Router 테스트는 구현 전404로 실패했다. 이를 200+빈 items로 고치는 것에서 시작했다.

WAM 원본을 직접 열어 확인한 참고 위치:

- `../web-agentic-memory/web/src/routes/+layout.svelte:26`: 공개 leaderboard/My page 진입과 privacy 안내.
- `../web-agentic-memory/web/src/routes/leaderboard/+page.svelte:1`: 실 API 목록, 가입 안내, 승인 기여20점, 공개 선택, 동점/전체·공개 순위 분리.
- `../web-agentic-memory/crates/wam-server/src/application/profiles.rs:1`: 선택 공개 프로필404, 본인 profile/dashboard 분리.
- `../web-agentic-memory/crates/wam-server/src/http/read_routes.rs:119`: 공개 leaderboard/profile 조회 경계.

별도 비밀번호 저장이나 WAM의 미구현 보상 이벤트를 복사하지 않았다. 기존 Resend 링크 확인/영속 owner/세션/CSRF를 사용하고, 이 제품에서 확인 가능한 승인 기여20점만 제공한다. `score.md`의 receipt/outcome 성공 사용 보상은 별도 후속 impact 계약으로 구분했다.

## 저장·점수·공개 경계

`0004_member_profiles.sql`은 기존 accounts를 외래 키로 참조하는 profile 테이블을 추가한다. 기존 계정에는 쓰기 없이 handle=null/public=false를 반환한다. handle을 이메일에서 자동 생성하지 않으며, public=true와 handle 미설정은 DB 제약과 입력 검증이 함께 막는다. NOCASE unique 제약과 upsert 트랜잭션으로 동시 닉네임 선점은 한 명만 성공한다. 충돌은 고정409 메시지이며 타 소유자를 반환하지 않는다.

`members.rs`는 승인된 contributions와 실제 public catalog template가 함께 있는 행만 세고20을 곱한다. 임의 점수 필드를 저장하지 않는다. 승인 재시도는 기존 상태 규칙으로 거절되며 철회 시 다음 조회부터 점수/공개 양식 목록이 줄어든다. 공개 여부와 닉네임 변경은 기여의 승인 상태를 수정하지 않는다. 다른 세션의 contribution review pipeline과 검수 결과를 보존한다.

본인 overall rank는 모든 양수 점수 계정 기준으로 본인에게만 제공한다. public rank는 공개를 선택한 양수 계정만으로 별도 SQL RANK를 계산한다. 1,1,3 동점 규칙을 적용한 뒤20개 페이지를 나누고 handle순으로 안정 정렬한다. 공개 profile은 opt-in인 경우만 조회되며, 승인된 public template payload만 최대20개 읽는다. 공개 JSON에서 이메일, 계정 ID, private template/reference/document ID가 나가지 않는지 sentinel을 검사한다. GET은 no-store이며 공개 선택 해제 뒤 profile은404가 된다.

## UI와 검토

Sign in/Create account는 구분된 안내를 보이며 같은 이메일 링크 API를 사용한다. 인증 전에는 가입 완료나 계정 존재를 노출하지 않는다. My page는 개인 전체 순위/공개 순위/현재 기여 점수와 선택 공개 폼을 제공한다. Leaderboard와 public profile은 익명 직접 hash 진입을 지원하고, 실제 데이터만 표시한다. 빈 목록·오류·재시도와0점 프로필을 처리한다. 비동기 결과에는 generation/cleanup을 두어 화면 전환 뒤 오래된 결과를 적용하지 않는다.

실제 승인 데이터를 사용한 desktop/390/320px 브라우저 테스트와 이미지 검토로 표·프로필 폼의 가로 넘침과 공개 항목을 확인했다. 현재 승인 상태를 설명하도록 문구를 조정했다. 기간별 점수, 사용 보상, 점수 이력 ledger는 범위 밖이며 UI에서 제공한다고 주장하지 않는다.

전체 회귀 중 기존 runtime smoke가 새 starter catalog에도 총18/영문9개를 기대해 실패했다. 검색은20개 한도이므로 실제 starter JSON 입력과 legacy18/9개를 기준으로 기대값을 고쳤다. 기존 양식 복사/생성/내보내기/재시작 검증은 유지한다.

검증 수치와 운영 release는 [검증 기록](../test/member-leaderboard-v1-results.md)에 기록한다.
