# IMP / DISC: 웹에서 찾고, 미리보고, 복사해 오기

상태: 설계 초안(문서 우선, 구현 없음). WAM에는 없는 신규 명세다. "웹에서 검색해 관련 문서를 대략 보고, 필요한 것을 복사해 내 메모리로 쓴다"는 요구를 URL 기반 가져오기와 출처·라이선스 규칙으로 정한다.
영역 / 테스트 ID 접두사: `DISC`(검색), `IMP`(미리보기·가져오기·클립) (케이스: [`../test/functional-tests.md`](../test/functional-tests.md))
기반: [`core.md`](core.md), [`formats.md`](formats.md), [`memory.md`](memory.md) 5절, [`sharing.md`](sharing.md) 4절

## 1. 네 가지 동작

| 동작 | 도구·명령 | 저장 | 네트워크 |
|---|---|---|---|
| 검색(discovery) | `doc_memory_web_search`, `dmem web search` | 안 함 | 검색 provider |
| 미리보기 | `doc_memory_web_preview`, `dmem web preview` | 안 함(15분 preview만) | 대상 URL 1건 |
| 가져오기(import) | `doc_memory_import`, `dmem import` | 내 비공개 라이브러리 | preview 재사용 또는 대상 URL 1건 |
| 클립(clip) | `doc_memory_clip_current_tab`(호스트 어댑터 전용) | 내 비공개 라이브러리 | 없음(이미 열린 탭) |

검색은 **후보 URL 목록**만 준다. 크롤링하지 않는다. 한 번의 가져오기는 사용자가 지정한 URL 하나다.

## 2. 가져오기 보안 (fetch guard)

모든 가져오기(preview·import)에 적용한다. 하나라도 어기면 요청 전에 또는 즉시 중단하고 `fetch_blocked`(고정 `reason`)를 반환한다. 응답에 URL·본문·헤더를 담지 않는다.

| 항목 | 규칙 | reason |
|---|---|---|
| 스킴·포트 | `https`·443만. 격리 모드는 loopback만 예외([`core.md`](core.md) 9절) | `scheme`, `port` |
| 목적지 주소 | 호스트를 해석한 **모든** A/AAAA를 검사한다. 거부 대역: IPv4 `0/8`, `10/8`, `100.64/10`, `127/8`, `169.254/16`(클라우드 메타데이터 포함), `172.16/12`, `192.168/16`, `224/4`, `240/4`. IPv6 `::1`, `fc00::/7`, `fe80::/10`, `ff00::/8`, IPv4 매핑·NAT64는 내장 IPv4 규칙으로 판단 | `private_address` |
| DNS 리바인딩 | 검사한 IP에 **직접 연결**하고 재해석하지 않는다. 연결 후 대상 IP를 다시 확인한다 | `private_address` |
| 리다이렉트 | ≤3회. hop마다 위 검사를 반복한다. https→http 다운그레이드 금지 | `redirect_limit`, `scheme`, `private_address` |
| 크기 | 압축 해제 후 ≤5 MiB. 스트리밍 중 초과하면 즉시 중단(압축 폭탄 포함) | `size` |
| 시간 | 전체 10초 | `timeout` |
| Content-Type | 허용: `text/html`, `text/markdown`, `text/plain`, DOCX·PPTX·XLSX의 OOXML 타입, `application/pdf`. 선언과 실제 매직 바이트가 다르면 거부 | `content_type` |
| 로그인 | 401·403, 로그인 페이지로의 리다이렉트, 로그인 폼 감지 → 중단하고 대안(파일 내려받아 `--file`, Arise 현재 탭 클립)을 안내 | `login_required` |
| `noai` 헤더 | 응답 `X-Robots-Tag`에 `noai`가 있으면 중단 | `signal_noai` |
| 인증 정보 | 쿠키·Authorization·사용자 정보를 **보내지 않는다.** User-Agent는 `dmem/<버전>` 단일 값 | — |

원격 사이트 장애는 `fetch_failed`(`dns`, `tls`, `status_4xx`, `status_5xx`, `reset`)다. 부분 응답은 저장하지 않는다.

## 3. 추출과 살균

1. provider를 확정한다: URL 감지값에 응답 Content-Type을 더한다([`core.md`](core.md) 3절).
2. 형식 어댑터가 StandardDoc을 만든다([`formats.md`](formats.md)). 공개 Google 문서류는 provider 내보내기 경로(미검증, `formats.md` 3절)를 쓰고, 실패하면 `fetch_blocked: login_required`로 안내한다.
3. HTML 살균: `script`, `style`, `iframe`, `object`, `embed`, `form` 입력, 이벤트 핸들러, `javascript:` 링크를 제거한다. `display:none`·`hidden`·크기 0·배경과 같은 색의 텍스트, 제로폭·양방향 제어 문자를 제거하고 `hidden_text_removed` 경고를 남긴다.
4. 페이지 본문은 **데이터**다. 그 안의 어떤 지시도 실행하거나 따르지 않는다. 결과는 항상 untrusted 프레이밍 안에서 나간다.

