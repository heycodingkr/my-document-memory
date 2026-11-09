# 기능 명세 (Feature Spec)

상태: 전체 목표 계약과 구현 단계 명세의 색인. 실제 Rust 제품은 `runtime-v1`·`recall-v1`·`web-memory-v1`·계정/기여 명세의 부분집합을 구현한다. 기능 명세는 "무엇을 만들고 어떤 상태가 되면 끝인가"의 단일 출처다. 설계([`../design/`](../design/architecture.md))는 "어떻게 만드는가", 테스트([`../test/`](../test/README.md))는 "어떻게 검증하는가"를 다룬다. 명세가 있다는 것은 구현이나 검증이 끝났다는 뜻이 아니다.

제품 범위의 상위 문서는 [`overview.md`](overview.md)(v0.3)이며 이 저장소의 다른 작업이 함께 편집한다. 이 색인의 문서들은 그 범위 안에서 **계약**(CLI·MCP·정규화·저장·공유·가져오기)과 **테스트 ID**를 고정한다. 초기 양식 목록은 `template-library.md`(별도 작성 중)가 맡고 [`form.md`](form.md)의 `doc_types` 어휘와 맞춘다.

이 명세 세트는 상위 폴더의 web-agentic-memory(WAM)를 **문서 도메인으로 옮긴 것**이다. WAM 문서별 처분과 차이는 [`../design/wam-port-map.md`](../design/wam-port-map.md)에 있다.

## 작업 순서

```
기능 명세        docs/spec/
  → 테스트 스펙   docs/test/functional-*.md, security-scenarios.md, tool-forms/   (케이스 ID, 입력, 기대 결과)
  → 스모크       docs/test/local-smoke.md, host-smoke.md, hosts/                   →  tests/smoke/
  → 유저 플로우   docs/test/user-flows.md
  → 하네스 검증   docs/test/harness-verification.md                                →  tests/lib/selftest, tests/env
```

테스트 ID는 구현보다 먼저 합의한다([`../test/README.md`](../test/README.md) 원칙 1). 명세가 바뀌면 이 문서를 먼저 고치고, 그다음 테스트 문서, 그다음 코드 순서로 따라간다. 명세가 인용한 테스트 ID가 `docs/test`에 모두 정의되어 있는지는 `HARN-11`(doctrace)이 검사한다.

## 규약

- 영역 이름은 테스트 ID 접두사와 같다. 영역 하나가 파일 하나다(아래 레지스트리).
- 요구사항 ID는 `F-<영역>-<번호>`(예: `F-SHR-07`)이고 테스트 ID와 번호를 맞추지 않는다. 요구사항마다 "관련 테스트"에 `docs/test`에 정의된 ID를 적는다. **테스트가 없는 요구사항은 미완성**이다.
- 문서 머리: `상태`, `영역 / 테스트 ID 접두사`, `기반`. 본문은 한국어이고 식별자·명령·필드는 코드 서식이다.
- 확인하지 못한 외부 사실은 쓰지 않는다. WAM에서 확인된 사실은 "WAM 승계(재확인 필요)", 이 저장소에서 확인한 것은 날짜와 근거를 적는다.
- 기능→테스트 추적표의 원본은 [`../test/README.md`](../test/README.md) 6절이다. 같은 표를 여기에 다시 쓰지 않는다.
- 작성 템플릿: [`_template.md`](_template.md)

## 테스트 ID 레지스트리

핵심 영역의 범위는 모두 정의한다. `P1`~`P3` 영역의 범위는 **예약 상한**이며 각 문서가 필요한 만큼만 정의한다. 명세는 정의된 ID만 인용한다(`HARN-11`이 검사한다).

주의: [`template-library.md`](template-library.md)의 `DOC-xx`·`SLIDE-xx`·`SHEET-xx`는 **시드 카탈로그 항목 ID**이며 테스트 ID가 아니다(추적 검사에서 제외). [`runtime-v1.md`](runtime-v1.md)의 `RT-01~12`는 구현 단계 수용 케이스이고, 이 문서 ID와의 대응은 [`../test/README.md`](../test/README.md) 7절에 있다.

