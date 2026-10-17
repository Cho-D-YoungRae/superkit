# clean-code

『Clean Code』(Robert C. Martin, 2008)의 원칙을 챕터별 레퍼런스로 담아 코드 작성·리팩터링·리뷰에 적용하게 하는 플러그인이다. 스킬 둘(apply·review), 리뷰어 에이전트 하나, 레퍼런스 md로 이루어진다. 저장소 공통 규칙(브랜치·커밋·버전·태그)은 루트 [AGENTS.md](../../AGENTS.md)를 따른다.

## 구조

- `.claude-plugin/plugin.json` — 매니페스트. `version`이 버전의 유일한 출처다.
- `skills/apply/SKILL.md` — 작업 → 챕터 파일 대응표와 적용 기준. 레퍼런스 파일을 더하거나 이름을 바꾸면 이 표도 고친다.
- `skills/review/SKILL.md` — 리뷰 대상을 정하고 리뷰어를 띄워 결과를 합친다. 판정은 하지 않는다.
- `agents/clean-code-reviewer.md` — 읽기 전용 리뷰어. 판정 기준과 출력 형식의 유일한 출처다. 모델은 이 파일에서만 정한다.
- `skills/apply/references/index.md` — 책 전체 목차, 챕터별 한 줄 요약, 파일 링크. 파일이 없는 챕터도 목차에 남긴다.
- `skills/apply/references/chapter_NN_<제목>.md` — 챕터별 요약.
- `scripts/verbatim_check.py` — 레퍼런스와 원서 텍스트의 연속 일치 구절 대조(유지보수용).
- `tests/test_references.py` — 구조 검사.

## 레퍼런스를 고칠 때

이 저장소는 공개되어 있고 원서는 저작권이 있는 책이다.

- 본문은 한국어로 다시 쓴 요약으로 둔다. 원서 문장을 옮기지 않는다. 인용은 큰따옴표와 `(p. N)`을 붙인 15단어 미만 구절만, 파일당 2개까지 쓴다.
- 챕터·절 제목, 원칙 이름, 휴리스틱 코드와 제목, 핵심 용어는 원서 영어 표기를 그대로 쓴다.
- 코드 예시는 원서 Listing이나 그 식별자를 옮기지 않고 다른 도메인으로 새로 쓴다. 언어는 Java, 한 예시는 20줄 안팎, Bad/Good은 같은 동작이어야 한다.
- 원서에 없는 내용은 `## 원서 밖 보충` 절에만 쓴다. 본문에 섞지 않는다.
- 챕터 파일 형식: `# Chapter N: <English> — <한국어>` → 원서 쪽 표기와 한 줄 요약 인용 블록 → `## 핵심` → 원칙 절(어떻게·왜·예시) → `## 체크리스트` → `## 관련` → (선택) `## 원서 밖 보충`. 테스트가 이 뼈대를 검사한다.
- 고친 뒤 원서 텍스트를 가진 사람은 `python3 -I scripts/verbatim_check.py <파일> <원서 텍스트>`로 대조한다. 원서 텍스트는 저장소에 넣지 않는다.

## 검증

플러그인 디렉터리에서:

```bash
python3 -m unittest discover -s tests -q
```

저장소 루트에서 `claude plugin validate .`, 로컬 로드는 `claude --plugin-dir plugins/clean-code`.
