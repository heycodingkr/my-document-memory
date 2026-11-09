# Agent handoff smoke v1 — 2026-11-09

상태: **로컬 설치·영어 문서 생성/편집/다운로드 PASS. 웹 프롬프트 복사 FAIL. 공개 사이트는 HTTPS·인증 화면까지 PASS, 인증 후 흐름은 배포 토큰 부재로 미검증.**

명세: [agent-handoff-smoke-v1.md](../spec/agent-handoff-smoke-v1.md).
데모 양식·참고자료·최종 문서 제목과 본문·시연용 요청문은 사용자의 추가 지시에 따라 영어로 작성했다. 기존 앱 UI는 한국어다.

## 결과

| ID | 판정 | 직접 확인한 증거 |
|---|---|---|
| AHS-01 | 공개 화면 PASS / 인증 후 BLOCKED | 처음에는 DNS 실패와 Arise 연결 오류. 마지막에는 https://mydocumentmemory.com/ 에서 실제 My Document Memory 앱과 빈 토큰 입력 화면, /healthz 200 ready=true. 무인증 및 로컬 토큰 요청은 각각 401 auth_required. |
| AHS-02 | PASS | 사용자 Cargo 경로에 dmem 설치. --help와 local status 정상. 영어 fixture를 실제 설치된 CLI import로 저장. |
| AHS-03 | 로컬 PASS | 프로젝트 설정 등록 후 호스트 검색에 7개 도구 노출. 호스트에서 document_memory_status, template/source search, create, get를 실제 호출. 공개 서버용 토큰과 로컬 토큰은 다름. |
| AHS-04 | PASS | Arise에서 en-US 양식의 영어 제목·소개·4개 섹션 순서·작성자·라이선스를 직접 읽고 스크린샷 검사. |
| AHS-05 | FAIL — #390 | 실제 양식 모달의 버튼은 개인 양식 복사와 작성 2개뿐. promptControls=0. 프롬프트 미리보기/클립보드 복사 기능 없음. |
| AHS-06 | PASS | CLI로 영어 Markdown 5개 span 저장. Arise 개인 양식 복사 후 원본 template/version/author/license 보존. |
| AHS-07 | PASS, 언어 기본값 결함 별도 | 실제 호스트 MCP create로 문서 생성. 선택한 template와 source가 모두 v1로 고정되고 실제 source 원문 3개가 인용됨. |
| AHS-08 | PASS | Arise에서 영어 본문 4개와 근거 제목을 편집해 v2 저장. 전체 페이지 재탐색 후 문서를 다시 열어 v2와 내용을 확인. MCP get에서도 동일한 저장본 확인. |
| AHS-09 | PASS | Arise 다운로드 id 18이 complete, file_exists=true, 1973 bytes. 실제 DOCX ZIP/XML 및 영어 제목·본문·근거 제목 검증. |
| AHS-10 | PASS | Rust 16 tests, workspace build, Svelte check 0 errors/0 warnings, Vite production build, 격리 DB runtime smoke와 Playwright 3 tests 통과. |
| AHS-11 | FAIL — #391 | en-US 양식도 v1 초안의 확인 필요 placeholder와 근거 제목이 한국어. 최종 데모는 웹에서 영어로 직접 편집했으며 런타임 결함을 수정했다고 주장하지 않음. |

## 설치와 사용

- CLI: /Users/jason2/.cargo/bin/dmem
- MCP: /Users/jason2/.cargo/bin/dmem-mcp
- 설치: cargo install --path crates/dmem-cli --locked --debug 및 cargo install --path crates/dmem-mcp --locked --debug
- 프로젝트 호스트 등록: .meshcode/mcp.json의 document-memory
- 등록된 URL: http://127.0.0.1:3847
- 토큰은 기존 .env에서 설정으로 전달했다. 설정 파일 권한 0600, .gitignore에 /.meshcode/mcp.json 추가. 전역 MCP 설정과 알 수 없는 필드는 보존했다.
- CLI는 .env를 자동으로 읽지 않는다. 저장소에서 다음처럼 환경을 전달한다.

```sh
set -a
. ./.env
set +a
dmem status
dmem templates 'Project Review'
dmem documents 'Project Review - English Demo'
```

기존 API PID 68074와 Vite PID 68076을 재사용했다. 새 개발 서버를 시작하거나 기존 서버를 종료하지 않았다.

## 영어 데모 데이터

