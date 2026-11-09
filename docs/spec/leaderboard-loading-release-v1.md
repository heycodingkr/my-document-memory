# 리더보드 시간 제한 커밋·배포

2026-11-09. 이슈 #408. 사용자가 커밋·푸시 및 가능한 운영 배포를 승인했다.
원래 [시간 제한 계약](leaderboard-loading-v1.md)과
[재현 입력/결과](../test/leaderboard-loading-v1.md)를 유지한다.

## 현재 확인한 상태

- 원본 수정은 원격 main의 `92657d0`에, 재현 테스트·명세는 `82633bd`에 통합됐다.
  따라서 기존 코드를 중복 구현하지 않고 원격 포함 여부를 직접 확인한다.
- 운영 frontend는 `b11e064` / `20261109T055832Z-bugfix-b11e064`이며, 실제
  운영 JS에 timeout 메시지가 없고 해당 소스의 session/leaderboard도 무제한이다.
- main은 아직 운영에 없는 다른 기능을 포함한다. 운영과 일치하는 `b11e064`
  소스에서 리더보드 API 수정만 적용해 현재 UI·동영상·서버 상태를 보존한다.
- 공유 main의 미커밋 README/landing/번역/동영상 작업은 스테이지하거나 덮어쓰지 않는다.

## 의존 순서·경로·산출물·독립 확인

| 목표 | 경로 | 산출물 | 부모의 독립 확인 | 선행 |
|---|---|---|---|---|
| P0 상태/동결 | 부모 inline | git/remote/API·테스트·배포 코드, 운영 manifest, 격리 release/기록 worktree | 실제 원격 main 포함 커밋, SSH 활성 release/파일 hash, 변경 전 빌드 일치 | 없음 |
| P1 최소 릴리스 | 부모 inline | 운영 소스+timeout 수정, focused 테스트, 검토된 커밋·원격 release branch | 수정 파일 직접 diff, check/build, production bundle focused5, 기존 회원/계정 경로 | P0 |
| P2 운영 전환 | 부모 inline | 파일 hash manifest, archive, 새 release와 rollback 경로 | 배포 lock 안에서 예상 base/index/server 검사, 기존 서버·설정/PID 보존, atomic symlink 전환 | P1 |
| P3 공개 검증/기록 | 부모 inline | 실제 HTTPS와 브라우저 결과, main의 최종 결과 commit/push, 이슈 해결 | 배포 JS/hash 일치, 공개 실제0명, 운영 번들 지연/Retry 테스트, origin ref 재확인 | P2 |

모든 구현·판단·테스트·배포 루프는 부모가 직접 수행한다. 배포 base가 도중에
바뀌면 전환하지 않고 새 base를 다시 확인한다. 실패 시 확인된 이전 release로
되돌리고 검증한다. 사용자 데이터/계정/공개 설정을 테스트 데이터로 변경하지 않는다.

## 배포 입력과 기대 결과

| 입력 | 기대 결과 |
|---|---|
| untouched b11e064 빌드 | 실제 운영 index 및 연결 JS/CSS와 동일 SHA-256 |
| candidate api.ts diff | helper/timeout 메시지와 session/leaderboard만 변경 |
| 기존 LL-01~07 | pending headers/body/session의10초 제한, 실제 abort, Retry 성공/0명/503/성공 후 타이머 정리 |
| 실제 임시 SQLite 회원·계정 | 가입/명시적 이메일 확인/세션/공개 선택·승인·철회/순위 정상 |
| 배포 전 예상 base/hash 불일치 | 전환 거부, 기존 운영 유지 |
| 운영 HTTPS index/JS/CSS 및 고정 공개 파일 | candidate manifest와 hash 일치, video byte-range와 양쪽 health 정상 |
| 운영 #leaderboard 정상 조회 | 실제0명 안내, 오류와 로딩 없음; 임의 회원 생성 없음 |
| 운영 번들에서 응답 정지 입력 | 10초 후 오류+Retry, Retry에 새 요청으로 복구 |
| 배포 전후 서버/config/PID | 동일, 서버 재시작과 DB migration 없음 |

## 설계·검토

운영과 main의 frontend 차이를 그대로 배포하면 검증 범위를 벗어난 기능을 함께
출시하게 된다. 따라서 검증된 운영 소스에 동일한 작은 수정을 적용하고 별도의
release branch로 정확한 배포 소스를 남긴다. 현재 manifest의 동영상은 기존
release에서 보존한다. 서버 binary와 기존 static 파일을 복사하고 새 hashed bundle을
추가해 오래 열린 탭도 유지한다. 최종 배포 정보와 확인 결과는 기존 테스트 문서에
별도 날짜 기록으로 추가하고 main에 푸시한다.
