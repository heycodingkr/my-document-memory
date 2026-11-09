# 유저 플로우 (FLOW)

상태: 케이스 정의(문서 우선). 사용자 한 명이 목표를 이루는 **여정**을 웹·CLI·MCP·호스트에 걸쳐 끝까지 확인한다. 단위 계약은 [`functional-tests.md`](functional-tests.md)가, 호스트 연결은 [`host-smoke.md`](host-smoke.md)가 다루고, 여기서는 단계가 이어질 때의 상태 일관성과 증거를 본다. 단계 열은 `R1`(runtime-v1 이상)·`F`(전체)다. 웹 단계는 제품의 L3 테스트가 실행하고 하네스는 CLI·MCP 단계를 실행한다.

| ID | 단계 | 여정(입력 → 단계) | 기대와 판정 근거 | 관련 케이스 |
|---|---|---|---|---|
| FLOW-01 | R1 | **내 양식 만들어 쓰기**: DOCX 양식(`tpl01`)을 올린다 → 추출 미리보기(구조·스타일) 확인 → 개인 양식으로 저장 → 그 양식으로 새 문서 → 편집 → 저장 → Markdown·DOCX 내보내기 | 저장한 양식의 섹션 순서·표·스타일이 문서에 이어지고, 저장 v1·v2가 남으며, 내보낸 파일이 `FMT` 규칙을 지킨다. 새로고침 뒤 재조회해도 같다(`RT-12`) | FMT-05, LIB-02, LIB-05, TPL-01, DOC-01 |
| FLOW-02 | R1 | **공개 양식 찾아 복사해 쓰기**: 공개 시드 양식 검색 → 미리보기(작성자·라이선스·버전) → 내 라이브러리로 복사 → 새 문서 작성 → 내보내기 | 복사본은 비공개 새 메모리이고 원본 id·버전·작성자·라이선스를 보존한다. 원본은 변하지 않는다 | SHR-10, SHR-11, TPL-02 |
| FLOW-03 | F | **에이전트가 내 양식으로 작성**: 라이브러리(`RCL-LIB`)를 둔 뒤 에이전트가 Docs 편집 화면 URL과 `doc_type=resume`, `locale=ko-KR`로 recall → 힌트의 슬롯을 채움 → 값이 없는 슬롯은 `{{확인 필요: 항목}}`로 남김 → 사용 결과 보고 | 첫 힌트가 M1(`RCL-01`), 지어낸 값이 없고, 연결 계정이면 receipt로 outcome이 기록된다. recall 요청에 원본 URL·프롬프트가 없다 | RCL-01, RCL-17, BEH-01, BEH-03, DOC-02 |
| FLOW-04 | F | **다른 사람 양식 둘러보기 → 복사 → 편집 → 게시**: `bob`이 공개 검색에서 `alice`의 CC-BY 양식을 찾고 `expand`로 라이선스 확인 → `copy` → 수정해 새 버전 → 동의하고 CC-BY로 게시 | 복사 시 `derived_from`이 최초 작성자 `alice`를 가리키고, 게시본의 attribution에 `alice`가 있으며, 검수 뒤 공개 검색에 `bob`의 게시본이 `alice` 출처와 함께 나온다. `alice`의 원본은 변하지 않는다 | SHR-01, SHR-11, SHR-13, SHR-20 |
| FLOW-05 | F | **웹에서 찾아 가져오기(허용 라이선스)**: `web search` → `web preview resume-ko.html`(CC-BY 감지) → `import --as template` → `recall`로 다시 찾기 | preview는 저장 없음, import는 preview 시점 내용 그대로, 출처 블록(`origin: fetched`, canonical URL, `content_hash`)이 있고 recall 힌트에 라이선스·출처가 표시된다 | DISC-02, IMP-01~04, SMK-09 |
| FLOW-06 | F | **웹에서 가져오기(라이선스 없음)**: `license-none.html` preview → import → 구조 전용 양식에 내 내용으로 작성 → 게시 시도 | 본문 prose가 저장되지 않고 구조만 남으며, `--copy-mode full`은 `license_forbids`, 게시는 거부된다(제3자 `unknown`) | IMP-05, IMP-06, MEM-14, SHR-13 |
| FLOW-07 | F | **현재 탭 클립(Arise)**: 사용자가 연 문서 탭에서 명시적으로 `doc_memory_clip_current_tab` → 내 라이브러리 → `recall` | `captured` 출처, 탭 URL이 canonical로 저장(쿼리·fragment 없음), 숨김 문구 없음, 사용자 탭·다른 세션 탭은 건드리지 않는다. 클립 뒤 `dmem`이 만든 탭이 없다 | IMP-19, SMK-10, HOST-09 |
| FLOW-08 | F | **국가별 변형**: 같은 회사가 KR·US·JP 이력서와 인보이스 양식을 따로 저장 → 목적지 국가별로 recall → US Letter 양식을 한국 작업에 쓸 때 경고 확인 | locale에 맞는 변형이 1순위, 불일치 시 `paper_mismatch` 등 경고가 나오고 양식은 바뀌지 않는다 | FORM-12, FORM-16, TPL-04, TPL-05 |
| FLOW-09 | F | **provider별 가져오기**: Docs 모양·Slides 모양·Notion 모양 fixture 페이지를 각각 가져와 Markdown·DOCX(문서), PPTX(슬라이드)로 내보내기 | provider와 family가 맞게 감지되고(Slides는 pptx 경로만), 손실은 `warnings`로 보고되며 내보낸 파일이 유효하다 | CORE-15~17, FMT-08~10, FMT-12, IMP-18 |
| FLOW-10 | R1 | **저장 충돌과 복구**: 두 클라이언트가 같은 양식 v1에서 수정 → 먼저 저장한 쪽 v2 → 늦은 쪽은 `version_conflict` → 이전 버전 조회·병합 후 `base_version=2`로 저장 | 충돌 시 변화 0, 미저장 내용은 사용자에게 남고(웹), v1·v2·v3가 모두 불변으로 조회된다 | LIB-05, LIB-16, VER-02, RT-08 |
| FLOW-11 | F | **철회와 삭제**: 게시 취소 → 타인 복사본 유지 확인 → 내 메모리 삭제 → 로컬 저장소 스윕 → 계정 삭제 | 게시 취소 즉시 공개 조회에서 사라지고 복사본은 남는다. 삭제 후 센티널 0. 계정 삭제 후 연결 해지 | SHR-14, LIB-11, PRIV-04, PRIV-08, PRIV-09 |
| FLOW-12 | F | **오프라인·장애**: 서버 중지 → 로컬 저장·검색·recall(mine) 계속 → 서버 필요 명령은 안내와 함께 종료 5 → 가져오기 원격 5xx·타임아웃 → 복구 후 재시도 | 로컬 동작 유지, 부분 저장 0, 재시도가 멱등(`created:false`), 오류가 원인을 구분하되 URL·토큰을 노출하지 않는다 | CLI-21, IMP-14, FAIL-01, FAIL-11 |
