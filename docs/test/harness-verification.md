# 테스트 하네스 자체 검증 (HARN)

상태: 케이스 정의와 실행 상태 표. 실험이 신뢰되려면 **하네스가 먼저 검증되어야 한다.** 이 문서는 하네스(`tests/lib/dmtest`, `tests/env`, `tests/smoke`)의 검증 케이스를 정의한다. 제품 기능 테스트가 아니다. WAM `harness-verification.md`(HARN-01~12)의 정확도·정리·재현성 검사를 승계하고, 이 프로젝트에서는 **테스트 더블에 대한 변이 검사**(테스트가 실제 결함을 잡는가)를 추가했다.

테스트 더블(`tests/env/dmem-double`)은 계약을 실행 가능하게 만든 참조 구현이며 **제품이 아니다.** 더블이 통과한다는 사실은 "테스트가 계약대로 쓰였다"는 근거이지 "제품이 맞다"는 근거가 아니다. 반대로 변이가 모두 검출된다는 사실은 "테스트가 실제 결함에 반응한다"는 근거다.

실행:

```
python3 -B -m unittest discover -s tests/lib/selftest -p "test_*.py"          # HARN-01,03,04,05,07,08,09,12,14,15,16 (브라우저·네트워크 없음)
python3 -B tests/smoke/run_all.py --target double                           # 깨끗한 더블 전체 통과(HARN-02 음성 대조, HARN-13은 두 번 비교)
python3 -B tests/env/mutation_check.py                                      # HARN-02, HARN-13
python3 -B tests/smoke/arise_smoke.py                                       # HARN-05, HARN-06 (설치된 Arise 필요)
PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all                    # HARN-11
PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace                         # HARN-10
PYTHONPATH=tests/lib python3 -B -m dmtest.porttrace --require-upstream     # HARN-17 (상위 WAM 원본 필요)
```