| 역할 | 값 |
|---|---|
| 원본 양식 | Project Review Brief - English Demo / tpl_2803c89eda6e459b9cced56c6c85ac90 / en-US / v1 / private |
| 웹에서 복사한 양식 | tpl_c703adc8ca874277b58b076b862079ad / 원본 v1 출처 보존 |
| 참고자료 | Project Review Notes - English Demo / src_c38558f57b034168ba8aa7fa8cf41904 / v1 |
| 작성 문서 | Project Review - English Demo / doc_cf590529f0b64ffc9a07559637494fe6 / v2 |
| 섹션 | Purpose; Progress and Evidence; Risks and Open Questions; Next Steps; Selected Source Excerpts |
| 내보내기 | .artifacts/agent-handoff-smoke/Project-Review-English-Demo.docx |

처음 선택한 en-US 양식은 기존 API로 준비했다. 웹 양식 작성 폼은 locale을 ko-KR로 고정하므로 API 준비 단계와 UI 검증 단계를 구분한다. 본문은 합성 프로젝트 기록에만 근거하며 실제 출시일을 만들지 않았다.

[영어 시연 요청문](../../.artifacts/agent-handoff-smoke/demo-request.txt)은 관측한 양식과 자료로 수동 구성했다. 사이트에서 복사한 프롬프트라고 표시하지 않는다. 앱의 생성은 deterministic outline이며 외부 LLM 호출은 없다.

## 공개 배포 확인과 남은 입력

최종 관측에서 시스템 DNS는 mydocumentmemory.com을 121.167.167.102로 해석했고, 기본 인증서 검증을 사용하는 HTTPS 요청에 /healthz 200 JSON ready=true가 반환됐다. Arise 전용 창에서 동일 도메인의 앱과 토큰 입력 화면을 직접 검사했다. 초기의 DNS 오류를 최종 미연결 상태로 보고하지 않는다.

별도로 시도한 @1.1.1.1 직접 UDP DNS 질의는 timeout이었다. 이 timeout은 DNS 레코드가 없다는 증거가 아니다. 다른 네트워크에서의 전 세계 도달성은 검증하지 않았다.

로컬 .env의 토큰은 공개 API에서 401이다. Arise 저장 계정 검색에도 이 사이트용 자격값이 없었다. 배포용 토큰 파일 경로 또는 해당 배포 서버의 접속 경로가 있어야 공개 서버 인증 후 검색·생성·저장·다운로드를 이어서 검증할 수 있다. 이 세션은 배포 서비스·DNS·인증 설정을 변경하지 않았다. 설치한 MCP/CLI는 검증된 로컬 서버를 가리킨다.

## 원인과 검토

#390: web/src/App.svelte:218의 양식 모달에는 프롬프트 미리보기/클립보드 동작이 없다. 양식 객체 복사를 프롬프트 복사로 간주하지 않았다.

#391: crates/dmem-server/src/store.rs:339, :345, :357, :362의 문구가 한국어로 고정되어 template.form.locale을 따르지 않는다. v2 최종 본문과 DOCX에는 한글이 없음을 별도로 확인했다. v1 이력에는 재현 증거가 남는다.

호스트 경유 Arise 호출 중 선택 대상이 새 about:blank 탭으로 바뀌고 이전 is_mine 탭의 acquire가 tab_busy로 거부되는 현상이 있었다. 공개 agent_browser --mcp-server stdio 연결 하나를 유지하고 전용 창을 만든 뒤 브라우저 작업을 완료했다. private socket이나 CDP를 사용하지 않았다. 다른 세션의 탭은 조작하지 않았다. 이 작업이 만들고 lease가 만료된 탭 12·17만 정리했다. 전용 창 4에 저장된 영어 데모 탭 19와 공개 로그인 탭 23을 남겼고 브라우저 lease와 stdio 자식은 종료했다.

제품 소스 코드는 편집하지 않았다. 이 세션의 저장소 변경은 이 명세/보고서와 private MCP 설정의 Git 제외 규칙이다. 다른 세션의 uncommitted/untracked 파일은 보존했다. 빌드·테스트·브라우저 검증과 원인 판단은 모두 직접 수행했다.

## 증거

증거 디렉터리: .artifacts/agent-handoff-smoke/ (Git 제외).

- english-template.png, english-editor.png, public-login.png: 실제 Arise 렌더 화면을 이미지로 검사.
- template-actions.json, created-document-v1.json, copied-template.json, saved-document.json, editor-state.json, reopened.json.
- browser-download-final.json: 실제 다운로드 경로와 complete 상태.
- export-verification.json: SHA-256 e4580783f2b59bd618f306bb4a4f795c089bd20e2469c8d3d53cf6bc3068793c, 1973 bytes, 유효 ZIP/XML, 영어 문서 내용.
- domain-check.json, domain-browser.json, public-status.json: 공개 도메인 최종 확인.

DOCX는 ZIP/XML과 텍스트를 검사했다. Word 네이티브 렌더 품질은 이 스모크의 검증 범위에 포함하지 않았다.

테스트 로그:
- /var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794187048522.log
- /var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794187091578.log
