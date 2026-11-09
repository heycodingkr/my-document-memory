# SHR: 다른 사람의 메모리 찾기·미리보기·복사, 게시와 라이선스

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM의 contribution → gatekeeper → 공개 카탈로그 흐름을 "소유자의 명시적 게시"로 바꾸고, 라이선스와 복사 정책을 추가한 명세다. 제품 규칙의 상위 기준은 [`overview.md`](overview.md) 3·5절이다.
영역 / 테스트 ID 접두사: `SHR` (케이스: [`../test/functional-tests.md`](../test/functional-tests.md))
기반: [`memory.md`](memory.md) 5·6절, [`library.md`](library.md), [`privacy.md`](privacy.md), 검수 파이프라인은 [`gatekeeper.md`](gatekeeper.md)

## 1. 흐름 한눈에

```
내 메모리 --publish(동의·라이선스)--> 검수(scrub·license·중복) --> 공개/팀 카탈로그
                                                                      |
다른 사람 --search(범위·필터)--> expand(미리보기: 출처·라이선스·버전) --copy--> 그 사람의 비공개 라이브러리
```

다른 사람의 메모리는 **참고하고 복사한다.** 원본을 직접 편집하거나 덮어쓰지 않는다. 사용하려면 내 라이브러리로 복사해 새 메모리로 관리한다. 복사본에는 원 작성자·원본 버전·라이선스가 남는다.

## 2. 가시성과 검수 상태

| `visibility` | 누가 보나 | 게시 검수 |
|---|---|---|
| `private` | 소유자만(기본) | 없음 |
| `team` | 같은 workspace 구성원 | 자동 scrub만(큐 없음) |
| `public` | 가입 없이 누구나 읽기 | scrub + license + 중복 검수, `review_state`: `queued` → `approved` / `rejected` |

runtime-v1은 `private`·`public`(공개 시드 양식 조회와 복사)만 구현 범위로 삼는다. `team`과 게시 검수는 다중 사용자 단계다.

비공개 문서의 본문·사실·메타데이터는 소유자의 명시적 게시 없이는 어떤 검색에도 나타나지 않는다. 팀 전용 항목을 비회원이나 다른 workspace 사용자가 조회하면 `not_found`다. 공개 여부만으로 권한을 우회하지 못한다.

## 3. 게시(publish)

`doc_memory_publish(memory_id, visibility, license, consent, consent_version)`. 모두 필요하다.

1. **소유자**만 가능하다. 아니면 `not_found`.
2. **명시적 동의**: 게시마다 `consent=true`와 현재 `consent_version`(`share-v1`)이 필요하다. 계정의 허용 스위치는 동의가 아니다. 동의가 없으면 서버 요청과 쓰기가 0건이고 `consent_required`다.
3. **라이선스**: [`../../contracts/vocab/licenses.json`](../../contracts/vocab/licenses.json) 어휘 안의 값. 4절 표에 따라 출처가 제3자인 메모리는 재게시가 막힐 수 있다.
4. **게시 직전 재스캔**: 비밀값이 있으면 `rejected`(reason `secret`). `contains_personal_data`가 true인 reference나 개인 정보가 남은 template은 `rejected`(reason `personal_data`). 부분 마스킹으로 게시하지 않는다.
5. **중복과 같은 양식 후보**: 정규화된 content fingerprint가 이미 공개되어 있으면 `rejected`(reason `duplicate`). `scope_key`는 [`core.md`](core.md) 6절의 owner-scoped 버전 계보 키다. 같은 소유자의 개선은 명시적 `memory_id`와 `base_version`으로 새 immutable version을 만든다. 공개 카탈로그 후보는 owner를 뺀 `catalog_scope=(site_host,canonical_url_pattern,kind,provider,doc_type,locale,region,variant)`로 찾는다. 서로 다른 소유자의 다른 내용은 검토 후 별도 기여로 함께 검색될 수 있고, scope가 같다는 이유로 자동 병합·덮어쓰기하지 않는다. near-duplicate 후보는 [`gatekeeper.md`](gatekeeper.md)의 검토 규칙을 따른다.
6. **공개 데이터 구성**: L0·L1·L2, `author_handle`, `license`, `attribution`, 버전을 공개한다. `attribution`은 복사본의 `source.derived_from`(직전 출처 `memory_id`·`version`과 원 저작자 `author_handle`·`license`)으로 공개되며 복사 사슬을 거쳐도 원 저작자와 원 라이선스를 잃지 않는다. `source_ref`, 원본 파일, 능력 URL, 계정 이메일·내부 ID는 공개하지 않는다.

