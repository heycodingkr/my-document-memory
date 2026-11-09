# My Document Memory — 해커톤 90초 영상 구성안

상태: v1 · 2026-11-09 · 요청: "문제 → 명령 → 시연 동작 → 공유를 통한 시간 절감", 구글독스·구글슬라이드·네이버 블로그를 에이전트 여러 명이 Arise Browser에서 동시에 처리하는 3~4분할 화면  
기반: [`demo-video.md`](demo-video.md)(2:42 컨셉 영상)의 렌더 도구와 클레임 원장 규칙, 형제 프로젝트 `web-agentic-memory`(WAM) 영상의 구조(문제 → 실제 실행을 빠르게 → 공유 → 파급 효과 가정 → 마무리)와 실제 녹화 합성 방식  
렌더 도구: `demo/video/build.mjs --cut hackathon`, 음성: `demo/video/make-voice.py --cut hackathon`

## 한눈에

| 항목 | 내용 |
|---|---|
| 길이 | 90.0초, 1920×1080, 30fps, H.264 + AAC(스테레오 44.1kHz). 화면에 자막을 굽는다 |
| 언어와 음성 | **영어.** 데모 자료·요청문은 모두 영어라는 소유자 지시(2026-11-09, `agent-handoff-smoke-v1.md`)를 따른다. ElevenLabs Eric(WAM 영상과 같은 목소리). 한국어판은 만들지 않는다 |
| 한 줄 메시지 | *Share the memory. Save the time.* |
| 제품 한 줄 | 양식·참고자료·검토 기준을 기억해 두고, AI가 그 기준으로 문서·슬라이드·글을 쓰게 한다 |
| 표기 | Google Docs·Google Slides·Naver Blog·Arise Browser는 **글자로만** 쓴다(로고 없음). 모든 장면에 무엇이 실제이고 무엇이 그림인지 표시한다 |
| 음악 | 없음 |

## 이야기와 장면표

시연에 쓰는 요청문(영상 속 에이전트 창에 입력): *"In Google Docs, write a one-page overview of this project. In Google Slides, build a 10-slide deck. Then go to Naver Blog and write a post that promotes it."*

| 시간 | 씬 | 화면 | 성격 |
|---|---|---|---|
| 0:00–0:15 | 1 문제 | 빈 문서·슬라이드·글 세 장이 같은 준비 단계(양식 찾기 → 목차 → 자료 → 서식 → AI에게 다시 설명)에서 멈춰 있다 | 그림 |
| 0:15–0:28 | 2 명령 | Arise Browser 에이전트 창에 요청문이 입력된다. 에이전트의 첫 행동은 Document Memory 조회 | 그림 + 실제 요청문 |
| 0:28–1:02 | 3 동시 시연 | **2×2 네 창.** ① Docs 한 장 ② Slides 10장 ③ Blog 글 ④ Document Memory(MCP 호출·응답). 끝에 세 창이 "검토 대기"로 멈춘다 | 창별로 다름(아래) |
| 1:02–1:15 | 4 공유 | 실제 앱: 양식 라이브러리 검색 → 미리보기(섹션·작성자·버전·라이선스) → 내 라이브러리로 복사 → 편집기. "오늘: 내장 카탈로그 · 다음: 사람 사이 공유" | 실제 녹화(가속) |
| 1:15–1:26 | 5 시간 | 매번 건너뛰는 준비 단계 → "만약 한 번에 10분이면, 1,000번 재사용하면 약 167시간" | **가정**(측정 아님) |
| 1:26–1:30 | 6 마무리 | 제품명과 "Share the memory. Save the time." | — |

### 자막과 내레이션(비트)

자막은 한 줄(영어 66자 이하, 초당 17자 이하). 내레이션 `vo`는 자막과 같거나 길 수 있고 창 안에 들어가야 한다(한 비트는 최대 1.25배속까지 허용). 정본은 `demo/video/hackathon/script.json`이다.

