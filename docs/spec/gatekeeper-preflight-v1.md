# 게시 전 점검 v1: Gatekeeper preflight (runtime-v1 부분집합)

상태: 구현 계약 (2026-11-09). [`gatekeeper.md`](gatekeeper.md)의 GK 계약 중 큐·모델·동의 기록·팀 가시성·OOXML 없이 **내 비공개 템플릿 한 개를 공개 전에 결정적 규칙으로 점검**하는 부분(R1 scrub, R2 사용권, R3 중복, R4 구조)이다. LLM 판정, 큐, 저장소 변경, 공개 상태 변경은 없다. WAM의 Gatekeeper(redaction → dedup → 판정)를 문서 양식 도메인으로 옮긴 쓰기 경로의 안전장치다. 기준 구현은 `tests/env/dmem-double/dmem_double/scrub.py`와 `engine.py`의 `op_publish`, 합격 오라클은 `tests/sentinels.json`이다. 사용권 규칙은 [`accounts-community-v1.md`](accounts-community-v1.md)의 공개 기여 계약(`CC0-1.0`·`CC-BY-4.0`, 재기여 시 원 라이선스 유지)을 따른다. 이 점검은 그 계약의 관리자 검수를 대체하지 않으며, 구현한 것은 판정 보조뿐이다.
영역 / 테스트 ID 접두사: `GP` (케이스: [`../test/gatekeeper-preflight-v1.md`](../test/gatekeeper-preflight-v1.md))

## 의존 순서와 원자 목표

| 순서/경로·담당 | 산출물 | 부모의 독립 검증 | 선행 |
|---|---|---|---|
| 1 명세·테스트 / 부모 | 이 문서, 테스트 문서, 골든 해시 | 더블·센티널·계약과 대조 | 없음 |
| 2 contracts·core / codex:gpt-6-luna, 작업 사본 | DTO, 정규화·스캐너·규칙·해시 순수 함수, 단위 테스트 | `cargo test`, 센티널 40개 전수 | 1 |
| 3 server / luna | `POST /v1/templates/{id}/check`, 공개 후보 로드, 통합 테스트 | 실제 Router·임시 SQLite | 2 |
| 4 client·CLI / luna | `dmem check`, 종료 코드 | 실제 바이너리 E2E, HTTP=CLI 동등 | 3 |
| 5 반영·회귀 / 부모 | 검증한 패치만 실제 저장소에 반영 | 새 사본 `cargo test --workspace` | 4 |

## 1. 입력과 결과

`POST /v1/templates/{id}/check`, 본문 `{"author": string, "license": string}`(각 200자 이하, 알 수 없는 필드·누락·문자열이 아님은 400 `invalid_input`). 소유자의 템플릿만 점검한다(타 소유자·없는 id는 같은 404 `not_found`). 응답은 항상 같은 모양이고 저장소를 바꾸지 않는다.

```
{ "schema_version": 1, "policy": "preflight-v1", "template_id": "...", "version": 1,
  "verdict": "approve" | "reject" | "escalate_to_human",
  "reasons": ["duplicate","injection","license","personal_data","secret","structure","takedown_match"의 부분집합, 사전순, 중복 없음],
  "findings": [ { "rule": "R1".."R4", "reason": <reasons 값> | null, "action": "block"|"review"|"info", "field": "...", "code": "..." } ],
  "content_hash": "sha256:<소문자 hex 64>" }
```

**응답·로그에는 검사한 문자열, 위치, 일부 조각, 일치한 값을 절대 담지 않는다.** 고정 코드와 필드 경로만 있다. `findings`는 같은 (rule, field, code)를 한 번만 담고 (rule, field, code) 문자열 오름차순으로 정렬한다.

`field`는 `title`, `summary`, `tags[i]`, `sections[i]`, `author`, `license`, `form`, `tags`, `sections`, `visibility`, 중복 후보를 가리키는 `public:<공개 템플릿 id>`다.

## 2. 규칙

공통 정규화: 모든 문자열은 NFKC로 바꾸고 제로폭·양방향 제어 문자(`U+200B-200F`, `U+202A-202E`, `U+2060`, `U+2066-2069`, `U+FEFF`, `U+180E`, `U+00AD`)를 **제거한 뒤** R1을 검사하고 해시한다. 제거한 문자가 있으면 그 필드에 `info` finding `hidden_text_removed`(reason `null`)를 하나 남긴다. 숨은 문자로 쪼갠 비밀값도 제거 뒤 잡혀야 한다.

### R1 scrub (`title`, `summary`, `tags[i]`, `sections[i]`, 요청 `author`) — 모두 `block`

모든 검사는 **형식 기준이고 fail closed**다. 값이 유효한지(날짜·체크섬 등)는 보지 않는다. 앞뒤가 영문·숫자가 아닐 때만 일치로 본다.