응답: `visibility`, `review_state`, `review_id`, `reasons[]`(고정 enum). `visibility=private`으로 호출하면 **게시 취소(unpublish)** 이며 동의가 필요 없다.

게시 취소는 이후의 recall·search·expand·copy에서 즉시 제외하고, 이미 만들어진 복사본은 건드리지 않는다. 운영자 조치(takedown)는 `status=taken_down`으로 공개 조회에서 숨기고(소유자 자신의 `mine` 목록에 상태를 표시하며 남길지는 열린 결정이다. 제안: 남기고 `taken_down`을 표시한다), 복사본에는 `origin_taken_down` 경고 코드을 붙여 재게시를 막으며, 같은 `content_hash`의 재게시를 차단한다.

## 4. 라이선스와 복사 정책

법률 자문이 아니라 **보수적인 제품 기본값**이다. 어휘 밖이거나 NC/ND 계열처럼 이 표로 판단할 수 없는 라이선스는 `proprietary-structure-only`로 취급한다.

| license | `copy_policy` 상한 | 복사(copy) | 복사본 재게시 | 요건 |
|---|---|---|---|---|
| `CC0-1.0` | `full` | 허용 | 허용 | 없음 |
| `CC-BY-4.0` | `full` | 허용 | 허용 | 저작자·라이선스 표시 유지 |
| `CC-BY-SA-4.0` | `full` | 허용 | 같은 라이선스(`CC-BY-SA-4.0`)로만 | 표시 + 동일조건 |
| `MIT`, `Apache-2.0` | `full` | 허용 | 허용 | 라이선스 고지 유지 |
| `proprietary-structure-only` | `structure_only` | 구조만 | 불가 | 표시 유지 |
| `unknown` | `structure_only` | 구조만 | 불가 | — |

`structure_only` 복사는 제목, 섹션 순서, 슬롯, 스타일, 표 머리글만 복사하고 본문 문장을 제거한다([`memory.md`](memory.md) 5절). `copy_mode` 요청이 상한을 넘으면 `license_forbids`이며 응답에 허용되는 `allowed_modes`(고정 enum 목록)를 담는다. 출처가 사용자 자신(`origin: user`)이면 본인 비공개 복사는 항상 `full`이고, 게시할 때 라이선스를 고른다.

## 5. 찾기(search)와 미리보기

### search

`doc_memory_search`는 사용자가 **직접 시작하는 탐색 경로**다. 자유 텍스트 `query`(≤200자)를 허용하되 비밀값 형태를 거부하고(`secret_detected`) 로그에는 해시만 남긴다. `scope=mine`은 로컬 전문 검색이고 네트워크 요청이 0건이다. `team`·`public`을 포함하면 질의가 서버로 가며 응답에 `remote: true`가 표시된다.

필터: `kind`, `doc_type`, `locale`, `provider`, `license`, `visibility`. 정렬: 필터 적용 후 필드별 전문 검색 점수(제목·키워드·요약 가중), 동점은 `updated_at` 내림차순·`memory_id`. 페이지는 ≤20개이며 `cursor`로 넘긴다. 익명은 `public`만, 로컬 모드는 `mine`만 볼 수 있다(`scope_unavailable_local`).

결과 항목: `memory_id`, `version`, `kind`, `title`, `summary`(≤300자), `form`, `source`(`tier`, `author_handle`, `license`, `copy_policy`, `origin`), `visibility`, `updated_at`. 전체에 untrusted 프레이밍이 붙는다.

### 미리보기

별도 도구 없이 `doc_memory_expand`가 미리보기다. level 1은 L1(개요·출처·라이선스·버전), level 2는 구조(StandardDoc)와 슬롯·규칙이다. 타인의 공개 항목은 작성자·라이선스·버전을 항상 함께 반환하고, 보이지 않는 항목은 `not_found`다. `structure_only` 항목의 L2에는 본문이 없다.

