# CORE: URL·양식 키 정규화와 공통 계약

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. WAM `docs/spec/core.md`를 문서 도메인에 맞게 적응했다([포팅 지도](../design/wam-port-map.md)).
영역 / 테스트 ID 접두사: `CORE` (케이스 원본: [`../test/functional-tests.md`](../test/functional-tests.md))
기준 문서: [`overview.md`](overview.md) v0.3 (제품 범위), [`form.md`](form.md) (양식 객체)

## 1. 목적

메모리는 "어디서(URL 범위) 어떤 양식(provider·문서 종류·로케일)의 문서를 쓰는가"에 붙는 재사용 자산이다. 같은 `docs.google.com` 안에서도 문서·슬라이드·시트는 서로 다른 양식 체계이고, 같은 이력서도 국가별로 용지·날짜·필수 항목이 다르다. 모든 클라이언트(CLI, MCP, host adapter, 서버)가 같은 정규화를 써야 recall, 중복 판정, 공유, 점수 귀속이 일치한다.

URL은 **위치 키**, 양식은 **형태 키**다. 둘 다 정규화된 값만 저장·전송한다. 원본 URL 문자열은 어느 저장소·로그·요청에도 두지 않는다.

## 2. URL 정규화 계약

입력은 브라우저 주소나 사용자가 붙여 넣은 링크다. 결과는 `host + path pattern`으로 이루어진 **canonical URL pattern**(스킴 없음)이며 원래 URL 문자열이 아니다. 순서는 다음과 같다.

1. **스킴**: `https`만 허용한다. 그 밖(`http`, `file`, `ftp`, `data`, `javascript` 등)은 `url_rejected: scheme_not_allowed`. 예외는 9절의 격리 테스트 모드뿐이다.
2. **userinfo·fragment·쿼리**: userinfo가 있으면 `url_rejected: userinfo_not_allowed`로 거부한다. fragment와 **쿼리 전체**(키 이름 포함)는 버린다. `usp`, `resourcekey`, `utm_*`, `gclid` 같은 목록을 따로 두지 않고 전부 제거한다.
3. **호스트**: NFKC·소문자·IDNA(Punycode)로 표준화하고 후행 점을 지운다. IP 리터럴(IPv4/IPv6, 10진·16진·8진 표기 포함), `localhost`, 단일 라벨 호스트, 사설·링크로컬·메타데이터 주소로 해석되는 이름은 `url_rejected: host_not_allowed`다. 기본 포트(443)는 지우고, 그 밖의 포트는 `host_not_allowed`다.
4. **경로 분해**: 퍼센트 디코드 후 NFKC, 세그먼트로 나눈다. 세그먼트마다 아래 5절 규칙을 순서대로 적용한다.
5. **동적 세그먼트 변수화**(위에서부터 첫 일치):
   1. provider 전용 규칙(3절)이 지정한 위치.
   2. 이메일 형태(`@`와 `.` 포함): URL 전체를 `url_rejected: pii_in_url`로 거부한다.
   3. `@handle` → `:handle`.
   4. 숫자만으로 이루어진 세그먼트 → `:id`.
   5. UUID(8-4-4-4-12 hex) 또는 길이 16 이상의 hex만으로 된 세그먼트 → `:id`.
   6. `<slug>-<hex 8자 이상 또는 숫자 4자 이상>`으로 끝나는 세그먼트 → `:id` (slug는 버린다. slug에 사적인 단어가 있을 수 있다).
   7. 길이 20 이상이고 `[A-Za-z0-9_-]`만 쓰며 숫자와 영문자를 모두 포함 → `:id`.
   8. 그 밖에는 고정 단어다. 허용 문자는 유니코드 글자·숫자와 `._~-`, 길이는 40 이하이며 **소문자로 바꾼다**(변수 판정을 먼저 하고 소문자화는 마지막에 한다. `/Templates`와 `/templates`는 같은 패턴이다). `/document`처럼 `/d/<id>` 없는 Google 경로는 `docs.google.com/document`로 후퇴한다.