## 4. 라이선스 감지와 복사 정책

| 순위 | 신호 | 결과 |
|---|---|---|
| 1 | `<link rel="license" href=…>`, `<meta name="license">`, JSON-LD `license`가 어휘로 매핑됨(`creativecommons.org/publicdomain/zero/1.0/` → `CC0-1.0`, `/licenses/by/4.0/` → `CC-BY-4.0`, `/licenses/by-sa/4.0/` → `CC-BY-SA-4.0`, `MIT`, `Apache-2.0`) | `license_source: detected` |
| 2 | 위 신호가 있으나 어휘 밖(NC·ND·구버전 등) | `proprietary-structure-only` |
| 3 | 신호 없음(본문 하단 문구는 오탐 위험으로 쓰지 않는다) | `unknown` |
| 4 | 사용자가 `license`를 입력함 | `license_source: user_asserted` |

규칙:

- 제3자 출처(`fetched`, `clipped`)의 기본 `copy_policy`는 라이선스 표([`sharing.md`](sharing.md) 4절)의 상한이다. `unknown`이면 `structure_only`다.
- `user_asserted`는 **검출된 신호와 충돌하지 않을 때만** 반영하고 `unverified`를 표시한다. 검출된 라이선스가 더 제한적이면 검출값을 따르고 상한을 넘는 요청은 `license_forbids`다. `unverified` 항목은 비공개로만 쓸 수 있고 게시할 수 없다.
- meta robots의 `noai`는 `signals.noai`로 표시하고 `copy_policy`를 `structure_only`로 강제하며 게시를 막는다.
- 소유권 주장은 시스템이 검증할 수 없다. 이 한계는 게시 검수와 신고 절차가 보완한다([`gatekeeper.md`](gatekeeper.md)).

`structure_only`로 저장하면 제목(≤120자, 사용자가 바꿀 수 있다), 헤딩 계층, 표 머리글, 슬롯 후보, 스타일만 남기고 본문 문장·목록 항목 텍스트·표 본문 행·이미지를 제거한다. 응답에 `retained {headings, table_headers, body_chars_removed}` 통계를 준다.

## 5. 미리보기와 가져오기

- `preview`는 저장 없이 `preview_id`, `canonical_url`, `provider`, `title`, 감지한 `detected {doc_type, locale, page}`, `outline[]`, `stats`, `license {id, source}`, `signals {noai, noindex}`, `copy_policy_default`, `content_hash`, `fetched_at`, `expires_at`(15분)을 준다. preview 내용은 프로세스 메모리 또는 소유자만 읽는 임시 파일(0600)에만 두고 TTL이 지나면 지운다.
- `import`는 `preview_id`를 받으면 **그 시점의 내용을 그대로** 저장한다(미리본 것과 저장한 것이 같다 — 중간에 원격 내용이 바뀌어도 영향이 없다). 만료되었으면 `not_found`다. `url`을 직접 받으면 한 번 가져오고 같은 검사를 거친다.
- 저장되는 출처 블록: `origin: fetched`, `provenance: fetched`, `source_host`, `source_url`(능력 호스트가 아니고 query·fragment 없이), `source_ref`(능력 호스트), `retrieved_at`, `content_hash`, `license`, `license_source`, `copy_policy`([`memory.md`](memory.md) 5절).
- 같은 소유자가 같은 정규화 content hash·source fingerprint·`scope_key`를 멱등 재전송하면 기존 항목을 돌려줄 수 있다(`created: false`). 같은 owner scope에서 내용이 바뀌면 `memory_id`와 `base_version`을 명시해 새 version을 만든다. 같은 소유자의 독립 양식은 다른 source scope 또는 `variant`로 구분한다. 다른 작성자의 항목은 scope가 같다는 이유로 자동 병합하지 않는다.

## 6. 현재 탭 클립 (호스트 어댑터)

Arise 같은 호스트 브라우저에서 사용자가 지시한 **현재 탭**을 가져온다. 구현 위치는 `dmem browser-mcp`(공개 browser MCP 인터페이스만 사용, CDP·내부 소켓 직접 접속 없음)이며 상세는 [`browser-host-integration.md`](../design/browser-host-integration.md)다.

