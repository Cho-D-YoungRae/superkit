# 기여 가이드

superkit에 기여해 주셔서 감사합니다. 이 문서는 브랜치 전략, 커밋 규칙, 릴리즈 절차를 설명합니다. 저장소 구조와 작업 규칙은 [AGENTS.md](AGENTS.md)에 있습니다.

## 브랜치 전략

`main` 하나를 상시 브랜치로 두는 GitHub flow를 사용합니다. 작업 브랜치는 `main`에서 분기해 `main`으로 PR을 보냅니다.

| 접두사 | 용도 |
|---|---|
| `feat/<설명>` | 기능 추가 |
| `fix/<설명>` | 버그 수정 |
| `docs/<설명>` | 문서 |
| `chore/<설명>` | 빌드·설정 등 기타 |

설명은 kebab-case로 씁니다. 예: `feat/superglossary-lookup-skill`.

## 커밋 메시지

[Conventional Commits](https://www.conventionalcommits.org/ko/)를 따르고, 범위에 플러그인 이름을 적습니다.

```
<타입>(<플러그인>): <설명>
```

주요 타입: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`. 예: `fix(infra): sync가 확인하지 못한 provider를 보고한다`. 여러 플러그인에 걸친 변경은 범위를 생략합니다.

## 개발·검증

Claude 원본은 `plugins/<이름>/`, Codex 전환본은 `plugins/<이름>-codex/`에서 관리합니다. 전환 기록은 `porting/<이름>/`에 둡니다. 원본을 갱신한 뒤 프로젝트의 `claude-to-codex` 스킬로 기존 전환본에 변경을 반영합니다.

```bash
# 마켓플레이스와 플러그인 매니페스트 검증 (저장소 루트에서)
claude plugin validate .

# 플러그인을 로컬에서 띄워 동작 확인
claude --plugin-dir plugins/<이름>

# 플러그인별 테스트
bash plugins/infra/tests/run_tests.sh
(cd plugins/superrelease && python3 -m unittest discover -s tests -q)
uv run --no-project --with pytest --with pyyaml --with pymupdf pytest plugins/llm-wiki/tests -q
```

Codex 전환본은 `.agents/plugins/marketplace.json`에만 등록합니다. `python3 porting/superdomain/check_repository.py`로 카탈로그·기준 상태를, `python3 porting/superdomain/check_git_scopes.py`로 리뷰의 Git 범위를 검사합니다. 공식 매니페스트 스키마·스킬 형식·내부 링크 검사는 `.github/workflows/superdomain-codex.yml`의 절차를 따릅니다. 설치 후 스킬 선택과 모델 실행은 별도로 확인합니다.

## 릴리즈 절차

Claude 플러그인마다 따로 릴리즈합니다. 버전은 [유의적 버전(SemVer)](https://semver.org/lang/ko/)을 따릅니다. 아래 `claude plugin tag` 절차는 Claude 원본에만 적용합니다. Codex 전환본은 원본 업무 버전을 유지하고 전환 이력·검증 결과를 `porting/<이름>/`에 남깁니다.

1. 작업 브랜치에서 그 플러그인의 `plugin.json` `version`을 올립니다. superrelease는 `plugins/superrelease/.superrelease/scripts/version.py set <version>`(또는 그 디렉터리에서 연 세션의 `release` 스킬)을 씁니다.
2. 그 플러그인의 `CHANGELOG.md`에 버전과 날짜로 변경 사항을 정리합니다.
3. `main`으로 PR을 보내 병합합니다.
4. `main`에서 플러그인 디렉터리로 이동해 태그를 답니다: `claude plugin tag --push` (태그 이름은 `<이름>--v<버전>`).
