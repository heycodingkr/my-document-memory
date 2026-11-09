# REL: 출시 게이트와 증거

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. 공개 기능은 **runtime-v1 이후 단계**다. runtime-v1은 로컬 제품 부분집합이며 공개 게시·검색·복사 기능의 출시를 뜻하지 않는다.
영역 / 테스트 ID 접두사: `REL` (케이스: [`functional-release.md`](../test/functional-release.md))
기반: [테스트 전략](../test/README.md), [하네스 검증](../test/harness-verification.md), [테스트 실행](../../tests/README.md), [runtime-v1](runtime-v1.md)

## 1. 필수 출시 게이트

같은 후보 커밋에서 적용되는 모든 게이트가 통과해야 한다. 실패·미실행·증거 누락은 PASS가 아니다.

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-REL-01 | 계약 시험 전량 | 후보 프로필 범위의 계약 케이스 전부 PASS, in-scope SKIP·누락 0 | REL-01 |
| F-REL-02 | 변이 검사 | 변이 18/18 지정 실패 감지, 깨끗한 더블의 양성 대조 통과 | REL-02 |
| F-REL-03 | 하네스 자체 검증 | 적용 가능한 HARN 검증 전부 통과, oracle·격리·정리·재현성 증거 보관 | REL-03 |
| F-REL-04 | Arise 환경 스모크 | 필수 환경 점검 통과, 세션 소유 자원만 사용하고 사용자 탭 무변경 | REL-04 |
| F-REL-05 | 호스트 스모크 | 지원 행렬의 필수 케이스 통과; 최소 2개 호스트, Arise 포함 | REL-05 |
| F-REL-06 | SEC-A04 보안 스윕 | 완전한 sink 수집, sentinel 유출·스캔 오류 0건 | REL-06 |
| F-REL-07 | `doctrace` | 인용 테스트 ID의 UNDEFINED 0건 | REL-07 |
| F-REL-08 | `codetrace` | 구현 ID의 문서 미정의·조용한 누락 0건 | REL-08 |
| F-REL-09 | 후보 동일성 | 커밋 전체 SHA·clean checkout·고정된 gate policy hash 일치 | REL-09 |
| F-REL-10 | 증거 검토·보관 | 모든 필수 gate PASS, 검토자와 manifest 무결성 확인 | REL-10 |

runtime-v1 후보는 적용 가능한 R1 케이스를 실행하고 범위 밖 F 케이스는 사유가 있는 `SKIP(profile)`으로 기록한다. 전체 공개 기능 출시에서는 in-scope 기능 계약의 전량 통과를 요구한다. Arise 스모크와 일반 호스트 스모크는 별도 증거로 남긴다.

## 2. 게이트 증거

- 매 실행의 원본은 `target/e2e-logs/<suite>/<run-id>/`에 `meta.json`, `cases.jsonl`, `trace.jsonl`, `sinks/`, `summary.md`로 보존한다. SEC-A04에는 수집된 각 sink의 경로·hash·판정·누락/오류 여부가 있어야 한다.
- 후보별 bundle은 `target/release-evidence/<full-commit-sha>/`에 모은 뒤 접근이 통제되는 장기 아티팩트 저장소에 복제한다. manifest는 후보 전체 SHA와 clean 상태, gate policy SHA-256, 대상·프로필, OS·도구 버전, 실행 명령, UTC 시작/종료 시각, 테스트 run ID, 게이트별 결과, 검토자, 상대 경로·각 파일 SHA-256을 기록한다.
- 저장된 파일은 bundle 안의 일반 파일만 허용한다. 절대 경로·경로 탈출·symlink·빈 파일·해시 불일치는 거부한다. token, sentinel 원문, 사용자 문서와 계정 식별자는 넣지 않는다. gate evidence 검사 자체는 원 시험의 oracle·권리 검토가 진실했음을 증명하지 않으므로 원본 결과를 검토한다.
- WAM 승계 보관 정책 제안: 증거는 관측 뒤 14일 이내여야 하고 미래 시각 허용은 5분 이내, 단일 파일 상한은 64 MiB로 둔다. 장기 보존은 12개월 이상을 제안한다. 정책 확정 전에는 이 숫자를 자동 합격 판정으로 쓰지 않고 manifest에 관측 날짜·파일 크기를 기록한다.
- 정책·후보 SHA·필수 케이스가 바뀌면 새 bundle을 만든다. 요약 텍스트·합성 fixture 단독·테스트 더블 단독 결과를 실제 제품/호스트 통과 증거로 승격하지 않는다.

## 3. 실행 순서

- 실행 전에 후보 전체 SHA, clean checkout, 대상 프로필, 적용 ID 목록, gate policy hash를 고정한다. 실행 뒤 소스·fixture·정책이 바뀌면 기존 증거를 새 후보의 근거로 쓰지 않는다.
- 제품 후보는 제품 바이너리와 `DMEM_PROFILE`을 명시한다. `double` 결과는 계약과 하네스 확인 자료로 보관하되 제품 게이트의 PASS로 승격하지 않는다.
- 계약 시험·변이·하네스·Arise·호스트·SEC-A04 결과를 같은 후보 bundle에 모은 뒤 다음 추적 명령 결과도 첨부한다.

```sh
python3 -B tests/smoke/run_all.py --suite contract
python3 -B tests/env/mutation_check.py
python3 -B tests/smoke/arise_smoke.py
PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all
PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace
```

## 4. 요구사항과 테스트

`REL-01~10`의 입력과 케이스 정의는 [`docs/test/functional-release.md`](../test/functional-release.md)의 소유다. 출시 판정은 실제 후보와 검토 가능한 증거를 기준으로 하며, 명세나 증거 메타데이터만으로 배포 승인을 생성하지 않는다.
