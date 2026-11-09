# LINK: 계정과 MCP 기기 연결

상태: 설계 초안(문서 우선, 구현 없음). Device authorization은 WAM 승계(재확인 필요)이며 runtime-v1 이후 단계다. 원격 MCP OAuth도 WAM 승계(재확인 필요)다.
영역 / 테스트 ID 접두사: `LINK` (케이스: [`../test/functional-connect.md`](../test/functional-connect.md))
기반: [`mcp.md`](mcp.md), [`cli.md`](cli.md), [`runtime-v1.md`](runtime-v1.md)

## 1. 목적과 인증 티어

`dmem link`는 사용자가 CLI/MCP 기기를 웹 승인에 연결해 개인 서버 기능을 쓰게 한다. `dmem unlink`와 웹 승인 페이지는 연결을 해지하고, 연결 토큰은 OS 보안 저장소에서만 보관한다.

인증 상태는 [`mcp.md`](mcp.md) 4절과 일치한다.

| 티어 | 권한 |
|---|---|
| `anonymous` | 서버의 공개 recall/search/expand 및 웹 기능 읽기. 영수증·outcome·점수 생성 없음 |
| `linked` | 연결 사용자 본인의 라이브러리와 게시·공유 권한을 token scope에 따라 사용 |
| `local-owner-token` | runtime-v1의 로컬 단일 소유자 서버. `DMEM_TOKEN`은 로컬 서버 인증이며 계정 연결·공개 게시를 뜻하지 않음 |

`mcp.md` 4절은 로컬 계정 없는 라이브러리 모드와 서버의 anonymous/linked를 구분하지만 `local-owner-token` 이름은 아직 정의하지 않는다. 여기서는 runtime-v1의 필수 `DMEM_TOKEN`을 그 별도 인증 티어로 명시한다. mcp.md와 이 용어의 정합성은 후속 정리 항목이다.

저장된 credential이 거부되거나 만료되면 `reauth_required`를 표시한다. 이를 익명 상태로 조용히 낮추지 않는다.

## 2. 기기 승인 흐름

1. `dmem link`가 서버에 시작 요청을 보내고 `user_code`, 승인 페이지 URL, 만료 시각, polling 간격을 받는다. device secret은 화면·인자에 출력하지 않는다.
2. 사용자가 브라우저의 승인 페이지에 로그인하고 `user_code`와 요청 권한을 확인한다.
3. 승인 뒤에만 기기가 계정에 연결된다. 거부·만료·오입력 시 credential을 발급하지 않는다.
4. CLI는 승인 전 `pending` 상태로 poll하고, 승인 완료 때 access token을 한 번만 받는다.
5. CLI는 token을 OS secure store에 저장하고, 상태 출력은 연결 여부·만료·권한 이름만 표시한다.
6. `dmem unlink`는 현재 기기 credential을 서버에서 revoke한 뒤 secure store 항목을 지운다. 서버 연결 실패 시 해지를 완료했다고 표시하지 않는다.

`user_code`는 짧은 수명, 추측 제한, 1회 승인 정책을 가진다. 서버는 device secret/token을 해시로 저장하고 token 소유자를 검증된 credential에서 정한다.

## 3. 권한 범위

서버 token은 요청 목적에 필요한 최소 scope만 갖는다. scope 이름은 다음으로 고정한다.

| Scope | 허용 기능 |
|---|---|
| `read:library` | 연결 사용자의 비공개 라이브러리 읽기 |
| `write:library` | 사용자 소유 메모리 생성·수정·삭제 |
| `write:share` | 명시 동의를 받은 publish·share 동작 |
| `report:outcome` | 허용된 receipt의 outcome 제출 |
| `read:dashboard` | 본인 사용량·상태 조회 |
| `manage:account` | 본인 계정·기기 관리 및 연결 해지 |

서버는 scope가 없는 요청을 `scope_required`로 거부한다. local-owner-token의 권한은 로컬 소유자에 한정하며 위 서버 계정 scope를 가장하지 않는다.

## 4. 토큰 보호와 원격 MCP

Access token, device secret, 승인 code는 CLI/MCP 출력, 오류, 로그, 설정 파일, 프로세스 인자에 쓰거나 되돌려 주지 않는다. 연결 token은 OS secure store에만 저장한다. OS secure store를 사용할 수 없으면 평문 파일 fallback 없이 익명 읽기만 허용한다.

원격 MCP host OAuth discovery, 동의, refresh 및 revoke는 WAM 승계(재확인 필요)다. 각 host와 배포 환경의 scope·callback 지원을 재확인하기 전까지는 이 문서가 현재 동작을 보장하지 않는다. Local stdio 연결은 이 원격 OAuth 대신 위 device flow를 쓴다.

## 5. runtime-v1 경계

runtime-v1은 로컬 `DMEM_TOKEN` 기반 단일 소유자 서버를 정의한다. 사용자 계정 device flow, secure-store 연결, 다중 계정 token scope와 remote MCP OAuth는 runtime-v1 이후 단계다.

## 6. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-LINK-01 | device start 정보 | 시작 응답에 user_code·승인 URL·만료가 있고 비밀 token은 없다 | LINK-01 |
| F-LINK-02 | 명시적 사용자 승인 | 승인 전에는 pending이고 승인된 코드만 account device가 된다 | LINK-02 |
| F-LINK-03 | 거부·만료·오입력 | terminal 상태에서 credential을 발급하지 않는다 | LINK-03 |
| F-LINK-04 | 일회성 poll | 승인 결과와 token은 한 번만 반환되며 code 재사용은 거부된다 | LINK-04 |
| F-LINK-05 | secure-store 전용 | token은 OS secure store에만 존재하고 출력·파일·로그에 없다 | LINK-05 |
| F-LINK-06 | scope 적용 | 각 scope가 허용한 동작만 통과하고 없는 scope는 scope_required다 | LINK-06 |
| F-LINK-07 | revoke | 해지된 기기의 다음 요청은 인증 실패한다 | LINK-07 |
| F-LINK-08 | 티어 분리·비노출 | anonymous는 receipt를 만들지 않고 linked/local-owner-token 경계가 구별되며 token echo가 없다 | LINK-08 |
