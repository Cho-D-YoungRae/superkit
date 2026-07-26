# CLAUDE.md

`infra` — 인프라 하네스를 구성·운영하는 Claude Code 플러그인. 이 파일은 **이 저장소를 수정하는
세션**을 위한 것이다(플러그인 사용법은 README.md, 확정 설계는 docs/ 참조).

## 명령

```bash
bash tests/run_tests.sh   # 전체 테스트(55개). 스킬·스크립트·hook 수정 후 항상 실행
claude --plugin-dir .     # 개발 모드 로드 → 세션 내 /reload-plugins 로 변경 반영
```

`scripts/`·`hooks/scripts/`는 **python3 표준 라이브러리만** 쓴다(PyYAML 등 외부 의존 금지).

## 구조

- `.claude-plugin/plugin.json` — 매니페스트. **이 디렉토리엔 이 파일만** 둔다(다른 파일은 로드 안 됨).
- `skills/<name>/SKILL.md` — 스킬 9종. `ops/references/*.md`는 필요 시 온디맨드 로드.
- `templates/` — init이 하네스로 복사·치환하는 골격 11종.
- `scripts/harness_lib.py` — 하네스 상향 탐색 + frontmatter/YAML 파서(audit·sync 공용).
- `hooks/scripts/change_reminder.py` — PostToolUse(Bash) hook.
- `tests/fixtures/` — harness-ok(정상)·harness-bad(오염)·harness-off(hook off).

## 수정 시 반드시 지킬 것

- **원칙 1·2 (이 플러그인의 존재 이유)**: 스킬 본문·스크립트·references 어디에도 시크릿 **값**을
  읽거나 출력·cat·echo 하는 지시를 넣지 않는다. 참조 실행(`${VAR}`, `ssh -i <경로>`,
  `sops exec-env`, `op run`)만. 명령 예시엔 항상 `--context`/`--profile` 명시(원칙 6).
  10개 원칙 전체는 README §4, 확정 근거는 docs/superpowers/specs/.
- **hook은 절대 차단하지 않는다**: `change_reminder.py`는 어떤 경로로도 `exit 0`. 독립 실행형이라
  `harness_lib`를 import하지 않는다(플러그인 배포 경로 문제 회피).
- **SKILL.md frontmatter**: `name`은 디렉토리명과 일치, `description`은 한 줄 스칼라 + 한국어
  3요소(역할 / 트리거 발화 / 인접 스킬 경계). `tests/test_skills.py`가 이를 강제한다
  (본문에 "원칙"·"harness.yaml" 포함, description ≥ 80자도 검사).
- **frontmatter 파서 한계**: 엔티티 frontmatter는 플랫 구조만(`key: value`, `[a, b]`, 따옴표).
  중첩 맵은 harness.yaml 전용 로더(`parse_yaml_subset`)에서만 처리.
- **하네스 발견은 cwd 상향 탐색만**(스펙 D1) — 전역 포인터·사용자 설정을 건드리지 않는다.

## 확정 설계 (변경 전 반드시 확인)

- `docs/superpowers/specs/2026-07-19-infra-plugin-design.md` — 불변 원칙 10개, 데이터 스키마,
  결정 D1~D9.
- `docs/superpowers/plans/2026-07-19-infra-plugin.md` — 태스크별 구현 계획.

원칙·스키마·D 결정은 **확정 사항**이다. 이를 바꾸는 변경은 스펙을 먼저 갱신하고 진행한다.