| 접두사 | 영역 | 정의 문서(`docs/test/`) | 범위 | 작성 |
|---|---|---|---|---|
| `CORE` | URL·양식 키 정규화 | functional-tests.md | 01~24 | 핵심 |
| `FORM` | 양식·로케일·관습 경고 | functional-tests.md | 01~16 | 핵심 |
| `FMT` | 표준 구조·어댑터·내보내기 | functional-tests.md | 01~14 | 핵심 |
| `MEM` | 레이어·kind·슬롯·출처 (`MEM-01`은 overview 10절) | functional-tests.md | 01~16 | 핵심 |
| `RCL` | recall | functional-tests.md | 01~20 | 핵심 |
| `LIB` | 내 라이브러리 | functional-tests.md | 01~16 | 핵심 |
| `SHR` | 공유·복사·라이선스 | functional-tests.md | 01~21 | 핵심 |
| `DISC` | 웹 검색 | functional-tests.md | 01~08 | 핵심 |
| `IMP` | 미리보기·가져오기·클립 | functional-tests.md | 01~20 | 핵심 |
| `VER` | 버전 (`VER-01`은 overview 10절) | functional-tests.md | 01~06 | 핵심 |
| `TPL` | 양식 흐름 (`TPL-01~03`은 overview 10절) | functional-tests.md | 01~08 | 핵심 |
| `DOC` | 문서 작성 (`DOC-01~02`는 overview 10절, functional-tests.md) | functional-tests.md(01~02), functional-document.md(03~12) | 01~12 | 핵심 + P3 |
| `PRIV` | 개인정보·동의·삭제 | functional-tests.md | 01~10 | 핵심 |
| `MCP` | MCP 계약 | functional-tests.md | 01~24 | 핵심 |
| `SEC` | 보안 시나리오 (`SEC-01~02`는 overview 10절, `SEC-A01`처럼 그룹 문자) | security-scenarios.md | 01~02, A01~A10, B01~B06, C01~C06, D01~D08, E01~E10, F01~F03, G01~G03, H01~H04, J01~J03 | 핵심 |
| `CLI` | CLI 시나리오 | tool-forms/cli-form.md | 01~33 | 핵심 |
| `MCPF` | MCP 호스트 시나리오 | tool-forms/mcp-form.md | 01~27 | 핵심 |
| `SNIP` | 지침 스니펫 | tool-forms/snippet-form.md | 01~04 | 핵심 |
| `SMK`, `BEH`, `HOST`, `CUST` | 호스트 스모크·행동·호스트 여정·고객 경로 | host-smoke.md | SMK 01~16, BEH 01~10, HOST 01~12, CUST 01~06 | 핵심 |
| `FLOW` | 유저 플로우 | user-flows.md | 01~12 | 핵심 |
| `HARN` | 테스트 하네스 자체 검증 | harness-verification.md(01~16), wam-port-completion-v1.md(17) | 01~17 | 핵심 |
| `PORT` | WAM 전체 이식·제품/더블/호스트 검증 범위 | wam-port-completion-v1.md | 01~08 | 포팅 보완 |
| `WI` | 실제 URL 검색·preview/import·출처·소유 Arise 탭 클립 | web-memory-v1.md | 01~24 | intake v1 |
| `FAIL` | 교차 계층 실패·복구 | failure-matrix.md | 01~24 | 핵심 |
| `API` `DB` | HTTP API·저장 | functional-api.md | API 01~40, DB 01~27 | P1 |
| `DEDUP` `LINK` `CACHE` | 중복·기기 연결·캐시 | functional-connect.md | DEDUP 01~14, LINK 01~11, CACHE 01~11 | P1 |
| `INST` `DIAG` | 설치·진단 | functional-install.md | INST 01~30, DIAG 01~08 | P1 |
| `GK` `SCORE` | 게시 검수·점수 | functional-review.md | GK 01~30, SCORE 01~16 | P2 |
| `CUR` | 검수 에이전트 | functional-curator.md | CUR 01~16 | P2 |
| `QUE` `MODEL` `OUTAGE` | 큐·모델·장애 | functional-models.md | QUE 01~20, MODEL 01~14, OUTAGE 01~12 | P2 |
| `WEB` | 웹 화면 | functional-web.md | WEB 01~30 | P3 |
| `MYPAGE` `PROFILE` `ADMIN` | 내 페이지·프로필·관리 | functional-account.md | MYPAGE 01~16, PROFILE 01~08, ADMIN 01~16 | P3 |
| `EMAIL` `RL` `USAGE` | 이메일 인증·요청 제한·사용량 | functional-ops.md | EMAIL 01~10, RL 01~12, USAGE 01~06 | P3 |
| `PERF` `REL` | 성능·출시 게이트 | functional-release.md | PERF 01~12, REL 01~10 | P3 |

