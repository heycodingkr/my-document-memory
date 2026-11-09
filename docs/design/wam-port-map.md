# WAM → My Document Memory 포팅 지도

상태: 2026-11-09 기준. 상위 폴더 `../web-agentic-memory`(WAM, 읽기 전용 원본)의 명세·테스트·하네스를 이 저장소의 **문서 메모리** 도메인으로 옮기는 기준이다. WAM 경로는 저장소 루트 기준 `../web-agentic-memory/…`로 표기한다. WAM은 수정하지 않는다.

## 1. 한 줄 요약

WAM은 **웹 작업 노하우를 URL로 색인**해 에이전트가 재사용하게 한다. My Document Memory(DMEM)는 **문서 양식·참고자료·작성 규칙을 URL + 양식(문서 종류·로케일·provider)으로 색인**해 내 것은 저장·가져오고, 다른 사람 것은 찾아 보고 복사하고, 웹의 문서는 미리보고 가져오게 한다. 구조화 레이어, URL 정규화, 기본 비공개, 항목별 동의, 불변 version, 귀속, 합성 fixture 원칙을 가져온다. 점수·leaderboard·curator와 호스트 자동 호출은 각 기능의 별도 계약·실행 상태로 관리한다. 문서 URL fetch는 WAM의 no-fetch 경계와 달라 별도 SSRF 방어를 둔다.

2026-11-09 보완: WAM `docs/spec` Markdown 31개와 `docs/test` 62개, 합계 **93개**를 [`../../contracts/wam-port.v1.json`](../../contracts/wam-port.v1.json)에 개별 처분했다(**적응 72, 제외 21**). 원본 실험·배포 기록은 이 제품의 실행 결과로 복사하지 않는다. `PYTHONPATH=tests/lib python3 -B -m dmtest.porttrace --require-upstream`이 실제 원본 집합·중복·누락·대상 존재를 검사한다. 내용 리뷰와 실행 결과는 [`../test/wam-port-completion-v1.md`](../test/wam-port-completion-v1.md).

## 2. 개념 대응

| WAM | DMEM |
|---|---|
| 웹 작업 노하우 (`workflow`, `site_note`, `gotcha`) | 문서 메모리 (`template`, `reference`, `style_rule`) |
| 키: URL 패턴 + `task_category` | 키: URL 패턴 + **양식**(`provider`, `doc_type`, `locale`, `region`, `variant`) |
| `recall(url, keywords, task)` → ≤3 L1 힌트, BM25/RRF | `recall(url, doc_type, locale, provider, keywords, kind, scope)` → ≤3 L1 힌트, **결정적 튜플 순위**. 자유 텍스트는 `search` |
| 기여 `propose`(navigate/edit/save 코드만) | 저장(내 비공개, 로컬 우선) + **게시**(소유자의 명시적 동의, 라이선스) |
| Gatekeeper G0~G6(redaction, dedup, 재현 검증, 판정) | 게시 검수(비밀·개인 정보 재스캔, 라이선스, 중복, 구조 검증, 판정) |
| 남의 메모리: 공개 카탈로그를 recall로 받음 | 남의 메모리: `search` → `expand`(출처·라이선스) → `copy`(내 비공개 복사본) |
| 쿼리·ID 제거로 개인정보 보호 | 같은 규칙 + **능력 URL**(공유 링크 ID가 곧 권한) 비저장, 개인 정보 슬롯화 |
| (없음) | **웹 검색·미리보기·가져오기·클립**, 라이선스 감지, SSRF 방어 |
| `web_memory_*` 도구 10개 | `doc_memory_*` 도구 12개(+호스트 어댑터 1개). WAM과 한 호스트에 공존 |
| `wam`, `wam-mcp`, `WAM_*` | `dmem`, `dmem-mcp`, `DMEM_*` |
| fixture 사이트(리치 에디터, iframe 에디터…) | fixture 사이트(provider 모양 문서, 국가별 변형, 라이선스 변형, 악성 페이지) |
| 센티널 500개(10 family) | 센티널 + 문서 개인 정보 family |
| 종료 코드 0~6 | 0~7(7 = 없음·접근 불가) |

## 3. 명세(`docs/spec`) 포팅표

