# Web memory v1 설계·원인·리뷰

2026-11-09. 계약: [`../spec/web-memory-v1.md`](../spec/web-memory-v1.md), 입력/기대 결과: [`../test/web-memory-v1.md`](../test/web-memory-v1.md).

현재 제품은 파일 업로드·양식/자료/작성 문서와 공개 기여·recall을 제공한다. URL fetch/search/preview와 현재 탭 clip이 없으므로 명세/더블만 통과한 상태였다. 기존 소유자 인증·검수·파일 추출 경계를 재사용하고 별도 web intake 모듈을 추가한다. preview 원문은 영속 저장하지 않고, 저장된 항목과 출처 원장은 같은 SQLite 트랜잭션으로 쓴다. 밖에서 가져온 내용과 출처 권리의 검수 경계를 보존한다.

구현과 red/green·실제 제품/Arise 검증 뒤 결과·제약·최종 리뷰를 추가한다.