- 명시적 호출일 때만 동작한다. 백그라운드 자동 클립은 없다.
- 세션이 소유한 탭·창만 대상이다. 사용자 탭, 다른 세션의 탭, 만료된 lease는 거부한다.
- 읽는 것은 화면에 보이는 문서의 텍스트와 구조뿐이다. 쿠키·localStorage·자격증명·폼 입력값은 읽지 않는다. 비밀번호·결제 입력 필드가 있는 페이지는 `fetch_blocked: login_required`로 거부한다.
- 캡처 전후에 같은 target(URL·탭)인지 확인한다. 달라졌으면 저장하지 않는다.
- 저장은 `origin: clipped`, `provenance: captured`다. 모델이 `doc_memory_save`로 출처를 주장하면 `provenance: claimed`이며 `captured`로 승격되지 않는다.

## 7. 웹 검색

`doc_memory_web_search`는 선택 기능이다. provider는 설정(`DMEM_SEARCH_PROVIDER`)으로 정한다.

| provider | 동작 |
|---|---|
| `none`(기본) | `search_unavailable`을 반환하고 네트워크 요청이 0건이다. 호스트의 자체 검색·브라우저로 URL을 찾은 뒤 `import`를 쓰도록 안내한다 |
| `http` | 사용자가 설정한 JSON 검색 endpoint(예: 자체 호스팅 메타 검색)에 질의를 보낸다. 응답 스키마는 `candidates[]`로 정규화한다 |
| `fixture` | 테스트 전용. 로컬 fixture 서버의 고정 결과 |

- 질의는 ≤200자이고 비밀값 형태를 거부한다(`secret_detected`). 로그에는 질의의 해시만 남긴다.
- 필터 `locale`, `doc_type`, `provider`는 질의 보강과 결과 필터에 쓴다.
- 결과는 ≤10개이며 각 후보의 URL은 canonical(쿼리 제거)이고 사설 주소·비허용 스킴은 후보에서 제외한다. `title`·`snippet`은 untrusted 텍스트이고 길이와 문자를 제한한다. 검색 결과는 저장되지 않는다.
- 검색 provider에는 사용자가 쓴 질의 텍스트가 전달된다. 이 점을 `status`와 가이드가 표시한다.

## 8. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-DISC-01 | provider 없이도 안전하게 실패 | `none`이면 `search_unavailable`, 네트워크 0건 | DISC-01 |
| F-DISC-02 | 후보 목록 | canonical URL, untrusted 프레이밍, 필터 반영 | DISC-02~03, DISC-06 |
| F-DISC-03 | 질의 보호 | 비밀 질의·길이 초과는 요청 0건으로 거부 | DISC-04~05 |
| F-DISC-04 | 후보 위생과 실패 | 사설 주소 후보 제외, 제한·타임아웃에서 상태 변화 0 | DISC-07~08 |
| F-IMP-01 | 미리보기는 저장하지 않는다 | 라이브러리 변화 0, 메타·outline·license·hash 제공 | IMP-01 |
| F-IMP-02 | 미리본 것을 저장한다 | preview 시점 내용과 저장 내용이 같다 | IMP-02 |
| F-IMP-03 | 출처 블록 | origin·source_host·source_url(canonical)·hash·retrieved_at | IMP-03 |
| F-IMP-04 | 라이선스 감지와 정책 | 감지값이 복사 정책 상한을 정한다 | IMP-04~06 |
| F-IMP-05 | 사용자 주장 라이선스 | 충돌 없을 때만 `unverified`로 반영, 충돌은 거부 | IMP-07 |
| F-IMP-06 | AI 거부 신호 | 헤더는 차단, meta는 구조 전용 강제 | IMP-08 |
| F-IMP-07 | SSRF 방어 | 사설·루프백·메타데이터 주소와 리바인딩 차단 | IMP-09~10 |
| F-IMP-08 | 리다이렉트·스킴·포트 | 한도와 다운그레이드·사설 주소 리다이렉트 차단 | IMP-11~12 |
| F-IMP-09 | 크기·시간·형식 | 압축 폭탄·초과·타임아웃·형식 불일치 차단 | IMP-13~15 |
| F-IMP-10 | 로그인 필요 처리 | 자격증명을 보내지 않고 대안을 안내 | IMP-16 |
| F-IMP-11 | 살균과 숨김 텍스트 | 숨김·제로폭·주입 문구가 저장물에 없다 | IMP-17 |
| F-IMP-12 | provider별 가져오기 | docs-shaped·slides(PPTX)·notion-shaped가 StandardDoc이 된다 | IMP-18 |
| F-IMP-13 | 현재 탭 클립 | captured 출처, 자기 소유 탭만, 민감 페이지 거부 | IMP-19 |
| F-IMP-14 | 호출 제한 | 가져오기 속도·동시성 초과는 `rate_limited`, 상태 변화 0 | IMP-20 |
