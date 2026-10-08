# superkit

Claude Code 플러그인 여러 개를 한 저장소에서 관리하는 모노레포다. 저장소 루트가 마켓플레이스이고, 플러그인은 `plugins/<이름>/` 아래에 하나씩 있다. 플러그인마다 고유한 규칙은 그 디렉터리의 `AGENTS.md`나 README에 있다.

## 구조

- `.claude-plugin/marketplace.json` — 마켓플레이스 카탈로그. 플러그인 항목의 `source`는 `./plugins/<이름>` 상대 경로로 둔다. `version`은 여기에 적지 않는다(플러그인의 `plugin.json`이 유일한 출처).
- `plugins/superdomain/` — 도메인 정의·도메인/컨벤션 리뷰·ADR.
- `plugins/superglossary/` — 프로젝트 용어사전. 플러그인 지침은 [plugins/superglossary/AGENTS.md](plugins/superglossary/AGENTS.md).
- `plugins/infra/` — 인프라 하네스. 플러그인 지침은 [plugins/infra/AGENTS.md](plugins/infra/AGENTS.md).
- `plugins/superrelease/` — 프로젝트 전용 릴리스 툴킷 생성기. 플러그인 지침은 [plugins/superrelease/AGENTS.md](plugins/superrelease/AGENTS.md). 자기 자신을 릴리스하는 툴킷(`.superrelease/`, `.claude/skills/`)이 이 디렉터리 안에 있다.
- `plugins/llm-wiki/` — LLM 위키. 플러그인 지침은 [plugins/llm-wiki/AGENTS.md](plugins/llm-wiki/AGENTS.md).
- `.github/workflows/` — 플러그인마다 하나씩, 그 디렉터리가 바뀔 때만 도는 CI.

## 지켜야 할 것

- **지침 파일은 `AGENTS.md`만 쓴다.** 저장소 어디에도 `CLAUDE.md`·`CLAUDE.local.md`를 두지 않는다. 하나라도 생기면 Claude Code가 기본 설정에서 `AGENTS.md`를 읽지 않는다.
- **플러그인은 자기 디렉터리 밖을 참조하지 않는다.** 설치할 때 `plugins/<이름>/`만 캐시로 복사되므로 `../` 경로나 다른 플러그인의 파일은 설치본에서 보이지 않는다.
- **플러그인이 사용자 프로젝트의 지침 파일에 쓸 때**: 대상은 프로젝트 루트의 `AGENTS.md`다. 프로젝트에 `CLAUDE.md` 계열 파일이 있으면 Claude Code가 `AGENTS.md`를 읽지 않으므로 그 `CLAUDE.md`에 쓴다. 지침을 읽을 때는 `AGENTS.md`와 `CLAUDE.md`를 모두 본다.
- 플러그인 이름(`plugin.json`의 `name`)과 마켓플레이스 항목 이름은 같게 둔다. 이름은 설치 ID(`<이름>@superkit`)라 바꾸면 기존 설치가 깨진다. 바꿔야 하면 `marketplace.json`의 `renames`에 옛 이름을 남긴다.

## 브랜치·커밋

- `main` + 작업 브랜치(GitHub flow). `main`에서 `feat/…`·`fix/…`·`docs/…`·`chore/…` 브랜치를 따서 `main`으로 PR을 보낸다.
- 커밋 메시지는 Conventional Commits 형식에 한국어 설명을 쓴다. 범위에 플러그인 이름을 적는다. 예: `fix(superglossary): lint가 지침 파일 블록을 대조하지 않는다`.

## 버전·릴리즈

- 플러그인마다 SemVer를 따로 쓴다. `plugin.json`의 `version`을 올려야 사용자에게 업데이트가 간다. 한 플러그인의 변경이 다른 플러그인의 버전을 바꾸지 않는다.
- 릴리즈할 때 그 플러그인의 `CHANGELOG.md`를 정리하고, `main`에 병합한 뒤 플러그인 디렉터리에서 `claude plugin tag --push`로 `<이름>--v<버전>` 태그를 단다.
- superrelease는 자기 툴킷으로 릴리스할 수 있다 — `plugins/superrelease`에서 연 세션에서 `release` 스킬을 쓰면 버전·CHANGELOG·`superrelease--v<버전>` 태그를 함께 처리한다.

## 검증

저장소 루트에서:

```bash
claude plugin validate .
```

플러그인별 테스트:

```bash
bash plugins/infra/tests/run_tests.sh
```

```bash
cd plugins/superrelease && python3 -m unittest discover -s tests -q
```

```bash
uv run --no-project --with pytest --with pyyaml --with pymupdf pytest plugins/llm-wiki/tests -q
```

로컬에서 플러그인을 바로 써 보려면 `claude --plugin-dir plugins/<이름>`으로 띄우고, 고친 뒤 `/reload-plugins`로 반영한다.
