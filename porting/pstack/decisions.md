# pstack 옮기기 — 결정 기록

원본: [cursor/plugins의 pstack](https://github.com/cursor/plugins/tree/main/pstack) (Lauren Tan, MIT). 대상: `plugins/pstack/` — Claude Code·Codex 공용 플러그인.

## 2026-11-17: 처음 옮김 (upstream `e1cc031`, 0.15.43)

### 알게 된 것

- upstream이 이미 Claude Code를 지원한다. `pstack/`(Cursor 원본)에서 `scripts/generate-pstack-harness-trees.mjs`가 `harness/pstack/claude-code/`를 만들고, upstream의 Claude 마켓플레이스(`pstack@cursor-plugins`)가 그 폴더를 가리킨다. 생성기는 Cursor 이름을 쓰는 SKILL.md 22개의 H1 아래에 Claude Code 어댑터(`docs/harness/claude-code.md`)를 읽으라는 문장을 넣고, 어댑터 표가 그 이름을 모두 덮는지 검사한다.
- Codex 지원은 upstream에 없다.
- 스킬 58개 중 57개가 `disable-model-invocation: true`다(`setup-pstack`만 아니다). Codex 0.160.0은 이 frontmatter를 읽지 않아, 원본 그대로 설치하면 57개가 모두 모델의 스킬 목록에 실렸다.

### 결정

| 원본 | 대상 | 처리 | 근거 |
|---|---|---|---|
| `harness/pstack/claude-code/` 전체 | `plugins/pstack/` | copy | upstream이 검증해 낸 Claude Code 생성본을 그대로 쓴다. Cursor 원본에서 다시 생성하면 upstream 생성기의 변화를 따라가야 한다. |
| 루트 `plugin.json` | — | omit | 저장소 관례대로 버전을 `.claude-plugin/plugin.json` 한 곳에 둔다. Codex도 그 파일을 읽는다(0.160.0에서 0.15.43으로 설치됨). |
| `.claude-plugin/plugin.json` | 같은 경로 | adapt | `homepage`·`repository`만 superkit으로 바꾼다. 이름·버전·저자·설명은 원본 그대로. |
| SKILL.md의 Claude Code 어댑터 문장 | 같은 문장 + Codex 어댑터 문장 | adapt | 런타임 차이를 문구로 흡수하는 공용 폴더 방식(저장소 AGENTS.md). Claude Code 어댑터 문장은 그대로 둔다. |
| `disable-model-invocation: true` | `skills/<이름>/agents/openai.yaml`의 `policy.allow_implicit_invocation: false` | adapt | claude-to-codex 스킬의 전환표. Codex 내장 skill-creator 문서: 모델 컨텍스트에서 빠지고 `$스킬`로는 부를 수 있다. |
| `agents/poteto-agent.md`, `agents/comment-sicko.md` | 같은 경로 | copy | Claude Code는 에이전트로 등록한다. Codex는 등록하지 않으므로(0.160.0 관찰) Codex 어댑터가 역할 문서로 넘기라고 한다. 도구 제한은 Codex에서 지시문뿐이다. |
| — | `docs/harness/codex.md` | 새로 씀 | Claude Code 어댑터와 같은 절·같은 첫 칸으로 Cursor 이름을 Codex에 맞춘다. 테스트가 Claude 어댑터의 행을 빠짐없이 덮는지 검사한다. |
| — | `AGENTS.md` | 새로 씀 | 이 폴더가 생성물이라는 것과 갱신 방법. |
| `pstack/automations`, `pstack/assets` | — | omit | upstream 생성본도 빼는 Cursor 전용 파일이다. |

### Codex 어댑터의 근거

도구 이름을 고정 대응표로 만들지 말라는 [호환 판단표](../../.agents/skills/claude-to-codex/references/compatibility.md)를 따라, 관찰한 도구 이름은 "세션이 제공하면 쓴다"로 적고 대체 경로를 함께 둔다. 각 행의 출처:

- `spawn_agent`·`wait_agent`·`followup_task`, `fork_turns`, 전체 이력 fork는 `model`·`reasoning_effort`를 받지 않음, 동시 슬롯 4개(부모 포함), 모든 에이전트가 같은 디렉터리를 씀, `request_user_input`은 목록에 있을 때만: 격리 `CODEX_HOME`에서 `codex debug prompt-input`이 낸 개발자 지침(0.160.0).
- 플러그인 스킬 이름 `pstack:<이름>`, 설치 위치 `$CODEX_HOME/plugins/cache/<마켓플레이스>/<플러그인>/<버전>/`: 같은 방법으로 설치해 관찰. 나머지 57개를 숨기면 스킬 루트 표에는 마켓플레이스 캐시(`.../plugins/cache/superkit`)만 남고, 경로가 보이는 pstack 스킬은 `pstack:setup-pstack`(`r2/pstack/0.15.43/skills/setup-pstack/SKILL.md`)뿐이다. 그래서 어댑터는 `<pstack>`을 그 항목에서 찾게 한다.
- `allow_implicit_invocation`의 의미와 `$스킬` 호출: Codex에 내장된 skill-creator 스킬의 `references/openai_yaml.md`.
- 모델 목록과 effort 단계: `codex debug models`.
- 세션 기록 위치와 첫 줄의 `session_meta`·`payload.cwd`: 로컬 `~/.codex/sessions`의 파일 이름과 첫 줄의 키(값은 읽지 않음).
- `/create-skill` → `skill-creator`: Codex 내장 스킬 목록.
- `$pstack:<이름>`이라는 입력 표기는 위 두 사실(스킬 이름, `$스킬` 호출)에서 이끈 것이고 실제 입력으로 확인하지 않았다.

### 원본을 따라가는 방법

- `sync.py --upstream <체크아웃>`이 폴더 전체를 다시 쓰고 커밋·버전(`upstream.json`)과 원본 파일 해시(`upstream-manifest.json`)를 고정한다.
- CI는 네트워크 없이 `--verify`로 대조한다. 설치본에서 superkit이 더한 것을 걷어 낸 결과가 고정한 해시와 같고, 그것을 다시 변환하면 설치본과 바이트 단위로 같아야 한다. upstream 커밋이 사라져도 CI는 영향을 받지 않는다.
- 원본이 어댑터 문장을 바꾸거나, overlay·`openai.yaml`과 같은 경로를 내거나, Claude 어댑터에 행을 더하거나, 플러그인 밖이나 없는 파일로 링크하면 sync나 테스트가 실패한다.
- 버전은 upstream을 따른다. superkit 쪽만 바뀐 수정은 다음 upstream 동기화 때 함께 나간다.

### 사용자에게 보이는 차이

- Codex에서 여러 모델 패널(arena·interrogate)은 Codex 카탈로그의 모델로만 돈다. 기본값이 모두 Claude·Gemini라 `inherit-parent`가 되고, 패널은 모델 다양성을 잃는다. arena의 다른 공급사 심사는 건너뛴다.
- Codex에서 `poteto-agent`·`comment-sicko`의 제한, `readonly`, worktree 격리는 지시문이다. 강제되지 않는다.
- Claude Code 쪽 README·`docs/guide/01-setup.md`·`poteto-help`의 설치·업데이트 안내는 upstream 문장(`/plugin install pstack@cursor-plugins`) 그대로다. superkit 사용자는 `pstack@superkit`으로 설치한다(저장소 README). Codex 어댑터에는 `pstack@superkit` 설치 행을 넣었다.
- Codex는 `~/.claude/rules`처럼 규칙 폴더를 자동으로 읽지 않으므로 `setup-pstack`은 `$CODEX_HOME/pstack-models.md`에 쓰고, 어댑터가 매 세션 그 파일을 읽게 한다.
- upstream 마켓플레이스의 `pstack@cursor-plugins`와 함께 설치하면 Claude Code에서 같은 `/pstack:*` 이름과 같은 모델 설정 파일을 쓴다.

### 검증

- `python3 -m unittest discover -s porting/pstack/tests -q`: 12개 통과(변환 규칙 9개, 설치본 대조·어댑터 행 대조·어댑터 문장 3개).
- `sync.py --upstream <e1cc031 체크아웃> --check`: 최신.
- `claude plugin validate .`, `claude plugin validate plugins/pstack --strict`: 통과(아이콘 없음 경고만).
- `.github/workflows/marketplace.yml`의 검사를 로컬에서 돌려 통과.
- git 왕복: 임시 인덱스에 올린 뒤 `git checkout-index`로 꺼낸 사본에서도 테스트가 통과했다(줄 끝·실행 권한이 커밋에서 바뀌지 않는다. 저장소에 `.gitattributes`가 없다).
- Codex CLI 0.160.0, 격리 `CODEX_HOME`: `pstack@superkit` 0.15.43으로 설치. 모델 컨텍스트에 실리는 pstack 스킬은 `pstack:setup-pstack` 하나. 설치본에 Codex 어댑터, 어댑터 문장 22개, `openai.yaml` 57개, 실행 권한이 있다. `openai.yaml` 없이 설치했을 때는 57개가 실렸다.
- 하지 않은 것: 실제 Codex·Claude Code 세션에서 스킬을 돌려 본 시험(모델 호출과 인증이 필요하다), `$pstack:<이름>` 입력, GitHub의 실제 workflow 실행.
