# 테스트 전략 (문서 우선)

상태: 케이스 정의와 하네스 구현 진행 중. 이 저장소에는 [`runtime-v1.md`](../spec/runtime-v1.md)에 적힌 로컬 제품 부분집합과 이를 검증하는 제품 테스트가 있으며, 전체 목표 계약은 아직 범위 밖이다. 참조 구현인 **테스트 더블**은 제품이 아니다. 실행 결과는 `DMEM_TARGET=double|product`와 `DMEM_PROFILE`로 구분한다. WAM `docs/test/README.md`의 원칙·계층·증거 규약을 문서 메모리 도메인으로 옮겼다([포팅 지도](../design/wam-port-map.md)).

| 문서 | 내용 |
|---|---|
| 이 문서 | 원칙, 계층·프로필, 환경, 증거 규약, 기능→테스트 추적표, Runtime v1 대응, 게이트, 수치 기준 |
| [`fixtures.md`](fixtures.md) | 합성 입력의 단일 정의(신원, 라이브러리 `RCL-LIB`, 공유 카탈로그 `SHR-CAT`, 웹 fixture, 파일 빌더, 센티널) |
| [`functional-tests.md`](functional-tests.md) | 핵심 케이스: `CORE` `FORM` `FMT` `MEM` `RCL` `LIB` `SHR` `DISC` `IMP` `VER` `TPL` `DOC-01~02` `PRIV` `MCP` |
| [`functional-api.md`](functional-api.md), [`functional-connect.md`](functional-connect.md), [`functional-install.md`](functional-install.md) | 플랫폼 케이스: `API` `DB` / `DEDUP` `LINK` `CACHE` / `INST` `DIAG` |
| [`functional-review.md`](functional-review.md), [`functional-curator.md`](functional-curator.md), [`functional-models.md`](functional-models.md) | 검수·모델: `GK` `SCORE` / `CUR` / `QUE` `MODEL` `OUTAGE` |
| [`functional-web.md`](functional-web.md), [`functional-account.md`](functional-account.md), [`functional-ops.md`](functional-ops.md), [`functional-release.md`](functional-release.md) | 웹·계정·운영: `WEB` `DOC-03~` / `MYPAGE` `PROFILE` `ADMIN` / `EMAIL` `RL` `USAGE` / `PERF` `REL` |
| [`security-scenarios.md`](security-scenarios.md) | 공격 서술과 방어 기대(`SEC`), 센티널 sink 스윕 |
| [`harness-verification.md`](harness-verification.md) | 하네스 자체 검증(`HARN`): 변이 검사, oracle 정확도, 정리, 추적 |
| [`local-smoke.md`](local-smoke.md), [`host-smoke.md`](host-smoke.md), [`hosts/`](hosts/README.md) | 호스트 없는 로컬 스모크, 호스트 스모크(`SMK` `BEH` `HOST` `CUST`), 호스트별 기록(Arise 중심) |
| [`tool-forms/`](tool-forms/README.md) | CLI·MCP·스니펫 형태 시나리오(`CLI` `MCPF` `SNIP`) |
| [`user-flows.md`](user-flows.md), [`failure-matrix.md`](failure-matrix.md) | 사용자 여정(`FLOW`), 교차 계층 장애·복구(`FAIL`) |
| [`environment.md`](environment.md) | 이 머신에서 확인한 도구와 실행 결과 |
| [`../../tests/README.md`](../../tests/README.md) | 테스트 코드 구성, 대상 어댑터, 하네스 API, 변이 목록 |

## 1. 원칙

1. **합의된 ID 먼저**: 기능 구현과 테스트 코드는 해당 ID가 문서에 있어야 시작한다. 코드는 새 ID를 만들지 않는다(`HARN-10`).
2. **합성 값만**: 키·개인 정보·계정·문서·사이트는 전부 가짜(센티널)다. 실제 값을 테스트 데이터로 쓰지 않는다.
3. **격리**: 일회용 `HOME`·`XDG_*`·`TMPDIR`·`DMEM_HOME`, loopback fixture 서버, 임의 빈 포트. 사용자의 실제 프로필·설정·탭·계정을 건드리지 않는다.
4. **증거 기반 합격**: "대상이 성공했다고 말함"은 증거가 아니다. 파일 시스템, fixture 요청 로그, 센티널 스캔 같은 **독립 oracle**로 판정한다.
5. **보안은 0 허용**: 센티널 유출, 사설 주소 요청, 비공개 노출은 한 건이라도 실패다.
6. **블랙박스·구현 독립**: 테스트는 CLI·stdio MCP·HTTP·브라우저로만 대상을 다룬다. 구현 언어를 가정하지 않는다.
7. **더블은 제품이 아니다**: 더블 통과는 "테스트가 계약대로 쓰였다"는 근거이고, 변이 검출은 "테스트가 결함에 반응한다"는 근거다. 제품 합격은 제품에 같은 케이스를 돌려 얻는다.
8. **정리**: 테스트가 만든 프로세스·탭·파일·포트만 정리한다. 남의 것(실행 중인 사용자 Arise 포함)은 건드리지 않는다.
9. **조용한 누락 금지**: 건너뛴 케이스는 사유를 남긴다. 정의된 ID가 구현도 `coverage.json` 사유도 없으면 실패다.