| ID | 시간 | 자막 | 내레이션(vo가 다르면) |
|---|---|---|---|
| h01 | 0.6–4.6 | Every document starts from zero. | |
| h02 | 5.0–10.2 | Find a format. Plan the outline. Gather sources. Fix the style. | |
| h03 | 10.6–14.6 | Then explain all of it to your AI. Again. | |
| h04 | 15.4–19.0 | One sentence. Three documents. Three websites. | |
| h05 | 19.4–23.6 | In Arise Browser, an agent works on each one. | |
| h06 | 24.0–27.7 | But first, it asks Document Memory. | |
| h07 | 28.5–33.0 | Three agents. Three windows. At the same time. | |
| h08 | 33.4–39.4 | Each asks for the format, the sources and the rules. | |
| h09 | 39.8–46.6 | It returns structure, citations, and open questions. | It returns the structure, the citations, and a flag on anything still unconfirmed. |
| h10 | 47.0–53.6 | So they write instead of guessing. | So they write instead of guessing. The Slides window is a real run, fast-forwarded. |
| h11 | 54.4–61.4 | Docs, deck and post. Ready for your review. | A one-pager, a ten-slide deck, and a blog post, ready for your review. |
| h12 | 62.4–69.2 | Templates and sources live in a shared library. | Templates, references and rules live in a shared library, with author, version and license attached. |
| h13 | 69.6–74.6 | Copy one, and your agent starts from good work. | Copy one, and your agent starts from someone else's good work. |
| h14 | 75.4–77.6 | Every reuse skips the setup. | |
| h15 | 78.0–85.6 | Ten minutes saved, a thousand reuses: about 167 hours. | Say each reuse saves ten minutes. A thousand reuses: about 167 hours. A what-if, not a measurement. |
| h16 | 86.3–89.7 | Share the memory. Save the time. | My Document Memory. Share the memory. Save the time. |

## 무엇이 실제이고 무엇이 그림인가

| 요소 | 상태 | 화면 표기 |
|---|---|---|
| 씬 1 문제, 씬 2 에이전트 창 | 그림. 요청문은 시연용 문장 | `ILLUSTRATION` |
| 씬 3 ④ Document Memory 창의 호출·응답 | **실제.** 격리 런타임(임시 DB·임의 포트)에 `dmem-mcp`를 stdio로 붙여 실제 JSON-RPC 호출. 걸린 시간은 측정값(`mcp-trace.json`) | `REAL · MCP` |
| 씬 3 ② Slides 창 | **실제 녹화.** Arise 0.1.69 + Muse Spark 1.3(Meta Model API)이 Google Slides에서 **10장 덱**을 만든 2026-11-03의 **1회 실행**(WAM 프로젝트의 영상 소재, 덱 내용은 그 프로젝트). 가속 배율을 화면에 적는다 | `REAL RUN · ×N` |
| 씬 3 ① Docs·③ Blog 창 | **그림.** 글은 `fixtures/my-document-memory-notes.md`의 사실만 풀어 썼다. 실제 Google Docs·네이버 블로그를 녹화한 것이 아니다 | `ILLUSTRATION` |
| 씬 4 | **실제 녹화.** 실제 웹 앱과 서버(격리 런타임, 합성 데이터). 클릭은 Playwright 스크립트가 한다(에이전트 실행이 아니다). 가속 배율 표기 | `REAL APP · ×N` |
| 씬 5 | **가정.** 10분과 1,000번은 가정이며 측정값이 없다 | `WHAT-IF · NOT MEASURED` |

씬 3 전체에는 `ILLUSTRATION · FOUR WINDOWS` 배지를 달고, 창마다 위 표기를 창 제목줄에 붙인다. 영상 어디에도 "Google Docs·네이버 블로그에서 실제로 실행했다"는 말은 없다. 제품 랜딩 페이지의 고지("These examples describe the experience we are building toward")와 같은 입장이다.

## 클레임 원장

영상의 말과 숫자는 이 표 밖으로 나가지 않는다.

| # | 화면의 말 | 근거 | 허용 · 금지 |
|---|---|---|---|
| C1 | 문서는 매번 양식 찾기·목차·자료·서식 맞추기·AI 재설명에서 시작한다 | README "The Problem" | 허용: 일반적 상황 서술. 금지: 통계·인원수 |
| C2 | 양식·참고자료·작성 결과를 따로 기억하고, 양식 섹션·출처·버전을 문서에 고정한다 | README "메모리의 구조" | 같은 단서 |
| C3 | AI 호스트(Arise Browser)가 MCP로 양식·자료를 검색하고 편집 가능한 초안을 만든다. MCP 도구 7개 | README "에이전트 연결" | 금지: 호스트가 Google Docs·Slides·네이버에 **직접 쓴다**는 제품 기능 주장 |
| C4 | 근거 문장은 원문 위치로 연결되고, 없는 사실은 "확인 필요"로 남는다 | README "현재 초안은…" | 금지: "틀리지 않는다" |
| C5 | 에이전트 세 명이 각자 창에서 Docs·Slides·Blog를 동시에 처리하는 모습 | 그림 | 반드시 `ILLUSTRATION`. 실제 동시 실행을 주장하지 않는다 |
| C6 | Slides 창은 Google Slides에서 10장 덱을 만든 실제 실행 1회이며 ×N로 빨리 감았다 | `web-agentic-memory/demo/video/README.md` "The Muse run in scene 3", `captures/run-muse-deck.json` | 금지: 시간·속도 우위 주장, 이 프로젝트의 결과물이라는 암시. 덱 내용은 이전 프로젝트의 것(`earlier project` 표기) |
| C7 | 공유 라이브러리: 작성자·버전·라이선스가 붙은 양식을 내 비공개 라이브러리로 복사하고 원 출처를 보존한다 | README "document_template_copy", `accounts-community-v1.md` | 허용: "오늘은 내장 카탈로그". 금지: 사람들이 이미 많은 양식을 공유한다는 암시. 사람 사이 공유는 `NEXT` |
| C8 | 한 번에 10분 × 1,000번 = 10,000분 ≈ 167시간(166.7) | 산수 | 반드시 `WHAT-IF · NOT MEASURED`. "절약한다/절약됐다" 같은 사실형 금지 |
| C9 | MCP 호출 횟수·걸린 시간 | `mcp-trace.json`(측정) | 화면 숫자는 파일 값과 같아야 한다 |
| C10 | 씬 4의 제품 화면 | 실제 앱 녹화 | 합성 데이터 표기. 토큰·이메일·실제 자료가 보이면 안 된다 |

