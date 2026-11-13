# superglossary

프로젝트 용어사전 — 이름에 쓰는 단어를 md 표 하나로 관리하고, Claude가 같은 단어로 이름을 짓도록 돕는 [Claude Code](https://code.claude.com) 플러그인입니다. 개발자와 Claude가 **같은 용어집**을 보고 이름을 지어, 같은 개념을 매번 다르게 번역하는 일(청구 → claim / billing / charge)을 막습니다.

스크립트나 중간 형식 없이, Claude가 `docs/superglossary/glossary.md`를 직접 읽고 고칩니다.

## 핵심 개념

- **단어별 등록.** 합성어를 통째로 등록하지 않고 단어마다 한 행을 둡니다 — `체결수량`이 아니라 `체결`(execution) + `수량`(quantity) → `execution_quantity`. 이미 있는 단어는 조합해 씁니다.
- **나누는 기준은 영문.** 합성어의 영문이 부분 영문의 조합과 다르거나 전체 개념의 통용 약어가 있으면 한 항목으로 둘 수 있습니다. `매도호가` → `ask`, `투자자 관계` → 영문 `investorRelations`·축약 `ir`이 예입니다. 이런 예외는 근거와 함께 확인받습니다.
- **영문과 축약 구분.** 기본 영문과 허용된 줄임말을 각각 적습니다. 둘 다 사용할 수 있으며 특정 용도의 표기는 설명을 따릅니다. 새 약어를 영문 열에만 넣거나 모든 이름에 축약을 강제하지 않습니다.
- **문맥별 표준.** 같은 개념은 재사용하고, 표기가 같아도 뜻이 다르면 설명으로 구분합니다. 색인과 주가지수의 `index`는 각각 등록할 수 있습니다.
- **금지 단어.** 해당 항목의 의미·용도에서 금지된 표기를 둡니다. 토큰 발급의 `issue` 금지는 증권 발행의 `issue`에 적용하지 않습니다. 의미·적용 범위가 불명확하면 확인이 필요한 이유를 보고합니다.

## 설치

```bash
/plugin marketplace add Cho-D-YoungRae/superkit
/plugin install superglossary@superkit
```

superglossary는 superkit 마켓플레이스로 배포됩니다.

로컬 개발용으로는 superkit 저장소 루트에서 `claude --plugin-dir plugins/superglossary`로 띄우고, 고친 뒤 `/reload-plugins`로 반영합니다.

## 빠른 시작

```
1. /superglossary:glossary 용어집 만들어줘
   → docs/superglossary/glossary.md 생성(기본 용어: 식별자·이름·일시)
   → 코드가 이미 있으면 기존 이름에서 용어를 찾아볼지 묻습니다(glossary-scanner)
   → 지침 파일(AGENTS.md, CLAUDE.md가 있으면 그 파일)에 포인터 줄을 넣을지 묻습니다

2. (작업)  Claude가 이름을 짓기 전에 규칙·인덱스를 읽고 관련 용어를 검색합니다.
           없는 단어가 필요하면 그 자리에서 등록하고 한 줄로 알립니다 — "용어 등록: 체결 → execution"

3. /superglossary:check
   → 현재 사전으로 코드와 사전 변경의 기존 코드 영향을 검토합니다(파일은 고치지 않습니다)
   → 위반·추가 후보·확인 필요·미검토를 구분해 보고합니다
```

포인터 줄은 이렇게 들어갑니다. `@import`를 쓰지 않으므로 용어집은 매 세션이 아니라 이름을 지을 때만 읽힙니다.

```
- 용어 사전: docs/superglossary/glossary.md (이름을 짓기 전에 읽는다. 없는 단어는 /superglossary:glossary로 추가한다)
```

## 구성 요소

| 종류 | 이름 | 역할 |
|------|------|------|
| 스킬 | `/superglossary:glossary` | 용어집 생성·추가·수정·삭제·분리. 이름을 짓다 사전에 없는 단어가 필요하면 Claude가 스스로 씁니다 |
| 스킬 | `/superglossary:check` | 코드와 사전 변경의 기존 코드 영향을 현재 용어집으로 검토 |
| 서브에이전트 | `glossary-scanner` | 기존 코드에서 용어 후보와 혼용(영문 변형·빈도)을 찾음 (model: sonnet) |

## 용어집 파일

```markdown
| 한글 | 영문 | 축약 | 금지 | 설명 |
| --- | --- | --- | --- | --- |
| 식별자 | identifier | id |  | 데이터를 고유하게 식별하는 값. {엔티티}_id 형식 |
| 투자자 관계 | investorRelations | ir |  | URL 필드는 irUrl을 사용 |
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

Claude는 규칙·인덱스를 먼저 읽고 사전 전체에서 한글 의미·영문·축약·금지·활용형을 검색합니다. 일치한 행은 설명까지 읽으며, 부족하면 관련 구간으로 넓힙니다. 검색 결과가 없다는 이유만으로 미등록을 확정하지 않습니다. 별도 Markdown 파서나 색인은 만들지 않습니다. 형식과 규칙은 [glossary-guide.md](skills/glossary/glossary-guide.md)에 있습니다.

**팀 공유**: `docs/superglossary/`와 포인터 줄이 든 지침 파일을 git에 커밋하세요.

## 검사 기준

- 인자 없는 검사는 staged·unstaged·untracked 변경, 경로 인자는 해당 현재 코드, 커밋 범위는 그 diff와 종료 리비전 코드를 봅니다.
- **사전은 언제나 현재 작업 트리 기준**입니다. 현재 표준으로 옛 코드도 위반이 될 수 있으며, 명시적 사전 규칙은 기존 코드 관례보다 우선합니다.
- 사전의 표준·축약·금지·의미·용도가 바뀌면 관련 표기의 기존 사용을 현재 프로젝트 전체에서 찾습니다. 사전만 수정했어도 영향 검사를 합니다.
- 읽지 못한 범위는 미검토로 보고합니다. 요청 범위와 영향 검사를 마쳤을 때만 이상 없음을 알립니다.

구버전 JSON·CLI·약어 전용 영문 항목을 위한 호환 처리나 자동 마이그레이션은 제공하지 않습니다. 용어집은 현재 형식과 규칙으로 관리합니다.

## 출처

이 플러그인의 용어사전 개념은 강의 **[「김영한의 실전 데이터베이스 - 설계 1편, 현대적 데이터 모델링 완전 정복」](https://www.inflearn.com/course/김영한-실전-데이터베이스-설계1편/dashboard?cid=338886)** 의 '용어 사전' 파트를 참고했습니다.

## 라이선스

[MIT](LICENSE)
