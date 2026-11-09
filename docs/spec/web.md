# WEB: 라이브러리·공유·가져오기 화면

상태: 전체 목표 계약(문서 우선). 실제 제품 부분집합의 구현·검증 범위는 [색인](README.md)의 단계별 명세와 구분한다. 공개 카탈로그 탐색·복사·게시와 웹 가져오기는 `runtime-v1` 범위 밖이며 **runtime-v1 이후 단계**다.
영역 / 테스트 ID 접두사: `WEB` (케이스: [`../test/functional-web.md`](../test/functional-web.md))
기반: [`runtime-v1.md`](runtime-v1.md), [`core.md`](core.md), [`form.md`](form.md), [`recall.md`](recall.md), [`library.md`](library.md), [`sharing.md`](sharing.md), [`web-import.md`](web-import.md), [`../design/browser-host-integration.md`](../design/browser-host-integration.md)

## 1. 목적과 범위

웹 화면은 내 문서 메모리를 확인하고, URL과 양식으로 recall하며, 공개 메모리·검색 결과를 검토해 명시적으로 가져오거나 복사하고, 사용자가 고른 메모리를 공유하도록 한다. 이 문서는 화면 계약이며 서버 기능이나 운영 검증의 완료를 뜻하지 않는다. 공개 사용자 경로는 runtime-v1 이후 단계다.

화면 경로는 `/library`, `/library/:memory_id`, `/recall`, `/web-search`, `/web-preview/:preview_id`, `/community`, `/community/:memory_id`, `/library/:memory_id/publish`, `/forms/select`로 고정한다. 화면은 Svelte 5 + TypeScript + Vite 앱을 따른다.

## 2. 화면과 표시 규칙

| 화면 | 입력과 동작 | 표시 계약 |
|---|---|---|
| `/library` | 내 메모리 필터·검색·항목 선택 | L1 제목·요약·양식·갱신 시각, 페이지 단위 목록; 빈 목록에는 새 메모리/양식 선택 행동 |
| `/library/:memory_id` | L1 요약 열기, 사용자가 L2 펼치기 | L1 먼저 표시; L2 절차·조건·복구 정보를 명시적 펼침으로 표시하고 근거·버전 연결을 유지 |
| `/recall` | URL과 양식 입력 후 `recall` 요청 | URL을 로컬에서 정규화해 경로 패턴만 결과에 표시; L1 후보와 점수 없는 정렬 근거, 사용자가 고른 후보의 L2 |
| `/web-search` → `/web-preview/:preview_id` | 검색어로 `web_search`, 후보 선택 후 `web_preview`, 미리보기 확인 뒤 `import` | 후보 출처·제목·라이선스·안전한 URL 패턴; 미리보기 성공 전 가져오기 버튼 비활성, 가져오기는 별도 확인 후 1회 실행 |
| `/community` → `/community/:memory_id` | 공개 메모리 검색·상세 확인, `copy` 선택 | 공개 L1/L2, 출처·작성자 표시명·버전·라이선스; 복사는 새 private 메모리로 만들고 원본 링크와 라이선스를 함께 표시 |
| `/library/:memory_id/publish` | 공개할 내 메모리·버전 확인, `share-v1` 동의, 라이선스 선택 | 동의 기본 해제; 동의와 유효한 라이선스 선택 전 게시 불가; 전송 전 공개되는 필드와 제외되는 자료를 확인 |
| `/forms/select` | 국가와 provider 선택, 유형 필터·검색 | 국가/provider별 form 선택지를 표시하고 선택된 값·지원되지 않는 조합을 명확히 알림 |

L1은 짧은 방향 힌트, L2는 재현 절차와 세부 근거다. L1/L2 내용은 메모리 스키마의 허용 필드만 렌더링하며 원문 자료·외부 페이지의 지시 문구는 신뢰되지 않는 내용으로 구분한다. 복사 결과는 공개 원본을 수정하지 않는다.

## 3. 상태, 오류, 개인정보