6. **분류 불가**: 8번을 만족하지 못하는 세그먼트가 있으면 그 세그먼트부터 뒤를 전부 버리고 상위 경로로 후퇴한다. 세그먼트는 최대 8개만 남긴다. 후행 슬래시는 지운다. 호스트만 남으면 `host/`다.
7. 결과 문자열은 `host` + `/` + 세그먼트 목록이다. 예: `docs.google.com/document/d/:id/edit`.

### 예시

| 입력 | canonical pattern | provider |
|---|---|---|
| `https://docs.google.com/document/d/FIXTURE_DOC_ID_0123456789ABCDEFGHIJKLMNOPQ/edit?usp=sharing&resourcekey=0-x#heading=h.abc` | `docs.google.com/document/d/:id/edit` | `google_docs` |
| `https://docs.google.com/document/u/1/d/FIXTURE_DOC_ID_0123456789ABCDEFGHIJKLMNOPQ/edit` | `docs.google.com/document/d/:id/edit` | `google_docs` |
| `https://docs.google.com/presentation/d/FIXTURE_DECK_ID_0123456789ABCDEFGHIJKLMNO/edit#slide=id.p3` | `docs.google.com/presentation/d/:id/edit` | `google_slides` |
| `https://docs.google.com/spreadsheets/d/FIXTURE_SHEET_ID_0123456789ABCDEFGHIJKLMN/edit?gid=0` | `docs.google.com/spreadsheets/d/:id/edit` | `google_sheets` |
| `https://www.notion.so/myws/Quarterly-Report-0123456789abcdef0123456789abcdef?pvs=4` | `www.notion.so/:id` | `notion` |
| `https://acme.notion.site/Invoice-Template-0123456789abcdef0123456789abcdef` | `acme.notion.site/:id` | `notion` |
| `https://www.example.org/forms/invoice.docx?download=1` | `www.example.org/forms/invoice.docx` | `docx` |
| `https://example.com/templates/resume/modern?utm_source=x#top` | `example.com/templates/resume/modern` | `other` |
| `https://example.com/people/948203/profile` | `example.com/people/:id/profile` | `other` |
| `https://example.com/blog/my-private-project-948203` | `example.com/blog/:id` | `other` |
| `https://user:pw@example.com/` | 거부 `userinfo_not_allowed` | |
| `http://example.com/` | 거부 `scheme_not_allowed` | |
| `https://192.168.0.1/x` | 거부 `host_not_allowed` | |
| `https://example.com/u/jane.doe@corp.test/doc` | 거부 `pii_in_url` | |

## 3. provider 감지와 전용 경로 규칙

provider는 canonical URL과 확장자로 결정한다. URL만으로 정할 수 없으면 `other`이며, 가져오기에서 Content-Type을 확인한 뒤 `html`·`pdf` 등으로 갱신될 수 있다([`web-import.md`](web-import.md)).

| provider | family | 감지 규칙 | 전용 경로 규칙 |
|---|---|---|---|
| `google_docs` | document | `docs.google.com` + `/document/` | `/document[/u/N]/d/<id>[/<tail>]` → `/document/d/:id/<tail>`. `u/N` 제거. `<tail>`은 `edit`, `view`, `preview`, `copy`, `export`, `template` 첫 단어만 유지하고 나머지는 버린다 |
| `google_slides` | deck | `docs.google.com` + `/presentation/` | 위와 같다(`/presentation/d/:id/...`) |
| `google_sheets` | sheet | `docs.google.com` + `/spreadsheets/` | 위와 같다(`/spreadsheets/d/:id/...`) |
| `notion` | document | `notion.so`, `www.notion.so`, `*.notion.site` | 마지막 세그먼트가 `<slug>-<hex32>` 또는 `<hex32>`이면 `:id`. `notion.so`의 앞쪽 워크스페이스 슬러그 세그먼트는 버린다. `*.notion.site`의 서브도메인(호스트)은 유지한다 |
| `docx` / `pptx` / `xlsx` | document / deck / sheet | 경로 확장자 `.docx` / `.pptx` / `.xlsx` | 일반 규칙 |
| `pdf` | document | `.pdf` | 일반 규칙 |
| `markdown` / `txt` | document | `.md`·`.markdown` / `.txt` | 일반 규칙 |
| `html` | document | 가져오기 응답이 `text/html`일 때만(URL 단계에서는 `other`) | 일반 규칙 |
| `other` | — | 그 밖 전부(Google Forms, Drive 폴더, Canva, Figma 포함) | 일반 규칙 |