## 6. 복사(copy)

`doc_memory_copy(memory_id, version?, title?, copy_mode?)`.

- 호출자에게 **보이는** 항목만 복사할 수 있다. 아니면 `not_found`(존재 여부를 구분할 수 없다).
- 결과는 호출자 라이브러리의 **새 비공개 메모리**(`origin: copied`)이며 `derived_from {memory_id, version, author_handle, license}`을 가진다. 원본의 버전·`updated_at`·내용은 바뀌지 않는다.
- `copy_mode`는 4절 상한 안에서만 가능하다. 생략하면 상한 모드다.
- 익명 사용자도 공개 항목을 **로컬 라이브러리로** 복사할 수 있다(계정이 필요 없다). receipt·outcome·점수는 연결된 계정만 만든다.
- 복사본을 다시 복사하면 `derived_from.memory_id`·`version`은 **직접 복사한 원본**이고 `author_handle`·`license`는 **최초 작성자**의 값이다(체인을 따라가도 최초 작성자와 라이선스가 유지된다). 복사본의 재게시는 4절의 라이선스 조건과 원 작성자 표시를 충족할 때만 가능하다.
- 원본이 이후 게시 취소·takedown되어도 이미 만든 복사본은 남는다. takedown된 원본의 복사본은 재게시할 수 없다.

## 7. 결과 보고와 점수

recall이 연결된 호출에 `receipt_id`를 준다. 사용자가 실제로 쓴 버전만 `doc_memory_outcome`으로 보고하며, 다른 계정이 성공적으로 쓴 공개 양식에만 작성자 점수가 생긴다. 익명 조회, 본인 사용, 캐시 결과는 점수를 만들지 않는다. 상세는 [`score.md`](score.md)가 정한다.

## 8. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-SHR-01 | 명시적 동의 게시 | 동의 없으면 서버 쓰기 0건, 있으면 검수 큐로 | SHR-01~03 |
| F-SHR-02 | 게시 직전 재스캔과 개인 정보 차단 | 비밀값·개인 정보가 공개 카탈로그에 0건 | SHR-04~05 |
| F-SHR-03 | 팀·공개 가시성 | 팀 항목은 구성원만, 비구성원은 not_found | SHR-06, TPL-03 |
| F-SHR-04 | 범위별 검색 | mine/team/public/all과 익명 제한, 결과 필드, 안정 정렬 | SHR-07~08 |
| F-SHR-05 | 검색 질의 프라이버시 | 비밀 질의 거부, `mine` 검색은 네트워크 0건 | SHR-09 |
| F-SHR-06 | 출처와 함께 미리보기 | 작성자·라이선스·버전 표시, 원본 불변 | SHR-10, TPL-02 |
| F-SHR-07 | 복사 | 새 비공개 메모리, derived_from, 원본 불변 | SHR-11, TPL-02 |
| F-SHR-08 | 라이선스 복사 상한 | 상한 초과는 license_forbids, structure_only는 본문 제거 | SHR-12 |
| F-SHR-09 | 재게시 조건 | CC-BY 허용, SA는 같은 라이선스, 구조 전용은 불가 | SHR-13 |
| F-SHR-10 | 게시 취소와 takedown | 즉시 조회에서 제외하고 사본 유지, 재게시 차단 | SHR-14~15 |
| F-SHR-11 | 접근 경계 | 타인의 비공개·비소유 조작은 구분 불가한 not_found | SHR-16~17, SEC-01 |
| F-SHR-12 | 익명 경계 | 익명 쓰기는 auth_required, 로컬 복사는 허용 | SHR-18 |
| F-SHR-13 | 중복·스팸 | 중복 게시 거부, 게시 속도 제한 | SHR-19 |
| F-SHR-14 | 귀속 체인 | 복사의 복사에도 최초 작성자·라이선스 유지 | SHR-20 |
| F-SHR-15 | 같은 공개 양식 범위의 독립 기여 | 다른 작성자의 다른 내용은 별도 공개 결과로 남고 복사는 정확한 출처 버전을 고정 | SHR-21 |