## 2. 테스트 계층과 적용 단계(프로필)

| 계층 | 범위 | 도구 | 실행 주체 |
|---|---|---|---|
| L0 단위 | URL·양식 정규화, 순위, scrub, 어댑터 | 제품 언어의 단위 테스트 | 제품 개발. 블랙박스 하네스는 `SKIP(L0)` |
| L1 통합 | API 라우터 + 저장소(SQLite, 후속 PostgreSQL) | 제품 통합 테스트 | 제품 개발 |
| L2 계약 | CLI·stdio MCP의 입력·출력·종료 코드·스키마 | **이 저장소의 하네스**(`tests/smoke/`) | 더블과 제품 |
| L3 웹 E2E | 라이브러리·미리보기·복사·편집기·내보내기 화면 | Playwright 또는 Arise browser MCP | 제품 개발, `functional-web.md` |
| L4 호스트 스모크 | 실제 호스트(Arise 우선)에서 설치→호출→정리 | `tests/smoke/arise_smoke.py`, 수동 체크리스트 | 릴리스 전 |
| L5 보안 | 공격 시나리오, 센티널 sink 스윕 | 하네스 + 전용 스캐너 | 매 PR(핵심) |
| L6 성능 | 규모별 recall·검색·가져오기 | 후속(`functional-release.md` PERF) | 주간 |

**적용 단계**(케이스 표의 "단계" 열)는 구현 범위와 케이스를 연결한다. 범위 밖 케이스는 조용히 건너뛰지 않고 `SKIP(profile)` + 사유로 보고한다.

| 값 | 의미 | `runtime-v1` 대상 | `full` 대상 |
|---|---|---|---|
| `R1` | [`runtime-v1.md`](../spec/runtime-v1.md) 단계 이상에서 요구 | 실행 | 실행 |
| `F` | 전체 목표 계약(recall 확장, 공유·게시, 웹 가져오기, 클립 등) | `SKIP(profile)` | 실행 |
| `L0` | 제품 내부 단위 테스트가 확인 | `SKIP(L0)` | `SKIP(L0)` |

## 3. 환경과 fixture

| 이름 | 위치 | 설명 |
|---|---|---|
| 대상 어댑터 | `tests/lib/dmtest/target.py` | `DMEM_TARGET=double\|product`, `DMEM_BIN`, `DMEM_MCP_BIN`, `DMEM_SERVER_CMD`, `DMEM_PROFILE` |
| 테스트 더블 | `tests/env/dmem-double/` | 계약의 참조 구현(CLI·stdio MCP·서버 모드 모사). 제품이 아니다 |
| fixture 사이트 | `tests/env/fixture-sites/` | provider 모양 문서, 국가별 변형, 라이선스 변형, 악성 페이지, `fixture` 검색 provider |
| 파일 빌더 | `tests/lib/dmtest/builders.py` | DOCX·PPTX·PDF·악성 파일을 실행 때 생성(결정적) |
| 센티널 | `tests/sentinels.json` | 합성 비밀·개인 정보·URL 조각·본문 표식(한 곳에서만 정의) |
| 호스트 프로필 | 일회용 디렉터리 | 호스트별 `HOME`·설정(실제 설정은 건드리지 않음) |
| Arise | 설치된 `/Applications/Arise.app`의 공개 stdio MCP | 세션 소유 탭만 사용([`../design/browser-host-integration.md`](../design/browser-host-integration.md) 4절) |

## 4. 센티널 규약

센티널은 실제 서비스에서 유효하지 않은 합성 값이며 형태만 같다. 정의와 가족은 [`fixtures.md`](fixtures.md) 6절이다. 판정은 값 자체를 출력하지 않는 스캐너가 하고(출력에는 센티널 id), 리터럴·JSON 이스케이프·퍼센트 인코딩·Base64·16진 변형을 검색한다. sink 8종과 방법은 [`security-scenarios.md`](security-scenarios.md)다. 주민·결제·계좌 형식은 검증값이 무효이거나 시험용으로 알려진 번호만 쓴다.

## 5. 증거 규약