| reason | code | 일치 조건 |
|---|---|---|
| secret | `api_key_sk` | `sk-`(대소문자 무관) + `[A-Za-z0-9_-]` 16자 이상 |
| secret | `aws_access_key` | `AKIA` + `[A-Z0-9]` 16자 |
| secret | `github_token` | `ghp_`·`gho_`·`ghu_`·`ghs_`·`ghr_` + 영숫자 36자 |
| secret | `jwt` | `eyJ`로 시작하는 base64url 8자 이상 + `.` + 8자 이상 + `.` + 8자 이상 |
| secret | `bearer_token` | `Bearer` + 공백 + `[A-Za-z0-9._~+/=-]` 8자 이상(대소문자 무관) |
| secret | `private_key` | `-----BEGIN ` + 대문자 단어들 + `PRIVATE KEY-----`(머리줄만으로 충분) |
| secret | `slack_token` | `xox` + `[abprs]` + `-` + `[A-Za-z0-9-]` 10자 이상 |
| secret | `google_api_key` | `AIza` + `[0-9A-Za-z_-]` 35자 |
| secret | `credential_assignment` | (대소문자 무관) `password`·`passwd`·`secret`·`api_key`·`apikey`·`access_token`·`auth_token` 바로 뒤에 공백 0개 이상, `:` 또는 `=`, 공백 0개 이상, 공백 없는 값 8자 이상. 값이 `{{`·`<`·`$`로 시작하거나 `_ * . - x X #`로만 이루어지면 자리표시자라 제외 |
| personal_data | `email` | `[A-Za-z0-9._%+-]+@도메인.영문2자이상`(모든 도메인, `.test` 포함) |
| personal_data | `phone` | `+1 (ddd) ddd-dddd`, `(ddd) ddd-dddd`, `ddd-ddd-dddd`, `010-dddd-dddd`, `090-dddd-dddd`, `01[016789]` + 구분자(`-`·`.`·공백) 선택 + 3~4자리 + 구분자 선택 + 4자리, `+` 국가번호 1~3자리 + 공백·하이픈 + 8~12자리(구분자 허용) |
| personal_data | `national_id` | `dddddd-ddddddd` 또는 `ddd-dd-dddd`(숫자 경계). 날짜·체크섬은 보지 않는다 |
| personal_data | `card_number` | 숫자 13~19개(그룹 사이 공백·하이픈 허용)이고 Luhn 체크섬이 맞음 |
| personal_data | `account_number` | 영문 대문자 2 + 숫자 2 + 영숫자 11~30(그룹 사이 공백 허용), 체크섬 없음 |
| injection | `prompt_override` | (대소문자 무관, 공백 연속은 하나로) `ignore previous instructions`, `ignore all previous instructions`, `disregard previous instructions`, `이전 지시를 무시`, `이전 지시사항을 무시`, `send the document to` 뒤 `http`, `외부로 전송`, `run the following command`, `비밀번호를 입력` |

### R2 사용권 (`license`, `author`) — `block`, reason `license`

요청 `license`는 `contracts/vocab/licenses.json`의 id여야 한다(아니면 `license_unknown`). 그리고 게시 허용 목록 `CC0-1.0`, `CC-BY-4.0`에 있어야 한다(아니면 `license_not_allowed`). 템플릿에 `origin`이 있고 `origin.license`가 `CC0-1.0`이 아니면 요청 `license`가 `origin.license`와 같아야 한다(아니면 `relicense_forbidden`, 원 라이선스를 낮추거나 바꿔 재게시할 수 없다). `author`는 1~80자이고 제어 문자가 없어야 한다(아니면 reason `structure`, code `author_invalid`, field `author`). 허용 목록은 옵션이며 기본값이 위 두 개다.

### R3 중복 — 옵션으로 받은 공개 후보·takedown 지문과 비교

`content_hash` 정의: 아래 문자열의 UTF-8 바이트의 SHA-256 소문자 hex에 `sha256:`를 붙인다.

```
"dmem-preflight-v1" \n family \n provider \n doc_type \n locale \n (region 또는 "") \n (variant 또는 "") \n 섹션1 \n 섹션2 …
```

`family`·`provider`는 직렬화 이름(`document`, `docx`)이다. 섹션은 NFKC → 숨김 문자 제거 → 소문자 → 모든 공백 연속을 하나로 → 앞뒤 공백 제거한 값이다. **제목·요약·태그·작성자·라이선스·페이지는 해시에 넣지 않는다.** 섹션 순서는 해시에 영향을 준다.

