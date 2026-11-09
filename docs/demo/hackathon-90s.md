# My Document Memory — 해커톤 90초 영상 구성안

상태: v2 완료 · 2026-11-09 · 요청: "문제 → 명령 → 시연 동작 → 공유를 통한 시간 절감", 구글독스·구글슬라이드·네이버 블로그를 Arise Browser에서 처리하는 4분할 화면. 실제 소재는 **각각 따로 녹화한 실행을 합성**한다. 재개 명세·원인·검증 기록: [`hackathon-resume.md`](hackathon-resume.md).

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
| 0:28–1:02 | 3 실행 합성 | **2×2 네 창.** ① 실제 Docs 작성 ② Slides 10장 ③ 실제 Blog 초안 작성 ④ Document Memory(MCP 호출·응답). 각각 녹화한 실행임을 표시하며 Docs·Blog는 저장된 초안이다 | 실제 녹화·트레이스의 합성(아래) |
| 1:02–1:15 | 4 공유 | 실제 앱: 양식 라이브러리 검색 → 미리보기(섹션·작성자·버전·라이선스) → 내 라이브러리로 복사 → 편집기. "오늘: 내장 카탈로그 · 다음: 사람 사이 공유" | 실제 녹화(가속) |
| 1:15–1:26 | 5 시간 | 매번 건너뛰는 준비 단계 → "만약 한 번에 10분이면, 1,000번 재사용하면 약 167시간" | **가정**(측정 아님) |
| 1:26–1:30 | 6 마무리 | 제품명, "Share the memory. Save the time.", **mydocumentmemory.com** | — |

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
| h07 | 28.5–33.0 | Three workflows. Recorded separately in Arise. | |
| h08 | 33.4–39.4 | Each asks for the format and the sources. | |
| h09 | 39.8–46.6 | It returns structure, citations, and open questions. | It returns the structure, the citations, and a flag on anything still unconfirmed. |
| h10 | 47.0–53.6 | So they write instead of guessing. | So they write instead of guessing. The Slides window is a real run from an earlier project, fast-forwarded. |
| h11 | 54.4–61.4 | Docs, deck and post. Ready for your review. | A one-pager, a ten-slide deck, and a blog post, ready for your review. |
| h12 | 62.4–69.2 | Templates live in a shared library, with credit attached. | Templates live in a shared library, with author, version and license attached. Your references stay private. |
| h13 | 69.6–74.6 | Copy one, and your agent starts from a good structure. | |
| h14 | 75.4–77.6 | Every reuse skips the setup. | |
| h15 | 78.0–85.6 | Ten minutes saved, a thousand reuses: about 167 hours. | Say each reuse saves ten minutes. A thousand reuses: about 167 hours. A what-if, not a measurement. |
| h16 | 86.3–89.7 | Share the memory. Save the time. | My Document Memory. Share the memory. Save the time. |

## 무엇이 실제이고 무엇이 그림인가

| 요소 | 상태 | 화면 표기 |
|---|---|---|
| 씬 1 문제, 씬 2 에이전트 창 | 그림. 요청문은 시연용 문장 | `ILLUSTRATION` |
| 씬 3 ④ Document Memory 창의 호출·응답 | **실제.** 격리 런타임(임시 DB·임의 포트)에 `dmem-mcp`를 stdio로 붙여 실제 JSON-RPC 호출. 걸린 시간은 측정값(`mcp-trace.json`) | `REAL · MCP` |
| 씬 3 ② Slides 창 | **실제 녹화.** Arise 0.1.69 + Muse Spark 1.3(Meta Model API)이 Google Slides에서 **10장 덱**을 만든 2026-11-03의 **1회 실행**(WAM 프로젝트의 영상 소재, 덱 내용은 그 프로젝트). 가속 배율을 화면에 적는다 | `REAL RUN · ×N` |
| 씬 3 ① Docs·③ Blog 창 | **실제.** Codex가 로그인된 Arise의 공개 MCP를 통해 영어 문서와 네이버 초안을 작성했다. `browser_screenshot`의 실제 뷰포트와 시각을 기록하고 유휴 구간을 편집했다. 원문은 프로젝트 사실만 사용. Docs는 저장 후 재열기와 DOCX 내용 확인, Blog는 새 임시저장 글로 저장 | `REAL CAPTURE · EDITED` |
| 씬 4 | **실제 녹화.** 실제 웹 앱과 서버(격리 런타임, 합성 데이터). 클릭은 Playwright 스크립트가 한다(에이전트 실행이 아니다). 가속 배율 표기 | `REAL APP · ×N` |
| 씬 5 | **가정.** 10분과 1,000번은 가정이며 측정값이 없다 | `WHAT-IF · NOT MEASURED` |

