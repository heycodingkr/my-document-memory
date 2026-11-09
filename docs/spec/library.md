# LIB: 내 메모리 저장·가져오기·수정·삭제·내보내기

상태: 설계 초안(문서 우선, 구현 없음). WAM의 "기여(propose)" 대신 **내 라이브러리에 직접 저장하는 로컬 우선 흐름**을 정한 신규 명세다. 공유(게시)는 [`sharing.md`](sharing.md)가 맡는다.
영역 / 테스트 ID 접두사: `LIB` (케이스: [`../test/functional-tests.md`](../test/functional-tests.md))
기반: [`memory.md`](memory.md), [`formats.md`](formats.md), [`privacy.md`](privacy.md), [`overview.md`](overview.md) 2·5절

## 1. 범위

내 메모리는 내 DOCX·PPTX·Markdown·TXT·HTML·텍스트 PDF 양식과 참고자료, 작성 규칙이다. 기본은 **비공개**이고 로컬 모드에서는 계정 없이 쓴다. 로컬 모드는 `DMEM_HOME` 데이터 디렉터리의 단일 라이브러리를 쓰고, 서버 모드는 같은 계약을 계정 라이브러리에 적용한다.

## 2. 저장 흐름

1. **입력**: `--file`(CLI 전용), `--stdin`(Markdown·텍스트·HTML 또는 StandardDoc JSON), 인라인 `content`(MCP), `from_preview_id`(웹 가져오기 결과, [`web-import.md`](web-import.md)). MCP는 **파일 경로를 입력으로 받지 않는다**: 모델이 임의 파일을 읽게 만드는 경로를 막기 위해서다.
2. **추출**: provider·형식 어댑터가 StandardDoc을 만든다([`formats.md`](formats.md)). 추출이 비면 `extract_empty`, 지원하지 않는 형식은 `unsupported_format`.
3. **양식 결정**: `form`은 사용자가 주거나 추출기가 제안한다. 확정은 사용자(또는 명시적 인자)가 한다. 어휘 밖 값은 거부한다.
4. **정화(scrub)**: 비밀값이 있으면 전체 거부(`secret_detected`). template은 개인 값을 슬롯으로 치환하고 치환 목록을 보고한다. reference는 값을 보존하고 `contains_personal_data`를 표시한다([`memory.md`](memory.md) 7절).
5. **미리보기**: `dry_run`은 아무것도 저장하지 않고 `preview`(종류, 양식, outline, 슬롯, 통계, 경고, 정화 요약)만 돌려준다.
6. **저장**: 새 `memory_id`와 `version`를 만든다. 원본 파일은 `sha256` 주소로 보존한다. 같은 소유자의 같은 정규화 content hash와 같은 `scope_key` 재저장은 기존 항목을 돌려줄 수 있다(`created: false`). 같은 소유자의 같은 scope에서 내용이 바뀌면 명시적 `memory_id`와 `base_version`으로 새 version을 저장한다. 새 독립 양식은 다른 source scope 또는 `variant`를 지정한다. scope만으로 기존 내용을 자동 덮어쓰지 않는다.
7. **응답**: `memory_id`, `version`, `created`, `kind`, `form`, `warnings`, `scrub` 요약.

## 3. 수정과 버전

수정은 `save`에 `memory_id`와 `base_version`을 주어 새 버전을 만든다. `memory_id` 없이 저장했는데 같은 `scope_key`([`core.md`](core.md) 6절)의 active 메모리가 이미 있으면 **그 메모리의 새 버전**이 되고(이전 버전은 `superseded`) `base_version` 충돌 검사는 하지 않는다. `kind`·`provider`·`doc_type`·`locale`·`region`·`variant`·URL 패턴 중 하나라도 다르면 별개 메모리다([`core.md`](core.md) 6절의 `scope_key`). `base_version`이 현재 head와 다르면 `version_conflict`이며 아무것도 바뀌지 않는다. 이전 버전은 `superseded`로 남고 `expand --version`으로 읽을 수 있다. 두 프로세스가 동시에 같은 메모리를 수정하면 하나만 성공하고 나머지는 `version_conflict`다. 저장소 쓰기는 잠금과 원자적 교체로 보호한다.

