# clean-code

『Clean Code: A Handbook of Agile Software Craftsmanship』(Robert C. Martin, Prentice Hall, 2008)의 원칙을 챕터별 레퍼런스로 정리해, Claude가 코드를 쓰고 리팩터링하고 리뷰할 때 판단 근거로 쓰게 하는 Claude Code 플러그인.

- 작업에 맞는 챕터만 골라 읽는다. 이름 짓기면 2장, 함수 분리면 3장, 리뷰면 17장의 냄새 목록부터 본다.
- 원칙마다 "어떻게 하라"와 "왜 그런가"를 함께 담았다. 코드 예시는 Java다.
- 프로젝트 지침, 린터 설정, 다른 컨벤션 스킬과 부딪치면 그쪽을 따른다.

스킬은 스크립트 없이 동작하므로 Claude Code 말고는 설치할 것이 없다.

## 설치

Claude Code 세션 안에서:

```
/plugin marketplace add Cho-D-YoungRae/superkit
/plugin install clean-code@superkit
```

터미널에서:

```bash
claude plugin marketplace add Cho-D-YoungRae/superkit
```

```bash
claude plugin install clean-code@superkit
```

## 스킬

| 스킬 | 언제 쓰나 |
|---|---|
| `/clean-code:apply` | 코드를 새로 쓰거나 리팩터링·리뷰할 때, 이름을 짓거나 바꿀 때. 관련 요청이면 이름을 부르지 않아도 걸린다 |

## 레퍼런스

[`skills/apply/references/index.md`](skills/apply/references/index.md)가 책 전체 목차와 챕터별 한 줄 요약을 담는다. 코드 작성에 쓰이는 챕터는 `chapter_NN_<제목>.md` 파일로 따로 있다.

| 구분 | 챕터 |
|---|---|
| 챕터 파일 있음 | 1~13장(13장 파일은 부록 A Concurrency II를 함께 담는다), 14·16장(사례 연구의 교훈과 변환 패턴만), 17장(냄새와 휴리스틱 전체) |
| index에만 있음 | 서문·들어가며·표지 설명, 15장(JUnit Internals), 부록 B(SerialDate 코드), 부록 C(휴리스틱 교차 참조), 에필로그, 찾아보기 |

챕터 파일은 모두 같은 형식이다: 핵심 → 원칙별 "어떻게·왜·예시" → 체크리스트 → 관련 휴리스틱과 챕터 → (있으면) 원서 밖 보충.

## 출처와 작성 원칙

레퍼런스는 원서를 대신하지 않는 요약 노트다. 원서의 저작권은 저자와 출판사에 있다.

- 챕터·절 제목, 원칙 이름, 휴리스틱 코드(`G5: Duplication` 등)와 핵심 용어는 뜻이 흐려지지 않도록 원서 영어 표기를 그대로 쓴다.
- 본문은 한국어로 다시 쓴 요약이다. 원서 문장을 옮겨 오지 않고, 인용은 쪽 번호를 단 짧은 구절로 한정한다.
- 코드 예시는 원서의 Listing을 옮기지 않고 같은 원칙을 보여 주도록 새로 작성했다.
- 원서(2008, Java 5/6 기준) 이후 달라진 관행은 각 파일의 `원서 밖 보충` 절에만 쓴다. 본문의 주장은 모두 원서에 근거가 있다.
