# Runtime v1 — 설계·원인 분석·검증 기록

검증일: 2026-11-09. 범위는 이 저장소의 로컬 실행 런타임이다. 제품 전체 목표 명세의 모든 기능이 완성되었다는 의미는 아니다. 현재 기능/제한은 [README](../../README.md)와 [runtime-v1 계약](../spec/runtime-v1.md)을 기준으로 본다.

## 설계 결정

- WAM의 Cargo workspace와 core/contracts/server/client/cli/mcp 경계를 읽고 참고했다. 도메인 모델과 구현은 문서·양식·자료·출처·리비전에 맞게 작성했다.
- 단일 로컬 소유자가 추가 서비스 없이 실행하도록 SQLite 어댑터를 선택했다. 소유권은 DTO 입력이 아니라 인증자에서 주입한다. 테스트 인증자는 두 소유자를 사용해 격리를 검증한다.
- 공개 시드 양식과 개인 양식을 같은 라이브러리에서 검색하되, 공개 접근은 catalog 소유의 양식 구조에만 허용한다. 개인 자료와 문서는 소유자 조건을 먼저 적용한다.
- 자료 원본 bytes와 SHA-256, 추출 위치를 함께 보존한다. 문서는 양식/자료 버전을 고정하고 이후 저장 때 현재 base_version과 비교한다. 리비전은 INSERT만 한다.
- 외부 LLM 없이 편집 가능한 빈 구조를 만들고 선택한 자료의 처음 3개 span을 각 최대 2,000자 발췌로 연결한다. 인용은 원문 prefix 및 해당 자료/버전/위치로 검사한다. 초안을 완성된 사실 문서라고 표시하지 않는다.
- Office 지원은 기본 텍스트·제목·표와 슬라이드 순서다. 원본 렌더링/스타일 재현이나 서버 PDF 엔진을 구현했다고 표시하지 않는다.

## 원인 분석과 수정

아래 동작 문제는 각각 먼저 실패하는 자동 검증으로 재현하고 수정 후 같은 검증이 통과하는 것을 확인했다.

