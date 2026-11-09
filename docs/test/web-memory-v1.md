# Web memory v1 입력·기대 결과

상태: 구현 전 고정한 케이스와 2026-11-09 실제 제품 실행 결과. 원본 계약은 [`../spec/web-memory-v1.md`](../spec/web-memory-v1.md). 합성 입력·임시 DB·loopback fixture와 설치된 Arise 0.1.77의 공개 MCP를 사용한다.

| ID | 입력 | 기대 결과 / 독립 oracle |
|---|---|---|
| WI-01 | CC-BY 한국어 이력서 HTML: 제목·경력/학력 heading·표·본문 | title/locale/outline/표 추출, detected license, full 허용; 스크립트 없음 |
| WI-02 | license 없음/NC/ND, 본문 PROSE_TEST·목록 LIST_TEST·표 본문 CELL_TEST, heading 경력 | structure_only 저장물에 세 본문 표식 없음, 경력/표 머리글 유지; full 요청 거부 |
| WI-03 | script/style/iframe/form, hidden/display:none/size0/same-color/zero-width, 주입 지시 | 저장/preview 구조에 숨김·실행·주입 표식 없음; 경고·untrusted framing |
| WI-04 | password/payment form, noai header/meta | 고정 fetch_blocked 이유, 저장물 없음 |
| WI-05 | https 공개 DNS; IPv4 private/reserved와 IPv6 mapped/NAT64/ULA/linklocal/multicast | 공개만 허용, 혼합 A/AAAA에 private 하나라도 있으면 요청 0 |
| WI-06 | http·userinfo·IP literal·443 외 포트·민감 query URL | 금지 목적지는 요청 전 거부; 오류와 저장 출처에 원문 없음 |
| WI-07 | redirect→private/로그인·4번째 hop·timeout·5MiB 초과·잘못된 MIME | 각 고정 오류, 부분 저장 0; fixture 요청 로그로 확인 |
| WI-08 | preview 후 원격 페이지 내용 변경 → preview_id import | 미리본 이전 내용/hash 저장; preview는 DB 항목 수 불변 |
| WI-09 | A preview를 B가 import, 만료·없는 ID | 모두 같은 not_found; 타 소유자 내용 없음 |
| WI-10 | 동일 owner/source/form/content/mode import 두 번, DB 재열기 | 같은 id, created true→false, 항목/출처 1개, 재조회 동일 |
| WI-11 | 같은 URL에 KR/US/JP locale/variant 또는 다른 doc_type/provider; JP 참고자료 저장·재조회·양식 추출 | 독립 양식 공존, template와 reference origin의 form 보존, 참고자료→양식에도 provider/doc_type/locale/region/variant 유지; 기존 recall로 자기 양식 조회 |
| WI-12 | source full 허용 → 저장·생성에 참고자료 사용 | 살균한 원문 span만 저장, 원문 HTML/입력 폼/hidden 없음 |
| WI-13 | 외부 unknown/NC 또는 제약 있는 출처를 가져온 뒤 recall·CC0 기여 | recall도 원래 license와 structure_only를 반환, 검출 권리/출처가 검수에서 유지, 허용되지 않은 재게시 거부 |
| WI-14 | 공개 Google Docs/Slides URL과 fixture DOCX/PPTX export | 올바른 export 형식·문서/덱 구조, 원본 ID/query/fragment는 DB/응답 출처에 없음 |
| WI-15 | 검색 provider 미설정 / 합성 Brave 응답 / 유효하지 않은 결과 URL | 미설정 명시, 설정 시 후보만 반환·저장 0; 비공개/위험 결과 제외, 키 비노출 |
| WI-16 | HTTP 무인증·세션 CSRF 누락·알 수 없는 필드·잘못된 형식/ID | 기존 고정 오류, side effect 없음 |
| WI-17 | 실제 dmem web preview→import→origin과 stdio MCP 동일 요청 | 같은 DTO/출처/정책, stdout JSON 순수, 입력/토큰 오류 비노출 |
| WI-18 | 웹에서 한국어 URL 미리보기→미국/영어 선택→구조 가져오기 | 버튼 상태·미리보기·권리 경고·저장 알림, 재조회한 양식이 `locale=en-US`, `region=US`. 원래 한국 region이 남지 않음 |
| WI-19 | browser adapter initialize/list/call forwarding 두 번 | 공개 browser 도구 보존, 같은 child 연결과 private lease, 알 수 없는 요청은 명시 오류 |
| WI-20 | 소유 session/tab/window/client/ready/lease 모두 일치 → clip | 실제 visible 구조 저장, captured 서명 검증, canonical 출처·원본ID/query 없음 |
| WI-21 | 사용자/다른 session 탭·public-name만 같은 no-local-lease·만료·탭/URL 변경 | 캡처/저장 거부, 타인 탭 조작·생성 항목 0 |
| WI-22 | clip 도구에 URL/HTML/다른 옵션·민감 폼·잘못된 서명/만료 시각 | 고정 오류, captured provenance를 위조할 수 없음 |
| WI-23 | 실제 Arise fixture 소유 탭에서 clip→실제 CLI 재조회 | 합성 문서/권리/형식·출처 일치, 사용자 탭 전후 동일, 캡처 이미지 직접 검사 |
| WI-24 | 기존 workspace·runtime·recall·community 및 web check/build | 회귀 없음, 배포·원본 데이터·동시 작업 보존 |

