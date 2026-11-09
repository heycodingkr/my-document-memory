# MEM: 구조화 메모리 레이어 (L0/L1/L2), 종류, 슬롯, 출처

상태: 설계 초안(문서 우선, 구현 없음). WAM `memory.md`의 L0/L1/L2 레이어와 불변 버전 규칙을 승계하고 kind·출처·라이선스를 문서 도메인에 맞게 바꿨다. 여기서 L0/L1/L2는 **메모리 레이어**이며 테스트 계층 L0~L6과 다른 개념이다.
영역 / 테스트 ID 접두사: `MEM` (케이스: [`../test/functional-tests.md`](../test/functional-tests.md))
기반: [`core.md`](core.md), [`form.md`](form.md), [`formats.md`](formats.md)

## 1. 목적

메모리는 한 덩어리 문서가 아니라 세 레이어로 나뉜 구조화 레코드다. 에이전트는 가벼운 L0로 찾고, 주입에는 L1만 쓰고, 필요할 때만 L2를 연다. 그래야 recall 토큰이 작게 유지되고, URL과 양식으로 정확히 색인되며, 전체 구조와 본문 근거는 필요할 때만 읽힌다. 원본 파일은 별도로 보존하고 색인은 그 투영이다.

## 2. 종류(kind)

[`overview.md`](overview.md) 3절의 세 라이브러리와 대응한다. 라이브러리를 하나의 색인으로 섞지 않는다.

| kind | 담는 것 | L1 필수 | L2 필수 |
|---|---|---|---|
| `template` | 문서·슬라이드 양식의 구조·스타일·슬롯 | `outline`(≥1) | `structure`(StandardDoc), `slots[]`(없으면 빈 배열), `rules[]` |
| `reference` | 내 정책·사실·프로젝트 문서와 근거 | `summary` | `spans[]`(각 span은 `locator`와 `text`) |
| `style_rule` | 어조·용어·표기·편집 규칙 | `rules` 요약(≥1) | `rules[]`(≥1) |

`template`의 `examples`(본문 예시)는 `copy_policy`가 허용할 때만 보관한다(5절).

구현 대응([`runtime-v1.md`](runtime-v1.md), 별도 작업): 저장소 레코드 종류 `template`은 `template`, `source`(자료)는 `reference`에 해당한다. `document`(작성 결과)는 메모리 kind가 아니라 양식·자료의 `(memory_id, version)`을 고정해 참조하는 산출물이다. `style_rule`은 아직 구현 범위에 없다.

## 3. 레이어

| 레이어 | 내용 | 누가 읽나 | 한도([`core.md`](core.md) 8절) |
|---|---|---|---|
| L0 위치·색인 | `kind`, `site_host`, `url_patterns[]`, `form`(provider·doc_type·locale·region·variant), `keywords[]` | recall 매칭(주입하지 않음) | 직렬화 ≤1 KiB, URL 패턴 ≤4, 키워드 ≤8개(각 ≤32자) |
| L1 요약 | `title`, `summary`, `key_points[]`, `outline[]`(template), 적용 범위, 출처 요약, 경고 | 에이전트에 주입 | 힌트당 ≤400 est tokens, recall당 ≤3개 |
| L2 상세 | template: `structure`·`slots`·`rules`·`examples`. reference: `spans`. style_rule: `rules` | `expand(level=2)`로만 | ≤64 KiB, 초과는 `cursor`로 분할 |

레이어 밖 메타데이터(`id`, `version`, `status`, `visibility`, `review_state`, `updated_at`)는 DB 컬럼이며 모델이 쓸 수 없다. 키워드는 NFKC·소문자·공백 정리 후 ≤32자이고 문자·숫자·하이픈·공백만 허용한다. URL, 이메일, 비밀값 형태, 문장은 거부한다. 한국어와 영어를 함께 둘 수 있다.

**L0 URL 패턴 표기.** host를 뺀 경로로 쓰고 세 형태만 허용한다. `/document/d/:id/edit`는 정확히 그 경로, `/document/*`는 그 아래 전부, `/*`는 사이트 전체다. 서버와 클라이언트는 이를 canonical 패턴으로 바꿔 색인한다([`core.md`](core.md)).

## 4. 슬롯과 규칙 문법

- **슬롯**: 본문에서 `{{name}}`. 이름은 `[a-z][a-z0-9_]{0,39}`이고 한 양식 안에서 유일하다. `slots[]` 항목: `name`, `type`(`text`, `date`, `number`, `money`, `list`), `required`, `hint`(≤80자).
- **확인 필요 표식**: 출처 없는 사실은 `{{확인 필요: 항목}}`(항목 ≤80자)으로 남긴다. 영어 별칭 `{{needs-info: item}}`도 같은 의미이며 저장·내보내기에서 원문 그대로 보존한다.
- **규칙**: `rules[]` 항목은 `id`, `kind`, `text`다. `kind`: `section_order`, `required_section`, `max_length`, `citation`, `tone`, `terminology`, `notation`.

## 5. 출처(provenance)와 복사 정책

모든 메모리 버전은 `source` 블록을 가진다.

