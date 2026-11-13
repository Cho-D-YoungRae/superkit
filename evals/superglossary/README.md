# superglossary 행동 평가

설치 패키지 밖의 개발용 fixture와 수동 판정 기준이다. Markdown 파서나 제품 런타임을 추가하지 않는다. `prepare.py`는 합성 데이터와 일회용 Git 이력만 만들며, 에이전트를 실행하거나 결과를 통과로 판정하지 않는다.

## 재현

저장소 루트에서 실행한다. 목적지는 아직 없는 `/tmp` 하위 경로여야 한다.

```bash
python3 evals/superglossary/prepare.py /tmp/superglossary-run
```

각 fixture의 `PROMPT.md`를 **새 컨텍스트**에서 실행한다. 검토 대상 패키지의 `skills/glossary/SKILL.md` 또는 `skills/check/SKILL.md`와 그 안의 guide를 실제로 읽고 적용하게 한다. fixture 밖의 사용자 프로젝트, 글로벌 설정, 네트워크를 읽지 않는다. `03-abbreviation`은 등록 완료 후 같은 fixture에서 `CHECK.md`도 실행한다. `06-truncated`는 복구할 수 없는 잘린 읽기 응답을 재생하는 별도 조건이며, 추가 파일/도구 접근 없이 최종 보고만 수행한다.

`EXPECTED.md`와 이전 실행 결과는 평가 에이전트에게 주지 않는다. 검토자는 실행이 끝난 뒤 도구 기록, 최종 응답, 실제 diff를 기대 행동과 대조한다. 예상 문자열이 skill 문서에 있는지만 검사해서 통과로 세지 않는다.

### Claude CLI

인증 가능한 별도 평가 환경에서 아래와 같이 실행하면 native plugin 로딩과 기계 판독 가능한 도구 기록을 함께 확인할 수 있다. `--bare`는 사용자 설정/메모리/자동 탐색을 배제하고 API key 기반 인증만 사용한다. 로그인하거나 키를 복사하는 작업은 이 suite가 하지 않는다. 패키지 경로는 평가할 **Claude 원본**의 절대 경로다.

```bash
task_package=/absolute/path/to/plugins/superglossary
task_fixture=/tmp/superglossary-run/02-scoped
task_output=$(mktemp -d /tmp/superglossary-output.XXXXXX)
cd "$task_fixture"
CLAUDE_CONFIG_DIR="$task_output/config" claude \
  --bare --setting-sources '' --strict-mcp-config \
  --mcp-config '{"mcpServers":{}}' --no-session-persistence \
  --plugin-dir "$task_package" --verbose --output-format stream-json \
  --permission-mode dontAsk \
  --allowedTools 'Read,Glob,Grep,Skill,Bash(git rev-parse *),Bash(git diff *),Bash(git status *),Bash(git ls-files *),Bash(git show *)' \
  -p < PROMPT.md > "$task_output/events.jsonl"
git diff > "$task_output/after.diff"
git status --short > "$task_output/status.txt"
```

`glossary` 등록 평가에서만 허용 도구에 `Edit,Write`를 더한다. `check`는 시작/종료 시 작업 파일의 SHA-256과 `git status --short`를 대조해 읽기 전용인지 확인한다. 이미 변경이 있는 04 fixture는 빈 diff가 아니라 **시작 상태와 동일함**이 기준이다. `06-truncated`는 tool replay 조건이므로 위 파일 접근 실행과 구분한다.

### 대체 하네스

native CLI 인증/실행이 불가능하면 대화 이력을 넘기지 않은 새 서브에이전트에게 패키지 경로, fixture 경로, 해당 `PROMPT.md`만 준다. 전용 `Read/Grep` 대신 shell `rg`와 범위 읽기를 사용하는 등 실제 도구 차이를 기록한다. 이 방식은 지침을 따른 판단을 검증하지만 Claude의 slash-command dispatch, frontmatter의 `allowed-tools` 강제, 설치 캐시 동작, 특정 모델의 성능은 증명하지 않는다. Codex 전환본에도 같은 방식으로 별도 실행할 수 있다.

평가 요청 템플릿:

```text
행동 평가를 수행하세요. 패키지: <패키지의 절대 경로>.
fixture: <fixture의 절대 경로>. PROMPT.md의 요청을 해당 skill과
연결된 guide를 읽고 실제로 실행하세요. 패키지를 수정하거나 개선하지 마세요.
fixture 외의 사용자 데이터, 네트워크, 글로벌 설정에 접근하지 마세요.
check는 읽기 전용입니다. 등록 요청은 fixture의 용어집만 수정할 수 있습니다.
실제 명령/읽기/검색 기록, 최종 응답, 실행 전후 diff와 읽지 못한 범위를 남기세요.
EXPECTED.md 및 이전 결과는 읽지 마세요.
```

## 기록과 범위

- 패키지 버전, 평가한 파일의 SHA-256, 날짜, 하네스/모델 식별 가능 범위, fixture ID를 기록한다.
- `PASS`: 기대한 의미 판정과 필요한 검색/읽기 근거가 실제로 관찰됨. `FAIL`: 반례 관찰. `NOT RUN`: 미실행. 하네스 실패는 동작 실패와 별도 기록한다.
- 읽기 효율은 답변 내용만으로 판정하지 않는다. 05의 실제 검색과 범위 읽기 기록을 검토한다. 검색 없음만으로 용어 미등록을 단정하면 실패다.
- 합성 이력 커밋은 `/tmp`의 평가 저장소 안에만 생긴다. 평가 대상 저장소에는 커밋하거나 플러그인을 설치하지 않는다.
- 결과는 `results/`에 남긴다. 단일 회차의 통과는 통계적 안정성이나 native runtime 호환성 전체를 보증하지 않는다.
