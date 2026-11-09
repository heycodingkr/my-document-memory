# WAM 포팅 완료: 입력·기대 결과

상태: 2026-11-09 계약 작성 후 직접 실행·검증 완료. 전체 목표 기능의 구현 완료를 뜻하지 않는다. 아래에 제품·더블·브라우저 결과를 구분한다.
대상: [`../spec/wam-port-completion-v1.md`](../spec/wam-port-completion-v1.md).

| ID | 입력 / 실행 | 기대 결과와 판정 근거 |
|---|---|---|
| PORT-01 | WAM 전체 `docs/spec`·`docs/test`와 `contracts/wam-port.v1.json`; `PYTHONPATH=tests/lib python3 -B -m dmtest.porttrace --require-upstream` | 원본마다 정확히 한 처분, 적응 대상 존재, 제외 이유 존재. 누락·유령·중복·경로 이탈 0. 실제 파일 집합과 비교 |
| PORT-02 | `run_all.py --suite contract --ids 'CORE-*,FORM-*,FMT-*,MEM-*,LIB-*,VER-*,RCL-*,SHR-*,TPL-*'` | 내 저장/재조회/버전과 공개 복사·국가/provider 분리 케이스 실행. 각 판정은 저장 파일·독립 fixture·고정 기대값 기반. SKIP은 사유 포함 |
| PORT-03 | `run_all.py --suite contract --ids 'DISC-*,IMP-*,PRIV-*,SEC-*'` | 검색 provider 없음/있음, 미리보기 저장 없음, 권리별 가져오기, 위험 URL·리다이렉트 차단, 비밀값 전체 거부. 브라우저 어댑터 미구현은 명시적으로 SKIP |
| PORT-04 | `run_all.py --suite all`(기본 `double/full`) | 구현된 계약+스모크 238개가 실패 없이 끝남. 케이스 0개나 판정 0회는 성공 근거가 아니다. `meta.json`·`cases.jsonl`·`trace.jsonl`·`summary.md` 저장 |
| PORT-05 | `cargo test --workspace`; `cargo build --workspace`; `runtime-v1.py`, `recall-v1.py`, `community-v1.py` | 실제 Rust 코드와 바이너리에 임시 DB·포트·합성 신원으로 실행. 프로필이 다른 전체 더블 계약을 제품 합격으로 세지 않는다. 공유 작업 중 실패는 케이스·원인·이슈 기록 |
| PORT-06 | `arise_smoke.py`와 세션 소유 loopback 탭 | 실제 Arise의 공개 stdio MCP로 provider·국가·라이선스·적대 fixture가 렌더링됨. 소유 탭만 닫음. 캡처는 이미지 도구로 직접 확인. 환경 통과와 제품 clip/자동 recall 행동의 통과를 구분 |
| PORT-07 | unittest selftest; `mutation_check.py --repeat 2`; `dmtest.doctrace --all`; `dmtest.codetrace` | 자체 검사 전부 통과, 깨끗한 대조군 전부 통과, 18/18 변이의 지정 케이스 실패, 대조군 반복 판정 동일, 정의되지 않은 인용 0, 필수 행 모두 구현 또는 사유 |
| PORT-08 | 포팅 지도·색인·환경·측정 문서와 실행 로그 대조 | 제품 없음·CLI/MCP 없음 같은 현재와 다른 안내 제거. 측정 기준은 사전에 정의. WAM 결과는 WAM 출처로만 표시. 미구현 기능을 통과로 쓰지 않음 |
| HARN-17 | 임시 원본/대상/manifest: 정상 목록, 새 원본 누락, 삭제 원본, 중복, 빈 이유, 잘못된 처분, 없는 대상, `../`·절대 경로, 원본 부재, 검사 대상 0개 | 정상만 통과. 모든 결함 입력은 실패하며 정상 대조군에 같은 false positive 없음. 원본 부재는 일반 모드에 명시, require 모드 실패. 빈 목록은 실패 |

## 실행 증거

