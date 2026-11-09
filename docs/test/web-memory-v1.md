# Web memory v1 입력·기대 결과

상태: 구현 전 케이스. 원본 계약은 [`../spec/web-memory-v1.md`](../spec/web-memory-v1.md). 합성 입력·임시 DB·loopback fixture만 사용한다.

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
| WI-11 | 같은 URL에 KR/US/JP locale/variant 또는 다른 doc_type/provider | 독립 양식 공존, form·출처 보존, 기존 recall로 자기 양식 조회 |
| WI-12 | source full 허용 → 저장·생성에 참고자료 사용 | 살균한 원문 span만 저장, 원문 HTML/입력 폼/hidden 없음 |
| WI-13 | 외부 unknown/NC 또는 제약 있는 출처를 가져온 뒤 CC0로 기여 | 검출 권리/출처가 검수에서 유지, 허용되지 않은 재게시 거부 |
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

실행 결과와 로그 경로는 구현·부모 검증 뒤 추가한다. 원격 실사이트 성공이나 OAuth 동기화는 합성 fixture 결과로 주장하지 않는다.
