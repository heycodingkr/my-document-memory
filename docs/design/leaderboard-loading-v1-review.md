# 리더보드 로딩 원인과 검토

2026-11-09, #408. [계약](../spec/leaderboard-loading-v1.md),
[입력/결과](../test/leaderboard-loading-v1.md).

## 근거와 설계

`App.svelte`는 최초 session 조회가 끝날 때까지 initialized=false이며 hash 경로도
조회 뒤에 해석한다. 직접 진입은 landing, 조회 중 화면 전환은 Opening your space에
머물 수 있다. `Leaderboard.svelte`는 조회 완료 전 busy=true를 유지한다. 공통
`Api.request()`에는 fetch/JSON 읽기 시간 제한이 없다. 서버가 실패 응답을 주면
기존 catch/finally로 복구되지만 요청 자체가 끝나지 않으면 실행되지 않는다.
기존 테스트는 503만 반환하므로 이 경우를 검증하지 않았다.

운영 응답과 DOM이 조사 시 정상인 사실만으로 사용자의 지연 원인을 서버/브라우저
중 하나로 단정하지 않는다. 재현 테스트는 네트워크를 멈춰 무한 로딩 경로를
입증한다. 실제 공개 순위가 0명인 것은 별도의 정상 데이터 상태다.

`Api`에 제한된 읽기 helper를 추가하고 session/leaderboard만 사용한다. helper는
AbortController와 10초 타이머를 만들고 `await request()`의 JSON 읽기 완료까지
유지한다. 시간 초과를 전용 ApiFailure로 바꾼 뒤 finally에서 타이머를 정리한다.
기존 컴포넌트의 오류/Retry와 generation 보호를 재사용한다. 인증·쓰기 요청과
서버 점수/공개 프로필 계산은 변경하지 않는다.

## 최종 검토

재현 테스트는 수정 전 pending headers/body에서 로딩이 유지되는 것을 확인했다.
session 정지는 실제 초기 화면과 대조한 기대값으로 다시 실행해 실패를 확인했다.
helper 추가 후 focused 브라우저 5개가 통과했다. 실제 fetch 중단 이벤트, Retry의
새 요청/40점 행, 정상 0명, 503 오류, JSON body, 성공 후 20초 유지까지 검사했다.

코드 검토: `await this.request()` 때문에 타이머가 response headers까지만 적용되는
오류를 피한다. catch는 이 helper의 signal이 중단된 경우만 전용 timeout으로 바꾸고,
다른 API 오류는 보존한다. finally는 성공/실패에서 타이머를 제거한다. helper의
호출자는 session/leaderboard 둘뿐이다. 쓰기와 인증 확인은 재전송하지 않으며 서버
계정·점수 데이터나 공개 여부를 변경하지 않는다. 기존 화면 generation 보호는 유지한다.

최종 검증은 빌드된 번들에서 새 지연 테스트5개와 실제 계정/회원 테스트6개가
함께 통과했다(11 passed). Rust 회원/순위 Router 테스트6개, svelte-check
0 errors/0 warnings, Vite production build도 통과했다. 구현 변경은 api.ts의
시간 초과 메시지/helper와 session/leaderboard 호출 변경으로 제한했다.

제한: 두 조회가 연속해서 모두 멈추면 각각 최대10초가 걸릴 수 있다. 브라우저가
background timer를 일시정지하면 실제 벽시계 시간도 늘어날 수 있다. 운영에서 처음
멈춘 네트워크 요청의 로그는 확보하지 못했으므로 그 원인을 확정하지 않는다.

운영 배포는 별도 행위이며, 배포하지 않은 로컬 변경을 운영에 적용됐다고 보고하지 않는다.
