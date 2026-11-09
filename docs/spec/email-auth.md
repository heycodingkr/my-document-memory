# EMAIL: 이메일 링크 로그인과 세션

상태: runtime-v1 이후 단계의 계정 인증 명세. 링크 UI는 [landing-email-links-v1.md](landing-email-links-v1.md) 계약을 따른다. 이 문서는 OTP 경로와 세션·기기 연결 경계를 통합해 정의하며 구현 완료를 뜻하지 않는다.
영역 / 테스트 ID 접두사: `EMAIL` (케이스: [`../test/functional-ops.md`](../test/functional-ops.md))
기반: [계정·공개 기여](accounts-community-v1.md), [계정 운영](accounts-operations-v1.md), [기기 연결](link.md), [landing email links](landing-email-links-v1.md), WAM `docs/spec/email-auth.md`

## 1. 범위

runtime-v1은 로컬 `DMEM_TOKEN` 하나로 소유자 한 명을 인증하며 공개 사용자 이메일 계정은 제공하지 않는다. 이 명세의 이메일 계정·세션은 runtime-v1 이후 서버 단계다. 기존 이메일 계정 명세의 OTP API와 30일 세션을 유지하면서 웹 기본 로그인은 링크를 쓴다.

이메일 로그인은 CLI/MCP 기기 연결, 공유 동의, 프로필 공개, 이메일 주소 변경이나 계정 복구를 대신하지 않는다. 이메일은 사용자 계정을 식별할 뿐 문서 내용이나 라이선스 권한을 증명하지 않는다.

## 2. 링크·코드 인증

1. `POST /v1/auth/email/link`는 이메일과 정확한 허용 `Origin`을 받고, 주소를 정규화해 일반적인 202 응답을 준다. 계정 존재 여부와 무관하게 같은 응답을 쓴다.
2. 발송 메일에는 허용된 웹 Origin의 `/#sign-in=<challenge>.<verifier>` 링크를 넣는다. challenge와 verifier는 각각 독립 난수(64 hex)이며, 서버에는 기존 challenge 저장소를 사용해 keyed hash만 기록한다. 만료는 10분이다.
3. 링크 GET은 로그인시키거나 proof를 소비하지 않는다. 화면은 fragment를 즉시 history에서 제거하고 Continue 동작을 보여준다. 사용자가 진행할 때 `POST /v1/auth/email/consume {token}`으로 확인하며, 발송을 시작한 브라우저 쿠키가 없어도 링크를 연 브라우저에서 동작한다.
4. consume은 허용 Origin, 전달 성공 상태, challenge/verifier 해시, 만료·미사용 상태를 원자 검증한다. 성공 한 번만 세션을 만들며 링크 재사용·변조·미발송 proof는 실패한다.
5. 기존 `POST /v1/auth/email/start {email}` 및 `POST /v1/auth/email/verify {code}` OTP API는 호환 유지한다. 6자리 코드도 10분 만료·challenge 쿠키 바인딩·1회 사용을 따르며 링크 소비와 같은 계정 및 세션 정책을 쓴다.
6. 처음 성공한 링크/코드 확인 transaction에서 계정을 만든다. 재로그인은 같은 정규화 이메일의 account_id를 쓴다. 비밀번호는 없고, 다른 이메일이나 기존 local owner는 자동 병합하지 않는다.

## 3. 세션과 `dmem link`

성공한 인증은 30일 서버 세션을 발급한다. 원문 대신 keyed hash를 저장하고 쿠키는 HttpOnly·SameSite=Lax·Path=/로 설정하며 HTTPS에서는 Secure를 켠다. `GET /v1/auth/session`은 현재 계정과 CSRF token을 돌려주고, `POST /v1/auth/logout`은 세션 폐기와 쿠키 삭제를 수행한다. 브라우저 쓰기와 인증 POST는 정확한 허용 Origin 및 CSRF 규칙을 검사한다. 모든 인증 응답은 no-store다.

`dmem link`는 이메일 링크 로그인과 별개의 device authorization이다. 링크로 승인 페이지에 로그인한 뒤에도 user_code·요청 scope를 다시 보여주고 사용자가 승인해야만 기기를 연결한다. 로그인만으로 CLI/MCP token을 만들거나 공개 게시 권한을 주지 않는다. runtime-v1의 `DMEM_TOKEN`은 로컬 owner 토큰으로 남으며 이메일 계정 세션과 교환되지 않는다.

## 4. 발송 제한·개인정보

링크와 OTP는 주소별 동일 제한을 공유한다. 재발송은 60초 대기 후 허용하고 시간당 이메일당 최대 5회로 제한한다. 브라우저/IP 및 전역 발송 제한도 적용하며, challenge당 코드 검증 오답은 5회에서 차단한다. 제한은 발송 전 예약해 병렬 요청으로 우회하지 못하게 하고, 재발송은 이전 proof·코드를 무효화한다. 429에는 Retry-After를 준다([rate-limits.md](rate-limits.md)).

이메일은 공백 제거·ASCII 소문자로 정규화하고 Gmail 점/plus 별칭은 합치지 않는다. 로그인 링크 proof는 fragment에만 두어 서버 URL·Referer에 전달하지 않는다. 메일 발송 실패, 오류, 진단, 로그, 분석에서 주소·코드·proof·쿠키 원문을 숨긴다. 응답은 no-store, callback은 Referrer-Policy를 설정하며 임의 외부 return URL은 받지 않는다.

## 5. 요구사항과 테스트

| F-EMAIL-nn | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-EMAIL-01 | 링크 발송 | Origin을 검증하고 generic 202를 반환하며 proof는 메일에만 둔다. | EMAIL-01 |
| F-EMAIL-02 | 링크 확인 | fragment를 먼저 제거하고 사용자 동작 후 원자적으로 한 번 소비한다. | EMAIL-02, EMAIL-03 |
| F-EMAIL-03 | OTP 호환 | 기존 start/verify API의 만료·쿠키·오답 동작을 유지한다. | EMAIL-04 |
| F-EMAIL-04 | 계정 생성·재로그인 | 성공 확인 때만 생성하고 정규화 주소의 account_id를 유지한다. | EMAIL-05 |
| F-EMAIL-05 | 세션·로그아웃 | 30일 세션, 안전 쿠키, no-store, 폐기·CSRF 경계를 적용한다. | EMAIL-06 |
| F-EMAIL-06 | 재발송·시도 제한 | 60초·이메일당 시간당 5회·challenge 오답 5회를 원자 적용한다. | EMAIL-07 |
| F-EMAIL-07 | 기기 연결 분리 | `dmem link` 로그인 뒤 명시적 기기 승인이 있어야 연결된다. | EMAIL-08 |
| F-EMAIL-08 | 오류·개인정보 | 주소·proof·코드·token을 로그/응답/URL에 노출하지 않는다. | EMAIL-09 |
| F-EMAIL-09 | 세션 경계 | 다른 이메일, local owner, 계정 존재 여부가 자동 연결·노출되지 않는다. | EMAIL-10 |