- 같은 해시가 공개 후보에 있으면 `block`, reason `duplicate`, code `exact_duplicate`, field `public:<id>`.
- 해시가 takedown 지문 목록에 있으면 `block`, reason `takedown_match`, code `takedown_match`, field `takedown`. 중복도 함께 있으면 둘 다 담는다.
- 해시가 다르고 `doc_type`·`locale`이 같은 공개 후보와 섹션 집합(정규화한 값의 집합) 유사도가 0.80 이상이면 `review`, reason `duplicate`, code `near_duplicate`. 유사도 = 교집합 / 합집합이며 **정수로 비교한다**(교집합×5 ≥ 합집합×4).

### R4 구조 — `block`, reason `structure`

| code | field | 조건 |
|---|---|---|
| `limit_exceeded` | `title`·`summary`·`sections`·`sections[i]`·`tags`·`tags[i]` | 제목 120자 초과, 요약 600자 초과, 섹션 12개 초과·각 60자 초과, 태그 8개 초과·각 32자 초과(문자 수) |
| `empty_field` | `title`·`sections`·`sections[i]` | 비었거나 공백뿐인 제목·섹션, 섹션이 0개 |
| `control_char` | 해당 필드 | `\n`·`\r`·`\t` 포함 제어 문자(요약은 `\n`·`\r`·`\t` 허용) |
| `markup` | 해당 필드 | `<` 바로 뒤(선택적 `/`)에 ASCII 영문자가 오는 태그 모양, `javascript:`(대소문자 무관), ` on` + 영문 + `=`. 한글 자리표시자 `<값 입력>`과 부등호 `a < b`는 제외 |
| `bad_family` | `form` | `form.family`가 `provider_family(form.provider)`와 다름 |
| `already_public` | `visibility` | 템플릿이 이미 공개 |

## 3. 판정

`block` finding이 하나라도 있으면 `reject`(reasons = block의 reason 집합), 없고 `review`가 있으면 `escalate_to_human`(reasons = review의 reason 집합), 둘 다 없으면 `approve`(reasons = `[]`)다. `info`는 판정에 영향이 없다.

## 4. 채널

- HTTP: 위 1절. 인증·소유자 경계는 기존 엔드포인트와 같다. 서버는 소유자의 템플릿과 **모든 공개 템플릿**(개수 상한 없음)을 불러 공개 후보(`id`, `content_hash`, `sections`, `doc_type`, `locale`)를 만든다. takedown 목록은 v1에 저장소가 없어 비어 있다.
- CLI: `dmem check <TEMPLATE_ID> --license <ID> --author <TEXT>`. 판정과 무관하게 응답 JSON을 stdout에 보기 좋게 출력한다. 종료 코드는 `approve` 0, `reject`·`escalate_to_human` 4, 그 밖의 오류 1이다.
- MCP 도구는 만들지 않는다(공개 기여는 웹 흐름이다).
- 순수 함수는 `dmem-core`에 둔다. 계정·기여 흐름이 나중에 같은 함수를 호출할 수 있어야 한다.

## 5. 하지 않는 것 (명세↔구현 차이)

동의(`consent`) 기록, 검수 큐, 모델·curator 판정, 팀 가시성, DOCX/OOXML·HTML export 재가져오기, 게시 상태 변경·롤백·takedown 저장, 점수. 이름과 방식은 `gatekeeper.md`의 R0~R5와 reason enum을 따르되 R0·R5는 구현하지 않는다.

## 6. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 | 대응 GK |
|---|---|---|---|---|
| F-GP-01 | 비밀·개인정보·주입 차단 | 2절 형식 기준, 센티널 전수, 오탐 없음 | GP-02~04, GP-40 | GK-03~05 |
| F-GP-02 | 숨김 문자 | 제거 후 검사·해시, 쪼갠 비밀도 차단 | GP-05 | GK-06 |
| F-GP-03 | 구조·마크업 | 한도·제어 문자·태그·family·이미 공개 | GP-06, GP-09, GP-25 | GK-15~16 |
| F-GP-04 | 사용권 | 어휘·허용 목록·재라이선스 금지·작성자 검사 | GP-07 | GK-08, GK-10 |
| F-GP-05 | 중복·takedown | 정확·근접 중복, 정규화 동치, takedown 우선 | GP-08, GP-11, GP-21 | GK-11~13, GK-18 |
| F-GP-06 | 판정과 안전한 출력 | 판정 우선순위, 정렬, 결정성, 원문 미노출 | GP-01, GP-10, GP-12, GP-24, GP-40 | GK-17 |
| F-GP-07 | 서버 경계 | 소유자 격리, 인증, 입력 검증, 읽기 전용 | GP-20, GP-22, GP-23, GP-25, GP-26 | GK-02 |
| F-GP-08 | 실제 시드 무오탐 | 시드 복사본에서 R1·R2·R4 finding 없음 | GP-27 | GK-17 |
| F-GP-09 | CLI | 종료 코드 0·4·1, HTTP와 같은 JSON | GP-30, GP-31 | — |