처분: ◎ 핵심 적응(작성 완료) · ○ 적응(설계 작성 완료) · △ 승계(변경 최소) · ✕ 제외. P1(서버·저장·연결), P2(검수·모델·점수), P3(웹·운영·출시)는 문서 묶음이다. 작성 완료는 제품 구현 완료를 뜻하지 않는다.

| WAM 파일 | 영역 | 처분 | DMEM 파일 | 핵심 변경 |
|---|---|---|---|---|
| `core.md` | CORE | ◎ | [`core.md`](../spec/core.md) | URL + 양식 키, provider 감지, 능력 URL, 공통 오류 코드·한도, 격리 모드 |
| `memory.md` | MEM | ◎ | [`memory.md`](../spec/memory.md) | kind 3종, 슬롯, 출처·복사 정책, 개인 정보 처리 |
| `recall.md` | RCL | ◎ | [`recall.md`](../spec/recall.md) | 양식·범위 튜플 순위, BM25 제거 |
| `mcp.md` | MCP | ◎ | [`mcp.md`](../spec/mcp.md) | 도구 12개, 로컬/서버 모드, clip |
| `cli.md` | CLI | ◎ | [`cli.md`](../spec/cli.md) | `dmem` 명령, 종료 코드 7 |
| `privacy.md` | PRIV | ◎ | [`privacy.md`](../spec/privacy.md) | 로컬 우선, 문서 개인 정보, 게시 동의 |
| `README.md`, `_template.md` | — | ◎ | [`README.md`](../spec/README.md), [`_template.md`](../spec/_template.md) | ID 레지스트리 |
| (신규) | FORM | ◎ | [`form.md`](../spec/form.md) | 양식 객체, 국가·provider 변형, 관습 경고 |
| (신규) | FMT | ◎ | [`formats.md`](../spec/formats.md) | StandardDoc(document/deck/sheet), provider 매트릭스, 내보내기 |
| (신규; WAM `기여` 일부) | LIB | ◎ | [`library.md`](../spec/library.md) | 내 메모리 CRUD, 멱등, 버전 충돌 |
| (신규; `gatekeeper`·`score` 일부) | SHR | ◎ | [`sharing.md`](../spec/sharing.md) | 게시·검색·복사·라이선스 |
| (신규) | DISC·IMP | ◎ | [`web-import.md`](../spec/web-import.md) | 웹 검색·미리보기·가져오기·클립 |
| `dedup.md` | DEDUP | ○ P1 | `dedup.md` | `scope_key=(host, 패턴, kind, doc_type, locale)`, `content_hash`, takedown 지문 |
| `api.md` | API | ○ P1 | `api.md` | 라이브러리·search·copy·publish·import·vocab 엔드포인트 |
| `database.md` | DB | ○ P1 | `database.md` | 메모리·버전·가시성·출처·동의·원장 스키마, 제약 |
| `link.md` | LINK | △ P1 | `link.md` | device flow 승계 |
| `install.md` | INST | ○ P1 | `install.md` | `claude-code`·`codex`·`arise` 등록, 스니펫 |
| `client-cache.md` | CACHE | ○ P1 | `client-cache.md` | 익명 공개 recall 캐시, preview TTL |
| `diagnostics.md` | DIAG | △ P1 | `diagnostics.md` | 안전한 진단 승계 |
| `gatekeeper.md` | GK | ○ P2 | `gatekeeper.md` | 게시 검수 단계 |
| `curator.md`, `curator/*` | CUR | ○ P2 | `curator.md`, `curator/` | 검수·어휘 제안 에이전트 지침·도구 |
| `model.md` | MODEL | ○ P2 | `model.md` | 검수·초안 생성용 모델 설정·예산 |
| `queue.md` | QUE | ○ P2 | `queue.md` | 게시 검수 큐, 백프레셔 |
| `provider-outage.md` | OUTAGE | ○ P2 | `provider-outage.md` | 모델 provider 장애 대기 |
| `score.md` | SCORE | ○ P2 | `score.md` | 다른 계정의 성공적 사용에 작성자 점수 |
| `profile.md` | PROFILE | ○ P3 | `profile.md` | 핸들·bio |
| `my-page.md` | MYPAGE | ○ P3 | `my-page.md` | 내 라이브러리·게시 상태·내 양식의 사용 성과 |
| `web.md` | WEB | ○ P3 | `web.md` | 양식 라이브러리·미리보기·복사 화면 |
| (overview 6절) | DOC | ○ P3 | `document.md` | 편집기·초안 생성·출처 패널·`{{확인 필요}}` |
| `admin.md` | ADMIN | ○ P3 | `admin.md` | 검수·takedown |
| `email-auth.md` | EMAIL | △ P3 | `email-auth.md` | 승계 |
| `rate-limits.md` | RL | ○ P3 | `rate-limits.md` | + 가져오기·검색 한도 |
| `usage-analytics.md` | USAGE | ○ P3 | `usage-analytics.md` | 내 사용량 |
| `search-performance.md` | PERF | ○ P3 | `search-performance.md` | 라이브러리·카탈로그 규모 측정 |
| `release.md` | REL | ○ P3 | `release.md` | 출시 게이트 |