| 문제 | 확인한 원인 | 수정과 검증 |
|---|---|---|
| 선택한 Markdown 자료에서 제목만 근거로 남음 | 자료의 spans.first()만 인용 | 처음 3개 span을 위치/버전과 함께 발췌. 실제 사실 문단 sentinel을 검사하는 store 테스트와 브라우저의 원문 값 검사 |
| 모바일 슬라이드가 화면 너비를 초과 | 16:9 aspect-ratio와 min-height가 auto width를 586px로 확대 | width:100%/min-width:0 지정. 390px 실제 Chromium에서 document.scrollWidth<=innerWidth 검사 및 PNG 확인 |
| 이전 버전 적용 시 DataCloneError | Svelte state proxy를 structuredClone에 직접 전달 | state.snapshot 후 복사. v1 적용→v3 저장→재열기까지 브라우저 검증. [Svelte의 snapshot 계약](https://svelte.dev/docs/svelte/$state#%24state.snapshot) 참고 |
| 일부 공유 링크에서 알파벳 토큰 노출 가능 | 일반 URL의 길이/문자 휴리스틱으로 capability token을 판별 | 알려진 capability route만 남기고 ID 치환, 알 수 없는 경로는 호스트로 후퇴. Drive/Dropbox/Figma/Canva 독립 입력으로 토큰 부재 검사 |
| Markdown 표가 일반 텍스트처럼 표시 | 첫 행 뒤 header delimiter 누락 | 구분선과 pipe escape 추가, 기대 Markdown 문자열 검사 |
| 새 DB가 OS 기본 0644로 만들어짐 | SQLite 생성 후 기본 umask를 그대로 사용 | Unix DB 0600 지정 후 WAL 생성, 기존 sidecar도 0600. 임시 DB 및 실행 중 개발 DB/설정 파일 권한 검사 |
| 큰 stdio frame이 줄바꿈 없이 끝날 때 정상 EOF로 처리 | 비어 있는 임시 buffer를 overflow flag보다 먼저 검사 | overflow를 우선 검사. 프레임 초과와 I/O 실패를 구분해 지속 I/O 오류 루프도 차단. 큰 버퍼/미종결 입력 회귀 테스트 |

초기 컴파일 과정의 Axum MultipartRejection 모듈 경로와 MutexGuard 명시 역참조도 실제 컴파일러 오류 위치를 읽어 수정했다. 브라우저 테스트의 부분 문자열 label 및 상태 알림 locator는 실제 UI 전환을 기다리는 정확한 locator로 정리했다.

## 실행한 검증

| 명령 / 독립 확인 | 결과 |
|---|---|
| cargo test --workspace | 16개 통과: core 9, MCP 3, store/실제 Router 4 |
| cargo fmt --all --check / cargo build --workspace | 통과 |
| pnpm --dir web check | 오류 0, 경고 0 |
| pnpm --dir web build | 통과 |
| python3 tests/smoke/runtime-v1.py --browser | HTTP 인증, CLI import/copy/create/show/export, JSON-RPC initialize/list/call/오류, 충돌, 서버 재시작/버전 보존 및 실제 브라우저 3개 흐름 통과 |
| node --test demo/video/*.test.mjs | 기존 데모 테스트 12개 통과 |
| PYTHONPATH=tests/lib python3 -m unittest discover -s tests/lib/selftest | fixture HTTP 테스트 8개 통과 |
| 독립 Office 파서 | 다운로드 DOCX를 python-docx로 읽어 편집한 문단 확인; PPTX를 python-pptx로 읽어 11장과 편집 제목 확인 |
| ZIP/XML 독립 검사 | Python zipfile/ElementTree로 DOCX 5개, PPTX 30개 XML/rels 부품 검사 |
| 독립 PPTX fixture | 파일 숫자 순서와 다른 presentation relationship 순서를 따르는지 Rust 테스트 |
| 입력 안전 | 알 수 없는 필드·빈 파일·잘못된 ZIP·6 MiB 확장 part·DOCTYPE entity·비공개 ID/검색/생성 접근·위조 citation 거부 |
| 실제 화면 | 데스크톱 양식/문서/덱 및 390px 모바일 PNG를 view_image로 직접 확인 |
| 로컬 실행 | scripts/dev.mjs로 생성한 별도 개발 라이브러리에서 3847 health / 5174 앱 / Vite 인증 proxy / 9개 시드 확인 |
| 정보 보존 | 기존 작업은 stage/commit/reset하지 않음. .env token을 로그나 웹 bundle에서 찾을 수 없음을 검사 |

스크린샷과 다운로드 파일은 web/test-results/에 생성된다. smoke runner의 DB/토큰/서버는 임시 자원이며 종료 시 정리한다. 개발 라이브러리에는 테스트 데이터를 넣지 않았다.

## 위임과 부모 확인

반복적인 Cargo manifest 6개만 사용자 설정의 첫 사용 가능 backend codex:gpt-6-luna로 위임했다(job 108). 완료 결과를 회수한 뒤 모든 manifest를 직접 읽었다. 로직·설계 판단·컴파일·테스트·오류 재현·최종 리뷰는 부모 세션에서 수행했다.

## 남은 제품 범위와 검증 한계

PostgreSQL/객체 저장소/worker, 외부 LLM, OAuth/공급자 동기화, 공개 게시·팀 공유, PDF import/OCR, 시트 편집, Office의 복잡한 레이아웃과 사용자 스타일은 후속 범위다. URL 투영은 네트워크 fetch/DNS/SSRF 검증기가 아니다. Word/PowerPoint 네이티브 시각 렌더링은 실행하지 않았으므로 Office 원본과 동일한 배치를 보장하지 않는다.
