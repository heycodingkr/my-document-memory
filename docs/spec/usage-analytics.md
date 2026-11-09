# USAGE: 계정 사용량과 익명 집계

상태: runtime-v1 이후 단계 제안. runtime-v1 로컬 실행은 원격 사용량 분석을 보내지 않는다. 이 문서는 서버 계정의 최소 집계와 opt-out 동작을 정하며 구현 완료를 뜻하지 않는다.
영역 / 테스트 ID 접두사: `USAGE` (케이스: [`../test/functional-ops.md`](../test/functional-ops.md))
기반: [runtime-v1.md](runtime-v1.md), [privacy.md](privacy.md), [rate-limits.md](rate-limits.md), WAM `docs/spec/usage-analytics.md`·`docs/test/service-abuse-performance.md`

## 1. 수집 목적과 최소 데이터

집계는 본인에게 호출량·현재 한도와 authored memory의 사용 결과를 보여주고, 서비스 운영 상태를 파악하기 위한 것이다. 요청별 이벤트를 저장하지 않고 일별 UTC 집계만 누적한다.

| 집계 | 허용 필드 |
|---|---|
| 계정 사용량 | 내부 계정 키, UTC 날짜, 고정 작업 종류(recall/search/expand/publish/preview/import/outcome 등), 요청 수·가중 cost units, 선택적 제한 거부 수 |
| authored memory 사용 | 본인 소유 memory version key, UTC 날짜, recall 결과 hit·expand 수·명시 outcome 수 |
| 서비스 상태 | 일 단위의 거친 작업 종류별 총량·성공/제한/오류 수; 작은 cohort는 숨김 |

수집하지 않는 값: 이름·이메일·IP·device/token·reader identity, 요청/receipt ID, 원본 URL과 query/fragment, 자유 텍스트 search query, 문서 제목·본문·발췌·첨부 파일, 인증 proof. rate-limit에 필요한 account/IP bucket은 별도 단기 운영 상태이며 analytics history가 아니다. URL·본문을 읽지 않아도 되는 호출 분류와 카운터만 기록한다.

## 2. 조회와 분리

로그인한 사용자는 `GET /v1/me/usage`에서 현재 account quota와 최근 30 UTC일의 요청 수·cost units를 작업 분류별로 본다. 거부된 인증 요청은 admitted calls와 분리한 `denied_requests` 합계로 표시한다. anonymous 및 잘못된 자격 증명 시도는 계정에 귀속하지 않는다. shared IP bucket은 노출하지 않는다.

`GET /v1/me/memories/analytics`는 호출자 소유 version의 날짜별 hit·expand·outcome 합계만 돌려준다. 다른 계정의 읽기는 요청 수일 뿐 고유 인원 수가 아니며 reader ID를 저장하지 않는다. 자기 호출은 authored impact에서 제외한다. 두 응답 모두 owner-scoped, no-store이며 집계가 없거나 조회 실패한 값을 0으로 가장하지 않는다. 점수·공개 순위는 이 데이터에서 자동 변경하지 않는다.

## 3. Opt-out·보관·삭제

계정 설정에서 personal usage analytics를 끌 수 있다. 기본 사용량 화면과 memory impact를 위한 집계는 기능 데이터이며 제3자 광고/추적 telemetry와 분리한다. 별도 telemetry는 계속 기본 off이고 별도 동의를 받는다.

Opt-out 즉시 새 account history와 authored-memory impact 집계를 중단하고 기존 계정 연결 집계를 삭제한다. 다시 켜면 그 시점부터 새로 집계하며 과거 기록은 복원하지 않는다. 공개 서비스의 비식별 총량은 개인 계정으로 되돌릴 수 없을 때만 남길 수 있다. 한도 적용에 필요한 단기 bucket은 계속 작동하지만 analytics 화면·영속 기록에 쓰지 않는다. 계정 삭제 시 남은 account/version 연결 집계도 제거한다.

기본 보관 제안은 최대 90일이다. account activity와 memory-version aggregate는 UTC 일 단위이며 매일 만료분을 정리한다. 이 기간은 정책·운영 검토 후 조정할 수 있고 서비스가 실제 purge를 검증하기 전에는 완료로 표시하지 않는다.

## 4. 요구사항과 테스트

| F-USAGE-nn | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-USAGE-01 | 최소 계정 집계 | 허용 목록의 카운터만 UTC 일 단위로 집계하고 요청 원문은 저장하지 않는다. | USAGE-01 |
| F-USAGE-02 | 개인 activity 조회 | 본인만 30일 요청/cost와 별도 거부 수를 보고 IP bucket은 보지 못한다. | USAGE-02 |
| F-USAGE-03 | memory impact 분리 | 본인 version aggregate만 조회하고 reader identity·receipt·본문을 반환하지 않는다. | USAGE-03 |
| F-USAGE-04 | 익명·서비스 집계 | 익명은 거친 총량만 더하며 개인/작은 cohort를 식별할 수 없다. | USAGE-04 |
| F-USAGE-05 | opt-out·보관·삭제 | opt-out은 새 수집 중지와 연결 집계 제거를 즉시 적용하고 최대 90일 보관·계정 삭제를 지킨다. | USAGE-05 |
| F-USAGE-06 | quota와 analytics 분리 | action quota 소진 후에도 제한 조회가 가능하며 장애·미확인 자료를 0으로 표시하지 않는다. | USAGE-06 |

