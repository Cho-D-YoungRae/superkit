# 기여 가이드

superglossary에 기여해 주셔서 감사합니다. 이 문서는 브랜치 전략, 커밋 규칙, 릴리즈 절차를 설명합니다.

## 브랜치 전략

`release` 브랜치 없는 경량 Git Flow를 사용합니다. 상시 브랜치는 두 개입니다.

| 브랜치 | 역할 | 갱신 방식 |
|---|---|---|
| `main` | 릴리즈(배포) 대상. 태그가 찍히는 finalized 버전 | `develop` → `main` PR 병합 |
| `develop` | 통합 개발 브랜치 | 작업 브랜치 PR 병합 |

작업 브랜치는 `develop`에서 분기합니다.

| 접두사 | 용도 | 분기 → 병합 |
|---|---|---|
| `feature/<설명>` | 기능 추가 | `develop` → `develop` |
| `fix/<설명>` | 버그 수정 | `develop` → `develop` |
| `hotfix/<설명>` | 운영 긴급 수정 | `main` → `main`, 이후 `develop` backmerge |

- 접두사는 풀워드(`feature/`, `fix/`, `hotfix/`), 설명은 kebab-case로 작성합니다. 예: `feature/glossary-lookup-skill`.
- 브랜치 접두사 `feature/`와 커밋 타입 `feat:`을 혼동하지 마세요.

## 커밋 메시지

[Conventional Commits](https://www.conventionalcommits.org/ko/)를 따릅니다.

```
<타입>(<범위>): <설명>
```

주요 타입: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`. 예: `feat: add glossary lookup skill`.

## 개발·검증

```bash
# 매니페스트 검증
claude plugin validate .

# 로컬 로드 후 동작 확인
claude --plugin-dir .

# 버전 일관성 점검
pnpm version:check
```

## 릴리즈 절차

릴리즈는 `develop`에서 준비합니다.

1. 버전 상향: `pnpm bump <version>` (예: `pnpm bump 0.2.0`)
2. `CHANGELOG.md`의 `[Unreleased]` 항목을 `[<version>] - <YYYY-MM-DD>`로 정리
3. `develop` → `main` PR 생성 및 병합
4. `main`에서 태그: `git tag v<version> && git push --tags`
5. 릴리즈 발행: `gh release create v<version>` (CHANGELOG 발췌를 릴리즈 노트로)

버전은 [유의적 버전(SemVer)](https://semver.org/lang/ko/)을 따릅니다.