제외(✕): 해커톤·데모 영상 문서, 4090 운영 배포 기록, Meta 모델 라이브 평가 기록, Medium/Naver/Google Slides 웹 작업 벤치마크(문서 작업 벤치는 구현 이후), `reference/` 스냅샷.

## 4. 테스트(`docs/test`·`tests/`) 포팅표

| WAM | DMEM |
|---|---|
| `docs/test/README.md`(원칙·계층·센티널·증거·게이트) | [`../test/README.md`](../test/README.md) |
| `functional-tests.md` | `functional-tests.md`(핵심) + `functional-{api,connect,install}.md`(P1) + `functional-{review,curator,models}.md`(P2) + `functional-{web,account,ops,release}.md`(P3) |
| `security-scenarios.md` | [`../test/security-scenarios.md`](../test/security-scenarios.md) (+ SSRF·라이선스·OOXML 악성) |
| `harness-verification.md` | [`../test/harness-verification.md`](../test/harness-verification.md) (+ 변이·양성/음성 대조) |
| `local-smoke.md`, `host-smoke.md`, `hosts/*` | [`../test/local-smoke.md`](../test/local-smoke.md), [`../test/host-smoke.md`](../test/host-smoke.md), [`../test/hosts/`](../test/hosts/README.md), [`../test/hosts/matrix.md`](../test/hosts/matrix.md)(미검증 호스트의 범위·정리·인증 분리) |
| `tool-forms/{cli,mcp,snippet}-form.md` | [`../test/tool-forms/`](../test/tool-forms/README.md) |
| `user-flows.md`, `failure-matrix.md`, `metrics.md`, `environment.md` | 같은 이름. A/B 사전 등록은 [`../test/prereg/_template.md`](../test/prereg/_template.md) |
| `tests/lib/wamtest/{doctrace,evidence,procs,sentinels}.py`, `tests/env/fixture-sites/fixture_server.py` | `tests/lib/dmtest/`(일반화), `tests/env/fixture-sites/` |
| `tests/env/check_browser_mcp_bridge.py`(Arise 공개 MCP + 현재 탭 recall) | `tests/smoke/arise_smoke.py`는 **브라우저 환경 부분만** 실행. 실제 제품 브리지는 `dmem browser-mcp`, 소유 탭 clip·음성 대조·실제 Arise 웹 입력은 `tests/smoke/web-memory-v1.py --browser --arise`로 별도 검증. [intake 입력·기대 결과](../test/web-memory-v1.md) |
| (WAM 실제 서버·바이너리) | `tests/env/dmem-double/`(**목표 계약 참조 구현**, 제품 아님); 실제 Rust 제품은 `runtime-v1.py`, `recall-v1.py`, `community-v1.py`로 따로 검증 |

## 5. 확정한 결정과 열어 둔 결정

