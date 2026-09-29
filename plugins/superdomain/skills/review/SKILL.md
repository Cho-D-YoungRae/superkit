---
name: review
description: 커밋·PR 전에 변경이 도메인 정의(docs/DOMAIN.md)와 코딩 컨벤션을 따르는지 검토할 때, 도메인이 너무 커지거나 경계가 흐려지지 않았는지 점검할 때 사용한다. "도메인 리뷰", "컨벤션 리뷰", "superdomain 리뷰" 같은 요청이 해당한다. 버그·보안 중심의 일반 코드 리뷰에는 쓰지 않는다.
argument-hint: "[domain|code] [경로 | 커밋 범위 | 전체]"
---

# 도메인·컨벤션 리뷰

변경을 두 관점에서 본다. 도메인 경계는 `superdomain:domain-reviewer`가, 코딩 컨벤션은 `superdomain:convention-reviewer`가 맡는다. 이 스킬은 대상을 정하고, 두 리뷰어를 동시에 띄우고, 결과를 한 리포트로 합친다.

**핵심 원칙:** 판정은 리뷰어가 한다. 이 스킬이 diff를 직접 읽고 판정하지 않는다. 코드는 사용자가 요청할 때만 고친다.

## 1. 대상 결정

작업 기준은 git 루트다(`git rev-parse --show-toplevel`). 인자(`$ARGUMENTS`)를 해석한다.

| 인자 | 모드 | 대상 |
|---|---|---|
| 없음 | 변경 검토 | 기준 브랜치와의 merge-base 이후의 모든 변경(커밋된 것 + 커밋하지 않은 것) |
| 커밋 범위(`A..B`) | 변경 검토 | 그 범위의 변경 |
| 경로 | 전체 점검 | 그 경로 아래 파일 |
| `전체` | 전체 점검 | 프로젝트 전체 |

기준 브랜치와 변경 목록은 이렇게 구한다.

```bash
git symbolic-ref --quiet --short refs/remotes/origin/HEAD   # 기준 브랜치 (예: origin/main)
git merge-base HEAD <기준 브랜치>                            # BASE
git diff --name-only <BASE>                                  # 추적 중인 파일의 변경 (커밋 + 작업 트리)
git ls-files --others --exclude-standard                     # 아직 추적하지 않는 새 파일
```

- `origin/HEAD`가 없으면 기준 브랜치를 추측하지 말고 사용자에게 묻는다.
- 변경 검토인데 변경이 없으면 알리고 끝낸다.

## 2. 관점 결정

- 인자에 `domain`이 있으면 도메인만, `code`가 있으면 컨벤션만, 없으면 둘 다 본다.
- `docs/DOMAIN.md`가 없으면 도메인 리뷰를 건너뛰고 `/superdomain:domain`을 안내한다.
- 대상에 `.kt`·`.java` 파일이 없으면 컨벤션 리뷰를 건너뛰고 그 사실을 알린다.
- 두 관점이 모두 건너뛰어지면 이유를 알리고 끝낸다.

## 3. 리뷰어 호출

두 리뷰어를 **한 메시지에서 동시에** Agent 도구로 호출한다. `model`은 지정하지 않는다(에이전트 파일에 정해져 있다). 세션 대화는 넘기지 않고 아래만 넘긴다.

`superdomain:domain-reviewer`:

```
모드: 변경 검토 | 전체 점검
프로젝트 루트: <절대 경로>
DOMAIN.md: <절대 경로>
기준 문서: ${CLAUDE_PLUGIN_ROOT}/skills/domain/domain-guide.md
대상: <변경을 보는 git 명령과 파일 목록, 또는 점검할 경로>
```

`superdomain:convention-reviewer`:

```
모드: 변경 검토 | 전체 점검
프로젝트 루트: <절대 경로>
DOMAIN.md: <절대 경로 | 없음>
기준 문서: ${CLAUDE_PLUGIN_ROOT}/skills/conventions/conventions.md
대상: <변경을 보는 git 명령과 .kt·.java 파일 목록, 또는 점검할 경로>
```

## 4. 합치기

- 심각도 순(Critical → Important → Minor)으로 모은다.
- 같은 위치의 같은 문제는 하나로 합치고 기준을 둘 다 적는다.
- 두 리뷰어의 판단이 충돌하면 둘 다 보여 준다.
- 위치나 기준이 없는 지적은 빼고, 뺐다는 사실을 적는다.

## 5. 보고와 후속

```markdown
## 리뷰 결과 — <대상 요약>
### Critical
### Important
### Minor
- [도메인|컨벤션] `경로:줄` 문제 — 기준 — 제안
### 질문
### 검토 범위
(건너뛴 관점과 그 이유를 포함한다)
```

- 코드 수정은 사용자가 요청할 때만 한다. 요청받으면 Critical부터 고친다.
- 리뷰어의 지적이 틀렸다고 보이면 근거와 함께 그렇게 말한다. 그대로 따르지 않는다.
- DOMAIN.md를 고쳐야 하면 `/superdomain:domain`을, 결정을 남겨야 하면 `/superdomain:adr`을 안내한다.

## 하지 않는 것

- 자동으로 코드를 고치지 않는다.
- 리뷰 결과를 파일로 저장하지 않는다.
- 리뷰어의 모델을 지정하거나 덮어쓰지 않는다.
