# 회원 진입·프로필·기여 리더보드 v1

상태: 구현·로컬 회귀·운영 HTTPS/Arise 검증 완료 (2026-11-09). [설계 검토](../design/member-leaderboard-v1-review.md), [검증 기록](../test/member-leaderboard-v1-results.md). 기존 [계정/기여 계약](accounts-community-v1.md), [이메일 링크](landing-email-links-v1.md), [운영 안내](accounts-operations-v1.md)를 확장한다. WAM의 공개 프로필 선택과 내 순위/공개 순위 분리를 참고한다. 입력/기대 결과: [테스트 명세](../test/member-leaderboard-v1.md).

## 의존 순서와 원자 목표

| 순서·경로·담당 | 산출물 | 부모 독립 확인 | 선행 |
|---|---|---|---|
| 0 WAM 참고 읽기 / codex:gpt-6-luna | 로그인·가입·프로필·점수·리더보드 file:line 최대8개와 짧은 근거 | 적용할 위치를 직접 열어 확인 | 없음 |
| 1 docs/spec + docs/test / 부모 | 이 계약과 합성 입력/기대 결과 | 현재 git diff·코드·기존 테스트와 대조 | 없음 |
| 2 server 회원 저장·점수 조회 / 부모 | 새 profile migration, 검증/점수/공개 순위/내 순위/공개 프로필 | 임시 실제 SQLite·실제 Router 테스트, 승인/철회 트랜잭션 결과 검사 | 1 |
| 3 server HTTP / 부모 | 인증·CSRF를 재사용하는 profile 및 공개 조회 경로 | 실제 Router로 401/404/409, 이메일/ID 미노출·페이지/동점 검사 | 2 |
| 4 web 진입/회원 / 부모 | Sign in / Create account, 선택 공개 프로필, My points / rank | 이메일 fixture와 실제 브라우저 가입/로그인/프로필 저장·오류·만료 | 3 |
| 5 web 공개 순위/프로필 / 부모 | 실데이터 leaderboard·pagination·공개 profile·empty/error states | 실제 승인 데이터·옵트아웃·좁은 화면·직접 hash 진입 | 3,4 |
| 6 통합/운영 / 부모 | 기존 기능 보존, 문서·리뷰·배포 | workspace tests/check/build, 전용 + 기존 E2E, 실제 HTTPS, DB backup·비밀 스캔 | 4,5 |

설계·코드 수정·빌드·테스트·브라우저 루프·통합·리뷰는 부모가 수행한다. WAM 다중 파일 참고 수집만 읽기 전용으로 위임하며 요약은 증거가 아니다. 다른 세션의 변경을 보존한다. 특히 현재 진행 중인 contribution review는 변경하지 않고 승인된 기여 상태를 조회해 점수를 계산한다.

## 로그인과 가입

- 공개 헤더에 Sign in / Create account / Leaderboard를 제공한다. 기존 My page·Public memories와 로컬 CLI/MCP 진입을 보존한다.
- 가입은 기존 Resend 이메일 링크를 검증한 뒤 처음 계정을 만드는 동일한 인증 경로다. UI의 가입 안내와 로그인 안내를 구분하되 계정 존재 여부를 이메일 전송 응답에서 노출하지 않는다. 비밀번호나 가짜 소셜 로그인 버튼은 추가하지 않는다.
- 최초 메일 검증 시에만 accounts가 생성된다. 기존 이메일로 가입 경로를 다시 거쳐도 같은 owner와 개인 자료를 유지한다. URL proof 제거·명시적 Continue·1회성·Origin/CSRF·로그아웃 규칙은 기존 계약 그대로다.

## 공개 프로필과 개인정보

