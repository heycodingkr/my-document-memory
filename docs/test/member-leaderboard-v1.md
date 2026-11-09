# 회원·리더보드 입력과 기대 결과

상태: 실제 Router/SQLite·전용 브라우저·기존 회귀·운영 검증 완료. [검증 기록](member-leaderboard-v1-results.md). 제품 계약 [member-leaderboard-v1](../spec/member-leaderboard-v1.md). 실제 Router+임시 SQLite와 example.test 이메일 capture를 사용한다. 모든 검증은 부모가 수행한다.

| ID | 입력 | 기대 결과와 oracle |
|---|---|---|
| LB-01 | 익명 header Sign in / Create account / Leaderboard | 각각 명시적 진입, 기존 Public memories/로컬 연결 보존 |
| LB-02 | 처음 이메일 가입 링크 검증, 같은 이메일 재검증 | 인증 전 계정 없음, 이후 owner1개, 기존 개인 문서 유지 |
| LB-03 | 기존 계정 GET profile | handle=null/public=false/0점/rank=null, DB 쓰기 없음 |
| LB-04 | handle=' Alice-One ' 저장 | alice-one 정규화, 새로 열어도 유지 |
| LB-05 | 2자/25자/이메일/슬래시/Unicode/하이픈 시작·끝 | 400, 공개 false 상태 보존 |
| LB-06 | 예약명, Alice와 Bob이 같은 handle을 대소문자 다르게 저장 | 409 handle_unavailable, 기존 프로필 유지, 동시 저장도 한 명만 성공 |
| LB-07 | handle=null+public=false / null+true | 전자 저장, 후자400 |
| LB-08 | 무인증/일반 local Bearer profile, session PUT CSRF 없음/외부 Origin | 401, account/프로필 변경 없음 |
| LB-09 | PUT에 owner/account_id/points 포함 | 400, 타 계정/점수 변경 없음 |
| LB-10 | 가입/개인 파일/조회/복사/pending/rejected | 0점, 공개 순위 없음 |
| LB-11 | Alice 기여2개 승인, Bob1개 승인 | Alice40점/2건, Bob20점/1건. 승인 재시도409 후 점수 불변 |
| LB-12 | 승인 기여 철회, pending 철회 | 승인분20점 차감, pending은 변화0, leaderboard/public profile 즉시 반영 |
| LB-13 | SQLite 재열기와 추가 승인 | profile/점수 유지, 이전 승인 중복 산정 없음 |
| LB-14 | Alice/Bob20점, Carol40점 | 40점 rank1, 20점2명 rank2, 다음0점 미순위 |
| LB-15 | 비공개 고득점 Alice와 공개 Bob | Bob 공개 rank1, 본인 overall rank는 Alice 다음. 공개 JSON에 email/account_id/private ID 없음, Alice profile404 |
| LB-16 | 공개 계정21명 동일 점수, offset0/20 | 각각20/1개, total21, 공유 rank1 유지, handle순서/next_offset 정확 |
| LB-17 | offset=-1/문자/10001, 미존재/옵트아웃 profile | offset400, profile404, 존재 구분 없음 |
| LB-18 | 웹 가입 링크→Continue→My page→handle/공개 저장→승인→leaderboard | 실제 API/DB 반영, 본인 점수/순위와 공개 행 일치 |
| LB-19 | direct #leaderboard / #profile/handle 진입, opt out/reload, API실패 후 retry | 로그인 없이 공개 조회, 비공개 전환 즉시 숨김, 오류/빈 상태/복구 표시 |
| LB-20 | desktop와390/320px, 키보드 폼/표·기존 editor·auth smoke | 가로 넘침 없음, 실제 읽을 수 있는 표/동점/페이지, 기존 로그인·문서·슬라이드 흐름 통과 |

브라우저 회귀 기대값: 기본 문서 언어는 en이고 본문은 영어다. 한국어 전환 버튼의 자국어 이름은 허용한다. Slides 예시 링크는 현재 표시 이름 Open presentation deck example과 `/examples/document-examples.svg#deck`을 사용한다. #documents의 저장 문서 v3를 연 뒤 새로고침하면 #documents의 My documents 목록을 유지하며 같은 v3를 다시 열 수 있어야 한다.

기존 runtime-v1 회귀 기대값: 빈 DB의 legacy18개 + `starter-memories.v1.json`의 추가 entries를 함께 제공한다. 전체·en-US 검색은 각각 해당 수와20개 페이지 한도의 작은 값이며, en-US 응답의 모든 항목이 en-US여야 한다. 예전 고정18/9개 검증은 확장된 catalog의 성공 응답을 실패로 판단하므로 이 입력 계약으로 갱신한다.

Source-level scoring tests must create real account/contribution rows, use actual approval and withdrawal APIs, and inspect independent DB/public JSON outcomes. Public serialization assertions scan known private sentinel email, owner IDs and private record IDs. No real account is used as a test fixture and no fabricated leaderboard entry is shipped.