쓰지 않는 말: 시간·비용 절감을 측정했다는 말, "항상/완전히/모든", 실제 사용자 수·공유 양식 수, 제3자 로고, "free"(목표일 뿐 현재 보장이 아니다).

## 제작 구조

- `demo/video/hackathon/` — `script.json`(씬·비트·음성·오버레이의 정본), `stage.html`, `stage/*.js`(시간의 순수 함수 `window.__render(t)`), `hackathon.test.mjs`, `fixtures/`
- `build.mjs --cut hackathon`, `make-voice.py --cut hackathon` — 기존 2:42 컨셉 영상(`--cut demo-day`, 기본값)은 바뀌지 않는다
- 실제 녹화는 `demo/out/footage/`(git 제외)에 두고 2차 ffmpeg 패스로 합성한다. 원본 녹화는 커밋·업로드하지 않는다
- 음성: ElevenLabs. 키는 화면·로그·저장소에 두지 않고 `ELEVENLABS_API_KEY` → `~/.config/mdm-demo/elevenlabs.key` → `~/.config/wam-demo/elevenlabs.key` 순서로 읽는다. 소유자가 2026-11-09 채팅에서 WAM 영상에 쓴 키로 음성을 넣으라고 승인했다(문구가 외부 서비스로 전송되고 크레딧이 쓰인다)

## 제품 캡처 명세(씬 4와 ④ 창의 실제 소재)

실제 제품에서 얻는다. 다른 세션이 쓰는 서버·DB·포트와 제품 코드는 건드리지 않는다.