| 대상 / 명령 | 직접 확인한 결과 | 증거 |
|---|---|---|
| `dmtest.porttrace --require-upstream` | 원본 Markdown 93개: 명세 31·테스트 62, 적응 72·제외 21, 누락·잘못된 대상 0 | [`../../contracts/wam-port.v1.json`](../../contracts/wam-port.v1.json), 실제 원본 파일 집합 비교 |
| unittest selftest | **138/138 통과**. 검사기 부재 실패를 확인한 뒤 포팅 게이트 양성·음성 대조 7개를 추가 | [`../../tests/lib/selftest/test_porttrace.py`](../../tests/lib/selftest/test_porttrace.py), 26.192초 |
| 더블 / full `run_all.py --suite all` | **235 PASS·0 FAIL·3 SKIP**, 총 238개 | `target/e2e-logs/contract/20261109-122609-5572/{meta.json,cases.jsonl,trace.jsonl,summary.md}` |
| `mutation_check.py --repeat 2` | 대조군 25개 ×2 통과, 판정 차이 0, **18/18 변이 검출** | `target/e2e-logs/mutation/20261109-123159/{result.json,summary.md}` |
| 실제 Arise `arise_smoke.py` | **21/21 통과**, 설치본 0.1.77·MCP 도구 62개. 자기 탭만 정리, 사용자 탭 유지 | `target/e2e-logs/arise/20261109-122711-6914/` |
| Rust `cargo test --workspace` | **92개 통과·0 실패** | `target/e2e-logs/wam-port/20261109-123328/cargo-test.log` |
| Rust `cargo build --workspace --examples` | 종료 0 | 같은 디렉터리 `cargo-build.log` |
| 실제 CLI/MCP `runtime-v1.py` | HTTP 인증·import/copy/create/export·MCP transport·충돌·불변 버전·재시작 영속성 통과 | 같은 디렉터리 `runtime.log` |
| 실제 recall `recall-v1.py` | **44/44 통과**, 출력·로그 59개 센티널 검사 | 같은 디렉터리 `recall.log` |
| 실제 계정 기여 `community-v1.py` | 비공개 저장·타인 비공개 차단·익명 공개 조회·복사·동의·검수·철회 통과 | 같은 디렉터리 `community.log` |
| 문서·코드 추적 | 정의되지 않은 인용 0, 구현 238개·R1/F 필수 행 203/203 구현 또는 사유 | `dmtest.doctrace --all`, `dmtest.codetrace --list` |
| 공백 정리 후 `FMT-08` | 1 PASS·0 FAIL·0 SKIP. EOF를 제외한 모든 bytes 불변, 이 작업 범위의 `git diff --check` 통과 | `target/e2e-logs/contract/20261109-124139-5459/`, 이슈 #400 |

Arise `shots/resume-ko.png`는 이미지 검사 도구로 열어 제목, 인적사항·경력·학력·기술, 경력 표가 실제로 보임을 확인했다. 캡처는 합성 문서이며 사용자 계정·문서는 사용하지 않았다. 제품 스모크의 명령·시간·종료 코드와 바이너리 SHA-256은 `target/e2e-logs/wam-port/20261109-123328/{results.json,meta.json}`에 있다.

3개 SKIP은 `IMP-19`(현재 탭 clip 어댑터 필요), `PRIV-09`(계정 삭제는 별도 웹/계정 기능), `RCL-20`(클라이언트 캐시 필요)다. 실제 Arise 제품 허브 등록·자발적 recall·현재 탭 clip은 이 실행에 포함하지 않는다. 웹 검색·원격 URL preview/import·provider OAuth·Google UI 링크·원본 레이아웃 충실도는 목표 계약 또는 별도 확인 범위다. Sheets/XLSX 전체 편집·PDF OCR도 이 검증의 합격 범위가 아니다.

초기 Rust 기준선은 관리자 이메일 테스트 3개가 실패했다. 다른 세션의 작업을 보존하고 #402에 위치·실패를 기록했다. 공유 구현 반영 후 재실행은 위 92개 모두 통과했으며 해당 이슈에도 결과를 남겼다. 과거 작업 사본의 GP 인용은 실제 정의된 번호 집합으로 고쳐 정의되지 않은 인용 17개를 제거했다. 설계·원인·리뷰는 [`../design/wam-port-completion-v1-review.md`](../design/wam-port-completion-v1-review.md)에 있다.

## 재실행 순서

저장소 루트에서 실행한다. 운영 서버·사용자 데이터와 분리한 임시 DB·포트·합성 신원을 사용한다. Arise 앱은 실행 중이어야 한다.

```sh
PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all
PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace --list
PYTHONPATH=tests/lib python3 -B -m dmtest.porttrace --require-upstream
python3 -B -m unittest discover -s tests/lib/selftest -p 'test_*.py'
python3 -B tests/smoke/run_all.py --target double --profile full --suite all
DMEM_PROFILE=full python3 -B tests/env/mutation_check.py --repeat 2
cargo test --workspace
cargo build --workspace --examples
python3 -B tests/smoke/runtime-v1.py
python3 -I tests/smoke/recall-v1.py
python3 -B tests/smoke/community-v1.py
python3 -B tests/smoke/arise_smoke.py
git diff --check -- docs/spec docs/test docs/design tests contracts
```

상위 WAM이 없는 checkout에서는 `porttrace`의 `--require-upstream`을 빼면 대상·처분만 확인하고 원본 대조는 명시적으로 미실행이라고 출력한다. 원본 전체 이식 합격은 원본을 제공한 strict 실행으로 판정한다. 실제 Rust 제품에 전체 더블의 `doc_memory_*` 계약을 직접 연결하지 않는다.

공유 작업 트리 주의: 전체 `git diff --check`는 최종 확인 시 다른 세션이 편집 중인 `docs/demo/hackathon-90s.md:3`의 Markdown hard break(줄 끝 공백 2개)를 표시했다. 이 작업 범위의 검사에는 문제가 없다. 의도된 데모 줄바꿈을 제거하지 않았으며 전체 릴리스의 공백 정책은 별도 확인 대상으로 남긴다.
