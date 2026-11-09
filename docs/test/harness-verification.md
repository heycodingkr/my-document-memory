# 테스트 하네스 자체 검증 (HARN)

상태: 케이스 정의와 실행 상태 표. 실험이 신뢰되려면 **하네스가 먼저 검증되어야 한다.** 이 문서는 하네스(`tests/lib/dmtest`, `tests/env`, `tests/smoke`)의 검증 케이스를 정의한다. 제품 기능 테스트가 아니다. WAM `harness-verification.md`(HARN-01~12)의 정확도·정리·재현성 검사를 승계하고, 이 프로젝트에서는 **테스트 더블에 대한 변이 검사**(테스트가 실제 결함을 잡는가)를 추가했다.

테스트 더블(`tests/env/dmem-double`)은 계약을 실행 가능하게 만든 참조 구현이며 **제품이 아니다.** 더블이 통과한다는 사실은 "테스트가 계약대로 쓰였다"는 근거이지 "제품이 맞다"는 근거가 아니다. 반대로 변이가 모두 검출된다는 사실은 "테스트가 실제 결함에 반응한다"는 근거다.

실행:

```
python3 -B -m unittest discover -s tests/lib/selftest -t tests/lib -v       # HARN-03,04,09,12 (브라우저·네트워크 없음)
python3 -B tests/smoke/run_all.py --target double                           # 깨끗한 더블 전체 통과(HARN-02 음성 대조)
python3 -B tests/env/mutation_check.py                                      # HARN-02, HARN-13
python3 -B tests/smoke/arise_smoke.py                                       # HARN-05, HARN-06 (설치된 Arise 필요)
PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all                    # HARN-11
PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace                         # HARN-10
```