## 실행과 결과

부모가 실행한 로그 묶음은 [`../../target/e2e-logs/web-memory-regression/`](../../target/e2e-logs/web-memory-regression/)다. 최신 intake 실행은 [`../../target/e2e-logs/web-memory/20261109-142843-34202/summary.md`](../../target/e2e-logs/web-memory/20261109-142843-34202/summary.md), 기계 판정은 같은 폴더의 `results.json`이다. 증거는 로컬 생성물이며 git에는 포함하지 않는다.

| 명령 | 직접 확인한 결과 | 근거 |
|---|---|---|
| `cargo test --workspace` | 120 통과, 실패·ignored 0 | `cargo-test.log`; 신규 core 9·server 10·browser ownership 2 포함 |
| `cargo build --workspace --examples` | 종료 0 | `cargo-build.log`; 실제 CLI·MCP·서버·명시적 fixture 바이너리 |
| `pnpm --dir web check` / `build` | 오류·경고 0 / 종료 0 | `web-check.log`, `web-build.log` |
| `python3 -B tests/smoke/web-memory-v1.py --browser --arise` | **33/33** | 위 intake 실행. CLI/MCP/HTTP·가짜 browser 음성 대조·실제 Arise clip/악성 페이지/네이티브 웹 입력·저장·사용자 탭 전후 동일 |
| 위 실행의 Playwright | **2/2** | `20261109-142843-34202/web.log`; KR→US region 저장, public/다른 언어 필터에서 새 private 항목 표시, 출처 재조회 |
| `python3 -B tests/smoke/runtime-v1.py --browser` | 실제 바이너리/영속성 종료 0; 웹 **35 통과·18 skip** | `runtime-smoke.log`. skip은 해당 실행에 없는 계정/실제 이메일/웹 fixture가 필요한 케이스; 신규 intake 2개는 위 전용 실행에서 별도로 통과 |
| `python3 -I tests/smoke/recall-v1.py` | **44/44** | `recall-smoke.log`; 정책 보정 뒤 기존 소유자·안전 오류·예산·CLI/MCP 회귀 |
| `python3 -B tests/smoke/community-v1.py` | 종료 0, 전 단계 PASS | `community-smoke.log`; 비공개·공개 복사·검수·철회 |
| `python3 -B -m unittest discover -s tests/lib/selftest -p 'test_*.py'` | **138/138** | `harness.log`; 제품 테스트와 별도인 하네스 자체 검사 |
| `PYTHONPATH=tests/lib python3 -B -m dmtest.doctrace --all` | 인용 ID 전부 정의됨 | `doctrace.log` |
| `PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace --list` | 종료 0 | `codetrace.log`; 더블·제품 구분 유지 |
| `PYTHONPATH=tests/lib python3 -B -m dmtest.porttrace --require-upstream` | 93 원본·72 이식·21 제외, 상위 WAM 비교 통과 | `porttrace.log` |
| 신규 Rust 모듈 11개 `rustfmt --check`, `git diff --check` | 종료 0 | `rustfmt.log`, `diff-check.log` |

