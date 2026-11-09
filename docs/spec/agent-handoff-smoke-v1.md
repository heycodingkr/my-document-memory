# Agent handoff smoke v1

상태: 실행 중인 runtime-v1의 설치 및 사용자 흐름 검증. 공개 도메인 배포와 프롬프트 복사 UI를 구현된 기능으로 간주하지 않는다.
영역 / 테스트 ID 접두사: `AHS`
기반: [runtime-v1.md](runtime-v1.md), [결과 보고서](../test/agent-handoff-smoke-v1.md)

## 목적과 계약

사용자가 Arise에서 문서 양식을 확인하고 요청에 사용할 프롬프트를 복사하는 흐름을 검증한다. Document Memory CLI와 stdio MCP를 실제 호스트에 설치·등록한 뒤, 동일한 로컬 API에서 검색·문서 생성·편집·내보내기를 확인한다. 기존 DB와 다른 세션의 파일·브라우저 탭은 보존한다. 합성 테스트 자료만 추가한다. 사용자 추가 지시(2026-11-09)에 따라 이번 데모에서 만드는 양식·참고자료·문서 제목과 본문, 시연용 요청문은 모두 영어로 작성하며 문서 locale은 en-US를 사용한다. 기존 다른 세션의 자료는 바꾸지 않는다.

## 의존 순서와 원자 작업

| 순서 / route | 산출물 | 독립적인 직접 확인 | 의존 |
|---|---|---|---|
| 1 inline | Git 상태·diff·코드·기존 테스트·DNS·API·MCP 설정 확인 | 직접 읽은 경로·실제 DNS 결과·Arise 접속 화면 | 없음 |
| 2 inline | 이 명세와 입력/기대 결과 | 현재 구현 및 사용자 요청과 대조 | 1 |
| 3 inline | CLI/MCP 빌드·사용자 설치, 프로젝트 MCP 등록 | 직접 workspace 테스트·바이너리 실행·호스트 도구 검색 및 status 호출 | 2 |
| 4 inline | Arise 양식 미리보기·개인 양식 복사, 합성 자료, MCP 문서 | 직접 DOM·스크린샷·ID·고정 버전·재조회 확인 | 3 |
| 5 inline | 편집·저장·DOCX 다운로드 및 회귀 검증 | 실제 다운로드 파일 ZIP/XML·저장본·기존 smoke 결과 검사 | 4 |
| 6 inline | 실패 이슈와 결과 보고서 | 실제 관측·설치 상태·미완료 경계·자신의 변경 재검토 | 5 |

빌드·테스트·브라우저 루프·설치·설정 변경·판단은 이 세션에서 수행한다. 별도 worker는 사용하지 않는다.

## 입력과 기대 결과

| ID | 입력 / 동작 | 기대 결과 |
|---|---|---|
| AHS-01 | apex/www DNS 및 https://mydocumentmemory.com/ 열기 | DNS 해석, 유효 HTTPS, 실제 앱. 실패하면 로컬 성공과 구분 |
| AHS-02 | 설치된 dmem --help, 토큰을 환경으로 전달한 status/templates | 실행 가능, JSON 정상 응답, 검색 결과 |
| AHS-03 | 등록된 MCP tools/list와 document_memory_status | 7개 도구·실제 API 연결. 등록·연결·인증·지원 기능을 각각 확인 |
| AHS-04 | Arise에서 회의록 양식 미리보기 | 문서 종류·en-US·영어 제목/본문·섹션 순서·작성자·라이선스 표시 |
| AHS-05 | 프롬프트 보기 및 복사 조작 | 실제 UI와 클립보드로 복사된 요청 확인. 양식 복사를 프롬프트 복사로 대체하지 않음 |
| AHS-06 | AHS 접두사 합성 Markdown을 CLI로 가져오기, 양식 UI 복사 | 비공개 자료와 원본 출처가 보존된 비공개 양식 |
| AHS-07 | 선택한 양식·자료 ID로 document_memory_create | 일치하는 template/source 고정 버전·확인 필요 항목·근거 원문 |
| AHS-08 | Arise에서 생성 문서 재열기·본문 수정·저장·재열기 | 버전 증가·수정 내용 유지 |
| AHS-09 | 웹 DOCX 내보내기 | Arise 다운로드 완료·유효 ZIP/XML·수정 내용 포함 |
| AHS-10 | 기존 workspace 테스트 및 격리 DB runtime browser smoke | 회귀 없음·다른 프로세스/DB/탭 보존 |
| AHS-11 | en-US 양식과 영어 자료로 최초 초안 생성 | 확인 필요 placeholder 및 근거 제목도 영어 |

## 설계·원인·검토

초기 관측: API PID 68074는 127.0.0.1:3847, Vite PID 68076은 127.0.0.1:5174에서 정상 응답한다. Document Memory는 기존 전역 MCP 등록에 없다. apex와 www는 getaddrinfo 실패이며 Arise는 This site can’t be reached를 표시한다. 다른 배포 세션이 사용 중인 탭은 접근하거나 변경하지 않는다.

직접 읽은 web/src/App.svelte의 양식 모달은 구조 미리보기·자료 선택·개인 양식 복사·초안 생성만 제공한다. prompt/clipboard 구현이 없으므로 AHS-05의 성공을 주장할 수 없다. 현재 생성은 외부 LLM이 없는 deterministic outline이다.

프로젝트 MCP 설정은 기존 설정·알 수 없는 필드를 보존하고 private token을 출력하지 않는다. 자격값 파일은 0600, Git 제외 경로에 둔다. CLI는 토큰을 자동으로 읽는다고 설명하지 않으며 실제 환경 전달로 검증한다. 공개 배포·DNS 변경은 이 설치/smoke 작업에 섞지 않는다.

최종 재확인: 작업 중 공개 도메인이 연결되어 /healthz 200과 실제 Arise 로그인 화면을 확인했다. 공개 API는 무인증 및 로컬 토큰에 각각 401이다. 초기 DNS 오류를 최종 상태로 혼동하지 않는다. 설치한 MCP/CLI의 로컬 검증과, 배포용 토큰 부재로 남은 공개 서버 인증 후 검증을 구분한다. 상세 결과와 #390·#391의 원인/증거는 결과 보고서에 기록했다.