Google 시트는 family `sheet`이며 v1에서는 provider 감지와 메타데이터 보존까지만 지원한다([`overview.md`](overview.md): 시트는 후속). provider 이름은 닫힌 어휘이고 [`form.md`](form.md)가 정한다(원본: [`../../contracts/vocab/providers.json`](../../contracts/vocab/providers.json), 확장자·호스트 매핑 포함).

## 4. 능력 URL (capability URL)

URL 자체가 접근 권한인 호스트다. "링크가 있는 모든 사용자" 공유 문서의 ID가 곧 열쇠이므로 ID를 저장하거나 공개하면 안 된다. 능력 호스트: `docs.google.com`, `drive.google.com`, `notion.so`·`*.notion.site`, `dropbox.com`, `onedrive.live.com`·`1drv.ms`·`*.sharepoint.com`, `canva.com`, `figma.com`.

- canonical pattern의 ID 세그먼트는 이미 `:id`다. 능력 호스트의 **원본 ID·`resourcekey`·공유 토큰**은 저장소, 로그, 캐시, 진단, 텔레메트리, 프로세스 인자, 오류 메시지, 게시 데이터 어디에도 남기지 않는다.
- 출처 추적(provenance)은 `source_ref`만 쓴다: `source_ref = "src_" + base32(HMAC-SHA256(library_key, url_without_query))[0:26]`. 입력 `url_without_query`는 **원본 URL에서 query·fragment·userinfo를 뺀 값**(경로의 문서 ID는 포함)이다. `:id`로 바뀐 canonical 패턴을 넣으면 모든 문서가 같은 값이 되어 중복 감지를 할 수 없다. `library_key`는 라이브러리마다 처음 사용할 때 만든 32바이트 난수이고 소유자만 읽을 수 있는 파일(0600)에 둔다. 같은 URL을 다시 가져오면 같은 `source_ref`가 나오므로 중복 감지는 가능하고, 값에서 ID를 복원할 수 없다. `source_ref`는 게시 데이터에 포함하지 않는다(공개 출처는 `source_host`만).
- 능력 호스트가 아닌 공개 사이트는 query·fragment를 뺀 canonical URL을 출처로 보존할 수 있다(출처 표시용, [`sharing.md`](sharing.md)).
- 가져오기 요청은 사용자가 준 원본 URL을 **프로세스 안에서 일시적으로만** 쓰고 저장하지 않는다.

## 5. 양식 키 정규화

양식 객체의 필드와 어휘는 [`form.md`](form.md)가 정한다. 이 문서가 정하는 것은 정규화 순서다.

1. `doc_type`: NFKC → 소문자 → 공백 정리 → 별칭 표로 canonical id. 별칭이 variant를 함의하면 함께 채운다(`履歴書` → `resume` + `jp_rirekisho`). 어휘에 없으면 `invalid_form: doc_type_unknown`.
2. `locale`: `ko_KR`, `KO-kr`, `ko-kr` → `ko-KR`. 언어만(`ko`)도 허용하며 region은 비어 있다. 어휘 밖이면 `invalid_form: locale_unknown`.
3. `provider`: 명시값이 있으면 그것을, 없으면 URL에서 감지한 값을 쓴다. 둘이 다르면 **명시값이 우선**이고 오류가 아니다.
4. `family`는 provider에서 파생한다. `doc_type`의 family와 다르면 `invalid_form: family_mismatch`다.

## 6. 비교 키

- 소유자 범위 키: `scope_key = (owner_id, site_host, canonical_url_pattern, kind, provider, doc_type, locale, region, variant)`. 한 소유자 라이브러리에서 같은 scope에는 active memory/template lineage 하나만 둔다. provider·region·variant가 다르면 별도 scope로 공존한다.
- 양식 정체성: `(owner_id, memory_id)`이며 template은 이를 `template_id`로 표시할 수 있다. scope의 active lineage 안에서 version을 불변으로 쌓는다. 서로 다른 소유자는 같은 scope를 각각 기여할 수 있고 공개 카탈로그의 중복/개선 판정은 [`sharing.md`](sharing.md)가 담당한다.
- `content_fingerprint`는 정확 중복 후보를 찾는 용도다. scope가 같다는 이유만으로 내용을 자동 병합·덮어쓰지 않는다. 같은 소유자의 변경은 `memory_id`와 `base_version`을 명시하고 새 version으로 저장한다.
- recall 조회 키: canonical URL + 선택적 `doc_type`, `locale`, `provider`, `kind`([`recall.md`](recall.md)).

