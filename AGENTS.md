# superkit

Claude Code 플러그인과 그 Codex 지원을 한 저장소에서 관리하는 모노레포다. 플러그인은 `plugins/<이름>/`에 둔다. Codex를 지원하는 플러그인(현재 llm-wiki·superdomain·superglossary·pstack)은 두 런타임이 같은 폴더를 함께 쓰는 공용 플러그인이다. 한 폴더로 두 런타임을 맞출 수 없을 때만 Codex 전환본을 `plugins/<이름>-codex/`에 따로 두며, 지금은 전환본이 없다. 폴더 접미사와 무관하게 두 플랫폼의 manifest 이름은 원본 이름을 유지한다. 플러그인마다 고유한 규칙은 그 디렉터리의 `AGENTS.md`나 README에 있다.

## 구조

- `.claude-plugin/marketplace.json` — 마켓플레이스 카탈로그. 플러그인 항목의 `source`는 `./plugins/<이름>` 상대 경로로 둔다. `version`은 여기에 적지 않는다(플러그인의 `plugin.json`이 유일한 출처).
- `.agents/plugins/marketplace.json` — Codex 전용 카탈로그. `source.path`는 저장소 루트 기준 상대 경로로, 공용 플러그인이면 `./plugins/<이름>`, 전환본이면 `./plugins/<이름>-codex`이다. 공용 플러그인은 같은 폴더를 두 카탈로그에 모두 등록한다. 전환본을 두면 원본은 Claude 카탈로그에만, 전환본은 Codex 카탈로그에만 등록한다. 두 카탈로그는 `marketplace` CI가 함께 검사한다.
- `plugins/superdomain/` — 도메인 정의·도메인/컨벤션 리뷰·ADR. Claude Code·Codex 공용 플러그인이다(0.10.0부터).
- `porting/<이름>/` — Codex 전환 기록. 설치 패키지에는 포함하지 않는다. superdomain·superglossary는 공용 폴더로 합치기 전의 기록(`decisions.md`·`review.md`)이 이력으로 남아 있다. `porting/pstack/`은 외부 플러그인을 옮겨 오는 도구(동기화 스크립트·고정한 원본·overlay·테스트)와 결정 기록이다. 전환본을 새로 두면 전환 결정·독립 리뷰·기준 상태와 검증 도구를 여기에 둔다.
- `plugins/superglossary/` — 프로젝트 용어사전. Claude Code·Codex 공용 플러그인이다(0.9.0부터). 플러그인 지침은 [plugins/superglossary/AGENTS.md](plugins/superglossary/AGENTS.md).
- `plugins/infra/` — 인프라 하네스. 플러그인 지침은 [plugins/infra/AGENTS.md](plugins/infra/AGENTS.md).
- `plugins/superrelease/` — 프로젝트 전용 릴리스 툴킷 생성기. 플러그인 지침은 [plugins/superrelease/AGENTS.md](plugins/superrelease/AGENTS.md). 자기 자신을 릴리스하는 툴킷(`.superrelease/`, `.claude/skills/`)이 이 디렉터리 안에 있다.
- `plugins/llm-wiki/` — LLM 위키. Claude Code·Codex 공용 플러그인이다. 플러그인 지침은 [plugins/llm-wiki/AGENTS.md](plugins/llm-wiki/AGENTS.md).
- `plugins/clean-code/` — 『Clean Code』 원칙 레퍼런스, 적용·리뷰 스킬과 리뷰어 에이전트. 플러그인 지침은 [plugins/clean-code/AGENTS.md](plugins/clean-code/AGENTS.md).
- `plugins/pstack/` — poteto(Lauren Tan)의 [pstack](https://github.com/cursor/plugins/tree/main/pstack)을 옮긴 Claude Code·Codex 공용 플러그인. upstream의 Claude Code 생성본에 Codex 어댑터를 얹어 `porting/pstack/sync.py`가 만든다 — 손으로 고치지 않는다. 플러그인 지침은 [plugins/pstack/AGENTS.md](plugins/pstack/AGENTS.md).
- `evals/<이름>/` — 설치 패키지 밖의 개발용 평가와 검사(현재 superglossary).
- `.agents/skills/claude-to-codex/` — Codex 전환본을 만들고 갱신하는 프로젝트 스킬. 공용 폴더로 충분한지 먼저 검토하는 기준도 여기에 있다.
- `.github/workflows/` — 플러그인마다 하나씩, 그 디렉터리가 바뀔 때만 도는 CI. `marketplace`는 모든 변경에서 두 카탈로그를 검사하고, `claude-to-codex`는 그 스킬의 테스트를 돌린다. 전환본을 두면 그 CI는 원본 디렉터리가 바뀔 때도 돌게 한다.

## 지켜야 할 것

- **지침 파일은 `AGENTS.md`만 쓴다.** 저장소 어디에도 `CLAUDE.md`·`CLAUDE.local.md`를 두지 않는다. 하나라도 생기면 Claude Code가 기본 설정에서 `AGENTS.md`를 읽지 않는다.
- **플러그인은 자기 디렉터리 밖을 참조하지 않는다.** 설치할 때 해당 패키지 디렉터리만 캐시로 복사되므로 패키지 밖으로 나가는 상대 경로나 다른 플러그인의 파일은 설치본에서 보이지 않는다.
- **플러그인이 사용자 프로젝트의 지침 파일에 쓸 때**: 대상은 프로젝트 루트의 `AGENTS.md`다. 프로젝트에 `CLAUDE.md` 계열 파일이 있으면 Claude Code가 `AGENTS.md`를 읽지 않으므로 그 `CLAUDE.md`에 쓴다. 지침을 읽을 때는 `AGENTS.md`와 `CLAUDE.md`를 모두 본다.
- 플러그인 이름(`plugin.json`의 `name`)과 마켓플레이스 항목 이름은 같게 둔다. 이름은 설치 ID(`<이름>@superkit`)라 바꾸면 기존 설치가 깨진다. 바꿔야 하면 `marketplace.json`의 `renames`에 옛 이름을 남긴다.
- **Codex를 새로 지원할 때는 공용 폴더를 먼저 검토한다.** 런타임 차이를 스킬 문구(자리표시자를 푸는 런타임 메모, Claude 전용 도구가 없을 때의 경로)로 흡수할 수 있으면 `-codex` 전환본을 만들지 않는다. Claude 에이전트(`agents/`)의 도구 제한과 모델은 공용 폴더에서도 Claude Code에서 그대로 강제되고, Codex에서는 어느 배치든 지시문뿐이므로 그 자체는 전환본을 둘 이유가 아니다. 전환본은 한 폴더에 두면 한쪽 런타임의 동작을 해칠 때(같은 경로에 런타임마다 다른 내용이 필요할 때 등) 만든다. 근거는 [llm-wiki ARCHITECTURE의 ADR-9](plugins/llm-wiki/ARCHITECTURE.md)와 [superdomain](porting/superdomain/decisions.md)·[superglossary](porting/superglossary/decisions.md) 전환 기록의 마지막 절에 있다.
- Codex 전환 시 원본·전환본·전환 기록을 함께 확인한다. 기존 전환본은 기록된 위치를 우선하며, 저장소의 기본 배치가 바뀌었다는 이유만으로 사용자 전환본을 자동 이동하지 않는다. 기존 전환본을 공용 폴더로 합치는 일도 사용자가 정할 때만 한다.

## 브랜치·커밋

- `main` + 작업 브랜치(GitHub flow). `main`에서 `feat/…`·`fix/…`·`docs/…`·`chore/…` 브랜치를 따서 `main`으로 PR을 보낸다.
- 커밋 메시지는 Conventional Commits 형식에 한국어 설명을 쓴다. 범위에 플러그인 이름을 적는다. 예: `fix(superglossary): lint가 지침 파일 블록을 대조하지 않는다`.

## 버전·릴리즈

- 플러그인마다 SemVer를 따로 쓴다. `plugin.json`의 `version`을 올려야 사용자에게 업데이트가 간다. 한 플러그인의 변경이 다른 플러그인의 버전을 바꾸지 않는다.
- 릴리즈할 때 그 플러그인의 `CHANGELOG.md`를 정리하고, `main`에 병합한 뒤 플러그인 디렉터리에서 `claude plugin tag --push`로 `<이름>--v<버전>` 태그를 단다.
- superrelease는 자기 툴킷으로 릴리스할 수 있다 — `plugins/superrelease`에서 연 세션에서 `release` 스킬을 쓰면 버전·CHANGELOG·`superrelease--v<버전>` 태그를 함께 처리한다.
- 공용 플러그인은 Codex도 `.claude-plugin/plugin.json`의 `version`을 읽으므로 버전이 한 곳에만 있다. 릴리즈 절차는 다른 Claude 플러그인과 같다.
- 위 태그 명령은 Claude 플러그인에 적용한다. Codex 전환본을 두면 원본 업무 버전을 따르고 전환 이력은 `porting/<이름>/`에 남긴다. Codex 전환본에 Claude 태그 명령을 실행하지 않는다.

## 검증

저장소 루트에서:

```bash
claude plugin validate .
```

두 마켓플레이스 카탈로그의 검사는 `.github/workflows/marketplace.yml`에 있고 모든 PR에서 돈다. Claude 카탈로그는 항목과 `plugins/*/.claude-plugin/plugin.json`을 대조한다. Codex 카탈로그는 이름·경로·정책을 보고, 공용 폴더 항목은 Claude 카탈로그에도 같은 폴더로 있고 `-codex` 전환본이 없을 때만 통과시킨다.

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

```bash
cd plugins/clean-code && python3 -m unittest discover -s tests -q
```

```bash
cd plugins/superdomain && python3 -m unittest discover -s tests -q
```

```bash
python3 -m unittest discover -s evals/superglossary/tests -q
```

```bash
python3 -m unittest discover -s porting/pstack/tests -q
```

superglossary의 Git 범위 검사는 check 스킬의 `rg` 예시를 실제로 실행하므로 ripgrep 실행 파일이 필요하다(없으면 로컬에서는 건너뛰고 CI에서는 실패한다).

```bash
python3 -m unittest discover -s .agents/skills/claude-to-codex/tests -q
```

로컬에서 플러그인을 바로 써 보려면 `claude --plugin-dir plugins/<이름>`으로 띄우고, 고친 뒤 `/reload-plugins`로 반영한다.