| 결정 | 값 | 바꾸려면 |
|---|---|---|
| CLI·서버 이름·접두사 | `dmem`, `dmem-mcp`, `doc_memory_*`, `DMEM_*` | 이 문서·`cli.md`·`mcp.md`·스키마 한 곳씩 |
| 메모리 키 | URL 패턴 + 양식 | — |
| 내 메모리 | 로컬 우선, 기본 비공개, 계정 없이 사용 | `library.md` |
| 타인 메모리 | search → expand → copy, 원본 불변, 출처·라이선스 유지 | `sharing.md` |
| 웹 문서 | 미확인 라이선스는 구조만 보존, 게시 불가 | `web-import.md` 4절 |
| 웹 검색 | 선택 기능, 기본 provider 없음 | `web-import.md` 7절 |
| provider 직접 연동(OAuth) | 후속. v1은 공개 URL·파일·현재 탭 클립 | `formats.md` 3절 |
| 구현 언어·서버 스택 | **결정됨(별도 작업)**: Rust 2024 + Axum 0.8 + SQLite 첫 어댑터 + Svelte 5 ([`runtime-v1.md`](../spec/runtime-v1.md)). PostgreSQL·객체 저장소는 다중 사용자 단계 | [`architecture.md`](architecture.md) 5절 |
| 라이선스 어휘 | CC0, CC-BY, CC-BY-SA, MIT, Apache-2.0, 구조 전용, unknown | 법률 검토 필요 |
| 한도·카탈로그 예산 | 초기값, 측정 후 조정 | `core.md` 8절 |

## 6. 이 포팅에서 확인한 것과 못 한 것

확인함: WAM 명세·테스트 문서·하네스 코드를 직접 읽었다. Google Drive API 내보내기 MIME 표(최종 갱신 2026-09-03)를 읽었다. 이 머신에 Python 3.14.7, Node 26.5.0, Arise 0.1.76이 있다.

현재 확인한 것: Rust 6개 crate·Axum·SQLite·Svelte 제품, 실제 CLI·stdio MCP, URL+양식 recall 부분집합, 계정별 공개 기여·검수·복사가 있다. `runtime-v1.md`는 최초 단계 계약이며 이후 `recall-v1.md`·`accounts-community-v1.md`·`memory-community-smoke-v1.md`가 확장한다. 실제 intake 구현은 [`web-memory-v1.md`](../spec/web-memory-v1.md)의 URL 검색·미리보기·비공개 저장·출처와 `dmem browser-mcp`의 소유 Arise 탭 클립이다. 전체 목표의 `doc_memory_*` 12개와 실제 제품 `document_*`는 이름·입력·인증·오류 계약이 달라 별도 테스트한다. 차이와 대응은 [`../test/README.md`](../test/README.md) 7절이다.

확인하지 못함: 실제 계정에서 Google 웹 UI 내보내기 URL과 `/copy` 링크를 이용하는 흐름, Docs·Slides API 구조, Notion 공식 문서 본문, WAM의 호스트별(Claude Code·Codex) 사실의 현재 유효성. 해당 항목은 "미검증" 또는 "WAM 승계(재확인 필요)"로 표시했다. Google의 export MIME·API 제한·Sheets locale 문서는 별도 공식 출처를 재확인했으며 제품 OAuth·동기화 검증을 뜻하지 않는다. Google-shaped DOCX/PPTX export와 Brave 응답은 합성 fixture로 검증하며 실사이트·실제 키 검증으로 세지 않는다.

## 7. 위임 작성 규약 (병렬 작업자용)

플랫폼 명세 포팅은 파일 묶음 단위로 나눠 병렬 작업자에게 맡긴다. 작업자는 목표에 적힌 **소유 파일**을 이 규약대로 쓴다.

