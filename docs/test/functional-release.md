# 기능·출시 준비 측정 케이스

상태: runtime-v1 이후 단계(측정 케이스). 이 문서는 기준과 게이트만 정의하며 실행 결과를 주장하지 않는다.
영역 / 테스트 ID 접두사: 성능·검색 품질 `PERF`; 출시 게이트 `REL`
기반: `docs/spec/runtime-v1.md` RT-01~12, `docs/spec/core.md` 8절, `docs/test/README.md`, `docs/test/harness-verification.md`; WAM `docs/test/release-readiness.md`, `release-gates.json`, `benchmarks.md`, `retrieval-benchmark.md`, `service-abuse-performance.md`의 절차. WAM 수치는 DMEM 성능 근거로 승계하지 않는다.

## 1. 측정 규칙

성능 실행은 합성 fixture와 고정 seed를 쓴다. 크기 단계는 1,000 / 10,000 / 100,000개 항목(제안), 검색 corpus는 독립 라벨 URL+양식 질의 500개(제안)로 고정한다. 각 결과에 제품 빌드·revision, runner/OS, 저장소, fixture·질의 hash, cache 상태, 오류 수, 처리량을 기록한다. 테스트 더블은 하네스 검증용이며 제품 성능 근거가 아니다.

각 크기·연산·cache profile에서 정답/범위 검사를 먼저 통과시킨 뒤 워밍업하고 독립 실행 5회(제안) 이상 측정한다. 요청별 원시 지연에서 p50/p95를 산출하고 p99도 보고한다. 숫자 예산은 전용 기준 runner에서 검증 전까지 모두 **제안**이다.

## 2. 성능·검색 품질 케이스

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| PERF-01 | 각 크기의 고정 라이브러리에서 URL·doc_type·locale·provider가 일치하는 recall 질의 corpus를 실행한다. | 각 크기의 p50/p95와 오류율을 기록한다. 100,000개 기준 p50 ≤100 ms, p95 ≤500 ms(제안); 응답 정답 검사를 통과하지 못하면 속도와 무관하게 실패다. |
| PERF-02 | 같은 크기 단계에서 keyword `search`의 고정 질의 corpus를 실행한다. | 크기별 p50/p95·오류율을 기록한다. 100,000개 기준 p50 ≤200 ms, p95 ≤750 ms(제안); 정답 범위·페이지 누락은 실패다. |
| PERF-03 | 크기별 알려진 ID의 짧은 L2와 cursor가 필요한 큰 reference를 `expand`한다. | 첫 페이지·후속 페이지 p50/p95를 각각 기록한다. 100,000개 기준 p50 ≤100 ms, p95 ≤500 ms(제안); ID·version·내용 누락은 실패다. |
| PERF-04 | compact JSON 직렬화 recall 응답에서 `est_tokens=ceil(UTF-8 bytes/4)`로 힌트를 센다(`core.md` 8절). | 힌트는 최대 3개, 각 ≤400 est tokens이며 합계 ≤3×400 est tokens(제안)다. 초과·중복·L2 포함은 실패다. |
| PERF-05 | 제품 MCP의 `tools/list` 직렬화 결과와 instructions 문자열을 합쳐 UTF-8 byte 길이를 측정한다. | 합계 ≤12,000 bytes(제안)이고 실제 byte 수를 보관한다. host tokenizer 결과는 별도 기록하고 이 byte 수와 혼용하지 않는다. |
| PERF-06 | 64 KiB보다 큰 합성 reference를 `expand` cursor로 끝까지 읽는다(`core.md` 8절). | 각 L2 페이지 직렬화가 64 KiB 이하이고, 페이지를 이어 복원한 hash가 입력과 같으며 바이트 중복·누락이 0이다. 마지막 cursor 종료도 확인한다. |
| PERF-07 | stdio MCP에서 recall/search/expand를 섞어 16개 요청을 동시에 보낸다(`core.md` 8절). | 요청별 결과가 단독 기준 결과와 같고 지연·오류 수를 기록한다. 요청 교차, timeout, 5xx, 누락 응답은 실패다. |
| PERF-08 | URL과 provider·doc_type·locale·region·variant를 포함한 500개 질의와 독립 라벨 정답 hint ID를 실행한다(질의 수는 제안). | 질의별 정답 순위·MRR·Hit@3를 보관한다. Hit@3 ≥90%, MRR ≥0.85(제안); fixture 생성기가 만든 라벨만으로 품질 통과를 주장하지 않는다. |
| PERF-09 | `en-US`, `ko-KR`, `ja-JP` 각각 정답·오답 양식 질의를 20개 이상(제안) 실행한다. | 로케일마다 분모·top-1 정답 수·정확도를 분리 보고한다. 각 로케일 정확도 ≥90%(제안); 다른 로케일의 힌트를 정답으로 세지 않는다. |
| PERF-10 | 같은 canonical URL에 양식/provider만 다른 항목을 넣고 질의 입력 순서를 섞어 recall한다. | query별 예상 hint 순위가 고정 라벨과 일치하고 입력 순열에도 결과 순위가 결정적이다. 양식이 다른 항목을 정답 처리하면 실패다. |
| PERF-11 | 존재하지 않는 URL·양식 및 라벨상 관련 항목이 없는 질의로 검색한다. | empty/no-match와 관련 없는 반환을 구별하고 오탐 수를 기록한다. 오탐 0건(제안); 빈 결과를 성공 매치로 세면 실패다. |
| PERF-12 | 같은 제품 revision·fixture hash·seed·runner profile로 전체 벤치를 반복 실행한다. | 질의별 정답 순위와 로케일 정확도가 재현되고 각 run의 원시 결과·환경이 보존된다. hash 불일치나 누락 측정은 실패다. |

