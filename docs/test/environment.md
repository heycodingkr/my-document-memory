# 테스트 환경 (ENV)

상태: 실행 기록. 아래 수치는 모두 2026-11-09에 이 저장소에서 직접 실행해 얻은 값이고, 실행하지 않은 것은 "미실행"이라고 적었다. 1~4절은 초기 **테스트 더블**(`tests/env/dmem-double`) 실행 기록이며, 최신 제품·하네스 검증은 6절과 [`wam-port-completion-v1.md`](wam-port-completion-v1.md)에 있다. 더블이 통과한다는 사실은 "테스트가 계약대로 쓰였고 실제 결함에 반응한다"는 근거이지 "제품이 맞다"는 근거가 아니다([`harness-verification.md`](harness-verification.md)).

## 1. 이 실행의 환경

| 항목 | 값 |
|---|---|
| 운영체제 | macOS 27.0 (Darwin 27.0.0, arm64) |
| 언어 | Python 3.14.7, 표준 라이브러리만(설치 단계 없음). `timeout` 명령이 없어 문서의 예시는 `perl -e 'alarm N; exec @ARGV'`를 쓴다 |
| 네트워크 | 계약·스모크 전량이 loopback(`127.0.0.1`)과 일회용 디렉터리만 쓴다. 외부 요청 0건(fixture 서버 요청 로그와 `SEC-A04`의 `remote_requests` sink가 증거) |
| 브라우저 | Arise 0.1.77(`/Applications/Arise.app`), 공개 stdio MCP(`agent_browser --mcp-server`) 도구 62개. 환경 스모크와 [intake v1 실제 소유 탭·웹 입력](web-memory-v1.md)을 별도 실행 |
| 호스트 앱 | Claude Code·Codex는 **미실행**([`hosts/README.md`](hosts/README.md)) |

## 2. 실행과 측정값

| 명령 | 결과 | 걸린 시간 |
|---|---|---|
| `python3 -B -m unittest discover -s tests/lib/selftest -p "test_*.py"` | 131개 통과(HARN-01·03·04·05·07·08·09·12·14·15·16) | 약 25초 |
| `python3 -B tests/smoke/run_all.py --suite all` (더블, `full` 프로필) | 238개 중 **235 통과, 0 실패, 3 건너뜀**. 건너뜀은 `IMP-19`(Arise 어댑터 필요)·`PRIV-09`(계정 삭제는 웹·계정 기능)·`RCL-20`(클라이언트 캐시·중지할 서버 없음)이며 모두 사유가 증거에 남는다 | 케이스 합 182초(가장 긴 것 `MCP-08` 15초, `IMP-20` 14초, `IMP-14` 10초) |
| `python3 -B tests/smoke/run_all.py --suite smoke` | 14개 통과(`SMK-01~05·07~09·11~14·16`, `CLI-04`) | 약 40초 |
| `python3 -B tests/env/mutation_check.py` | 18개 변이 **전부 검출**, 깨끗한 더블 대조군 통과 | 약 70초 |
| `PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace` | 238개 구현, R1·F 행 203/203이 구현 또는 사유와 함께 `coverage.json`에 있음 | 1초 미만 |
| `PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all` | 명세가 인용한 모든 테스트 ID가 정의되어 있음 | 1초 미만 |
| `python3 -B tests/smoke/arise_smoke.py` | 21/21(HARN-05·06, 증거 `target/e2e-logs/arise/20261109-101257-0323/`). 이 문서를 마무리한 뒤에는 다시 돌리지 않았다 | — |

영역별 케이스 수(계약+스모크, `--suite all` 한 번): CORE 24, FORM 16, FMT 14, MEM 15, RCL 18+1건너뜀, LIB 16, SHR 21, DISC 8, IMP 19+1건너뜀, VER 6, TPL 8, PRIV 9+1건너뜀, MCP 23, CLI 24, SEC 1, SMK 13. `MEM-10`·`MCP-24`는 `L0`(제품 단위 시험)이라 이 하네스가 건너뛴다.

재현성(HARN-13): 같은 238개 집합을 두 번 돌려 판정이 모두 같았다(차이 0, 증거 `target/e2e-logs/contract/20261109-120333-8264`와 `…-120635-1959`). 하네스 자체 검사는 전체 스위트와 동시에 돌릴 때 오류 1건이 한 번 났고 재현하지 못했다([`harness-verification.md`](harness-verification.md) HARN-13).

## 3. 격리