각 실행은 `target/e2e-logs/<suite>/<run-id>/`에 남긴다(git 무시).

| 파일 | 내용 |
|---|---|
| `meta.json` | 커밋(있으면), 대상(`double`/`product`)·프로필, OS, Python·Arise 버전, 시작·종료 시각 |
| `cases.jsonl` | 케이스 ID, 판정(`PASS`/`FAIL`/`SKIP`), 사유, 근거 경로(센티널 값 없음) |
| `trace.jsonl` | 구조화 이벤트. 완료는 명시적 Done/Failed 이벤트로 판정(로그 침묵은 완료 증거 아님) |
| `sinks/` | 유출 검색에 쓴 sink 스냅샷 |
| `summary.md` | 사람이 읽는 요약: 통과·실패·건너뜀(사유), 변이 검출 결과 |

통과한 대표 이미지(Arise 스크린샷)는 사람이 열어서 확인한다.

## 6. 기능 → 테스트 추적표

| 기능 | 기능 테스트 | 스모크·호스트 | 보안 |
|---|---|---|---|
| URL·양식 키 정규화, provider 감지, 능력 URL | CORE-01~24, FORM-01~16 | SMK-03 | SEC-A05, SEC-E |
| 표준 구조·가져오기·내보내기 | FMT-01~14, LIB-12 | SMK-07 | SEC-B05, SEC-C03~04 |
| 메모리 레이어·kind·슬롯·출처·버전 | MEM-01~16, VER-01~06 | SMK-05 | SEC-A01, SEC-B03 |
| URL + 양식 recall | RCL-01~20 | SMK-03~06, BEH-01~06 | SEC-A05, SEC-D |
| 내 메모리 저장·가져오기 | LIB-01~16, TPL-01 | SMK-07 | SEC-A01, SEC-A03 |
| 다른 사람 메모리 찾기·복사·게시·라이선스 | SHR-01~21, TPL-02~08 | SMK-08, SMK-11, BEH-07~08 | SEC-C01, SEC-D |
| 웹 검색·미리보기·가져오기·클립 | DISC-01~08, IMP-01~20 | SMK-09~10, BEH-09, HOST-09 | SEC-E, SEC-B02 |
| 개인정보·동의·삭제 | PRIV-01~10 | SMK-11, SMK-16 | SEC-G, SEC-A |
| MCP 계약·호스트 연결 | MCP-01~24, MCPF-01~27 | SMK-02, HOST-01~12, CUST-01~06 | SEC-H |
| CLI 계약 | CLI-01~33, SNIP-01~04 | SMK-01, SMK-13 | SEC-F, SEC-H02 |
| 서버 API·저장·연결·설치·캐시 | `functional-api.md`, `-connect.md`, `-install.md` | SMK-12~13, SMK-15 | SEC-D06, SEC-F |
| 게시 검수·점수·모델·큐 | `functional-review.md`, `-curator.md`, `-models.md` | — | SEC-C |
| 웹 화면·편집기·계정·운영·성능·출시 | `functional-web.md`, `-account.md`, `-ops.md`, `-release.md`, DOC-01~02 | — | SEC-B05, SEC-J |
| 교차 계층 장애·복구, 사용자 여정 | FAIL-01~24, FLOW-01~12 | HOST-12 | SEC-E, SEC-J |

## 7. Runtime v1(다른 작업)과의 대응과 차이

[`runtime-v1.md`](../spec/runtime-v1.md)는 이 명세 세트의 **부분집합**을 Rust·Axum·SQLite·Svelte로 구현하는 별도 작업이다. 그쪽 수용 케이스 `RT-01~12`는 이 문서의 ID로 다음과 같이 대응한다(블랙박스 하네스는 대상이 CLI·MCP를 노출한 뒤 `R1` 케이스를 실행한다).