## 7. 공통 오류 코드

모든 표면(CLI, MCP, HTTP)은 아래 고정 코드만 쓴다. 메시지는 코드별 고정 문구이며 **입력값을 되돌려 주지 않는다**(센티널·URL·본문 에코 금지). 선택 필드는 `reason`(고정 enum), `trace_id`, `retry_after_seconds`뿐이다.

| code | 의미 | CLI 종료 코드 | HTTP |
|---|---|---|---|
| `invalid_input` | 스키마·필드 검증 실패, 알 수 없는 필드. 기존 owner scope에 다른 내용을 식별자 없이 저장하면 `reason: scope_conflict` | 2 | 400 |
| `non_canonical_url` | MCP·서버가 비정규 URL을 받음 | 2 | 422 |
| `url_rejected` | 2절에서 거부. `reason`: `scheme_not_allowed`, `userinfo_not_allowed`, `host_not_allowed`, `pii_in_url`, `too_long`, `unclassifiable` | 2 | 422 |
| `invalid_form` | `reason`: `doc_type_unknown`, `locale_unknown`, `provider_unknown`, `variant_invalid`, `page_invalid`, `family_mismatch` | 2 | 422 |
| `secret_detected` | 비밀값 형태 발견. 위치·값은 응답에 넣지 않는다 | 2 | 422 |
| `payload_too_large` | 입력 한도 초과 | 2 | 413 |
| `unsupported_format` | 지원하지 않는 파일·콘텐츠 형식 | 2 | 415 |
| `extract_empty` | 추출 결과가 비었음. `reason`: `ocr_required`, `no_text` | 2 | 422 |
| `fetch_blocked` | 가져오기 정책 거부. `reason`: `private_address`, `scheme`, `port`, `redirect_limit`, `size`, `content_type`, `timeout`, `signal_noai`, `login_required`. `login_required`의 `message`는 대안(파일을 내려받아 `--file`로 가져오기, 현재 탭 클립)을 안내하는 입력과 무관한 고정 문장이다 | 2 | 422 |
| `auth_required` | 인증이 필요하거나 만료됨 | 3 | 401 |
| `consent_required` | 동의가 없거나 버전이 다름 | 4 | 403 |
| `scope_required` | 권한 부족 | 4 | 403 |
| `license_forbids` | 라이선스가 요청한 복사·게시를 허용하지 않음 | 4 | 403 |
| `version_conflict` | `base_version`이 현재 버전과 다름 | 4 | 409 |
| `handle_unavailable` | 공개 handle이 예약되었거나 이미 사용 중이다. 소유자·이메일을 공개하지 않는다 | 4 | 409 |
| `search_unavailable` | 웹 검색 provider 미설정 또는 장애 | 5 | 503 |
| `fetch_failed` | 원격 사이트 오류. `reason`: `dns`, `tls`, `status_4xx`, `status_5xx`, `reset` | 5 | 502 |
| `server_unavailable` | 서버·네트워크 불가 | 5 | 503 |
| `rate_limited` | 호출 제한 | 6 | 429 |
| `not_found` | 없거나 접근 불가. **존재 여부를 숨긴다**(타인의 비공개와 없는 ID를 구분할 수 없다) | 7 | 404 |
| `internal` | 예기치 않은 오류 | 1 | 500 |

## 8. 한도 (단일 출처)

다른 명세는 이 표를 인용한다. `est_tokens(x) = ceil(utf8_bytes(x) / 4)`다. `utf8_bytes(x)`는 `x`를 **컴팩트 JSON**(구분자 `,`·`:`에 공백 없음, 비ASCII 문자를 이스케이프하지 않음)으로 직렬화한 UTF-8 길이다. 공백이 있는 직렬화는 더 길어 같은 객체가 한도를 넘어 보일 수 있으므로 한도 판정에 쓰지 않는다.

