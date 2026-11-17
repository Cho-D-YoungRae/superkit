# pstack (superkit 사본)

[cursor/plugins](https://github.com/cursor/plugins/tree/main/pstack)의 pstack(Lauren Tan, MIT)을 Claude Code·Codex가 함께 쓰는 공용 플러그인으로 옮긴 것이다. 이 폴더는 `porting/pstack/sync.py`가 만든다. **손으로 고치지 않는다** — CI의 `--verify`가 고정한 원본과 다르면 실패한다.

## 무엇에서 어떻게 만드나

- 원본은 upstream이 Claude Code용으로 생성해 둔 `harness/pstack/claude-code/`다. 고정한 커밋·버전은 `porting/pstack/upstream.json`, 파일별 해시는 `porting/pstack/upstream-manifest.json`에 있다.
- sync가 원본에 더하는 것은 이것뿐이다. 나머지 파일은 원본과 바이트 단위로 같고, Claude Code 어댑터(`docs/harness/claude-code.md`)도 그대로 둔다.
  1. 루트 `plugin.json`을 뺀다. 버전은 `.claude-plugin/plugin.json` 한 곳에 두고 Codex도 그 파일을 읽는다. 그 파일의 `homepage`·`repository`는 superkit을 가리킨다.
  2. Claude Code 어댑터 문장이 있는 SKILL.md마다 Codex 어댑터(`docs/harness/codex.md`) 문장을 덧붙인다.
  3. `disable-model-invocation: true`인 스킬마다 `agents/openai.yaml`(`allow_implicit_invocation: false`)을 둔다. Codex는 그 frontmatter를 읽지 않으므로, 없으면 사용자가 부를 때만 쓰는 스킬 57개가 모두 모델 컨텍스트에 실린다.
  4. `porting/pstack/overlay/`의 파일(이 문서와 `docs/harness/codex.md`)을 얹는다.
- superkit 쪽 내용을 바꾸려면 overlay나 `sync.py`를 고친 뒤 sync를 다시 돌린다.
- 원본이 어댑터 문장을 바꾸거나, overlay·`openai.yaml`과 같은 경로를 내기 시작하거나, Claude Code 어댑터에 행을 더하면 sync나 테스트가 실패한다. 그때 Codex 어댑터와 규칙을 함께 고친다.

## 원본 따라가기

```bash
git clone --filter=blob:none --sparse https://github.com/cursor/plugins.git <체크아웃>
git -C <체크아웃> sparse-checkout set harness/pstack
python3 porting/pstack/sync.py --upstream <체크아웃>
```

원하는 커밋을 체크아웃한 뒤 돌린다. sync는 그 HEAD를 고정하고 폴더 전체를 다시 쓴다.

## 버전

- `version`은 upstream을 그대로 따른다. 같은 버전이면 설치본이 갱신되지 않으므로, superkit 쪽만 바꾼 수정은 다음 upstream 동기화 때 함께 나간다.
- CHANGELOG는 두지 않는다. 내용 변경의 출처는 upstream 이력이고, superkit 쪽 결정은 `porting/pstack/decisions.md`에 남긴다.

## 검증

```bash
python3 -m unittest discover -s porting/pstack/tests -q
```

```bash
claude plugin validate .
```
