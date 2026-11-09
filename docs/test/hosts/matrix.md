# 호스트 이식 범위와 확인 매트릭스

상태: 2026-11-09. WAM 호스트 문서의 구조·실패 모드를 적응했다. WAM에서 성공한 설치·인증·브라우저 작업을 이 제품에서 성공했다고 쓰지 않는다. 현재 실행 결과는 [`../wam-port-completion-v1.md`](../wam-port-completion-v1.md).

| WAM 원본 (`docs/test/hosts/`) | DMEM 대응 | 실행 방법·독립 판정 | 현재 확인 범위 |
|---|---|---|---|
| `arise.md` | [`arise.md`](arise.md), [`../../design/browser-host-integration.md`](../../design/browser-host-integration.md) | 공개 stdio MCP 한 연결, 세션 소유 탭, loopback fixture, landmark·저장 결과·캡처·탭 목록 비교 | 환경 스모크 21/21. 제품 clip·자동 recall은 별도 미실행 |
| `claude-code.md` | `HOST-01`, `HOST-03`, `MCPF`, `INST` | 임시 설정에 제품 MCP와 browser MCP 별도 등록, 도구 목록·실제 호출·인증 분리·제거 후 diff | 이 포팅에서는 미실행; WAM 설치 명령은 재확인 필요 |
| `codex.md` | `HOST-02`, `HOST-04`, `MCPF`, `INST` | 위와 같음. 실제 자식 환경·endpoint·선택된 설정을 확인하여 잘못된 설정이면 무효 | 이 포팅에서는 미실행; 호스트의 현재 설정 형식 확인 필요 |
| `chrome-mcp.md` | `HOST-08`, `MCPF` | 동일 세션의 browser MCP와 제품 MCP 공존, 다른 서버 장애 독립성·소유 탭 정리 | 미실행. 기본 검증 환경은 Arise |
| `meta-muse.md` | `MODEL`, `OUTAGE`, `HOST-12` | 실제 모델 응답은 fake provider 대조군과 분리; 비지원 도구·연결 만료·잘못된 JSON은 명시 실패 | 선택 모델 통합 후 검증. WAM 모델 실행 결과는 제외 |

## 공통 실행 순서

1. 설치·버전·실제 설정 경로·도구 목록·프로토콜을 기록한다. 호스트별 명령은 현재 공식 문서나 로컬 help를 확인한 뒤 사용한다.
2. 먼저 범용 stdio 클라이언트로 제품의 initialize→list→call을 확인한다. 제품의 `document_*`와 목표 계약의 `doc_memory_*`를 구분한다.
3. 같은 호스트에서 내 저장→재조회, 공개 검색→상세→복사, URL+양식 recall을 확인한다. 국가·provider 불일치와 타인 비공개 ID를 음성 입력으로 쓴다.
4. browser 도구를 추가하고 Arise의 세션·client·tab/window·lease를 전후 확인한다. 사용자 로그인 상태나 공개 session 이름만으로 소유권을 가정하지 않는다.
5. 웹 검색·클립·게시처럼 미구현인 단계는 미실행과 이유를 남긴다. 각 단계의 side effect가 없다는 것까지 확인한다.
6. 자기 자원만 제거하고 설정 diff·탭 목록·파일·로그의 센티널을 검사한다. 실패 후에도 같은 정리 규칙을 적용한다.

일반 계정의 로그인, CLI Bearer, 관리자 권한, browser 계정은 각각 독립적으로 검증한다. 라이브 허브 등록 성공이 자체 제품 기능의 성공을 뜻하지 않는다.