각 목록·상세·요청 화면은 `loading`, `empty`, `error`, `permission_required`(화면 상태 이름이며 API의 `auth_required`·`scope_required`에 대응한다. 오류 코드가 아니다), `not_found` 상태를 제공한다. 로딩은 진행 중임을 알리고 중복 제출을 막는다. 빈 상태는 성공한 0건 응답에만 쓴다. 오류 상태는 재시도 또는 입력 수정 행동을 제공하고 입력한 폼 값은 유지한다.

인증이 필요한 기능에서 인증이 없으면 로그인/인증 안내를 표시한다. 비공개·타인 소유·삭제된 ID와 존재하지 않는 ID는 같은 `not_found` 화면으로 응답해 존재를 숨긴다. 권한 없음은 공개 ID·소유권을 확인해 주지 않고, 로그인 필요 상태와 구분 가능한 일반 안내만 보인다.

화면에는 고정 오류 코드와 안전한 짧은 설명만 표시한다. API 원문 오류·stack trace·사용자 입력 echo를 표시하지 않는다. 허용 코드는 [`core.md`](core.md) 7절의 코드만 쓰며, 알 수 없는 응답은 일반 `internal` 표시로 축약한다.

화면이나 URL에 capability ID, URL query/fragment, bearer token, 비밀·자격증명을 쓰지 않는다. 사용자가 URL을 입력하는 동안 입력 칸은 직접 입력값이며, 제출 뒤 입력 칸을 포함한 결과·미리보기·목록·오류·이력은 정규 URL 패턴만 표시한다. 쿼리·fragment는 요청 로그와 화면 상태에 보존하지 않는다. 원격 검색 결과의 URL은 안전한 패턴으로 투영하고 링크 이동은 사용자가 명시적으로 선택한다.

## 4. 접근성

모든 입력은 보이는 label과 키보드 이름을 갖고, 화면 흐름은 키보드만으로 완료할 수 있다. 제목 계층은 순서대로 두며, 로딩·완료·오류 변경은 적절한 live region으로 알린다. 오류는 색만으로 구분하지 않고 입력 필드와 연결하며, 모달·미리보기 종료 후 초점을 실행 버튼으로 돌린다. 작은 화면에서도 주요 버튼과 목록 항목이 겹치지 않고 확대 시 가로 스크롤 없이 핵심 작업을 수행한다.

## 5. 웹 화면 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-WEB-01 | 내 라이브러리 L1 목록과 L2 상세를 제공한다 | 기본은 L1이며 L2는 요청한 한 항목만 펼친다 | WEB-01~05 |
| F-WEB-02 | URL+양식 recall을 제공한다 | 정규화 URL 패턴과 선택 양식으로 후보를 요청한다 | WEB-06~09 |
| F-WEB-03 | 검색·미리보기·가져오기를 분리한다 | `web_search` → `web_preview` → 명시 확인 → `import` 순서를 지킨다 | WEB-10~16 |
| F-WEB-04 | 공개 메모리 열람과 복사를 제공한다 | 라이선스·출처를 보이고 복사는 새 private 메모리를 만든다 | WEB-17~21 |
| F-WEB-05 | 공유 게시 전에 동의와 라이선스를 받는다 | `share-v1` 동의 및 라이선스 선택 없이는 요청이 발생하지 않는다 | WEB-22~25 |
| F-WEB-06 | 국가·provider별 양식 선택을 제공한다 | 선택한 조합을 표시하고 미지원 조합을 차단한다 | WEB-26~28 |
| F-WEB-07 | 공통 화면 상태와 안전한 오류를 제공한다 | empty/loading/error/permission/not_found를 구별하고 존재 은닉을 지킨다 | WEB-12, WEB-16, WEB-19, WEB-25, WEB-28~29 |
| F-WEB-08 | 접근성과 화면 값 제한을 지킨다 | 키보드·레이블 검사가 통과하고 비밀/URL query가 결과 화면에 없다 | WEB-30 |