| ID | 대상 | 합격 기준 | 도구 | 상태 |
|---|---|---|---|---|
| HARN-01 | oracle 정확도(fixture 서버·스캐너·로그가 판정 근거로 맞는가) | 의도적으로 성공·실패를 만든 시나리오 ≥20건에서 판정과 사유가 100% 일치. oracle이 대상에 노출되지 않는다(대상은 fixture 로그를 읽지 못한다) | `selftest/test_fixture_http.py`, `test_sentinels.py`, `test_builders.py` | 미실행 |
| HARN-02 | 변이 민감도 | `tests/README.md`의 변이 18개 각각에서 **지정한 케이스가 실패**하고, 깨끗한 더블은 해당 케이스를 모두 통과한다(양성·음성 대조). 어느 변이도 검출되지 않으면 하네스 실패 | `env/mutation_check.py` | 미실행 |
| HARN-03 | JSON Schema 검증기 | 알려진 적합·부적합 인스턴스 ≥40건(지원하는 모든 키워드)에서 판정이 맞고, 오류 문자열에 인스턴스 값이 없다. `contracts/*.json`이 스키마로서 유효하다 | `selftest/test_schema.py` | 미실행 |
| HARN-04 | 센티널 생성·스캔 | 같은 시드는 같은 말뭉치. 스캐너가 리터럴·JSON 이스케이프·퍼센트 인코딩·Base64·16진 변형을 찾고 값을 출력하지 않는다. 의도적으로 오염시킨 sink(센티널 1개)가 검출되고 깨끗한 sink는 0건(양성·음성 대조) | `selftest/test_sentinels.py` | 미실행 |
| HARN-05 | 격리와 정리 | 실행 뒤 하네스가 만든 프로세스·임시 디렉터리·포트 잔존 0. 남의 프로세스(실행 중인 사용자 Arise 포함)의 pid 집합이 전후 같다. `HOME`·`XDG_*`·`TMPDIR`가 일회용이다 | `selftest/test_procs.py`, `smoke/arise_smoke.py` | 미실행 |
| HARN-06 | Arise 환경 일치 | 세션 소유 탭만 열고 닫으며 사용자 탭 목록이 전후 같다. `browser_close`(전역)를 호출하지 않는다. fixture 페이지가 Arise에서 렌더링되고 지정한 landmark가 `browser_snapshot`/`browser_eval`로 읽힌다 | `smoke/arise_smoke.py` | 미실행 |
| HARN-07 | 증거 무결성 | 모든 실행이 `meta.json`, `cases.jsonl`, `summary.md`를 남기고, 건너뛴 케이스는 사유가 있다. `--strict`에서 범위 안 케이스의 `SKIP`은 실패다. 로그가 조용한 것을 완료로 보지 않는다(명시적 Done/Failed 이벤트). 판정(`expect`)을 한 번도 평가하지 않은 케이스는 `FAIL(vacuous)`다 | `selftest/test_runner.py` | 미실행 |
| HARN-08 | 프로필 게이트 | `DMEM_PROFILE=runtime-v1`이면 `단계 F` 케이스가 `SKIP(profile)`+사유로 보고되고 `R1`은 실행된다. `L0`는 `SKIP(L0)`다. 프로필 밖 케이스가 조용히 사라지지 않는다 | `selftest/test_runner.py` | 미실행 |
| HARN-09 | fixture 결정성 | 빌더가 같은 입력에 같은 bytes를 만든다. fixture 서버의 크기·지연·리다이렉트·헤더 동작이 `fixtures.md` 4절과 같다 | `selftest/test_builders.py`, `test_fixture_http.py` | 미실행 |
| HARN-10 | 문서↔코드 추적 | 코드가 쓰는 모든 케이스 ID가 `docs/test`에 정의되어 있고, 정의된 `R1`·`F` ID는 케이스로 구현되었거나 `coverage.json`에 사유와 함께 `skip`으로 있다. 둘 다 없는 ID는 실패 | `dmtest.codetrace` | 미실행 |
| HARN-11 | 명세→테스트 추적 | 명세가 인용한 모든 테스트 ID가 `docs/test`에 정의되어 있다(`template-library.md`의 시드 카탈로그 번호는 제외) | `dmtest.doctrace --all` | 미실행 |
| HARN-12 | 계약 정적 검사 | `mcp-tools.v1.json`의 도구 12개가 유일하고 `annotations`가 규칙(읽기·쓰기·파괴)과 일치하며 모든 스키마가 검증기로 해석된다. 서빙되는 `tools/list` 크기를 측정해 예산(12,000 bytes)과 비교. `doc_types`·`licenses` 어휘가 `form.md`·`sharing.md` 표와 일치 | `selftest/test_contracts.py` | 미실행 |
| HARN-13 | 재현성 | 같은 케이스 집합을 두 번 실행해 판정이 같다(불안정 케이스 0). 시간 변동은 보고만 하고 합격 조건이 아니다 | `env/mutation_check.py --repeat 2` | 미실행 |
| HARN-14 | sink 수집 완전성 | 보안 케이스마다 `security-scenarios.md`의 8개 sink 목록이 모두 비어 있지 않게 수집된다. 누락·중복·경로 이탈·심볼릭 링크·스캔 오류가 있으면 실패 | `selftest/test_sentinels.py` | 미실행 |
| HARN-15 | 멈춤 처리 | 응답하지 않는 자식(더블의 `hang` 변이 없이 `sleep` 스크립트)을 제한 시간에 프로세스 그룹째 종료하고 케이스를 `FAIL(timeout)`로 기록한다. 하네스가 멈추지 않는다 | `selftest/test_procs.py` | 미실행 |
| HARN-16 | 대상 어댑터 | 더블을 `DMEM_TARGET=product DMEM_BIN=… DMEM_MCP_BIN=…`로 지정해(제품 경로 흉내) 같은 케이스가 같은 판정을 낸다. 환경 변수 누락은 명확한 오류다 | `selftest/test_target.py` | 미실행 |

## 운영 규칙

- 하네스가 검증을 통과하기 전의 측정값은 README·보고에 수치로 쓰지 않는다.
- 변이 목록은 [`../../tests/README.md`](../../tests/README.md)가 정의한다. 새 변이를 추가하면 지정 실패 케이스와 함께 이 문서에도 반영한다.
- 케이스 ID를 새로 만들지 않는다. 필요하면 문서를 먼저 고친다.
- 이 문서의 "상태" 열은 실행한 날짜와 결과 요약으로 갱신하고, 실행하지 않은 항목은 "미실행"으로 둔다([`environment.md`](environment.md)).
