# 계정·공개 기여 테스트 명세

상태: 제품 구현 및 실제 Router/브라우저 검증. 기본 웹 로그인은 이메일 링크로 확장됐고 OTP API는 별도 통합 테스트로 유지한다. 제품 계약: [accounts-community-v1](../spec/accounts-community-v1.md). 합성 이메일 alice@example.test/bob@example.test, 임시 SQLite와 캡처 mailer를 쓴다. 실제 API key/사용자 메일은 fixture로 쓰지 않는다. 검증은 부모가 수행한다.

| ID | 입력 | 기대 결과·독립 oracle |
|---|---|---|
| AC-01 | 올바른 이메일 + 허용 Origin으로 start | 202, mailer에 한 건, HttpOnly challenge cookie, 응답에 코드/토큰 없음 |
| AC-02 | 잘못된 메일/알 수 없는 필드, 미설정·실패 mailer | 400 또는 503, 발송 성공 표시 없음, 고정 오류 |
| AC-03 | 캡처한 코드와 해당 challenge로 verify | 200, 30일 세션 쿠키, session API에서 동일 계정, SQLite에 원문 세션/코드 없음 |
| AC-04 | 다른 브라우저/틀린 코드/코드 재사용/만료 | 모두 거절, 계정·세션 생성 없음, 최대 5회 이후 올바른 코드도 거절 |
| AC-05 | 재발송 제한 후 새 코드, 기존 코드 | 60초 이내 제한, 이후 이전 코드 거절, 새 코드만 성공 |
| AC-06 | 로그인→DB 재열기→session→logout→session | 재시작 후 세션 보존, 로그아웃 후 401, 재로그인 시 같은 owner와 데이터 |
| AC-07 | 외부 Origin/Origin 없음의 start·verify | 401, mailer 호출 없음 |
| AC-08 | session 쿠키 쓰기에 CSRF 없음/잘못된 값/외부 Origin | 401, 데이터 변경 없음. 올바른 Origin+CSRF만 성공 |
| AC-09 | 이메일·브라우저 시간당 요청 반복 | 한도 뒤 429, mailer 호출 증가 없음 |
| AC-10 | Resend adapter에 HTTP 실패/timeout | 503, 인증이 준비됐다고 표시하지 않음; 수신자/코드 로그 없음 |
| AC-11 | Alice private 양식/자료/문서 후 Bob 목록·ID·통계 | Bob에 미노출, 직접 ID는 404, Alice 통계만 증가 |
| AC-12 | Alice 구조의 license/rights 없는 제출, Bob 양식 ID | 400/404; 올바른 제출은 pending, 익명 공개에는 미노출, private 원문 unchanged |
| AC-13 | 일반 계정/일반 Bearer가 관리자 검수 | 401, 별도 admin token 승인만 catalog 생성, 중복 결정 409 |
| AC-14 | 승인 snapshot을 익명 검색/상세→Bob 복사 | 원문·이메일/owner 없음, 새 private copy, id/version/author/license 고정 |
| AC-15 | 같은 양식 중복 제출, 타 owner 동일 구조 | 전자 409, 후자는 독립 pending |
| AC-16 | 기여 철회→공개 목록/상세/신규 복사→기존 복사 | 공개에서 제거/404, 이미 복사된 Bob 데이터와 attribution 유지 |
| AC-17 | CC-BY copy를 CC0로 재기여, 파생 게시물을 제3자가 다시 복사 | CC0 거절; CC-BY 재기여와 재복사에서 최초 기여자 attribution 보존. private copy ancestor ID는 공개 snapshot에 없음. 최대 16개 계보 초과 시 일부 제거 없이 거절 |
| AC-18 | 웹 익명 공개 탐색→이메일 코드→내 공간 새 양식→기여 제출 | 실제 DB/HTTP 반영, 기여 pending 표시, 새로고침 후 로그인·자료 유지 |
| AC-19 | 웹 로그아웃/세션 만료/로그인 실패/좁은 뷰포트 | 개인 화면 초기화, 오류·복구 안내, 키보드 가능한 폼, 가로 overflow 없음 |
| AC-20 | 기존 Bearer 문서·슬라이드 업로드/편집/저장/export smoke | 기존 workspace·CLI·MCP 시나리오 통과 |

테스트 코드는 실제 Router+Store 통합, server mailer 어댑터, Playwright E2E로 구성한다. 시계가 필요한 만료/제한 테스트는 명시적 clock 주입으로 sleep 없이 검증한다. Resend 실제 메일 수신과 Cloudflare DNS 검증은 외부 수동 검증이며, 수행하지 않은 경우 미검증으로 기록한다.
