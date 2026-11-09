# ADMIN: 게시 검수·takedown·계정 관리

상태: 설계 초안(문서 우선, 구현 없음). 공개 사용자·관리자 화면은 runtime-v1 이후 단계다.
영역 / 테스트 ID 접두사: `ADMIN` (케이스: [`../test/functional-account.md`](../test/functional-account.md))
기반: [`accounts-community-v1.md`](accounts-community-v1.md), [`privacy.md`](privacy.md), [`sharing.md`](sharing.md)
WAM 승계(재확인 필요): 일반 사용자와 분리된 관리자 권한, 검수 generation, 명시적 결정, no-store 응답, 최소 감사 기록.
제안: account-community-v1의 `DMEM_ADMIN_TOKEN`을 브라우저가 직접 보유하지 않도록 별도 관리자 세션으로 교환하는 경로. 세션 발급·수명은 미정이며 확정 전에는 UI에 인증 토큰을 넣지 않는다.

## 1. 목적과 권한 경계

화면은 게시 검수 큐, 결정·takedown 감사 기록, 계정 정지 상태를 보여준다. 일반 계정 세션, CLI의 `DMEM_TOKEN`, 연결 기기는 관리자 권한이 아니다. 관리자 자격은 서버에서 검증하고 모든 비공개 응답은 no-store다.

`accounts-community-v1.md`가 정한 `DMEM_ADMIN_TOKEN`을 유지한다. 기존 계정 계약에 없는 권한 분리 방식이나 역할 세분화는 제안으로만 다룬다. 변경 요청은 관리자 세션, 허용 origin, CSRF를 검사하고 결과를 확인하기 전에 성공 상태를 표시하지 않는다.

## 2. 검수 큐와 takedown

검수 큐는 pending 항목의 상태, 접수 시각, 제출자 식별의 마스킹값, 정규화된 문서 범위, 제안 snapshot, 현재 generation, 결정 이력을 보여준다. 원문 페이지·URL query/fragment·인증 정보는 목록에 넣지 않는다. 상세는 요청된 자료의 최소 메타데이터만 보여준다.

검수 결정은 현재 generation에 대해서만 가능하다. 승인·반려는 서로 다른 명시적 동작이며 원자적으로 기록한다. 승인된 snapshot만 공유 계약의 공개 전이를 거치고, 검수 실패나 오래된 generation은 게시되지 않는다.

운영자 takedown은 공유 계약의 `status=taken_down`을 사용해 공개 recall/search/expand/copy에서 즉시 숨긴다. 기존 복사본은 유지하되 `origin_taken_down` 경고와 재게시 차단을 따른다. takedown 사유는 최소 사유 코드로 기록한다. 작성자 자신의 목록에 남기는 방식은 `sharing.md`의 열린 결정이며, **제안**은 상태 `taken_down`으로 표시해 보존하는 것이다.

## 3. 감사 기록과 마스킹

모든 검수·takedown 결정은 행위자, 대상 ID, 작업, 사유 코드, 시각, 이전·이후 상태를 append-only 감사 기록으로 남긴다. 상태 변경과 기록 저장은 원자적이다. 기록 화면은 계정·문서 본문이나 비밀을 복제하지 않으며 일반 계정에는 공개하지 않는다.

관리자 목록의 이메일은 일부만 마스킹하고 token, device secret, raw IP, session cookie, private source, 개별 복사자 식별은 응답·DOM·감사 기록에 넣지 않는다. 복구 불가하게 지운 값은 **제안**: `마스킹됨`과 redacted 표시만 남기고 원문·역변환 정보·unmask 동작은 만들지 않는다.

## 4. 계정 정지

계정 정지는 문서 도메인의 신규 제안이다. 운영자가 대상 계정과 사유 코드를 확인한 뒤 별도 정지 동작을 실행하고, 행위자·대상·시각을 감사 기록에 남긴다. 정지 계정의 새 로그인·쓰기·게시·기기 연결은 거부한다. 정지만으로 라이브러리·게시물·기존 복사본을 삭제하거나 takedown하지 않는다. 공개 노출이 문제라면 게시물별 takedown을 별도로 실행한다.

## 5. 요구사항과 테스트

| ID | 요구사항 | 합격 기준 | 관련 테스트 |
|---|---|---|---|
| F-ADMIN-01 | 관리자 권한 분리 | 일반 세션·사용자 Bearer·local token은 관리자 경로에 접근하지 못한다 | ADMIN-01~02 |
| F-ADMIN-02 | 검수 큐·상세 | 상태와 최신순 목록은 보이고 민감 원문·비밀은 마스킹된다 | ADMIN-03~05 |
| F-ADMIN-03 | generation·결정 | 최신 검증 결과만 명시 승인되고 반려·충돌도 기록된다 | ADMIN-06~08, ADMIN-16 |
| F-ADMIN-04 | takedown | 공개 조회에서 숨기고 사본 경고·재게시 차단을 유지한다 | ADMIN-09 |
| F-ADMIN-05 | 계정 정지(제안) | 정지는 인증·쓰기·연결을 막되 데이터를 자동 삭제하지 않는다 | ADMIN-10 |
| F-ADMIN-06 | 마스킹(제안) | 이메일은 가리고 redacted 원문은 복구·노출할 수 없다 | ADMIN-11~12 |
| F-ADMIN-07 | 감사 기록 | 모든 변경은 행위자·대상·사유·시각과 상태 전이를 남기며 원문은 없다 | ADMIN-13~14 |
| F-ADMIN-08 | 웹 경계 | 잘못된 Origin/CSRF는 변경하지 않고 no-store 응답을 유지한다 | ADMIN-15 |