Arise 원본 `arise-source.png`와 저장 완료 상태가 보이는 `arise-web-ui.png`를 이미지 도구로 직접 열었다. 한국어 이력서의 경력·학력·기술·표와 실제 앱의 국가/양식·출처·라이선스·Saved 상태를 확인했다. 원래 사용자 탭은 보존하고 소유 탭 하나만 닫았으며 임시 서버·DB도 정리했다.

## 케이스와 실제 oracle

| 케이스 | 실행 코드 / oracle |
|---|---|
| WI-01~06 | `crates/dmem-core/tests/web.rs`: 추출물·구조 저장 문자열·비밀/placeholder·주입/숨김·IP/URL 판정. `crates/dmem-server/src/web.rs`의 모든 DNS 주소 검사·pinning·proxy/redirect 경계도 직접 리뷰 |
| WI-07~16 | `crates/dmem-server/tests/web_memory.rs`: 임시 HTTP·SQLite. 원격 내용 변경 후 원래 snapshot 저장, owner/만료 격리, 재열기·멱등, 국가 form·source→template, 권리/공개 승인 snapshot·recall, 검색 후보 필터, 서명, redirect/private/oversize/hop/noai 거부 |
| WI-14~17 | `tests/smoke/web-memory-v1.py`: 실제 바이너리·Google-shaped DOCX/PPTX export 요청·권리·출처·DB 내용·stdout 순수성 |
| WI-18 | `web/tests/web-memory.spec.ts`와 실제 Arise native click/type: UI 상태만이 아니라 HTTP 재조회한 저장 form·항목 확인 |
| WI-19~22 | `crates/dmem-mcp/tests/bridge.rs`, `tests/fixtures/browser-mcp-web.py`: 같은 child PID, foreign/만료/no-local-lease/native eval 실패/민감 폼/변경된 URL·인수 주입에서 저장 수 불변 |
| WI-23 | 공개 stdio MCP 한 연결에서 실제 소유 탭 clip → CLI 재조회, hostile fixture, 네이티브 웹 저장 → HTTP 재조회, 사용자 탭 전후 동등성·PNG 직접 검사 |
| WI-24 | 위 Rust·runtime·recall·community·web check/build; 다른 세션의 변경을 제거하거나 커밋하지 않음 |

## 재현과 한계

빌드 후 위 intake 명령만 실행하면 서버·fixture·DB·자기 browser child를 자동 생성/정리한다. 기본 실행은 CLI/MCP/가짜 browser 검증이며 `--browser`는 Playwright, `--arise`는 설치된 Arise의 실제 소유 탭을 추가한다. 외부 DNS 재바인딩 실험이나 운영 서버의 지연 측정은 이번 loopback 실행에 포함하지 않았다. SSRF 주소 판정은 단위 테스트와 hop별 pinning 코드 리뷰, redirect 거부의 요청 경계로 확인했다.

red→green 기록과 원인은 [설계 리뷰](../design/web-memory-v1-review.md)에 있다. Arise native click은 **보이는 대상**에만 동작하므로 저장 버튼의 실제 viewport 위치를 읽고 `browser_scroll`로 이동한 뒤 표시·활성 상태를 확인한다. `arise-save-target.json`은 스크롤 전 top 904.95/bottom 943.45, viewport height 651이라는 실패 조건을 기록한다. 저장 상태와 HTTP 결과를 확인해야 성공으로 세며 입력 dispatch 응답만으로 통과시키지 않는다.

실제 Brave 키·Google 계정은 사용하지 않았다. 검색 provider 설정 실패와 합성 Brave 응답, 공개 Google export 모양은 검증했지만 이를 원격 실사이트 성공·Google OAuth 동기화로 주장하지 않는다. 배포는 하지 않았다. 전체 WAM 계약 더블의 결과는 기존 [포팅 결과](wam-port-completion-v1.md)에 별도로 남겨 두었다.