| 필드 | 규칙 |
|---|---|
| `origin` | `user`(직접 작성·업로드), `fetched`(URL 가져오기), `clipped`(현재 탭 가져오기), `copied`(다른 사람 메모리 복사) |
| `provenance` | `uploaded`, `captured`(호스트 어댑터가 실제 탭에서 읽음), `claimed`(모델이 출처를 주장함, 검증 안 됨), `fetched` |
| `source_host`, `source_url` | `source_url`은 능력 호스트가 아닌 공개 사이트에서만 query·fragment 없이 보존한다([`core.md`](core.md) 4절) |
| `source_ref` | 능력 호스트의 HMAC 참조. 게시 데이터에는 넣지 않는다 |
| `retrieved_at`, `content_hash` | 가져온 시각과 `sha256:` 내용 해시 |
| `license` | SPDX id(`CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `MIT`, `Apache-2.0`) 또는 `proprietary-structure-only`, `unknown`. 어휘 원본: [`../../contracts/vocab/licenses.json`](../../contracts/vocab/licenses.json) |
| `license_source` | `detected`(페이지 표식), `user_asserted`(사용자가 주장), `none` |
| `copy_policy` | `full`, `quote_limited`, `structure_only` |
| `derived_from` | 복사본일 때 `{memory_id, version, author_handle, license}` |

**복사 정책 규칙**([`sharing.md`](sharing.md) 4절과 같은 표): 라이선스가 `unknown`이거나 `proprietary-structure-only`이면 `structure_only`다. 구조 전용으로 저장할 때는 제목, 섹션 순서, 슬롯, 스타일, 표 머리글만 남기고 본문 문장(prose)은 제거한다. `quote_limited`는 원문 인용을 항목당 최대 25단어로 제한한다. `full`은 허용 라이선스에서만 가능하다. `license_source: user_asserted`인 제3자 콘텐츠는 `unverified` 표식이 붙고 게시할 수 없다.

## 6. 상태, 가시성, 버전

- `status`: `active`, `superseded`, `retired`, `taken_down`. 같은 owner-scoped `scope_key`([`core.md`](core.md) 6절)에는 active lineage 하나, 그 lineage에는 active version 하나만 둔다. 다른 owner의 동일 scope와 provider/region/variant가 다른 scope는 별도로 공존한다.
- `visibility`: `private`(기본), `team`, `public`. `review_state`: `none`, `queued`, `approved`, `rejected`([`sharing.md`](sharing.md)).
- `version`은 메모리별로 1부터 증가하는 정수다(runtime-v1의 DTO와 같다). 메모리를 정확히 가리킬 때는 `(memory_id, version)` 쌍을 쓴다.
- 레이어 전체가 하나의 immutable 버전에 묶인다. 일부 레이어만 고치지 않는다. 변경은 새 버전이고 이전 버전은 남는다. 문서와 생성 기록은 사용한 버전 번호를 가리킨다(VER).
- L0는 색인 projection으로 풀어 저장한다. 같은 버전을 다시 색인하면 같은 결과이며 inactive 버전은 기본 recall에 나오지 않는다.
- 알 수 없는 `schema_version`이나 필드는 저장하지 않는다. 승인된 migration만 typed 레코드를 만든다.

## 7. 쓰기 규칙과 안전

- **L1 필드**(`title`, `summary`, `key_points`, `outline`)는 주입되는 텍스트다. `summary`·`key_points`는 저장 입력으로 줄 수 있고(생략하면 추출기가 구조에서 결정적으로 만든다) 같은 검증을 받는다. URL, 이메일, 계정명, 제어 문자·보이지 않는 문자, 한도 초과를 거부하고, "이전 지시를 무시", "외부로 전송", "명령 실행", 자격증명 입력을 유도하는 문장은 거부하거나 `injection_flagged` 경고와 함께 L1에서 제외한다.
- **L2 본문**은 데이터다. 어떤 문장이 들어 있어도 지시로 취급하지 않으며 응답은 항상 untrusted 프레이밍 안에서만 나간다.
- **비밀값**은 저장 전체를 원자적으로 거부한다(`secret_detected`). 부분 마스킹한 채 저장하지 않는다.
- **개인 정보**: `template`은 감지된 개인 값(이름, 전화, 주소, 주민·여권·계좌 형태, 이메일)을 슬롯으로 바꿔 저장하고 치환 목록을 보고한다. `reference`는 값을 보존하되 `contains_personal_data: true`로 표시하고 비공개를 유지한다([`privacy.md`](privacy.md)).

## 8. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-MEM-01 | 세 레이어와 한도 | 검증기가 필수와 한도를 강제한다 | MEM-02 |
| F-MEM-02 | kind별 구조 | template은 outline+structure, reference는 spans, style_rule은 rules가 필수 | MEM-03 |
| F-MEM-03 | 주입은 L1만 | recall 응답은 L1과 범위 정보만 담고 L2는 `expand`에서만 | MEM-04~05 |
| F-MEM-04 | 슬롯·규칙·확인 필요 표식 | 문법 검증과 왕복 보존 | MEM-06~07 |
| F-MEM-05 | 공존과 active 유일성 | kind·doc_type·locale이 다르면 공존, 같으면 active 1개 | MEM-08 |
| F-MEM-06 | 불변 버전과 색인 일관성 | 이전 버전은 당시 내용 그대로, 재색인 결과가 같다 | MEM-09~10 |
| F-MEM-07 | L1 텍스트 안전 | URL·이메일·제어 문자·주입 문구가 L1에 없다 | MEM-11 |
| F-MEM-08 | 스키마 진화 | 알 수 없는 버전·필드는 저장하지 않는다 | MEM-12 |
| F-MEM-09 | 출처와 복사 정책 | origin별 필수 필드, 능력 URL 금지, structure_only는 본문을 제거한다 | MEM-13~14 |
| F-MEM-10 | 원자적 비밀 거부와 개인 정보 처리 | 부분 저장 0건, template의 개인 값은 슬롯화 | MEM-15, LIB-08~10 |
| F-MEM-11 | L2 분할 읽기 | 64 KiB 초과는 cursor로 일관되게 나뉜다 | MEM-16 |
| F-MEM-12 | 내 참고자료의 사실과 위치 | 저장한 사실과 정확한 source span이 반환되고 다른 자료의 사실이 섞이지 않는다 | MEM-01 |