| ID | 대상 | 합격 기준 | 도구 | 상태 |
|---|---|---|---|---|
| HARN-01 | oracle 정확도(fixture 서버·스캐너·로그가 판정 근거로 맞는가) | 의도적으로 성공·실패를 만든 시나리오 ≥20건에서 판정과 사유가 100% 일치. oracle이 대상에 노출되지 않는다(대상은 fixture 로그를 읽지 못한다) | `selftest/test_fixture_http.py`, `test_sentinels.py`, `test_builders.py` | 2026-11-09 통과. `test_fixture_http`(8)·`test_sentinels`·`test_sweep`·`test_builders`로 의도적 성공·실패 시나리오 27건의 판정·사유 일치. 빌더 점검이 `evil-dde.docx`가 DDE 필드를 실제로는 담지 않던 결함을 찾아 고침. fixture 로그 위치는 대상 환경에 주지 않는다 |
| HARN-02 | 변이 민감도 | `tests/README.md`의 변이 18개 각각에서 **지정한 케이스가 실패**하고, 깨끗한 더블은 해당 케이스를 모두 통과한다(양성·음성 대조). 어느 변이도 검출되지 않으면 하네스 실패 | `env/mutation_check.py` | 2026-11-09 통과. 변이 **18/18 검출**, 깨끗한 더블 대조군 통과(증거 `target/e2e-logs/mutation/20261109-120045`). 첫 실행은 8/18이었고 약한 케이스 6건(CORE-19의 항진식, RCL-09·RCL-01의 동점 없음, SHR-16·IMP-09의 다른 방어층이 가림, 미작성 케이스)을 고친 뒤 18/18 |
| HARN-03 | JSON Schema 검증기 | 알려진 적합·부적합 인스턴스 ≥40건(지원하는 모든 키워드)에서 판정이 맞고, 오류 문자열에 인스턴스 값이 없다. `contracts/*.json`이 스키마로서 유효하다 | `selftest/test_schema.py` | 2026-11-09 통과. `test_schema` 50건이 지원 키워드 17개를 모두 쓰고 오류에 인스턴스 값이 없음. `contracts/*.json` 전부 파싱 |
| HARN-04 | 센티널 생성·스캔 | 같은 시드는 같은 말뭉치. 스캐너가 리터럴·JSON 이스케이프·퍼센트 인코딩·Base64·16진 변형을 찾고 값을 출력하지 않는다. 의도적으로 오염시킨 sink(센티널 1개)가 검출되고 깨끗한 sink는 0건(양성·음성 대조) | `selftest/test_sentinels.py` | 2026-11-09 통과. `test_sentinels`(결정적 생성·변형 5종·값 비출력·양성/음성 대조)와 `test_sweep`(8개 sink 각각에 심은 센티널 검출). 말뭉치 67개(`injection` 가족 추가) |
| HARN-05 | 격리와 정리 | 실행 뒤 하네스가 만든 프로세스·임시 디렉터리·포트 잔존 0. 남의 프로세스(실행 중인 사용자 Arise 포함)의 pid 집합이 전후 같다. `HOME`·`XDG_*`·`TMPDIR`가 일회용이다 | `selftest/test_procs.py`, `smoke/arise_smoke.py` | 2026-11-09 통과. `test_procs`(프로세스 그룹 종료, 일회용 환경)와 `arise_smoke` 정리 점검 5건. 남의 프로세스 pid 집합은 Arise 스모크가 전후 비교 |
| HARN-06 | Arise 환경 일치 | 세션 소유 탭만 열고 닫으며 사용자 탭 목록이 전후 같다. `browser_close`(전역)를 호출하지 않는다. fixture 페이지가 Arise에서 렌더링되고 지정한 landmark가 `browser_snapshot`/`browser_eval`로 읽힌다 | `smoke/arise_smoke.py` | 2026-11-09 통과(21/21, 증거 `target/e2e-logs/arise/20261109-101257-0323/`). 이 문서 마무리 뒤에는 다시 돌리지 않음 |
| HARN-07 | 증거 무결성 | 모든 실행이 `meta.json`, `cases.jsonl`, `summary.md`를 남기고, 건너뛴 케이스는 사유가 있다. `--strict`에서 범위 안 케이스의 `SKIP`은 실패다. 로그가 조용한 것을 완료로 보지 않는다(명시적 Done/Failed 이벤트). 판정(`expect`)을 한 번도 평가하지 않은 케이스는 `FAIL(vacuous)`다 | `selftest/test_runner.py` | 2026-11-09 통과. `test_runner`: 판정·증거 파일(meta·cases·summary)·건너뜀 사유·`--strict`·판정 0번 평가 케이스(`FAIL(vacuous)`) |
| HARN-08 | 프로필 게이트 | `DMEM_PROFILE=runtime-v1`이면 `단계 F` 케이스가 `SKIP(profile)`+사유로 보고되고 `R1`은 실행된다. `L0`는 `SKIP(L0)`다. 프로필 밖 케이스가 조용히 사라지지 않는다 | `selftest/test_runner.py` | 2026-11-09 통과. `test_runner` 프로필 게이트: `runtime-v1`에서 `F`는 `SKIP(profile)`+사유, `R1`은 실행, `L0`는 `SKIP(L0)`, 제품 대상의 `hooks` 케이스는 `SKIP(needs)` |
| HARN-09 | fixture 결정성 | 빌더가 같은 입력에 같은 bytes를 만든다. fixture 서버의 크기·지연·리다이렉트·헤더 동작이 `fixtures.md` 4절과 같다 | `selftest/test_builders.py`, `test_fixture_http.py` | 2026-11-09 통과. `test_builders`(같은 입력 같은 bytes, 악성 문서 구성 요소, 압축 폭탄 비율)와 `test_fixture_http` |
| HARN-10 | 문서↔코드 추적 | 코드가 쓰는 모든 케이스 ID가 `docs/test`에 정의되어 있고, 정의된 `R1`·`F` ID는 케이스로 구현되었거나 `coverage.json`에 사유와 함께 `skip`으로 있다. 둘 다 없는 ID는 실패 | `dmtest.codetrace` | 2026-11-09 통과. `dmtest.codetrace`: 238개 구현, R1·F 행 203/203이 구현 또는 사유와 함께 `tests/coverage.json`에 있음 |
| HARN-11 | 명세→테스트 추적 | 명세가 인용한 모든 테스트 ID가 `docs/test`에 정의되어 있다(`template-library.md`의 시드 카탈로그 번호는 제외) | `dmtest.doctrace --all` | 2026-11-09 통과. `dmtest.doctrace --all` 정의되지 않은 인용 0 |
| HARN-12 | 계약 정적 검사 | `mcp-tools.v1.json`의 도구 12개가 유일하고 `annotations`가 규칙(읽기·쓰기·파괴)과 일치하며 모든 스키마가 검증기로 해석된다. 서빙되는 `tools/list` 크기를 측정해 예산(12,000 bytes)과 비교. `doc_types`·`licenses` 어휘가 `form.md`·`sharing.md` 표와 일치 | `selftest/test_contracts.py` | 2026-11-09 통과. `test_contracts`: 도구 12개·annotations 규칙·모든 `$ref` 해석(**dangling ref 4건**을 찾아 고침: 케이스 하나가 MCP 서버를 멈추게 했다)·서빙되는 `tools/list`+instructions **11,103 bytes**(처음 12,565로 예산 초과였고 `status`의 `outputSchema`를 서빙하지 않기로 바꿈)·어휘 표 일치 |
| HARN-13 | 재현성 | 같은 케이스 집합을 두 번 실행해 판정이 같다(불안정 케이스 0). 시간 변동은 보고만 하고 합격 조건이 아니다 | `env/mutation_check.py --repeat 2` | 2026-11-09 통과. 전체 케이스 집합(238개)을 두 번 돌려 판정이 모두 같다(차이 0). 하네스 자체 검사에서 전체 스위트와 동시에 돌릴 때 오류 1건이 한 번 났으나 재현하지 못했다(단독 3회, CPU 부하 2회 모두 131/131) |
| HARN-14 | sink 수집 완전성 | 보안 케이스마다 `security-scenarios.md`의 8개 sink 목록이 모두 비어 있지 않게 수집된다. 누락·중복·경로 이탈·심볼릭 링크·스캔 오류가 있으면 실패 | `selftest/test_sentinels.py` | 2026-11-09 통과. `test_sweep`(sink마다 심은 센티널 검출, 비어 있는 sink 보고, 심볼릭 링크 불추적)와 `SEC-A04`(8개 sink 전부 수집, 센티널 0건) |
| HARN-15 | 멈춤 처리 | 응답하지 않는 자식(더블의 `hang` 변이 없이 `sleep` 스크립트)을 제한 시간에 프로세스 그룹째 종료하고 케이스를 `FAIL(timeout)`로 기록한다. 하네스가 멈추지 않는다 | `selftest/test_procs.py` | 2026-11-09 통과. `test_procs`(멈춘 자식을 제한 시간에 그룹째 종료)와 `test_runner`(멈춘 케이스 `FAIL(timeout)`, 하네스는 계속 진행). 이 규칙은 실제로 한 번 하네스를 멈추게 한 결함(계약의 dangling ref로 워커 스레드가 죽어 응답이 없음)에서 나왔다 |
| HARN-16 | 대상 어댑터 | 더블을 `DMEM_TARGET=product DMEM_BIN=… DMEM_MCP_BIN=…`로 지정해(제품 경로 흉내) 같은 케이스가 같은 판정을 낸다. 환경 변수 누락은 명확한 오류다 | `selftest/test_target.py` | 2026-11-09 통과. `test_target`: 제품 경로(절대 경로 래퍼로 더블 실행)에서 같은 케이스 5개가 같은 판정, 환경 변수 누락·상대 경로는 명확한 오류 |
| HARN-17 | WAM 포팅 목록 | 원본 누락·유령·중복·대상 누락·경로 이탈·빈 이유·잘못된 처분·빈 목록을 양성/음성 대조로 검출. 원본 없는 환경은 명시하며 require 모드는 실패 | `selftest/test_porttrace.py`, `dmtest.porttrace` | 케이스 원본은 [`wam-port-completion-v1.md`](wam-port-completion-v1.md). 검사기 부재 실패를 먼저 확인한 뒤 7개 자체 검사 통과; 실제 원본 93개(적응 72·제외 21)와 대조 통과 |

2026-11-09 포팅 보완 실행: 전체 더블 235 PASS·0 FAIL·3 SKIP, 지정 대조군 25개를 두 번 실행해 판정 동일, 변이 18/18 검출, 실제 Arise 환경 21/21 통과. 초기 기록과 별도의 최신 실행 증거·제품 테스트 결과는 [`wam-port-completion-v1.md`](wam-port-completion-v1.md)에 모았다. `HARN-17` 정의 행의 원본은 그 문서다.

## 운영 규칙

- 하네스가 검증을 통과하기 전의 측정값은 README·보고에 수치로 쓰지 않는다.
- 변이 목록은 [`../../tests/README.md`](../../tests/README.md)가 정의한다. 새 변이를 추가하면 지정 실패 케이스와 함께 이 문서에도 반영한다.
- 케이스 ID를 새로 만들지 않는다. 필요하면 문서를 먼저 고친다.
- 이 문서의 "상태" 열은 실행한 날짜와 결과 요약으로 갱신하고, 실행하지 않은 항목은 "미실행"으로 둔다([`environment.md`](environment.md)).