씬 3 전체에는 `REAL CAPTURES · RECORDED SEPARATELY` 배지를 달고, 창마다 위 표기를 창 제목줄에 붙인다. **동시 실행이나 소요 시간·속도 우위를 주장하지 않는다.** 외부 편집기 입력은 Arise를 사용하는 에이전트의 실행이며 MDM 자체의 Google·네이버 전용 커넥터를 뜻하지 않는다. 씬 1·2는 계속 `ILLUSTRATION`이다.

## 클레임 원장

영상의 말과 숫자는 이 표 밖으로 나가지 않는다.

| # | 화면의 말 | 근거 | 허용 · 금지 |
|---|---|---|---|
| C1 | 문서는 매번 양식 찾기·목차·자료·서식 맞추기·AI 재설명에서 시작한다 | README "The Problem" | 허용: 일반적 상황 서술. 금지: 통계·인원수 |
| C2 | 양식·참고자료·작성 결과를 따로 기억하고, 양식 섹션·출처·버전을 문서에 고정한다 | README "메모리의 구조" | 같은 단서 |
| C3 | AI 호스트(Arise Browser)가 MCP로 양식·자료를 검색하고 편집 가능한 초안을 만든다. MCP 도구 7개 | README "에이전트 연결" | 금지: 호스트가 Google Docs·Slides·네이버에 **직접 쓴다**는 제품 기능 주장 |
| C4 | 근거 문장은 원문 위치로 연결되고, 없는 사실은 "확인 필요"로 남는다 | README "현재 초안은…" | 금지: "틀리지 않는다" |
| C5 | Docs·Slides·Blog 실행을 네 창으로 합성 | 개별 실제 녹화 | 반드시 `RECORDED SEPARATELY`. 동시 실행·동일 프로젝트·측정된 속도 우위를 주장하지 않는다 |
| C6 | Slides 창은 Google Slides에서 10장 덱을 만든 실제 실행 1회이며 ×N로 빨리 감았다 | `web-agentic-memory/demo/video/README.md` "The Muse run in scene 3", `captures/run-muse-deck.json` | 금지: 시간·속도 우위 주장, 이 프로젝트의 결과물이라는 암시. 덱 내용은 이전 프로젝트의 것(`earlier project` 표기) |
| C7 | 공유 라이브러리: 작성자·버전·라이선스가 붙은 양식을 내 비공개 라이브러리로 복사하고 원 출처를 보존한다. **공개되는 것은 양식 구조뿐이고 참고자료는 비공개** | README "document_template_copy", `accounts-community-v1.md`, 앱의 공개 라이브러리 안내문("Only template structures are public. Copies stay in your private space with their original author and version.") | 허용: "오늘은 내장 카탈로그". 금지: 사람들이 이미 많은 양식을 공유한다는 암시, 참고자료·규칙이 공유된다는 말. 사람 사이 공유는 `PLANNED` |
| C8 | 한 번에 10분 × 1,000번 = 10,000분 ≈ 167시간(166.7) | 산수 | 반드시 `WHAT-IF · NOT MEASURED`. "절약한다/절약됐다" 같은 사실형 금지 |
| C9 | MCP 호출 횟수·걸린 시간 | `mcp-trace.json`(측정) | 화면 숫자는 파일 값과 같아야 한다 |
| C10 | 씬 4의 제품 화면 | 실제 앱 녹화 | 합성 데이터 표기. 토큰·이메일·실제 자료가 보이면 안 된다 |
| C11 | Docs·Blog에 영어 초안을 실제 입력하고 저장 | `demo/out/footage/arise/{docs,blog}/frames.json`, `edit.json`, `*-edited.mp4`; 로컬 검증 기록 `.artifacts/video-resume/` | `REAL CAPTURE · EDITED`. 각각 따로 녹화했으며 유휴·캐럿 프레임을 줄였다. 32초는 편집 길이이며 실행 성능 수치가 아니다. 블로그는 게시하지 않는다 |

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
| G2a 직접(위임을 시도했으나 취소) | PC-01~06 제품 캡처(스크립트·클립·`mcp-trace.json`·보고서) | 클립 프레임을 직접 열어 확인, 보고서와 파일을 대조, 포트·DB 불변 확인 | G0 |
| G2b 직접 | Slides 실제 클립 구간·가속·마스크(프라이버시 확인) | 프레임 직접 확인 | G0 |
| G3 직접 | 씬 1–6, 창별 표기 | HV-02·03 | G1, G2a, G2b |
| G4 직접 | 음성 합성·합성 믹스 | HV-04·05·09 | G3 |
| G5 직접 | 전체 렌더, 프레임·OCR 검토 | HV-04·06·07·08·10 | G4 |

모두 직접 했다. 제품 캡처는 처음에 위임하려 했으나 (1) 쓰기 금지 문구 때문에 읽기 전용으로 분류되어 취소했고 (2) 통과할 때까지 반복하는 브라우저 루프라 직접 하는 쪽이 맞아 위임하지 않았다.