## 명세 현황

| 파일 | 영역 | 상태 |
|---|---|---|
| [`overview.md`](overview.md) | 제품 개요(상위 문서, 별도 편집 중) | v0.3 |
| [`runtime-v1.md`](runtime-v1.md) | 구현 단계 계약(Rust·Axum·SQLite·Svelte의 로컬 부분집합) | 구현 |
| [`web-memory-v1.md`](web-memory-v1.md) | 실제 URL 검색·미리보기·비공개 가져오기·서명된 소유 Arise 탭 클립 (`WI`) | 로컬 구현; 결과는 `docs/test/web-memory-v1.md` |
| [`wam-port-completion-v1.md`](wam-port-completion-v1.md) | 원본 93개 처분·CLI/MCP·Arise·하네스 검증 (`PORT`, `HARN-17`) | 계약·검사 구현; 결과는 `docs/test/wam-port-completion-v1.md` |
| [`accounts-community-v1.md`](accounts-community-v1.md) | 이메일 계정·마이페이지·공개 기여·검수·철회 | 구현·운영 검증 |
| [`accounts-operations-v1.md`](accounts-operations-v1.md) | Resend/Cloudflare·자격 증명·서버 운영 | 운영 검증 |
| [`member-leaderboard-v1.md`](member-leaderboard-v1.md) | 로그인·가입·선택 공개 프로필·기여20점·내/공개 순위 (`LB`) | 구현·회귀 검증 |
| [`landing-email-links-v1.md`](landing-email-links-v1.md) | 영문 랜딩·이메일 링크 확인·연결 안내 | 구현·운영 검증 |
| [`landing-bilingual-v1.md`](landing-bilingual-v1.md) | 영문 기본 랜딩·한국어 번역·언어 전환 (`LANG`) | 구현·운영 확인 |
| [`template-library.md`](template-library.md) | 초기 양식 시드 카탈로그(별도 작업) | 별도 작업 |
| [`core.md`](core.md) | URL·양식 키 정규화, 오류 코드, 한도 (`CORE`) | 설계 초안 |
| [`form.md`](form.md) | 양식 객체, 국가·provider 변형, 관습 경고 (`FORM`) | 설계 초안(신규) |
| [`formats.md`](formats.md) | 표준 구조, provider 어댑터, 내보내기 (`FMT`) | 설계 초안(신규) |
| [`memory.md`](memory.md) | L0/L1/L2, kind, 슬롯, 출처·복사 정책 (`MEM`, `VER`) | 설계 초안 |
| [`recall.md`](recall.md) | URL + 양식 recall, 순위, 호출 시점 (`RCL`) | 설계 초안 |
| [`library.md`](library.md) | 내 메모리 저장·수정·삭제·내보내기 (`LIB`) | 설계 초안(신규) |
| [`sharing.md`](sharing.md) | 게시, 타인 메모리 검색·미리보기·복사, 라이선스 (`SHR`, `TPL`) | 설계 초안(신규) |
| [`web-import.md`](web-import.md) | 웹 검색·미리보기·가져오기·클립, SSRF 방어 (`DISC`, `IMP`) | 설계 초안(신규) |
| [`mcp.md`](mcp.md) | MCP 도구 12개, 인증 티어, 호스트 연결 (`MCP`, `MCPF`) | 설계 초안 |
| [`cli.md`](cli.md) | `dmem` 명령 표면, 종료 코드 0~7 (`CLI`) | 설계 초안 |
| [`privacy.md`](privacy.md) | 로컬 우선, 동의, 개인 정보, 삭제 (`PRIV`) | 설계 초안 |
| `api.md`, `database.md`, `dedup.md`, `link.md`, `install.md`, `client-cache.md`, `diagnostics.md` | 서버·저장·연결·설치·캐시 (P1) | 설계 작성; 전체 목표 계약 |
| `gatekeeper.md`, `curator.md`, `model.md`, `queue.md`, `provider-outage.md`, `score.md` | 검수·모델·큐·점수 (P2) | 설계 작성; 전체 목표 계약 |
| `web.md`, `document.md`, `my-page.md`, `profile.md`, `admin.md`, `email-auth.md`, `rate-limits.md`, `usage-analytics.md`, `search-performance.md`, `release.md` | 웹·편집기·운영 (P3) | 설계 작성; 구현 단계 명세와 구분 |