## 4. 삭제

`delete`는 `confirm`(MCP) 또는 `--yes`(CLI)가 필요하다. TTY가 없고 `--yes`가 없으면 종료 코드 2다. 삭제는 모든 버전의 내용·색인·보존된 원본을 지운다. 공개·팀 공유 중이면 먼저 `unpublish`(비공개 전환)가 함께 일어나고 응답에 `unpublished: true`가 나온다. 이미 다른 사람이 복사한 사본은 남는다([`sharing.md`](sharing.md) 6절). 삭제 후 같은 id는 `not_found`다.

## 5. 목록·검색·가져오기

`dmem list`는 `search --scope mine`의 별칭이다. 필터: `kind`, `doc_type`, `locale`, `provider`, `visibility`, 키워드. 정렬은 `updated_at` 내림차순 + `memory_id`로 안정적이며 `cursor`로 페이지를 넘긴다. 자유 텍스트 질의는 로컬 전문 검색이고 서버로 보내지 않는다.

## 6. 내보내기

`dmem export <memory_id> --format md|html|docx|pptx|json --out <절대경로>`. 규칙은 [`formats.md`](formats.md) 5절이다(덮어쓰기 거부, 0600, 심볼릭 링크 비추종). deck은 `pptx`, document는 `docx`를 지원한다. 내보내기는 L2의 구조만 쓰며 `structure_only` 메모리에서 본문을 만들어 내지 않는다.

## 7. 로컬 저장소

```
$DMEM_HOME/            0700   기본: OS 설정 경로(macOS ~/Library/Application Support/dmem, Linux $XDG_DATA_HOME/dmem)
  config.json          0600   비밀 아닌 값만(endpoint, search_provider, 동의 상태)
  library.key          0600   HMAC 키(core.md 4절)
  library.*            0600   메모리·버전·색인(구현이 정한다: SQLite 또는 JSON 스냅샷)
  originals/<sha256>   0600   보존한 원본 파일
```

`HOME`, `XDG_*`, `DMEM_HOME`을 존중해 격리 테스트가 가능해야 한다. 파일은 소유자만 읽고 쓰며 심볼릭 링크를 따라가며 쓰지 않는다. 저장소가 손상되었으면 사용 가능한 부분을 보존하고 명확한 오류를 내며 크래시하지 않는다. 한도는 [`core.md`](core.md) 8절이다.

## 8. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-LIB-01 | 파일·stdin·인라인 저장과 미리보기 | 기본 비공개, 원본 보존, dry-run은 저장 0건 | LIB-01~03 |
| F-LIB-02 | DOCX 양식 저장 | 섹션 순서·표·스타일을 추출해 개인 양식으로 저장 | LIB-02, TPL-01 |
| F-LIB-03 | 멱등 저장 | 같은 내용·scope의 재저장은 `created:false`, 같은 version | LIB-04 |
| F-LIB-04 | 수정과 충돌 | base_version 일치 시 새 버전, 불일치 시 변경 0 | LIB-05, LIB-16 |
| F-LIB-05 | 버전 조회 | 지정 버전은 당시 내용 그대로 | LIB-06, VER-01~03 |
| F-LIB-06 | 목록·필터·페이지 | 필터, 안정 정렬, cursor | LIB-07 |
| F-LIB-07 | 비밀값 원자적 거부 | 부분 저장 0건, 응답에 값 없음 | LIB-08 |
| F-LIB-08 | 개인 정보 처리 | template 슬롯화, reference 표시와 게시 차단 | LIB-09~10 |
| F-LIB-09 | 삭제 | 확인 필요, 전체 purge, 공개본 비공개 전환 | LIB-11, LIB-15 |
| F-LIB-10 | 내보내기 | md·html·docx·json, 덮어쓰기 거부, 0600 | LIB-12, FMT-14 |
| F-LIB-11 | 로컬 저장소 | 권한·심볼릭 링크·손상 복구 | LIB-13 |
| F-LIB-12 | 한도와 빈 추출 | `payload_too_large`, `extract_empty` | LIB-14 |
