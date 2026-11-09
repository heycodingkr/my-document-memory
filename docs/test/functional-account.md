# 계정·내 페이지·프로필·관리자 기능 테스트

상태: 문서 우선. 공개 계정과 관리자 화면은 runtime-v1 이후 단계다.
대상 명세: [`my-page.md`](../spec/my-page.md), [`profile.md`](../spec/profile.md), [`admin.md`](../spec/admin.md)
판정: 각 입력은 격리 fixture의 합성 계정·문서·토큰만 사용한다. 응답·화면·저장 상태를 직접 관찰한다.

| ID | 입력/시나리오 | 기대 결과와 판정 근거 |
|---|---|---|
| MYPAGE-01 | 세션 쿠키 없이 `GET /v1/me` 및 내 페이지 진입 | API는 401, 화면은 로그인 안내만 보이고 계정·문서 목록 데이터 0건이다 |
| MYPAGE-02 | 계정 A/B에 같은 kind의 비공개 문서 생성 후 A 세션으로 B의 문서 ID 조회 | 응답은 없는 ID와 같은 not-found이며 본문·존재 차이를 구별하지 않는다 |
| MYPAGE-03 | A 라이브러리에 template 2개, reference 1개 생성 후 kind=template 필터 | 결과는 template 2개뿐이고 reference는 0개다 |
| MYPAGE-04 | 같은 문서를 version 1·2·3으로 저장 후 버전 이력 열기 | 버전은 정수 3,2,1 순으로 표시되고 각 버전의 ID·시각이 연결된다 |
| MYPAGE-05 | 공개 문서와 version 1·2 및 B 복사본이 있는 상태에서 A가 확인 후 삭제 | A의 모든 버전·본문은 삭제되고 공개 조회에서 빠지며 B 복사본은 남는다 |
| MYPAGE-06 | B 세션으로 A 문서의 ID와 존재하지 않는 ID를 각각 삭제 요청 | 두 응답은 동일한 not-found이고 A 문서의 버전·내용은 바뀌지 않는다 |
| MYPAGE-07 | A 소유 document version 2를 지원 형식 md로 내보내기 | 다운로드 산출물은 요청 문서/version 2를 나타내며 기존 export 안전 규칙을 통과한다 |
| MYPAGE-08 | A가 존재하지 않는 ID 또는 지원하지 않는 kind-format 조합을 내보내기 | 명시 오류가 반환되고 목적지 파일은 생성·덮어쓰기 되지 않는다 |
| MYPAGE-09 | A가 공개 게시물 1개를 만들고 공개 상세를 조회 | 상세의 `author_handle`은 A의 공개 핸들이며 이메일·내부 계정 ID는 없다 |
| MYPAGE-10 | A 게시물 복사본을 B와 C가 각각 만들고 A의 복사 현황 조회 | 공개 집계는 2이며 B/C의 계정·이메일·기기 식별자는 응답에 없다 |
| MYPAGE-11 | B가 A의 public v3 문서를 복사하고 내 복사본 상세를 조회 | `derived_from`은 원본 ID·v3·A의 `author_handle`·license를 보존한다 |
| MYPAGE-12 | A에 active·revoked device link fixture를 만들고 연결 기기 화면 조회 | A의 두 상태와 허용 scope만 보이며 token·device secret·user code는 0건이다 |
| MYPAGE-13 | A가 active device link 하나를 확인 후 해지하고 해당 credential로 요청 | 해당 연결만 revoked되고 다음 요청은 인증 실패하며 다른 기기는 유지된다 |
| MYPAGE-14 | A가 서로 다른 두 문서를 `share-v1`로 게시하고 동의 기록 조회 | 두 기록 각각에 version·시각·memory_id·version·visibility·license가 보인다 |
| MYPAGE-15 | B 세션으로 A 동의 원장 ID를 조회하고 A의 private 게시 동의를 찾는다 | B에게 A 기록은 not-found이며 private scope와 내부 계정 식별은 public 응답에 없다 |
| MYPAGE-16 | 동의 원장 화면만 새로 열고 요청 전후 consent 저장 행 수를 비교 | 조회 전후 행 수·값이 같고 전역 동의 설정이 생성되지 않는다 |
| PROFILE-01 | `Alice-7` 핸들을 저장한다(유효한 3~24자 ASCII) | 저장 성공, 정규화 조회에서 같은 공개 핸들 하나가 반환된다 |
| PROFILE-02 | `ab`, `-alice`, 예약 `admin`, A와 대소문자만 다른 B 핸들을 저장 | 각 입력은 거부되고 기존 핸들·프로필 값은 그대로다 |
| PROFILE-03 | 프로필 생성 직후 비공개 조회 목록과 다른 사용자 공개 조회를 확인 | 기본 비공개이며 핸들·표시 이름·소개가 공개 목록/API에 없다 |
| PROFILE-04 | A가 프로필 공개를 켜고 공개 게시물을 열어 `/u/Alice-7` 조회 | 공개 허용 필드와 핸들이 보이고 게시물 `author_handle`은 Alice-7이다 |
| PROFILE-05 | A가 공개 프로필을 끄고 디렉터리·프로필·기존 공개 문서 조회 | 프로필/디렉터리에서 즉시 빠지고 기존 공유 문서의 불변 attribution은 그대로다 |
| PROFILE-06 | display_name만 공개하고 intro는 비공개, 이어서 반대로 scope 변경 | 각 응답은 공개된 필드만 포함하고 숨긴 필드는 키 자체가 없다 |
| PROFILE-07 | A 프로필에 B의 account_id를 본문에 넣어 B 세션으로 수정 요청 | 소유자 불일치로 거부되고 A/B 프로필 모두 수정되지 않는다 |
| PROFILE-08 | A 프로필에 합성 소개와 `<script>window.x=1</script>`를 저장하고 공개 응답 검사 | 스크립트 실행은 0회이며 응답 키는 허용 필드뿐이고 email·account_id·device_id가 없다 |
| ADMIN-01 | 사용자 세션과 익명 요청으로 `GET /v1/admin/contributions` 호출 | 둘 다 401/403, 검수 항목·계정 정보 반환 0건이다 |
| ADMIN-02 | 일반 사용자 Bearer, runtime `DMEM_TOKEN`, 별도 관리자 인증 fixture로 같은 경로 호출 | 일반 자격은 거부되고 관리자 자격만 허용된다. 관리자 token은 브라우저 저장소에 없다 |
| ADMIN-03 | pending·approved·rejected 요청 fixture 3개로 관리자 큐 열기 | 세 상태가 분리되고 최신순 페이지의 ID·상태·시각이 서버 결과와 같다 |
| ADMIN-04 | status=pending 필터와 cursor page size 2를 적용해 큐 두 번 조회 | 각 페이지 최대 2행이고 cursor 다음 페이지에 중복 ID가 없다 |
| ADMIN-05 | 제출 URL에 query/fragment와 private source sentinel을 넣고 상세 열기 | 정규화 URL·요청 task·snapshot 메타만 보이고 query·fragment·원문·token sentinel은 0건이다 |
| ADMIN-06 | 검수 generation 4 상세를 연 뒤 generation 5로 갱신하고 4에 결정 요청 | stale generation은 conflict로 거부되고 게시 상태·현재 generation은 변하지 않는다 |
| ADMIN-07 | generation 5의 검증된 snapshot을 명시 승인한다 | 새 immutable public version 하나가 생기고 license·attribution이 보존된다 |
| ADMIN-08 | pending 제출을 사유 코드 `rights_unclear`로 반려한다 | 공개 항목은 생성되지 않고 반려 상태·사유·행위자·시각이 감사 화면에 추가된다 |
| ADMIN-09 | 공개 S2와 B의 기존 복사본을 둔 뒤 S2에 운영자 takedown 실행 | S2는 public search/expand/copy에서 숨고 B 복사본은 `origin_taken_down` 경고, 재게시 거부를 보인다 |
| ADMIN-10 | 활성 계정을 사유 코드 `abuse_review`로 정지 후 로그인·쓰기·링크 요청 | 새 세션·쓰기·연결은 거부되고 개인 자료·게시물·기존 복사본은 자동 삭제되지 않는다 |
| ADMIN-11 | 관리자 계정 목록에 `alice@example.test`와 내부 ID를 넣어 목록 조회 | 이메일은 일부 마스킹되고 내부 ID는 기본 목록에서 제외되며 token·IP는 없다 |
| ADMIN-12 | 저장소에서 복구 불가 처리한 이메일 fixture를 상세·감사 화면에서 조회 | 값은 `마스킹됨`으로 표시되고 원문·복구/unmask 동작은 어디에도 없다 |
| ADMIN-13 | 검수 승인과 takedown을 순서대로 실행한 뒤 감사 기록 조회 | 각 이벤트에 actor·target·action·reason·time·상태 전이가 한 건씩 남는다 |
| ADMIN-14 | private source·raw IP·session/token sentinel이 든 요청을 처리하고 감사 기록 검색 | 각 sentinel의 원문은 응답·DOM·로그·감사 기록에 0건이다 |
| ADMIN-15 | 잘못된 Origin과 누락 CSRF로 takedown POST 후 응답 확인 | 요청은 거부되고 대상 상태는 불변이며 응답은 `Cache-Control: no-store`다 |
| ADMIN-16 | 두 관리자가 같은 generation을 동시에 승인·반려 요청 | 한 결정만 성공하고 다른 요청은 conflict이며 게시 전이와 감사 이벤트는 1건이다 |