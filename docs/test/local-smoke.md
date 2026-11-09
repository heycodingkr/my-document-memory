# 로컬 스모크 테스트

상태: 절차 정의(문서 우선). 호스트(Claude Code, Codex, Arise) 없이 **CLI + stdio MCP + loopback fixture 서버**만으로 [`host-smoke.md`](host-smoke.md)의 SMK 부분집합과 핵심 계약 케이스를 실행한다. 대상은 환경 변수로 바꾼다: 구현이 없는 지금은 **테스트 더블**(`tests/env/dmem-double`), 구현이 생기면 같은 명령으로 제품을 시험한다([`../../tests/README.md`](../../tests/README.md) "대상 어댑터").

## 실행

```
# 1) 하네스 자체 검사 (브라우저·네트워크 없음)
python3 -B -m unittest discover -s tests/lib/selftest -t tests/lib

# 2) 더블 대상 스모크 + 계약 (fixture 서버·일회용 홈을 하네스가 알아서 띄우고 정리)
python3 -B tests/smoke/run_all.py --suite smoke

# 3) 제품 대상 (runtime-v1 범위만)
DMEM_TARGET=product DMEM_BIN=/abs/dmem DMEM_MCP_BIN=/abs/dmem-mcp DMEM_PROFILE=runtime-v1 \
  python3 -B tests/smoke/run_all.py --suite smoke
```

모든 실행은 일회용 `HOME`·`XDG_*`·`TMPDIR`(`/tmp/dmem-*`)·`DMEM_HOME`과 임의 빈 포트의 fixture 서버를 쓰고, 끝나면 자기 프로세스·디렉터리만 정리한다. 증거는 `target/e2e-logs/smoke/<run-id>/`다.

## 시나리오 (SMK 로컬 부분집합)

| 순서 | 경로 | 내용 | 확인(oracle) | SMK |
|---|---|---|---|---|
| 1 | CLI | `dmem --version`, `--help`, 알 수 없는 서브커맨드 | 종료 0 / 0 / 2, 명령 이름 전부 | SMK-01 |
| 2 | MCP | `initialize` → `tools/list` | 도구 12개, 스키마·annotations, stdout 순수성, 카탈로그 크기 | SMK-02 |
| 3 | CLI | `RCL-LIB`을 저장한 뒤 `recall --stdin --json`(canonical·비정규 URL) | 순서(`RCL-01`~`04`), 힌트 ≤3, `untrusted`, `receipt_id` 없음, 요청 0 | SMK-03 |
| 4 | MCP | 같은 `recall`을 MCP로 | CLI와 같은 힌트·순서 | SMK-03 |
| 5 | CLI | 모르는 URL·양식 | 빈 결과·`no_match`·종료 0 | SMK-04 |
| 6 | CLI·MCP | `expand` level 1·2, `--version` 고정 | L2 센티널은 level 2에서만 | SMK-05 |
| 7 | CLI | `save --file resume-ko.md`(`--dry-run` → 저장 → 재저장) → `list` → `export --format md` → `delete --yes` → `expand` | 비공개, 원본 0600, `created:false`, 파일 0600, 종료 7 | SMK-07 |
| 8 | CLI | 서버 모드 더블에서 `search --scope public` → `expand` → `copy`(`SHR-CAT`) | 작성자·라이선스·버전, 복사본 `derived_from`, 원본 해시 불변 | SMK-08 |
| 9 | CLI | `web search`(fixture provider) → `web preview` → `import`(CC-BY, 라이선스 없음, 주입 페이지) | 라이선스별 `copy_policy`, 본문 prose 0, 숨김 문구 0, fixture 로그에 쿠키 헤더 이름 0 | SMK-09 |
| 10 | CLI | `publish` 동의 없음 → 있음 | 종료 4·쓰기 0 / `queued`·`approved` | SMK-11 |
| 11 | CLI | 연결 없는 `publish`·`outcome` | 종료 3·쓰기 0 | SMK-12(일부) |
| 12 | CLI | 서버 중지 뒤 `list`·`recall`(mine)·`search --scope public` | 로컬은 동작, 서버 필요 명령은 종료 5 | SMK-13 |
| 13 | 전체 | 센티널 스윕(8 sink) | 센티널 0건, sink 목록 모두 비어 있지 않음 | SMK-16 |
| 14 | 전체 | 정리 확인 | 남은 프로세스·임시 디렉터리·포트 0 | SMK-14(일부) |

SMK-06(자발적 호출), SMK-10(현재 탭 클립), SMK-12의 device flow, SMK-15는 호스트·제품이 필요해 로컬 스모크에 없다([`hosts/arise.md`](hosts/arise.md) 등).

## 합격

- 범위 안(프로필) 시나리오가 모두 통과하고 `SKIP`은 사유가 있다(`--strict`에서는 범위 안 `SKIP`이 실패).
- 더블 대상 통과는 **하네스와 계약 해석이 일관됨**을 뜻할 뿐 제품 합격이 아니다(`harness-verification.md`).
- 같은 명령을 제품에 적용했을 때 실패하는 케이스는 제품 결함 또는 명세와 구현의 차이다. 차이는 [`README.md`](README.md) 7절 표에 기록하고 어느 쪽을 고칠지 결정한다.
