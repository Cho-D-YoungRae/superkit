# superglossary

프로젝트 용어사전 — 이름에 쓰는 단어를 md 표 하나로 관리하고, Claude가 같은 단어로 이름을 짓도록 돕는 [Claude Code](https://code.claude.com) 플러그인입니다. 개발자와 Claude가 **같은 용어집**을 보고 이름을 지어, 같은 개념을 매번 다르게 번역하는 일(청구 → claim / billing / charge)을 막습니다.

스크립트나 중간 형식 없이, Claude가 `docs/superglossary/glossary.md`를 직접 읽고 고칩니다.

## 핵심 개념

- **단어별 등록.** 합성어를 통째로 등록하지 않고 단어마다 한 행을 둡니다 — `체결수량`이 아니라 `체결`(execution) + `수량`(quantity) → `execution_quantity`. 이미 있는 단어는 조합해 씁니다.
- **나누는 기준은 영문.** 합성어의 영문이 부분 영문의 조합과 다르면 한 항목으로 둡니다 — `매도호가` → `ask`(업계 용어), `국제증권식별번호` → `isin`(표준 약어), `재시도` → `retry`(영문 한 단어). 이런 예외는 Claude가 근거를 들어 확인을 받고 등록합니다.
- **축약어 통제.** 축약어는 표에 등록된 것만 씁니다(`id`, `at` 등). 미등록 축약(`reg_dt`의 `reg`)은 위반입니다.
- **금지 단어.** 같은 개념에 쓰면 안 되는 영문 변형을 표준과 함께 둡니다(예: `member`의 금지 = `customer`, `user`). `check`가 이를 위반으로 보고합니다.

## 설치

```bash
/plugin marketplace add Cho-D-YoungRae/superkit
/plugin install superglossary@superkit
```

superglossary는 [superkit](../../README.md) 마켓플레이스로 배포됩니다. 0.5.0 이하를 `superglossary@superglossary`로 설치했다면 그 마켓플레이스를 지우고(`/plugin marketplace remove superglossary`) 위 명령으로 다시 설치하세요.

로컬 개발용으로는 superkit 저장소 루트에서 `claude --plugin-dir plugins/superglossary`로 띄우고, 고친 뒤 `/reload-plugins`로 반영합니다.

## 빠른 시작

```
1. /superglossary:glossary 용어집 만들어줘
   → docs/superglossary/glossary.md 생성(기본 용어: 식별자·이름·일시)
   → 코드가 이미 있으면 기존 이름에서 용어를 찾아볼지 묻습니다(glossary-scanner)
   → 지침 파일(AGENTS.md, CLAUDE.md가 있으면 그 파일)에 포인터 줄을 넣을지 묻습니다

2. (작업)  Claude가 이름을 짓기 전에 용어집을 읽습니다.
           없는 단어가 필요하면 그 자리에서 등록하고 한 줄로 알립니다 — "용어 등록: 체결 → execution"

3. /superglossary:check
   → 변경된 코드의 이름을 용어집과 대조해 위반·추가 후보를 표로 보고합니다(코드는 고치지 않습니다)
```

포인터 줄은 이렇게 들어갑니다. `@import`를 쓰지 않으므로 용어집은 매 세션이 아니라 이름을 지을 때만 읽힙니다.

```
- 용어 사전: docs/superglossary/glossary.md (이름을 짓기 전에 읽는다. 없는 단어는 /superglossary:glossary로 추가한다)
```

## 구성 요소

| 종류 | 이름 | 역할 |
|------|------|------|
| 스킬 | `/superglossary:glossary` | 용어집 생성·추가·수정·삭제·분리. 이름을 짓다 사전에 없는 단어가 필요하면 Claude가 스스로 씁니다 |
| 스킬 | `/superglossary:check` | 코드 변경이 용어집을 따르는지 검토해 보고 |
| 서브에이전트 | `glossary-scanner` | 기존 코드에서 용어 후보와 혼용(영문 변형·빈도)을 찾음 (model: sonnet) |

## 용어집 파일

```markdown
| 한글 | 영문 | 축약 | 금지 | 설명 |
| --- | --- | --- | --- | --- |
| 식별자 | identifier | id |  | 데이터를 고유하게 식별하는 값. {엔티티}_id 형식 |
| 회원 | member |  | customer, user | 서비스 가입자 |
```

행은 한글 가나다순입니다. 사람이 직접 고쳐도 됩니다.

용어가 **300개를 넘으면** Claude가 도메인별 분리를 제안합니다. 동의하면 이렇게 나눕니다.

```
docs/superglossary/
  glossary.md   ← 규칙 + 도메인 index(도메인·파일·코드 범위) + 공통 용어
  order.md      ← 주문 도메인 용어
  member.md     ← 회원 도메인 용어
```

Claude는 지금 다루는 파일 경로를 index의 코드 범위와 맞춰 필요한 도메인 파일만 읽습니다. 형식과 규칙의 전체 내용은 [glossary-guide.md](skills/glossary/glossary-guide.md)에 있습니다.

**팀 공유**: `docs/superglossary/`와 포인터 줄이 든 지침 파일을 git에 커밋하세요.

## 0.6.0에서 옮기기

0.7.0은 `.claude/superglossary/`(JSON·생성물·CLI)를 쓰지 않습니다. 옮기는 방법은 [CHANGELOG](CHANGELOG.md)의 0.7.0 항목을 보세요.

## 출처

이 플러그인의 용어사전 개념은 강의 **[「김영한의 실전 데이터베이스 - 설계 1편, 현대적 데이터 모델링 완전 정복」](https://www.inflearn.com/course/김영한-실전-데이터베이스-설계1편/dashboard?cid=338886)** 의 '용어 사전' 파트를 참고했습니다.

## 라이선스

[MIT](LICENSE)