| 항목 | 한도 |
|---|---|
| URL 입력 길이 | 2,048자 |
| 경로 세그먼트 | 8개(고정 단어 ≤40자) |
| L0 직렬화 / `url_patterns` / `keywords` | ≤1 KiB / ≤4개 / ≤8개(각 ≤32자) |
| title / summary / key_points / outline | ≤120자 / ≤600자 / ≤6개×≤160자 / ≤12항목×≤60자 |
| L1 힌트 | 힌트당 ≤400 est tokens, recall당 ≤3개 |
| L2 직렬화 | ≤64 KiB. 더 큰 내용은 `cursor`로 나눠 읽는다 |
| search 페이지 | ≤20개 |
| 업로드 파일 / 인라인 `content` | ≤10 MiB / ≤1 MiB |
| 가져오기 응답 본문 / 시간 / 리다이렉트 | ≤5 MiB / 10초 / 3회 |
| preview 유효 시간 | 15분 |
| MCP stdio 프레임 / 동시 요청 | ≤64 KiB / ≤16 |
| 웹 검색 query | ≤200자 |
| `web preview`·`import`(URL) 호출 속도 / 동시 | 라이브러리(서버 모드는 사용자)당 분당 30회(제안) / 4건(제안). 초과는 `rate_limited`이고 상태가 바뀌지 않는다 |

## 9. 격리 테스트 모드

실제 사이트 없이 provider별 경로를 시험하기 위한 모드다. `DMEM_ISOLATED=1`**이고** 대상이 loopback일 때만 켜진다. 프로덕션 빌드에서는 비활성이어야 하며 켜지면 `status`가 `isolated: true`를 표시한다.

- loopback(`127.0.0.1`, `[::1]`, `localhost`)의 `http`와 임의 포트를 허용한다.
- 경로가 `/p/<provider-key>/...`이면 해당 provider의 실제 호스트로 간주해 같은 규칙을 적용한다. `google-docs`·`google-slides`·`google-sheets`는 `docs.google.com`, `notion`은 `www.notion.so`다(`google-sheets-csv`는 내보내기가 CSV만 제공하는 시험용 변형으로 `google-sheets`와 같은 호스트다)(예: `/p/google-docs/document/d/X/edit` → `docs.google.com/document/d/:id/edit`).
- 그 밖의 loopback 경로는 호스트를 `fixture.test`로 치환한다(포트와 무관하게 결과가 결정적이다).
- 이 모드에서도 사설 주소 차단 규칙은 loopback 외 대상에 그대로 적용된다.

## 10. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-CORE-01 | 정규화는 모든 구현에서 동일하다 | CLI·서버·host adapter가 같은 입력에 같은 canonical을 낸다 | CORE-01, CORE-22 |
| F-CORE-02 | 스킴·userinfo·쿼리·fragment·포트 규칙 | 거부 사유가 고정 코드이고 센티널이 응답·로그에 없다 | CORE-02~06 |
| F-CORE-03 | 호스트 안전 | IP·localhost·사설 대역·비기본 포트를 거부하고 격리 모드(9절)는 별도다 | CORE-06~08 |
| F-CORE-04 | 동적 세그먼트 변수화 | 두 계정의 서로 다른 ID가 같은 패턴이 된다 | CORE-09~14 |
| F-CORE-05 | provider 감지와 전용 경로 | docs·slides·sheets·notion·확장자·other가 규칙대로다 | CORE-15~18 |
| F-CORE-06 | 능력 URL의 원본 ID 비저장 | sink 전수에서 원본 ID 0건, 같은 URL의 `source_ref`가 안정적이다 | CORE-19~20 |
| F-CORE-07 | 정규화 실패는 안전하게 후퇴한다 | 요청 0건·원문 미저장, 빈 결과 또는 거부 | CORE-21~22 |
| F-CORE-08 | 오류는 고정 코드이며 입력을 에코하지 않는다 | 모든 표면의 오류에서 센티널 0건 | CORE-23 |
| F-CORE-09 | 한도를 강제한다 | 초과 입력은 `url_rejected: too_long` 또는 `payload_too_large` | CORE-24 |
| F-CORE-10 | 양식 키 정규화 | 별칭·locale·provider 충돌이 5절대로 처리된다 | FORM-01~07, FORM-10 |
