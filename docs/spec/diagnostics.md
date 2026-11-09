# DIAG: 로컬 진단 출력과 안전 경계

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM의 닫힌 진단 메타데이터·민감값 제외 원칙을 승계하고, 서버 로그 수집·이메일 알림은 이 CLI 계약에 포함하지 않는다.
영역 / 테스트 ID 접두사: `DIAG` ([케이스](../test/functional-install.md))
기반: [`cli.md`](cli.md) 2·3·4·6절, [`runtime-v1.md`](runtime-v1.md) 동작 계약, [`core.md`](core.md) 4절, [WAM 포팅 지도](../design/wam-port-map.md)

## 1. 명령과 범위

`dmem doctor [--json]`은 현재 실행 환경을 읽기 전용으로 점검한다. 명령 표면은 [`cli.md`](cli.md) 2절에 정의되어 있다. 연결·TLS·인증·동의·캐시·호스트 등록·vocab을 각각 판정하며 한 검사 실패가 나머지 판정을 중단시키지 않는다.

로컬 runtime-v1은 단일 소유자 서버 `http://127.0.0.1:3847`을 사용하고 `DMEM_TOKEN`이 필요하다. `/healthz`는 데이터 없는 준비 확인이며 `/v1` 요청은 Bearer 인증이 필요하다. 원격 endpoint는 HTTPS를 요구한다. loopback HTTP에는 TLS 검사를 적용하지 않고 `not_applicable`로 표시한다.

| 검사 | 관찰할 상태 |
|---|---|
| 연결 | 설정된 endpoint 도달·준비 상태. 실패는 `unreachable` |
| TLS | 원격 HTTPS 인증서 검증. 잘못된 인증서나 비 loopback HTTP는 `tls_error` |
| 인증 | 로컬 토큰의 존재·수락 여부만 `ok` 또는 `unauthorized`로 표시 |
| 동의 | 현재 동의 필요 여부와 상태. 필요하지만 미동의면 `consent_required`; 묻거나 동의를 쓰지 않음 |
| 캐시 | 캐시 경로 존재·접근 가능 상태만 확인. 항목 내용은 읽거나 나열하지 않음 |
| 호스트 등록 | 지원 어댑터에서 dmem 등록 유무·충돌 여부 확인. MCP 프로세스나 호스트 앱은 시작하지 않음 |
| vocab | 설치된 vocab 집합의 형식·버전 상태. 불일치는 `mismatch` |

## 2. 출력 계약

사람용 모드는 검사 이름과 고정 상태 코드만 출력한다. `--json`은 stdout에 schema version 1 JSON 문서 하나를 출력하며 진행 문구나 표준 출력 로그를 섞지 않는다. 최상위는 `schema_version`과 `checks`; 각 검사 항목은 고정 `check`, `status`와 선택적인 `host`, `version`, `path`만 가진다.

허용 상태 코드는 `ok`, `not_applicable`, `unreachable`, `tls_error`, `unauthorized`, `consent_required`, `unavailable`, `missing`, `conflict`, `mismatch`, `unsupported`다. 이는 진단 전용 상태이며 API 오류 코드와 혼용하지 않는다. 실행 자체가 보고서를 만들지 못한 경우 종료 코드는 [`cli.md`](cli.md) 3절을 따른다. 보고서가 완성되면 검사 실패는 항목별 상태로 반환한다.

출력 값은 검사 식별자, 상태 코드, 호스트 ID/서버 hostname, 호스트·바이너리·vocab 버전, 파일 경로로 제한한다. endpoint URL은 출력하지 않고 필요한 경우 hostname만 쓴다. 임시 검사 파일 경로는 정리 완료 후 보고하지 않는다.

## 3. 비밀과 문서 데이터

토큰, `DMEM_TOKEN` 값, Authorization 헤더, 쿠키, 키, 사용자 ID, URL path/query/fragment, 요청·응답 본문, 문서 제목·본문, vocab 항목, 설정 파일 원문, 오류 원문·stack trace를 출력·로그·진단 파일에 담지 않는다. 오류는 고정 상태 코드로 축약하고 입력을 echo하지 않는다.

검사는 네트워크 요청을 진단에 필요한 준비·인증 확인으로 한정한다. 동의 요청을 보내거나 캐시를 비우거나 설정·호스트 등록·데이터를 수정하지 않는다. 호스트 설정은 파싱해 dmem 항목의 상태만 확인하고 비 dmem 값은 출력하지 않는다. 설정 오류로 endpoint를 만들 수 없으면 로컬 오류를 반환하고 네트워크 호출을 하지 않는다.

## 4. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-DIAG-01 | 독립 검사 | 일곱 검사 상태를 각각 보고하고 한 실패 뒤에도 나머지를 계속 판정 | DIAG-01~08 |
| F-DIAG-02 | runtime 인증 경계 | loopback 준비 확인과 Bearer 인증 결과를 분리하며 토큰을 출력하지 않음 | DIAG-01, DIAG-04 |
| F-DIAG-03 | TLS 경계 | 원격 TLS 실패를 식별하고 loopback은 TLS 비대상으로 분류 | DIAG-02~03 |
| F-DIAG-04 | 안전한 출력 | JSON 스키마가 닫혀 있고 허용된 식별자·상태·hostname·버전·경로만 포함 | DIAG-01~08 |
| F-DIAG-05 | 데이터 비변경 | 검사 중 동의·캐시·호스트 설정·문서 메모리를 바꾸지 않음 | DIAG-05~07 |
| F-DIAG-06 | vocab 상태 | vocab 구조·버전 이상을 상태 코드로 보고하고 항목 값은 숨김 | DIAG-08 |