## 확정한 결정

- 소유자가 이 세션에서 **1분 30초**라고 확정했다. 이전에 저장한 3분 참가 안내의 길이를 이 영상에 적용하지 않는다. 해상도는 1920×1080, 별도 용량 제한은 제시되지 않아 최종 파일의 실측 용량을 보고한다.
- Docs·Blog 실녹화를 승인했다. 로그인된 Arise에서 새 영어 문서·새 임시저장 글을 작성하며 게시하지 않는다.
- 마지막 화면에 `mydocumentmemory.com`을 넣는다.
- 영어 음성과 영어 자막을 사용한다. 한국어판은 만들지 않는다.

## v1 검증 결과 (2026-11-09 · 실녹화 교체 전)

렌더를 만든 쪽이 아니라 최종 mp4와 소재에 대해 같은 명령을 직접 다시 실행해 확인했다. 산출물은 `demo/out/video/`(git 제외): `mdm-hackathon-90s.en.vo.mp4`(음성 포함 최종본), `mdm-hackathon-90s.en.mp4`(무음), `.en.srt`, `.en-poster.jpg`.

| ID | 결과 |
|---|---|
| HV-01 | `node --test "demo/video/hackathon/*.test.mjs"` 11/11 통과. 일부러 깨뜨린 변이 7종(자막 길이, 장면 이탈, 자막 겹침, 원장 밖 숫자, 음성 초과, 장면 공백, 틀린 산수)을 모두 잡았다. 기존 컨셉 영상 테스트 12/12도 그대로 통과(공용 코드 변경 회귀 없음) |
| HV-02 | `--cut hackathon --lint` 120개 시각 이슈 0건. 기존 컷 `--lint`는 en·ko 214개 시각 이슈 0건. 린트 첫 실행이 겹침 5건(입력 커서와 안내 문구, 큰 숫자와 설명줄)을 잡아 고쳤다 |
| HV-03 | 정지 화면과 최종 mp4에서 뽑은 프레임(4분할 3시점, 공유 장면 4시점 포함)을 직접 열어 확인했다 |
| HV-04 | H.264 High, 1920×1080, 30fps, 2,700프레임, AAC LC 스테레오 44.1kHz, 길이 90.000초, 통합 음량 −16.3 LUFS, true peak −4.5 dBFS, 검은 화면 0 |
| HV-05 | `.srt` 16큐가 `script.json`의 시간·문구와 일치 |
| HV-06 | 같은 시각(50초) 정지 화면을 두 번 렌더한 PNG의 SHA-256이 같다 |
| HV-07 | OCR(이메일·토큰·로컬 주소·계정 문구) 0건: 최종 mp4의 1초 간격 90프레임(3,051줄), 실제 Slides 클립 63프레임(832줄), 제품 클립 96프레임(4,142줄). 육안 확인: Slides 클립 6fps 모자이크 190프레임과 접촉 시트, 우상단 아바타 블러 확대. 이물 창·알림 배너 없음. 스캐너가 처음에 리소스 ID(`src_…`·`tpl_…`)를 토큰으로 오탐해 패턴을 43자 토큰 형식(40자 이상)으로 좁혔다 |
| HV-08 | 화면 텍스트 45개 시각에서 뽑은 숫자는 전부 원장·측정값과 일치(×45·×1.7·×1.8은 오버레이 속도, `8 calls · 12 ms`와 호출별 ms는 실제 트레이스, 10·1,000·167·10,000은 what-if 장면) |
| HV-09 | ElevenLabs로 16개 비트 949자 합성, 모든 비트가 창 안에 들어가고(최대 초과 0초, 가장 빠른 비트 1.04배속) 경고 없음. 키 값은 어디에도 출력되지 않았다 |
| HV-10 | 렌더 중 페이지 오류·요청 실패·4xx/5xx·외부 요청 0건 |
| PC-01 | 캡처 전후로 `data/dmem.sqlite3`(4096바이트, mtime)가 같고 3847·5174 포트의 서버는 같은 PID로 계속 살아 있다. 캡처가 시작한 프로세스는 모두 종료(`/tmp/mdm-capture` 경로 프로세스 0개). 토큰은 출력·파일·프레임에 없다 |
| PC-03 | 실제 `dmem-mcp` stdio: 도구 7개, 호출 8회 모두 성공, 합계 11.8 ms(로컬 디버그 빌드), 만들어진 문서 3개가 양식·자료 v1을 고정한 것을 HTTP로 다시 읽어 확인 |
| PC-04 | `library-preview` 15.7초, `agent-prompt` 17.0초, `create-draft` 26.1초, `deck-editor` 24.4초, `public-memories` 13.3초, 모두 1440×900 30fps. `library-preview`·`create-draft`·`public-memories` 세 개가 영상에 쓰였고 `agent-prompt`·`deck-editor`는 쓰지 않았다(예비 소재) |