| RT | 내용 | 대응 ID |
|---|---|---|
| RT-01 | Google Docs ID·resourcekey·query가 같은 canonical, 원본 ID 없음 | CORE-04, CORE-09, CORE-15, CORE-19 |
| RT-02 | http·userinfo·IP·localhost·이메일 경로 거부, 입력 echo 없음 | CORE-02, CORE-03, CORE-07, CORE-13, CORE-23 |
| RT-03 | 이력서+`KO_kr`, 履歴書, `google_slides`+resume | FORM-02, FORM-03, FORM-05, FORM-10, FORM-15 |
| RT-04 | 공개 회의록 양식 복사(private 복사, 원본 정보 보존) | SHR-11, SHR-20, TPL-02 |
| RT-05 | A의 비공개 자료를 B가 접근 | SHR-16, SEC-01, SEC-D01 |
| RT-06 | Markdown·DOCX 표·PPTX 슬라이드 추출, 체크섬, 빈·잘못된·대형 거부 | FMT-05, FMT-08, LIB-02, LIB-14, LIB-15 |
| RT-07 | 양식만 선택해 초안, 자료 추가, 확인 필요 | DOC-01, DOC-02, MEM-01, TPL-01 |
| RT-08 | `base_version` 저장 2회, 충돌, DB 재열기 | LIB-05, LIB-06, VER-02, VER-03 |
| RT-09 | `<script>`·`&` 포함 문서의 HTML·Office export 안전 | FMT-03, FMT-04, FMT-14 |
| RT-10 | API 연결 실패·401·빈 검색·저장 충돌의 웹 복구 | functional-web.md(WEB), FAIL-01~24 |
| RT-11 | MCP initialize/list/call, 잘못된 JSON·unknown tool, stdout 순수성 | MCP-01~08 |
| RT-12 | 웹에서 양식 검색→복사→자료 업로드→문서 작성→저장→export | FLOW-01, FLOW-02 |

### 발견한 명세↔구현 차이 (해결 대기)

| # | 항목 | 명세 | 현재 구현(`crates/`, 2026-11-09 시점) | 조치 |
|---|---|---|---|---|
| 1 | 경로 고정 단어 대소문자 | 소문자로 바꾼다(`core.md` 2절 5.8) | `normalization.rs`는 대소문자를 유지 | 구현을 명세에 맞추거나 명세를 바꿀지 결정. `CORE-06`이 기준 |
| 2 | 레코드 종류 | `template`·`reference`·`style_rule` | DB `template`·`source`·`document` | `source`↔`reference` 대응(문서화됨). 공개 CLI·MCP의 `kind` 이름은 이 명세가 기준 |
| 3 | 가시성 | `private`·`team`·`public` | `Private`·`Public` | team은 다중 사용자 단계(문서화됨) |
| 4 | CLI·MCP 표면 | `cli.md`·`mcp.md`·`contracts/mcp-tools.v1.json` | `dmem-cli`·`dmem-mcp`는 매니페스트만 있음 | 구현 시 이 명세를 따르거나 차이를 이 표에 기록 |
| 5 | recall·게시·웹 가져오기·클립 | 전체 계약 | runtime-v1 범위 밖 | 프로필 `runtime-v1`에서 `F` 케이스는 `SKIP(profile)` |

## 8. 마일스톤 게이트

| 마일스톤 | 통과해야 하는 것 |
|---|---|
| M0 계약 | 명세·스키마·케이스 ID 합의, `HARN-10`~`HARN-12`, 더블 전체 통과, 변이 18개 전부 검출 |
| M1 코어·로컬 라이브러리 | `CORE` `FORM` `FMT` `MEM` `LIB` `VER` 전부(`R1`), SEC-A·B 핵심(센티널 0) |
| M2 recall·공유 | `RCL` `SHR` `TPL` 전부, SEC-D, `MCP-01~23`·`CLI` 계약, 서버 모드 |
| M3 웹 가져오기·클립 | `DISC` `IMP` 전부, SEC-E(SSRF) 전부 0, Arise 스모크(SMK-09~10) |
| M4 호스트 | Arise 포함 최소 2개 호스트의 SMK 필수 항목과 BEH-04, CUST-01~06 |
| M5 운영 | 검수·점수·웹·성능·출시 게이트(`functional-*.md`), 보안 시나리오 전체 |

## 9. 수치 기준 (초안, 측정 후 조정)

| 항목 | 기준 |
|---|---|
| 센티널 유출, 사설 주소 요청, 비공개 노출 | 0건 |
| recall 힌트 | ≤3개, 힌트당 ≤400 est tokens, `tools/list`+`instructions` ≤12,000 bytes |
| 로컬 `recall`(라이브러리 1,000개) | p95 ≤100 ms(프로세스 시작 제외) |
| 서버 `recall` | loopback 왕복 p95 ≤500 ms |
| 가져오기 | 본문 ≤5 MiB, 전체 ≤10초, 리다이렉트 ≤3 |
| 변이 검출 | 18/18(깨끗한 더블 통과 포함) |
| 호스트 자발적 recall 호출률 | **측정값**(합격 조건 아님) |

## 10. 열린 질문

1. `runtime-v1`의 CLI·MCP 이름·입력이 확정되면 차이표(7절)를 닫고 `R1` 케이스를 제품에 연결한다.
2. Claude Code·Codex의 `dmem-mcp` 등록 명령과 환경 변수 상속은 해당 호스트의 현재 문서로 확인해야 한다(WAM 승계 사실).
3. 라이선스 어휘·복사 정책의 법적 검토.
4. PDF·HWP 어댑터의 테스트 범위.