| ID | 입력 / 동작 | 기대 결과 |
|---|---|---|
| PC-01 | 임의의 빈 포트·임시 DB·임의 토큰으로 별도 서버 실행 | 3847·5174 포트와 `data/dmem.sqlite3`(크기·mtime)가 캡처 전후로 같다. 캡처가 시작한 프로세스는 모두 종료된다. 토큰은 출력·파일·프레임에 없다 |
| PC-02 | 실제 API·CLI로 데모 양식 3개와 참고자료 1개 만들기 | 문서 양식 `One-Page Project Overview`(Purpose · The Problem · How It Works · What Runs Today · What's Next), 슬라이드 양식 `10-Slide Pitch Deck`(10장), 문서 양식 `Promo Blog Post`(Hook · The Problem · What It Does · How It Works · Try It), 참고자료 `My Document Memory: project notes`(`fixtures/my-document-memory-notes.md`) |
| PC-03 | `dmem-mcp`를 stdio로 실행해 `initialize` → `tools/list` → 8회 호출(`document_memory_status`, `document_template_search`×3, `document_source_search`, `document_memory_create`×3, 슬라이드는 `outline_approved=true`) | `tools/list`는 7개. 8회 모두 성공. 호출마다 이름·인자·응답·`elapsed_ms`를 `demo/out/footage/mcp-trace.json`에 기록. 만든 문서 3개는 양식·자료의 고정 버전을 가리킨다 |
| PC-04 | 실제 웹 앱(영어 UI)을 Playwright로 녹화 | `library-preview.mp4`(검색 → 양식 미리보기 → 복사), `create-draft.mp4`(양식 + 참고자료 → 작성 → 확인 필요·출처 블록 → 한 문단 편집 → 저장 v2), `deck-editor.mp4`(슬라이드 목차 승인 → 슬라이드 넘기기). 각 클립 1440×900, 30fps, H.264, 음성 없음. 선택: `public-memories.mp4`, `agent-prompt.mp4`(현재 빌드에서 동작할 때만) |
| PC-05 | 모든 클립의 프레임 | 브라우저 주소창·탭·계정 아바타 없음, 연결 토큰·이메일·실제 자료 없음, 영어 UI |
| PC-06 | 보고서 | `demo/out/footage/product/report.json`에 클립별 길이·큐 시각·무엇이 보이는지, 사용한 바이너리와 웹 빌드 경로, 대체 경로를 쓴 이유 |

## 검증: 입력과 기대 결과

| ID | 입력 | 기대 결과 |
|---|---|---|
| HV-01 | `node --test "demo/video/hackathon/*.test.mjs"` | 장면이 0에서 90까지 이어지고, 모든 비트가 자기 장면 안에 있으며, 자막 66자 이하·초당 17자 이하, 음성이 창 안에 들어간다(14.5자/초 기준 1.25배속 이내). 화면·자막·음성의 숫자가 원장 허용 목록 안에 있다 |
| HV-02 | `node demo/video/build.mjs --cut hackathon --lint` | 모든 샘플 시각에서 이슈 0건(화면 밖·상자 밖 글자, 자막 아래 내용, 글자 겹침, 자막 줄바꿈) |
| HV-03 | `--at 3,12,22,31,36,45,56,66,72,80,88` | 정지 화면 PNG를 사람이 열어 배지·창 표기·가독성 확인 |
| HV-04 | 전체 렌더 + 음성 후 `ffprobe`·`ebur128` | 1920×1080, 30fps, H.264, AAC 스테레오, 길이 90.0±0.1초, 통합 음량 −16±1.5 LUFS, true peak ≤ −1.0 dBTP |
| HV-05 | 생성된 `.srt` | 큐 수 = 비트 수(16), 시간이 증가하고 겹치지 않으며 문구가 `script.json`과 같다 |
| HV-06 | 같은 시각 정지 화면을 두 번 렌더 | 두 PNG의 해시가 같다 |
| HV-07 | 최종 mp4에서 1초 간격 프레임 + OCR | 이메일·토큰·계정 이름·`localhost` 주소·다른 앱 창이 없다. 실제 녹화 구간은 사람이 프레임을 직접 확인한다 |
| HV-08 | 화면의 숫자·고유명사를 DOM에서 뽑는다 | 모두 원장 C1–C10 또는 측정 파일의 값과 일치한다. ×N 배율은 오버레이 속도와 같다 |
| HV-09 | 음성 합성 | 16개 비트 모두 합성되고 "does not fit" 경고가 없다. 키 값이 로그에 없다 |
| HV-10 | 렌더 중 콘솔 | 페이지 오류·요청 실패·4xx/5xx·외부 요청 없음 |

## 원자 목표와 의존 순서

| 순서 / 경로 | 산출물 | 부모의 독립 확인 | 선행 |
|---|---|---|---|
| G0 직접 | 이 구성안, 클레임 원장, 테스트 | 현재 README·랜딩·스펙과 대조 | 없음 |
| G1 직접 | `--cut` 렌더 route, `script.json`, 빈 장면으로 HV-01·HV-04 일부 | 스크립트 테스트와 ffprobe를 부모가 실행 | G0 |
| G2a 위임(luna) | PC-01~06 제품 캡처(스크립트·클립·`mcp-trace.json`·보고서) | 클립 프레임을 부모가 직접 열어 확인, 보고서와 파일을 대조, 포트·DB 불변 확인 | G0 |
| G2b 직접 | Slides 실제 클립 구간·가속·마스크(프라이버시 확인) | 프레임 직접 확인 | G0 |
| G3 직접 | 씬 1–6, 창별 표기 | HV-02·03 | G1, G2a, G2b |
| G4 직접 | 음성 합성·합성 믹스 | HV-04·05·09 | G3 |
| G5 직접 | 전체 렌더, 프레임·OCR 검토 | HV-04·06·07·08·10 | G4 |

설계·씬 구현·음성·검증은 직접 한다. 위임하는 것은 독립적이고 출력이 큰 제품 화면 캡처뿐이다.

## 열린 결정

- 제출처의 길이·해상도 제한(90초 가정). 해상도·길이가 다르면 `script.json`과 `build.mjs` 인자로 바꾼다.
- Docs·Blog 창을 실제 녹화로 바꿀지. 소유자의 Google·네이버 계정에서 에이전트를 실제로 돌려 녹화하면 된다(글을 쓰되 게시하지 않는다). 계정에 쓰기를 하므로 소유자 승인 뒤에만 한다.
- 영상 끝에 주소(`mydocumentmemory.com`)를 넣을지. 공개 사이트는 로그인 화면이므로 넣지 않았다.
- 한국어판. 한국어 목소리를 듣고 고른 뒤 `script.json`에 `ko` 문구를 추가하면 된다.