1. **쓰기 범위**: 프로젝트 저장소 `/Users/jason2/projects/ai-coding/my-document-memory`에서 소유 파일만 만들거나 덮어쓴다. 나머지 파일은 다른 세션이 동시에 쓰는 공유 자료이므로 참고만 하고, 바꾸고 싶은 점은 최종 보고에 적는다. git index·branch·stash는 그대로 둔다(`git status/diff/log` 같은 읽기 명령은 쓸 수 있다). `docs/spec/overview.md`, `runtime-v1.md`, `template-library.md`, `demo/`, `docs/demo/`, `Cargo.toml`, `crates/`, `web/`는 다른 세션 소유다.
2. **원본 참고**: WAM 폴더 `/Users/jason2/projects/ai-coding/web-agentic-memory`의 `docs/`, `crates/`, `tests/`를 자유롭게 읽는다. `.env`, `credentials/`, `.wam-data/`는 비밀이 있어 범위 밖이다.
3. **읽는 순서**: 이 문서 → [`../spec/README.md`](../spec/README.md)(레지스트리·규약), [`../spec/_template.md`](../spec/_template.md) → 핵심 계약 `core`·`form`·`memory`·`recall`·`library`·`sharing`·`web-import`·`mcp`·`cli`·`privacy`·`formats` → [`../spec/overview.md`](../spec/overview.md)(제품 범위)와 [`../spec/runtime-v1.md`](../spec/runtime-v1.md)(다른 세션의 구현 계약: Rust 2024·Axum·SQLite 첫 어댑터, `127.0.0.1:3847` 단일 소유자 서버, `DMEM_TOKEN`, 정수 `version`)와 `crates/dmem-contracts/src/lib.rs`, `crates/dmem-server/migrations/0001_library.sql` → 소유 파일에 대응하는 WAM 명세와 WAM 테스트 문서.
4. **적응 원칙**: 새로 만들기보다 옮긴다. WAM의 상태 기계·한도·오류 처리·멱등성·보관·보안 메커니즘이 아직 맞는 곳은 유지하고, 웹 에이전트 도메인을 핵심 계약의 문서 메모리 도메인으로 바꾼다. 적용되지 않아 뺀 WAM 개념은 각 파일의 `상태` 머리말에 한 줄로 적는다. 설계로 쓰고 구현·검증이 끝났다고 쓰지 않는다. 외부 서비스 사실은 WAM이나 핵심 문서에 이미 있는 것만 쓰고 WAM 호스트 사실은 "WAM 승계(재확인 필요)"로 표시한다. 이 명세는 runtime-v1의 상위 집합이다. runtime-v1이 이미 정한 것과 일치시키고 확장하는 곳에는 "runtime-v1 이후 단계"라고 적는다.
5. **문체**: 한국어, 식별자·명령·필드는 코드 서식, 머리말은 `_template.md`와 같다(`상태` / `영역 / 테스트 ID 접두사` / `기반`), 절 번호, 요구사항 표 `| F-<AREA>-nn | 요구사항 | 합격 기준 | 관련 테스트 |`, 명세 한 개당 40~100줄(짧아도 된다). 오류 코드는 `core.md` 7절, 한도는 `core.md` 8절(새 한도는 "제안"). 이름: `dmem`, `dmem-mcp`, `doc_memory_*`, `DMEM_*`. kind: `template`·`reference`·`style_rule`. visibility: `private`·`team`·`public`. 버전은 정수(`version`, `base_version`). 라이선스·복사 정책은 `sharing.md` 4절. CLI 종료 코드 0~7.
6. **추적성(문서 우선)**: 명세가 인용하는 모든 테스트 ID는 소유 테스트 문서에 표 행 `| API-01 | 입력/시나리오 | 기대 결과와 판정 근거 |`로 정의한다. 각 행에는 스크립트가 확인할 수 있는 구체적 입력과 관찰 가능한 기대 결과가 있다. ID는 `../spec/README.md` 레지스트리의 자기 영역 범위 안이다(플랫폼 범위는 상한이므로 필요한 만큼만 정의한다). 핵심 영역(`CORE FORM FMT MEM RCL LIB SHR DISC IMP VER TPL PRIV MCP CLI MCPF SNIP SMK BEH HOST CUST FLOW HARN FAIL SEC`)의 ID는 레지스트리 범위 안에서 정확히 인용한다(정의는 핵심 작성자가 쓴다).
7. **자체 검사**: `cd /Users/jason2/projects/ai-coding/my-document-memory && PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace <소유한 명세 파일들>`. 자기 영역의 인용은 `UNDEFINED`가 0이어야 한다. 핵심 영역은 정의가 들어오기 전까지 `UNDEFINED`가 남을 수 있으며 최종 보고에 나열한다.
8. **완료 기준**: 소유 파일이 디스크에 모두 있고, 자체 검사를 실행했고, 최종 보고를 썼다. **최종 보고**(평문 30줄 이내): 쓴 파일과 줄 수, 접두사별 정의한 ID 수, 핵심 계약·runtime-v1에서 발견한 모순·모호함·빈틈(파일+절), 확신이 없는 부분.
