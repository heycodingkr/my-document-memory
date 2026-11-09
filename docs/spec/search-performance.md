# PERF: 검색 성능과 품질

상태: 설계 제안(문서 우선, 구현·측정 없음). 모든 성능 예산은 제안값이며 기준선 측정과 승인 전 합격 기준이 아니다.
영역 / 테스트 ID 접두사: `PERF` (케이스: [`functional-release.md`](../test/functional-release.md))
기반: [`recall.md`](recall.md), [`sharing.md`](sharing.md), [테스트 계층](../test/README.md), [하네스 검증](../test/harness-verification.md), [runtime-v1](runtime-v1.md)

## 1. 범위와 측정법

이 명세는 로컬 `recall`·`search`·`expand`와 인증된 서버 모드의 지연, URL+양식 질의의 검색 순위를 다룬다. 규모별 recall·expand는 runtime-v1 이후 단계다. 결과의 순위 정확성·격리 검사는 지연과 별도로 판정한다.

- 합성 데이터 규모는 1,000 / 10,000 / 100,000 메모리 항목을 제안한다. 1,000,000 항목 stress는 별도 관찰로 남기며 기본 예산과 합치지 않는다. 메모리 수, 자료 수·총 바이트, fixture hash와 분포를 함께 기록한다.
- 로컬 모드는 단일 소유자 저장소에서 프로세스 시작 시간을 제외한다. 서버 모드는 인증을 포함한 HTTP 왕복을 측정하고 서버 처리시간과 왕복시간을 분리한다. loopback과 원격 결과는 서로 다른 프로필로 보고한다.
- 고정 seed·동일 query set에서 warm-up 뒤 10개 표본씩 5회 반복한다. cold와 warm은 별도 run으로 측정한다. p50·p95는 원시 표본에서 산출하고 OS, CPU, 메모리, 빌드, DB·도구 버전, 동시성, 명령과 실행시간을 기록한다.
- 아래 예산은 각 칸의 `p50 / p95` 밀리초 제안 상한이다. 첫 기준선은 관측치만 보고한다. 측정 전에 이 상한을 합격·실패에 사용하지 않는다.

| 모드·항목 수 | recall p50/p95 | search p50/p95 | expand p50/p95 |
|---|---:|---:|---:|
| 로컬 1,000 | 50/100 | 100/250 | 30/75 |
| 로컬 10,000 | 100/250 | 200/500 | 50/125 |
| 로컬 100,000 | 250/750 | 500/1,500 | 100/300 |
| 서버 1,000 | 100/300 | 150/400 | 75/250 |
| 서버 10,000 | 200/600 | 300/900 | 100/300 |
| 서버 100,000 | 500/1,500 | 750/2,200 | 250/750 |

## 2. 응답 크기와 검색 품질

- recall 힌트 최대 3개·힌트당 최대 400 estimated tokens와 `tools/list` UTF-8 JSON 12,000 bytes는 이 문서의 성능 제안 예산이다. tokenizer/estimator 이름과 버전을 고정하고 실제 응답 크기를 측정한다. 측정·승인 전에는 성능 합격 문턱이 아니다. 기존 `recall.md`의 RCL 출력 계약과 HARN-12 정적 크기 검사는 각 문서 범위에서 유지되며 이 제안이 바꾸지 않는다.
- 골든 질의는 합성 URL과 `doc_type`, `locale`, `provider`, `region`, `variant`, `kind` 및 허용 키워드를 고정한다. 각 질의에 정답 hint ID·허용 정답 집합·기대 순위를 붙인다. 일치/불일치 URL 경로, 양식·provider, 로케일, no-match와 distractor를 포함한다.
- 지원 로케일마다 별도 결과를 낸다. 한국어(`ko-KR`), 영어(`en-US`), 일본어(`ja-JP`)를 초기 fixture로 제안하고, 추가 로케일은 동일한 골든 질의 규칙으로 등록한다.
- 로케일별 Hit@1, Recall@3, MRR@3, 정답 hint의 실제 순위를 보고하고 macro 평균은 별도 표시한다. 자동 생성 라벨은 순위 규칙 회귀만 확인한다. 제품 품질 주장은 held-out 질의와 독립 검토된 라벨이 준비되기 전 승인하지 않는다.
- 골든 세트는 버전·seed·질의/라벨 수·파일 hash·라벨 출처를 남긴다. 실제 문서·사용자 URL·프롬프트는 fixture에 넣지 않는다.

## 3. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-PERF-01 | 규모별 합성 데이터 | 제안 규모·분포·fixture hash 재현 및 기록 | PERF-01 |
| F-PERF-02 | 로컬 recall 지연 | 규모별 p50/p95 관측치와 원시 표본 보관 | PERF-02 |
| F-PERF-03 | 로컬 search 지연 | 규모별 p50/p95 관측치와 원시 표본 보관 | PERF-03 |
| F-PERF-04 | 로컬 expand 지연 | 규모별 p50/p95 관측치와 원시 표본 보관 | PERF-04 |
| F-PERF-05 | 서버 모드 지연 | 처리·왕복 p50/p95와 배포 위치 분리 보고 | PERF-05 |
| F-PERF-06 | recall 크기 예산 | ≤3 hints·≤400 estimated tokens를 측정; 제안 예산 승인 후에만 gate | PERF-06 |
| F-PERF-07 | `tools/list` 크기 예산 | UTF-8 JSON bytes 측정; 12,000 bytes 제안값 승인 전 gate 아님 | PERF-07 |
| F-PERF-08 | 측정 재현성 | cold/warm·환경·빌드·seed·원시 표본 보관 | PERF-08 |
| F-PERF-09 | URL+양식 골든 질의 | 질의별 정답 hint와 기대 순위 고정 | PERF-09 |
| F-PERF-10 | 로케일별 순위 품질 | Hit@1·Recall@3·MRR@3와 정답 순위 보고 | PERF-10 |
| F-PERF-11 | 순위 채점기 정확성 | 표본별 채점 결과를 독립 oracle과 대조 | PERF-11 |
| F-PERF-12 | 기준선·라벨 이력 | 골든 버전·held-out·라벨 출처·변경 근거 보관 | PERF-12 |

`PERF-01~12`의 입력과 케이스 정의는 [`docs/test/functional-release.md`](../test/functional-release.md)의 소유다. 이 명세는 테스트 케이스를 정의하지 않는다.