- 새 account_profiles(account_id, handle, public_profile, updated_at) 저장소를 추가한다. 이전 계정은 프로필 없음/비공개 기본값으로 읽는다. GET은 쓰기를 만들지 않는다.
- GET /v1/me/profile, PUT /v1/me/profile {handle, public_profile}. 이메일 계정만 사용한다. session 쓰기는 기존 CSRF/허용 Origin을 요구한다. 요청의 owner/account_id 등 알 수 없는 필드는 거절한다.
- handle은 trim+ASCII lowercase, 3~24자, 영문 소문자·숫자·하이픈만, 시작·끝은 영문/숫자. 예약 handle(admin/api/auth/help/support/me/leaderboard 등)은 거절한다. 비공개로 유지할 때 handle=null은 허용한다. public_profile=true에는 유효한 handle이 필요하다.
- handle은 전체 계정에서 대소문자 무관 유일하다. 잘못된 값은 400 invalid_input, 이미 사용/예약된 값은 409 handle_unavailable. 저장은 원자적이며 충돌 시 이전 프로필이 유지된다.
- 공개 선택은 기본 false다. 이메일이나 이메일 앞부분을 handle로 자동 생성하지 않는다. 공개 조회는 handle·포인트·순위·승인 기여 수·이미 공개된 양식만 제공하며 이메일/account ID/자료·작성 문서·private ID를 포함하지 않는다. 옵트아웃하면 다음 조회부터 leaderboard와 public profile에서 사라진다. private owner의 전체 순위는 본인에게만 제공한다.

## 점수와 순위

- v1 점수 = 현재 승인·공개 상태인 자기 기여 수 × 20. contributions.status='approved'와 해당 public catalog record가 함께 존재하고, owner가 verified accounts에 있을 때만 계산한다.
- pending/rejected/withdrawn, 개인 자료 업로드, 가입, 단순 조회, 양식 복사에는 점수가 없다. 승인 재시도/동일 트랜잭션 중복은 기존 상태 규칙으로 거절되며 점수가 중복 증가하지 않는다. 철회 시 현재 점수에서 해당20점이 빠진다. 점수는 조회 시 실제 승인 상태에서 산출하므로 별도의 누적 counter drift와 backfill 중복을 만들지 않는다.
- 전체 순위(본인 전용)는 점수>0인 모든 계정 기준이다. 공개 순위는 공개 프로필을 선택한 점수>0 계정만 별도로 계산한다. 동점은 같은 순위이며 1,1,3 경쟁 순위를 쓴다. 동점 출력 순서는 handle 오름차순으로 결정한다. 0점 계정은 rank=null이다.
- GET /v1/leaderboard?offset=0: 익명 허용, 최대20명, total/next_offset/points_per_approval=20. offset은 0~10000 정수. 순위는 전체 공개 집합에서 먼저 계산한 뒤 페이지를 나눈다. 가짜 사람이나 임의 점수로 빈 순위를 채우지 않는다.
- GET /v1/profiles/{handle}: 공개 프로필만, 비공개/미존재는 같은404. 이미 공개된 그 계정의 양식을 최대20개 제공한다. 공개 0점 프로필은 존재할 수 있지만 leaderboard에는 올리지 않는다.
- 사용자별 profile 응답에는 total_points/approved_contributions/overall_rank/public_rank를 함께 제공해 마이페이지에서 확인한다. handle/공개 선택은 포인트나 승인 상태를 바꾸지 않는다.

## 요구사항 추적

| 요구사항 | 테스트 |
|---|---|
| 별도 로그인·가입 진입, 같은 영속 owner, proof/명시 확인 보존 | LB-01,02,18 |
| private-by-default profile·검증·유일성·원자 충돌 | LB-03~07 |
| 계정/CSRF/Origin 경계와 공개 privacy | LB-08,09,15 |
| 승인만 점수·철회·다른 owner·재시작 | LB-10~13 |
| 전체/공개 순위·동점·페이지 | LB-14~17 |
| 실제 웹 저장/가입/공개 순위/직접 진입/모바일/실패 복구 | LB-18~20 |

WAM의 승인 기여20점과 일치시키되, 기존 score.md의 receipt/outcome 성공 사용 점수는 별도의 후속 impact 점수다. 이 v1의 contribution points에 아직 구현되지 않은 사용 보상을 합산하지 않는다.

WAM의 모든 보상 이벤트·점수 이력·부정행위 판정·기간별 랭킹을 그대로 포팅했다고 표시하지 않는다. v1은 위에 명시한 현재 승인 기여 점수와 전체 기간 순위다.
