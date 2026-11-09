# 아키텍처: 구성요소, 신뢰 경계, 모듈 계약

상태: 설계 초안(문서 우선, 구현 없음). WAM `docs/design/architecture.md`와 `module-boundaries.md`의 구조를 문서 도메인으로 옮긴 요약이다. 제품 범위는 [`../spec/overview.md`](../spec/overview.md) v0.3, 기능 계약은 [`../spec/`](../spec/README.md)가 정한다.

## 1. 한 장 그림

```
          사용자 / 에이전트(Claude Code, Codex, Arise)
                 |                    |
          dmem CLI              dmem-mcp (stdio)  ←─ Arise MCP 허브 / browser MCP 옆에 등록
                 \                    /
                  \                  /           dmem browser-mcp (선택): 공개 browser MCP child + clip_current_tab
                   +---- dmem-client ----+
                   |  (정규화·scrub·어휘·캐시·로컬 저장소)   ← 로컬 모드는 여기까지
                   +----------+----------+
                              | HTTPS (서버 모드)
                        dmem-server (API)
              인증 · 라이브러리 · 검색 · 게시 검수 · 카탈로그
                  |            |                 |
              PostgreSQL    객체 저장소        worker(추출·렌더·색인·검수)
              (메타·버전·    (원본·내보내기)     provider/형식 어댑터
               전문 검색)
                              |
                         웹 앱(양식 라이브러리·편집기·내 페이지)
```

## 2. 모듈과 계약

| 모듈 | 책임 | 의존 방향 |
|---|---|---|
| `dmem-core` | URL·양식 정규화(`CORE`, `FORM`), 어휘, scrub, L0 projection, recall 순위(`RCL`), 복사 정책 | 외부 I/O 없음(순수) |
| 형식 어댑터 | DOCX·PPTX·Markdown·HTML·PDF 추출과 내보내기(`FMT`) | `dmem-core`의 StandardDoc |
| provider 어댑터 | Google·Notion URL 규칙, 내보내기 경로, 능력 URL 처리 | `dmem-core` |
| `dmem-client` | 로컬 저장소, 서버 API 클라이언트, 캐시, 자격증명, 가져오기(fetch guard) | core, 어댑터 |
| `dmem` / `dmem-mcp` | 표면(명령·도구). 로직은 `dmem-client` 호출뿐 | client |
| `dmem-server` | 인증, 라이브러리·카탈로그 API, 게시 검수, 속도 제한 | core, 저장소 |
| worker | 비동기 추출·렌더·색인·검수 큐 | core, 어댑터 |
| 웹 앱 | 양식 라이브러리·편집기·내 페이지 | server API |

**고정 원칙**: DOCX·PDF·provider 어댑터는 StandardDoc 계약 뒤에서 독립적으로 바꿀 수 있다. CLI와 MCP는 같은 `dmem-client` 호출을 거치므로 같은 입력에 같은 결과를 낸다(`RCL-14`, `CLI-05`).

## 3. 신뢰 경계

| 경계 | 규칙 |
|---|---|
| 사용자 기기 ↔ 서버 | HTTPS. recall은 최소 전송, search·가져오기는 사용자가 시작한 경로로 표시 |
| 클라이언트 ↔ 원격 사이트(가져오기) | fetch guard([`web-import.md`](../spec/web-import.md) 2절): 사설 주소·리바인딩·크기·시간·형식·로그인 |
| 에이전트 ↔ 메모리 | 모든 결과는 untrusted 데이터. 모델이 출처를 주장해도 `claimed`다 |
| 에이전트 ↔ 브라우저 MCP | 별도 서버. `dmem browser-mcp`만 공개 인터페이스로 현재 탭을 읽는다 |
| 문서 본문 ↔ 지시 | 업로드·가져온 문서 안의 문장은 데이터다(`SEC-02`) |
| 사용자 ↔ 사용자 | 비공개·팀 항목은 구분 불가한 `not_found`로 숨긴다(`SEC-01`) |

## 4. 저장소 매핑

| 모드 | 메타·버전·색인 | 원본·내보내기 | 인증 |
|---|---|---|---|
| 로컬(첫 구현) | SQLite(`rusqlite`). 임베디드 또는 `127.0.0.1` loopback 서버 뒤에서 사용([`../spec/runtime-v1.md`](../spec/runtime-v1.md)) | 원본 bytes와 체크섬을 저장소에 보존 | 설정한 `DMEM_TOKEN` 하나가 로컬 소유자 하나 |
| 서버(다중 사용자 단계) | PostgreSQL(사용자·workspace·메타·버전·전문 검색) | 객체 저장소 | device flow·OAuth |

계약(CLI·MCP·API 동작)은 저장소 어댑터와 무관하다. 어댑터를 바꿔도 `CORE`·`RCL`·`SHR` 등 테스트 ID의 기대 결과는 같아야 한다.

## 5. 기술 스택 (결정됨: runtime-v1)

별도 작업이 [`../spec/runtime-v1.md`](../spec/runtime-v1.md)에서 2026-11-09에 다음을 정했고 이 저장소의 `Cargo.toml`·`crates/`·`web/`에 시작되었다. 이 문서는 그 결정을 따른다.

| 영역 | 결정 | 비고 |
|---|---|---|
| core·contracts·client·CLI·MCP·server | Rust 2024 워크스페이스(`dmem-contracts`, `dmem-core`, `dmem-server`, `dmem-client`, `dmem-cli`, `dmem-mcp`), Axum 0.8 | WAM의 경계 구성을 참고하되 브라우저 작업 지식·기여 점수·curator·OAuth 운영 코드는 복사하지 않는다 |
| 저장 | SQLite(`rusqlite`) 첫 어댑터 | PostgreSQL·객체 저장소·worker는 다중 사용자 운영 단계이며 현재 지원한다고 표시하지 않는다 |
| 웹 | Svelte 5 + TypeScript + Vite | |
| 테스트 하네스 | Python 3 표준 라이브러리만 | 구현 언어와 분리. 제품 바이너리는 환경 변수로 주입(`tests/README.md`) |

runtime-v1은 이 명세 세트의 **부분집합**이다: 로컬 단일 소유자, 양식·자료·문서, 공개 시드 양식 복사, 검색, 내보내기. recall·게시·웹 가져오기·클립은 이후 단계다. 테스트는 케이스마다 적용 단계(profile)를 표시해 구현 범위 밖 케이스를 조용히 건너뛰지 않고 이유와 함께 `SKIP`으로 보고한다([`../test/README.md`](../test/README.md) 2절).

## 6. 핵심 데이터 흐름

| 흐름 | 단계 |
|---|---|
| 내 메모리 저장 | 입력 → 추출(어댑터) → 양식 확정 → scrub → 미리보기 → 저장(원본 해시 보존 + 불변 버전 + 색인) |
| recall | URL·양식 정규화 → 후보(범위·권한) → 순위 튜플 → L1 힌트 + untrusted 프레이밍 |
| 타인 메모리 | search → expand(출처·라이선스) → copy(새 비공개 메모리, derived_from) |
| 게시 | 동의 → 재스캔 → 중복 → 검수 큐 → 공개 카탈로그(원본 파일·source_ref 제외) |
| 웹 가져오기 | 검색 후보 → preview(fetch guard·추출·라이선스) → import(preview 내용 그대로 저장) |
| 현재 탭 클립 | 명시 호출 → 자기 소유 탭 검증 → 텍스트·구조 읽기 → 정규화·scrub → 저장(`captured`) |
