# 교차 계층 장애·복구 매트릭스 (FAIL)

상태: 케이스 정의(문서 우선). WAM `failure-matrix.md`의 "장애를 주입하고 상태 일관성과 복구를 확인한다" 구조를 문서 메모리로 옮겼다. 공통 합격 조건은 **가짜 성공 없음, 부분 쓰기 없음, 입력·토큰·URL 비노출, 복구 안내, 정리**다. 장애는 loopback fixture·가짜 서버·테스트 resolver·시계 조작 등 **제어 가능한 수단**으로만 주입한다. 단계는 [`functional-tests.md`](functional-tests.md) 읽는 법과 같다.

| ID | 단계 | 장애 주입 | 기대 동작과 판정 근거 | 관련 |
|---|---|---|---|---|
| FAIL-01 | F | 서버 모드에서 서버 연결 거부 | 로컬 라이브러리 명령은 정상, 서버가 필요한 명령은 종료 5(`server_unavailable`), 부분 쓰기 0 | CLI-21, FLOW-12 |
| FAIL-02 | F | 서버 TLS 인증서 불일치(가짜 서버) | `server_unavailable`과 구분된 `reason`, 우회하지 않음, URL·토큰이 오류에 없음 | MCPF-21 |
| FAIL-03 | F | 만료·해지된 토큰 | `auth_required`, `status.auth == "reauth_required"`, 익명 읽기로 조용히 낮추지 않음 | MCPF-16, SEC-D06 |
| FAIL-04 | F | 서버가 429와 `Retry-After` 응답 | 종료 6, `retry_after_seconds` 표시, 상태 불변 | IMP-20 |
| FAIL-05 | F | 서버 500 응답 | 고정 오류, 같은 요청의 재시도가 멱등(`created:false`), 이중 기록 0 | LIB-04 |
| FAIL-06 | F | 서버가 응답을 지연(호스트 타임아웃 초과) | 도구 오류, 상태 불변, 재시도 멱등 | MCPF-14 |
| FAIL-07 | R1 | 로컬 저장소 파일 손상 | `internal` 종료 1, 고정 문구, 패닉·경로·입력 echo 없음, 다른 데이터 보존 | LIB-13 |
| FAIL-08 | F | 저장 중 쓰기 불가(읽기 전용 디렉터리, 디스크 한도) | 원자적 교체 실패 시 기존 데이터 불변, 부분 파일 0, 오류 코드 | LIB-13 |
| FAIL-09 | F | 두 프로세스의 동시 수정 | 정확히 하나만 성공, 저장소 유효 | LIB-16 |
| FAIL-10 | F | 저장 도중 프로세스 강제 종료(SIGKILL)를 반복 | 재시작 후 저장소가 일관(전부 있거나 없거나), 잠금이 풀려 다음 명령이 성공 | LIB-16 |
| FAIL-11 | F | 원격 사이트 5xx·연결 reset | `fetch_failed`(`status_5xx`·`reset`), 부분 저장 0 | IMP-14, FLOW-12 |
| FAIL-12 | F | 원격 사이트 지연 | `fetch_blocked` `timeout` | IMP-14 |
| FAIL-13 | F | DNS 해석 실패(테스트 resolver) | `fetch_failed` reason `dns` | IMP-10 |
| FAIL-14 | F | 검색 provider 5xx·미설정 | `search_unavailable`(종료 5), 상태 불변 | DISC-01, DISC-08 |
| FAIL-15 | F | 만료·없는 `preview_id`로 import | `not_found`, 새 preview 안내, 라이브러리 변화 0 | IMP-02 |
| FAIL-16 | F | MCP 자식이 stdout 파이프를 닫거나 비정상 종료 | 종료 1, stderr 참조, 호스트가 재시작할 수 있음, 저장소 손상 0 | MCPF-19, MCP-07 |
| FAIL-17 | F | Arise가 실행 중이 아니거나 창이 0개 | `dmem browser-mcp`가 명확한 오류로 끝나고 상태 불변, 하네스는 `SKIP(env)`와 복구 절차를 보고 | hosts/arise.md |
| FAIL-18 | F | 클립 중 lease 만료·target 변경·다른 세션 탭 지정 | 저장 0, 사용자·타 세션 탭 불변, 거부 코드 | IMP-19, HOST-09 |
| FAIL-19 | F | 페이지가 JS dialog를 띄움 | 자동 승인 0, 명시적 inspect→응답 뒤에만 재개, 하네스가 멈추지 않음 | HOST-12 |
| FAIL-20 | F | 시계를 앞당겨 preview·receipt·검수 payload TTL 경과 | 만료 항목이 삭제·조회 불가, 감사 사실만 유지 | PRIV-07 |
| FAIL-21 | F | 저장된 어휘 버전이 더 새롭거나 오래됨 | 데이터 보존, `needs_reverify`, 명확한 오류(조용한 변환 없음) | FORM-14 |
| FAIL-22 | F | 게시 검수의 모델 provider 장애 | 공개되지 않고(fail closed) 대기 상태, 장애 해소 뒤 처리 | functional-models.md(OUTAGE) |
| FAIL-23 | F | 잘린·손상된 DOCX/PPTX, 잘못된 확장자 | `unsupported_format` 또는 `extract_empty`, 저장 0 | LIB-14, FMT-06 |
| FAIL-24 | F | `dmem install` 중 호스트 설정 파일이 손상·읽기 전용 | 원본 보존, 롤백, 설치 성공으로 표시하지 않음 | INST (functional-install.md) |