- 케이스마다 새 세계를 만든다: 일회용 `HOME`·`XDG_*`·`TMPDIR`(`/tmp/dmem-*`), 신원마다 따로 둔 `DMEM_HOME`, 서버 모드면 신원들이 공유하는 서버 상태 파일 하나. 사용자의 실제 설정·문서·계정은 읽지도 쓰지도 않는다.
- fixture 웹 서버는 임의의 빈 loopback 포트에 한 번 띄우고 케이스마다 요청 로그를 비운다. 로그에는 경로·쿼리 유무·헤더 **이름**만 남고 값은 남기지 않는다.
- 하네스가 띄운 자식 프로세스는 자기 프로세스 그룹으로만 종료한다. 케이스는 `DMEM_CASE_TIMEOUT`(기본 90초) 안에 끝나야 하고, 넘기면 `FAIL(timeout)`이다(`HARN-15`).
- 센티널은 합성 값이다. 출력에는 sentinel id만 나오고 값은 나오지 않는다.

## 4. Arise 환경에서 확인한 것

[`hosts/arise.md`](hosts/arise.md)에 근거와 함께 적었다. 요약: 세션 소유 백그라운드 탭(lease 120초)만 열고 닫으며 사용자·다른 세션의 탭은 건드리지 않는다. 같은 앱을 다른 에이전트 세션이 동시에 쓴다(이 실행 중에도 다른 세션 5개가 탭을 쥐고 있었다). 활성 적대 페이지의 JS dialog는 `browser_dialog`로 명시 응답해야 재개된다. `innerText`는 크기 0·배경색 동일 텍스트를 내보내므로 클립 살균이 필요하다. 이 실행 말미에 `browser_tabs`로 확인한 결과 이 작업 세션이 소유한 탭은 없다.

## 5. 이 환경이 보증하지 않는 것

- **전체 목표 계약**: 실제 `dmem`·`dmem-mcp`·`dmem-server`가 있으며 전용 제품 스모크가 있다. 제품의 `document_*`와 더블의 `doc_memory_*`는 서로 다른 계약이다. 전체 더블 스위트의 `DMEM_TARGET=product` 지정만으로 이 제품에 연결되지 않는다. `runtime-v1` 프로필은 `단계 F` 케이스를 사유와 함께 건너뛴다.
- **호스트 앱 행동**(`SMK-06`, `BEH-*`, `RCL-15`)과 Arise 어댑터(`IMP-19`, `SMK-10`).
- **Google 웹 UI의 내보내기 URL·`/copy` 링크 형태**: 미검증이다([`../spec/formats.md`](../spec/formats.md) 3절). fixture는 이를 모사한 것이다.
- **실제 서버·네트워크 장애**: 더블은 `DMEM_TEST_SERVER_DOWN`과 fixture의 `429`·`500`·지연으로 모사할 뿐이다.
- **클라이언트 캐시**(`RCL-20`)·**기기 연결**(`CLI-01~03`)·**계정 삭제**(`PRIV-09`): 더블에 없다.

## 6. 포팅 보완 재검증 (2026-11-09)

| 대상 | 실행 | 결과 / 증거 |
|---|---|---|
| 원본 전체 목록 | `dmtest.porttrace --require-upstream` | Markdown 93개(명세 31·테스트 62), 적응 72·제외 21, 누락 0 |
| 하네스 | unittest selftest | **138/138 통과**(기존 131 + 포팅 검사 7), 26.192초 |
| 더블 / full | `run_all.py --suite all` | **235 PASS·0 FAIL·3 SKIP**, `target/e2e-logs/contract/20261109-122609-5572/` |
| 더블 / 변이 | `mutation_check.py --repeat 2` | 지정 대조군 25개 ×2 모두 통과·판정 차이 0, **18/18 검출**, `target/e2e-logs/mutation/20261109-123159/` |
| Arise 환경 | `arise_smoke.py` | **21/21 통과**, 설치본 0.1.77·도구 62개, `target/e2e-logs/arise/20261109-122711-6914/` |
| Rust 실제 제품 | `cargo test --workspace`; `cargo build --workspace --examples` | **92개 통과·빌드 성공**, `target/e2e-logs/wam-port/20261109-123328/` |
| 실제 CLI/MCP·HTTP | `runtime-v1.py`; `recall-v1.py`; `community-v1.py` | 세 스모크 종료 0; recall **44/44**, 같은 증거 디렉터리에 명령별 로그·바이너리 hash |

Arise의 `shots/resume-ko.png`는 이미지 도구로 직접 열어 제목·인적사항·경력·학력·기술·표가 보임을 확인했다. 사용자 탭 id·URL·제목 전후 동일, 자기 탭만 닫힘. 제품의 현재 탭 clip·허브 자동 호출을 통과시킨 결과는 아니다. 초기 Rust 실행에서 관리자 이메일 테스트 3개가 실패해 #402에 기록했으며, 공유 작업이 반영된 후 위 재실행은 모두 통과했다. 운영 배포는 하지 않았다.