### v1의 한계와 알아 둘 것

- **움직임과 소리.** 정지 화면·프레임·측정으로 확인했다. 영상을 처음부터 끝까지 재생해 보고 타이밍의 느낌과 목소리를 듣는 일은 사람이 한 번 해야 한다.
- **v1의 Docs·Blog 창은 그림이었다.** v2에서 실제 Arise 캡처로 교체한다. 두 버전 모두 세 에이전트가 동시에 실행됐다는 증거는 없다.
- **Slides 창은 이 프로젝트의 결과물이 아니다.** WAM 프로젝트의 2026-11-03 실행 1회(덱 내용은 그 프로젝트)이며 `EARLIER PROJECT`로 표기했다. 시간·속도 우위를 주장하지 않는다(실제 실행은 24분 49초였고 ×45로 빨리 감았다).
- **Memory 창의 MCP 기록(왼쪽)과 앱 화면(오른쪽)은 서로 다른 격리 런타임에서 따로 녹화한 실제 소재**다. 문서 ID가 서로 다르다.
- **시간 절감은 측정이 아니다.** 씬 5의 10분·1,000번·167시간은 what-if이며 화면과 음성에 그렇게 말한다.
- **같은 템플릿으로 만든 초안의 슬라이드 수.** `10-Slide Pitch Deck`에서 `document_memory_create`가 만든 덱은 13장이다(양식 10장 + 선택한 자료 원문 3장). 영상은 MDM 초안의 장수를 말하지 않고, 10장은 Slides 창의 실제 실행 결과다.
- **음성 키.** 쓴 키는 `~/.config/wam-demo/elevenlabs.key`(7일 제한 키, 2026-11-03 생성이라 약 2026-11-10 만료). 합성된 mp3는 `demo/out/voice-cache/`에 캐시되어 있어 재렌더·재합성은 키 없이 된다. `vo` 문구를 바꾸면 바뀐 비트만 새로 합성하므로 만료 뒤에는 새 키가 필요하다.

## v2 완성본과 검증 (2026-11-09)

- 최종 영상: `demo/out/video/mdm-hackathon-90s.en.final.mp4`. 영어 음성·영어 자막 포함, Docs·Blog 실녹화 합성, 마지막 `mydocumentmemory.com` 표시. 기존 v1 파일은 보존했다.
- 부속 파일: `.en.final.srt`, `.en.final-poster.jpg`. 무음 합성본: `.en.real.mp4`.
- 실측: **90.000초, 1920×1080, 30fps, 2,700프레임, H.264 High / AAC LC, 44.1kHz 스테레오, 7,848,210바이트(약 7.8MB)**. 통합 음량 −16.3 LUFS, true peak −4.5 dBFS. 검은 화면 0구간.
- 검증: 렌더러·스크립트 테스트 25/25 통과, 레이아웃 120개 시각 이슈 0건. SRT 16큐의 시간·문구가 정본과 일치하며 실제 음성 16개 비트 모두 자기 창 안에 들어간다. 바뀐 h07만 46자를 새로 합성했다.
- 개인정보 OCR: 최종본 1초 간격 90프레임 / 3,016줄, Docs·Blog 소재 64프레임 / 660줄, 모두 발견 0건. 실제 소재와 최종 4분할·끝 화면을 이미지로 열어 확인했다.
- Docs는 Drive 저장 배지 확인 후 재열기·DOCX 원문 확인(836자, 제목·다섯 섹션·주소 모두 존재). Naver는 새 임시저장 글로 저장했고, 기존 QA 초안도 유지되어 목록이 1개에서 2개가 됐다. 별도 새 창에서 저장 목록의 새 글을 열어 제목·전체 본문·URL·태그를 다시 읽었다. 게시하지 않았다.
- 개별 실행을 합성했고, Slides는 이전 WAM 프로젝트 소재다. 새 Docs·Blog 소재의 유휴 구간을 편집했으므로 소요 시간이나 속도 우위를 주장하지 않는다.
- 음성은 파일·비트 길이·음량으로 검증했다. 현재 Codex 도구 경로에서는 오디오 입력이 전달되지 않아 직접 들었다고 주장하지 않는다. 세로 Shorts 전용 `video_qc`의 1080×1920 / 6–60초 판정은 이 가로 90초 컷의 합격 기준으로 사용하지 않았다.

상세 입력·기대 결과·원인·리뷰는 [`hackathon-resume.md`](hackathon-resume.md), 로컬 증거는 `.artifacts/video-resume/`에 있다. 커밋·공개 업로드는 하지 않았다.