## 3. 출시 게이트

각 게이트는 동일한 출시 후보 revision의 증거로 판정한다. 필수 케이스의 FAIL·SKIP·증거 누락은 통과가 아니다. 제품 합격은 `DMEM_TARGET=product` 실행으로 증명하며 더블 결과를 대체 증거로 쓰지 않는다.

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| REL-01 | 출시 후보에 `DMEM_TARGET=product DMEM_BIN=/abs/dmem DMEM_MCP_BIN=/abs/dmem-mcp DMEM_PROFILE=full python3 -B tests/smoke/run_all.py --suite contract`를 실행한다. | CORE·FORM·FMT·MEM·RCL·LIB·SHR·DISC·IMP·VER·TPL·PRIV·MCP·CLI·SEC-A04 계약 케이스 전량 PASS, FAIL·SKIP 0건이다. |
| REL-02 | `python3 -B tests/env/mutation_check.py`로 `tests/README.md`의 변이 18개와 깨끗한 더블 대조를 확인한다. | 지정 케이스가 변이를 18/18 검출하고 깨끗한 더블은 통과한다. 이는 하네스 민감도 증거이며 제품 합격 증거는 아니다. |
| REL-03 | `python3 -B -m unittest discover -s tests/lib/selftest -p "test_*.py"`와 `DMEM_TARGET=double python3 -B tests/smoke/run_all.py --suite smoke`를 실행한다. | 하네스 자체 검증과 깨끗한 더블 smoke가 전부 PASS하고 oracle·정리·증거 판정 오류와 잔존 자원이 0이다. |
| REL-04 | 설치된 Arise에서 `python3 -B tests/smoke/arise_smoke.py`를 실행한다. | 브라우저 환경 검사 전부 PASS, fixture landmark 확인, 사용자 탭 집합이 실행 전후 같다. 미설치·건너뜀은 실패다. |
| REL-05 | `docs/test/hosts/README.md`의 각 출시 호스트에서 `host-smoke.md`의 SMK-01~05, SMK-07~09, SMK-11, SMK-14, SMK-16을 실행해 등록·연결·호출·정리한다. | 호스트별 버전과 증거를 보관하고 모든 필수 호스트가 PASS한다. 미검증 호스트나 필수 케이스 SKIP은 실패다. |
| REL-06 | R1·F 계약 케이스 뒤 SEC-A04 센티널 스윕을 8개 sink에 실행하고 오염 대조군을 한 sink에 넣는다. | 8개 sink가 모두 수집되고 정상 run 누출 0건, 오염 대조군은 검출된다. sink 누락·scan 오류·센티널 노출은 실패다. |
| REL-07 | `PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all` 및 `PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace --list`를 출시 후보 문서·코드에 실행한다. | 미정의 인용·미구현 ID·근거 없는 skip이 0이고 두 명령 모두 종료 코드 0이다. |
| REL-08 | 각 필수 run의 증거를 `target/e2e-logs/<suite>/<run-id>/`와 성능 artifact에 보관한다. | `meta.json`의 revision·target, `cases.jsonl`, `trace.jsonl`, `sinks/`, `summary.md`, raw benchmark·fixture hash가 있으며 케이스 판정과 revision을 역추적할 수 있다. |
| REL-09 | REL-01~08 결과의 `meta.json`에서 target과 revision을 대조한다. | 모든 제품 게이트가 같은 후보 revision의 `target=product` 증거를 가리킨다. `double` 또는 다른 revision의 증거로 바뀐 제품 게이트는 실패다. |
| REL-10 | 게이트 집계기에 전체 PASS 입력을 준 뒤 각 게이트를 한 번씩 FAIL·SKIP·evidence-missing으로 바꿔 판정한다. | 전체 PASS일 때만 release-ready; 필수 게이트 하나라도 FAIL·SKIP·증거 누락이면 출시 불가(non-zero)다. |

## 4. 판정과 증거

측정 예산은 전부 **제안**이며 전용 runner의 반복 측정으로 확정한다. WAM 벤치마크는 절차 참고일 뿐 DMEM 구현의 실측값이 아니다. 성능·품질 결과는 제품 revision, fixture와 라벨의 hash, runner 및 cache 조건과 함께 보관한다.
