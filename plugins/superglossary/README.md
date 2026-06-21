# superglossary

프로젝트 용어사전 — 프로젝트별 도메인 용어를 파일로 관리하고, Claude가 일관된 용어를 사용하도록 돕는 [Claude Code](https://code.claude.com) 플러그인입니다.

## 권장 워크플로우

```
1. 시작 전  — /superglossary:init 또는 glossary-check 스킬로 용어 정렬
2. 작업 중  — 검색 없이 작업하되, 사전에 없는 용어를 만나면 /superglossary:add 로 그것만 추가
3. 완료 후  — glossary-check 스킬로 전체 일관성 검사
4. (선택)   — 커밋/PR 전 자동 lint (아래 '자동 트리거' 참고)
```

## 구성 요소

| 종류 | 이름 | 역할 |
|------|------|------|
| 커맨드 | `/superglossary:init` | 프로젝트에 용어사전 초기화 |
| 커맨드 | `/superglossary:add` | 새 용어 추가 |
| 스킬 | `glossary-check` | 작업 결과물의 용어 일관성 검사 |
| 서브에이전트 | `check-analyzer` | 검사 결과 분석 |
| 서브에이전트 | `glossary-scanner` | 코드·문서에서 용어 스캔(model: sonnet) |
| CLI | `templates/glossary.mjs` | 의존성 0의 독립 CLI (서브커맨드: `init`/`build`/`add`/`update`/`remove`/`list`/`lookup`/`lint`) |

## 데이터 및 로딩

`/superglossary:init` 실행 시 사용자 프로젝트에 다음 파일들이 생성됩니다.

```
.claude/superglossary/
  glossary.json   — 용어 원본 데이터
  core.md         — Claude 상시 로드용 핵심 용어 요약
  terms.md        — 전체 용어 목록
  glossary.mjs    — 용어사전 관리 CLI (init/build/add/update/remove/list/lookup/lint, templates/glossary.mjs 복사본)
```

**상시 로드**: `.claude/CLAUDE.md`에 `@superglossary/core.md`를 추가하면 Claude가 세션마다 자동으로 용어를 참조합니다.

```markdown
<!-- .claude/CLAUDE.md 예시 -->
@superglossary/core.md
```

## 설치

### 배포판 설치 (권장)

```bash
/plugin marketplace add Cho-D-YoungRae/superglossary
/plugin install superglossary@superglossary
```

### 로컬 개발용 로드

```bash
claude --plugin-dir .
# 세션 중 변경 적용 시
/reload-plugins
```

## 자동 트리거 (선택)

기본 설정에는 포함되지 않습니다. 필요한 경우 아래 예시를 참고해 프로젝트에 맞게 추가하세요.

### pre-commit (경고 전용)

```bash
# .husky/pre-commit 예시 — exit code 무시, 경고만 출력
node .claude/superglossary/glossary.mjs lint || true
```

### CI에서 생성물 stale 검사

```yaml
# GitHub Actions 예시
- name: 용어사전 stale 검사
  run: |
    node .claude/superglossary/glossary.mjs build
    git diff --exit-code .claude/superglossary/
    # 위 명령이 실패하면 빌드 결과물이 커밋과 다른 것 (stale)
```

`git diff`가 비어야 정상입니다. 비어 있지 않으면 `glossary.mjs build`를 재실행한 뒤 커밋하세요.

## 기여

브랜치 전략·커밋 규칙·릴리즈 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 출처

이 플러그인의 용어사전 개념은 강의 **[「김영한의 실전 데이터베이스 - 설계 1편, 현대적 데이터 모델링 완전 정복」](https://www.inflearn.com/course/김영한-실전-데이터베이스-설계1편/dashboard?cid=338886)** 의 '용어 사전' 파트를 참고했습니다.

## 라이선스

[MIT](LICENSE)
