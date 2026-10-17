# Chapter 17: Smells and Heuristics — 냄새와 휴리스틱

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 17, pp. 285–315 · 교차 참조 Appendix C, pp. 409–410
> 한 줄 요약: 저자가 여러 프로그램을 리팩터링하며 고친 이유를 모은 냄새·휴리스틱 66개 목록으로, 리뷰·리팩터링 중에 `G5` 같은 코드로 찾아 쓴다.

## 핵심

- `G5` Duplication은 저자가 가장 중요하게 꼽는 규칙 중 하나다. 중복은 추상화를 놓친 자리이고, 저자는 (원서 시점까지) 지난 15년 사이 나온 디자인 패턴 대부분을 중복을 없애는 방법으로 본다.
- 함수는 한 가지만 하고, 본문은 이름보다 한 단계 아래 수준으로만 쓴다(`G30`, `G34`).
- The Principle of Least Surprise(놀람 최소화 원칙)가 여러 휴리스틱(`G2`, `G11`, `G17`)을 묶는다. 동작·이름·위치가 읽는 사람의 예상과 맞아야 한다.
- 죽은 코드·죽은 함수·주석 처리한 코드·잡동사니는 지운다. 소스 관리 시스템이 기억한다.
- 결정은 정확하게, 구조로 강제한다(`G26`, `G27`). 순서·경계·설정값처럼 숨기 쉬운 것은 코드 구조로 드러낸다(`G31`, `G33`, `G35`).
- 테스트는 깨질 수 있는 모든 것, 특히 경계 조건을 다루고, 빠르고, 명령 하나로 돌아야 한다.
- 저자는 이 목록이 완전할 수 없다고 인정한다. 규칙을 외운다고 깨끗한 코드가 나오지 않으며, 목록이 함축하는 가치 체계가 핵심이라고 맺는다.

## 목차

C = Comments, E = Environment, F = Functions, G = General, J = Java, N = Names, T = Tests.

목록은 위에서부터 읽어도 되고, 리팩터링·리뷰 중 코드로 찾아 써도 된다. 각 항목은 신호(무엇을 보면)·처방(어떻게)·이유(왜) 순이며, 다른 장과 이어지는 항목은 마지막 줄 끝의 '관련:'이 그 휴리스틱을 쓰거나 자세히 다룬 장을 가리킨다. 휴리스틱이 언급된 쪽은 Appendix C(pp. 409–410)에도 정리되어 있지만, 그 쪽 번호는 실제 쪽과 어긋나고 일부 항목은 본문 표시와 다르다. 그래서 관련 링크는 각 장 본문에 `[G9]`처럼 표시된 실제 위치를 기준으로 했고, 내용상 가까운 절도 함께 걸었다.

| 코드 | 제목 (English) | 한국어 한 구절 |
|---|---|---|
| C1 | Inappropriate Information | 이력·작성자 같은 메타데이터는 주석 말고 다른 시스템에 |
| C2 | Obsolete Comment | 낡은 주석은 바로 고치거나 지운다 |
| C3 | Redundant Comment | 코드가 이미 말하는 것을 되풀이하지 않는다 |
| C4 | Poorly Written Comment | 쓸 주석이면 간결하고 정확하게 |
| C5 | Commented-Out Code | 주석 처리한 코드는 지운다 |
| E1 | Build Requires More Than One Step | 빌드는 명령 하나로 |
| E2 | Tests Require More Than One Step | 전체 테스트도 명령 하나로 |
| F1 | Too Many Arguments | 인수는 적게, 셋을 넘기지 않는다 |
| F2 | Output Arguments | 출력 인수 대신 호출 대상 객체의 상태를 바꾼다 |
| F3 | Flag Arguments | 불리언 인수는 함수를 나누라는 신호 |
| F4 | Dead Function | 호출되지 않는 메서드는 지운다 |
| G1 | Multiple Languages in One Source File | 한 파일에 섞는 언어의 수와 분량을 줄인다 |
| G2 | Obvious Behavior Is Unimplemented | 이름에서 기대되는 동작은 구현한다 |
| G3 | Incorrect Behavior at the Boundaries | 경계 조건마다 테스트로 증명한다 |
| G4 | Overridden Safeties | 경고·실패 테스트 같은 안전장치를 끄지 않는다 |
| G5 | Duplication | 중복은 놓친 추상화, 찾아서 없앤다 |
| G6 | Code at Wrong Level of Abstraction | 상위·하위 개념을 다른 그릇에 완전히 나눈다 |
| G7 | Base Classes Depending on Their Derivatives | 기반 클래스는 파생 클래스를 모르게 |
| G8 | Too Much Information | 인터페이스는 작게, 나머지는 숨긴다 |
| G9 | Dead Code | 실행되지 않는 코드는 지운다 |
| G10 | Vertical Separation | 변수·함수는 쓰는 곳 가까이 정의한다 |
| G11 | Inconsistency | 비슷한 일은 같은 방식으로 |
| G12 | Clutter | 쓸모없는 생성자·변수·주석을 치운다 |
| G13 | Artificial Coupling | 무관한 것을 편의상 묶지 않는다 |
| G14 | Feature Envy | 남의 데이터를 주무르는 메서드는 그 클래스로 |
| G15 | Selector Arguments | 동작을 고르는 인수 대신 함수를 여럿으로 |
| G16 | Obscured Intent | 빽빽한 식·헝가리안·매직 넘버로 의도를 가리지 않는다 |
| G17 | Misplaced Responsibility | 코드는 읽는 사람이 찾을 곳에 둔다 |
| G18 | Inappropriate Static | 다형성이 필요할 수 있으면 static으로 두지 않는다 |
| G19 | Use Explanatory Variables | 계산 중간값에 이름을 붙인다 |
| G20 | Function Names Should Say What They Do | 호출만 보고 동작을 알 수 있게 |
| G21 | Understand the Algorithm | 테스트 통과에서 멈추지 말고 동작 원리를 안다 |
| G22 | Make Logical Dependencies Physical | 가정하지 말고 의존 대상에 명시적으로 묻는다 |
| G23 | Prefer Polymorphism to If/Else or Switch/Case | switch 전에 다형성을 먼저 고려한다 |
| G24 | Follow Standard Conventions | 업계 관행에 기반한 팀 표준을 모두 따른다 |
| G25 | Replace Magic Numbers with Named Constants | 뜻을 말하지 않는 리터럴은 이름 있는 상수로 |
| G26 | Be Precise | 결정은 근거와 예외 처리까지 정확하게 |
| G27 | Structure over Convention | 관례보다 구조로 설계 결정을 강제한다 |
| G28 | Encapsulate Conditionals | 조건식은 의도를 말하는 함수로 |
| G29 | Avoid Negative Conditionals | 조건은 가능하면 긍정형으로 |
| G30 | Functions Should Do One Thing | 함수는 한 가지만 |
| G31 | Hidden Temporal Couplings | 호출 순서를 인수 흐름으로 드러낸다 |
| G32 | Don't Be Arbitrary | 구조에 이유를 두고, 그 이유가 보이게 |
| G33 | Encapsulate Boundary Conditions | +1·-1 같은 경계 처리는 한 곳에 |
| G34 | Functions Should Descend Only One Level of Abstraction | 본문은 이름보다 한 단계 아래 수준만 |
| G35 | Keep Configurable Data at High Levels | 기본값·설정 상수는 상위 수준에 두고 내려보낸다 |
| G36 | Avoid Transitive Navigation | 협력자의 협력자를 따라가지 않는다 |
| J1 | Avoid Long Import Lists by Using Wildcards | 긴 import 목록 대신 와일드카드 (원서 입장) |
| J2 | Don't Inherit Constants | 상수를 쓰려고 인터페이스를 상속하지 않는다 |
| J3 | Constants versus Enums | `public static final int` 대신 enum |
| N1 | Choose Descriptive Names | 서술적인 이름을 고르고 자주 다시 본다 |
| N2 | Choose Names at the Appropriate Level of Abstraction | 구현이 아니라 추상화 수준에 맞는 이름 |
| N3 | Use Standard Nomenclature Where Possible | 패턴 이름·언어 관례·유비쿼터스 언어를 쓴다 |
| N4 | Unambiguous Names | 하는 일이 모호하지 않은 이름 |
| N5 | Use Long Names for Long Scopes | 범위가 길수록 이름도 길게 |
| N6 | Avoid Encodings | 타입·범위·서브시스템 접두어를 붙이지 않는다 |
| N7 | Names Should Describe Side-Effects | 부수 효과까지 이름에 드러낸다 |
| T1 | Insufficient Tests | 깨질 수 있는 모든 것을 테스트한다 |
| T2 | Use a Coverage Tool! | 커버리지 도구로 빈틈을 찾는다 |
| T3 | Don't Skip Trivial Tests | 사소한 테스트도 문서 가치가 있다 |
| T4 | An Ignored Test Is a Question about an Ambiguity | 모호한 요구사항은 무시한 테스트로 질문한다 |
| T5 | Test Boundary Conditions | 경계 조건을 특히 테스트한다 |
| T6 | Exhaustively Test Near Bugs | 버그가 나온 함수는 철저히 테스트한다 |
| T7 | Patterns of Failure Are Revealing | 실패 패턴에서 원인을 찾는다 |
| T8 | Test Coverage Patterns Can Be Revealing | 통과한 테스트가 실행한 코드에서 단서를 찾는다 |
| T9 | Tests Should Be Fast | 테스트는 빠르게 |

## Comments — 주석

자세한 논의는 [chapter_04_comments.md](chapter_04_comments.md)에 있다.

### C1: Inappropriate Information — 부적절한 정보
- **신호**: 주석에 변경 이력, 작성자, 최종 수정일, 이슈(SPR) 번호 같은 메타데이터가 있다.
- **처방**: 그런 정보는 소스 관리·이슈 추적 같은 기록 시스템에 맡긴다. 주석에는 코드와 설계에 관한 기술적 메모만 남긴다.
- **이유**: 변경 이력은 소스 파일을 지루한 옛 텍스트로 어지럽힌다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### C2: Obsolete Comment — 낡은 주석
- **신호**: 오래되어 코드와 무관하거나 틀린 주석, 설명하던 코드에서 떨어져 나와 떠도는 주석.
- **처방**: 낡게 될 주석은 애초에 쓰지 않는다. 발견하면 최대한 빨리 고치거나 지운다.
- **이유**: 주석은 빨리 낡고, 낡은 주석은 엉뚱한 곳을 가리키는 오해의 섬이 된다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### C3: Redundant Comment — 중복된 주석
- **신호**: `total += price; // total에 price를 더한다`처럼 코드를 되풀이하는 주석, 시그니처보다 더 말하지 않는(심지어 덜 말하는) Javadoc.
- **처방**: 지운다. 주석은 코드가 스스로 말하지 못하는 것만 말한다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### C4: Poorly Written Comment — 성의 없는 주석
- **신호**: 장황하고, 뻔한 말을 하고, 문법·문장부호가 엉성한 주석.
- **처방**: 쓸 가치가 있는 주석이면 잘 쓴다. 단어를 고르고, 문법을 지키고, 짧게 쓴다.

### C5: Commented-Out Code — 주석 처리한 코드
- **신호**: 주석으로 막아 둔 코드 덩어리. 누군가 쓸 거라 여겨 아무도 지우지 않는다.
- **처방**: 보는 즉시 지운다. 필요한 사람은 소스 관리 시스템에서 이전 버전을 꺼내면 된다.
- **이유**: 날마다 썩는다. 없어진 함수를 부르고, 이름이 바뀐 변수를 쓰고, 낡은 관례를 따르며 읽는 사람을 방해한다. 저자는 "Commented-out code is an abomination." (p. 287)이라고까지 쓴다.

## Environment — 환경

### E1: Build Requires More Than One Step — 여러 단계로 빌드해야 한다
- **신호**: 빌드하려고 조각을 따로따로 체크아웃하고, 알 수 없는 명령이나 상황 의존 스크립트를 돌리고, 흩어진 JAR·XML 같은 부속을 찾아다닌다.
- **처방**: 간단한 명령 하나로 체크아웃하고, 또 하나로 빌드할 수 있게 만든다.

### E2: Tests Require More Than One Step — 여러 단계로 테스트해야 한다
- **신호**: 단위 테스트 전체를 돌리는 방법이 명령 하나가 아니다.
- **처방**: IDE 버튼 하나, 최악이라도 셸 명령 하나로 모든 테스트를 돌리게 한다.
- **이유**: 전체 테스트 실행은 매우 근본적인 일이라 빠르고 쉽고 누구에게나 뻔해야 한다.

## Functions — 함수

자세한 논의는 [chapter_03_functions.md](chapter_03_functions.md)에 있다.

### F1: Too Many Arguments — 너무 많은 인수
- **신호**: 인수가 셋을 넘는다.
- **처방**: 인수는 0개가 가장 좋고 1, 2, 3개 순이다. 넷 이상은 매우 의심스러우므로 단호히 피한다. 관련: [ch03 Function Arguments](chapter_03_functions.md), [ch14](chapter_14_successive_refinement.md)(인수 둘을 하나로 줄이는 리팩터링)

### F2: Output Arguments — 출력 인수
- **신호**: 인수를 결과를 받아 오는 그릇으로 쓴다.
- **처방**: 상태를 바꿔야 한다면 인수 말고 호출 대상 객체의 상태를 바꾼다.
- **이유**: 읽는 사람은 인수를 입력으로 기대하므로 직관에 어긋난다. 관련: [ch03](chapter_03_functions.md)

### F3: Flag Arguments — 플래그 인수
- **신호**: 불리언 인수. 함수가 여러 일을 한다고 큰 소리로 밝히는 셈이다.
- **처방**: 없앤다. 참·거짓 경우를 각각의 함수로 나눈다(`G15`). 관련: [ch03 Flag Arguments](chapter_03_functions.md)

### F4: Dead Function — 죽은 함수
- **신호**: 아무 데서도 호출하지 않는 메서드.
- **처방**: 겁내지 말고 지운다. 소스 관리 시스템이 기억한다.
- **이유**: 죽은 코드를 남겨 두는 것은 낭비다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

## General — 일반

### G1: Multiple Languages in One Source File — 한 소스 파일에 여러 언어
- **신호**: Java 파일에 XML·HTML·YAML·JavaScript 조각이, JSP에 Java·태그 라이브러리·JavaScript가 섞여 있다.
- **처방**: 이상적으로는 한 파일에 언어 하나만 쓴다. 현실적으로 여럿을 쓸 수밖에 없으니, 덧붙는 언어의 가짓수와 분량을 줄이려 애쓴다.
- **이유**: 좋게 봐도 혼란스럽고, 나쁘게 보면 엉성하다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G2: Obvious Behavior Is Unimplemented — 당연한 동작을 구현하지 않음
- **신호**: 이름을 보면 당연히 기대할 동작이 빠졌다. 예: 결제 수단 이름을 enum으로 바꾸는 함수가 대소문자 차이나 흔한 약어를 처리하지 않는다.
- **처방**: The Principle of Least Surprise에 따라 다른 프로그래머가 합리적으로 기대할 동작을 구현한다.
- **이유**: 기대가 어긋나면 이름에 기댄 직관을 믿지 못하고 세부 코드를 읽어야 한다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G3: Incorrect Behavior at the Boundaries — 경계를 올바로 처리하지 않음
- **신호**: "될 것 같다"는 직관만 믿고 코너 케이스·경계 조건을 증명하지 않은 함수.
- **처방**: 직관에 기대지 않는다. 경계 조건을 모두 찾아 각각 테스트를 쓴다(`T5`).
- **이유**: 올바른 동작은 생각보다 복잡하고, 경계·예외 하나가 우아한 알고리즘을 무너뜨린다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G4: Overridden Safeties — 안전장치 무시
- **신호**: 컴파일러 경고를 끈다. 실패하는 테스트를 꺼 두고 나중에 고치겠다고 한다. `serialVersionUID`를 손으로 관리한다.
- **처방**: 안전장치를 끄지 않는다. 손으로 통제해야 할 때(`serialVersionUID`)도 늘 위험하다는 것을 안다.
- **이유**: 빌드는 통과해도 끝없는 디버깅을 부를 수 있다. 저자는 안전장치를 하나씩 끈 끝에 난 체르노빌 사고에 빗댄다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G5: Duplication — 중복
- **신호**: ① 복사·붙여넣기한 똑같은 코드 덩어리 ② 같은 조건을 검사하는 switch/case·if/else 사슬이 여러 모듈에 되풀이됨 ③ 코드 줄은 달라도 알고리즘이 비슷한 모듈.
- **처방**: ①은 단순한 메서드로, ②는 다형성으로, ③은 TEMPLATE METHOD나 STRATEGY 패턴으로 없앤다. 보이는 대로 찾아 없앤다.
- **이유**: 저자는 이를 "one of the most important rules in this book" (p. 289)이라 한다. 중복은 추상화할 기회를 놓친 자리다. 추상화로 묶으면 설계 언어의 어휘가 늘어 코딩이 빨라지고 오류가 준다. 지난 15년 사이 나온 디자인 패턴 대부분, Codd 정규형, OO, 구조적 프로그래밍도 결국 중복을 없애는 전략이다. 관련: [ch03 Don't Repeat Yourself](chapter_03_functions.md), [ch12 No Duplication](chapter_12_emergence.md), [ch09](chapter_09_unit_tests.md)(테스트 코드의 중복), [ch16](chapter_16_refactoring_serialdate.md)

### G6: Code at Wrong Level of Abstraction — 추상화 수준이 맞지 않는 코드
- **신호**: 기반 클래스(또는 상위 파일·모듈·컴포넌트)에 세부 구현에만 해당하는 상수·변수·유틸리티 함수가 있다. 일부 구현만 알 수 있는 개념이 일반 인터페이스에 있다. 예: 모든 `Inventory` 구현에 `remainingCapacityRatio()`를 요구하지만 용량 제한이 없는 창고는 답할 수 없다.
- **처방**: 하위 개념은 모두 파생 쪽에, 상위 개념은 모두 기반 쪽에 두고 분리를 완전하게 한다. 일부 구현만 아는 개념은 `BoundedInventory` 같은 파생 인터페이스로 내린다.
- **이유**: 잘못 놓인 추상화는 "항상 0을 반환" 같은 거짓 구현으로 얼버무릴 수 없다. 저자는 추상화 분리를 개발자가 하는 가장 어려운 일 중 하나로 본다. 관련: [ch06](chapter_06_objects_and_data_structures.md), [ch16](chapter_16_refactoring_serialdate.md)

### G7: Base Classes Depending on Their Derivatives — 파생 클래스에 의존하는 기반 클래스
- **신호**: 기반 클래스가 파생 클래스의 이름을 언급한다.
- **처방**: 일반적으로 기반 클래스는 파생 클래스를 전혀 모르게 한다. 예외: 파생 클래스 수가 엄격히 고정되어 기반 클래스가 그중 하나를 고르는 경우(유한 상태 기계 구현에 흔하다). 이때 둘은 강하게 결합되어 같은 jar로 함께 배포된다.
- **이유**: 기반과 파생을 다른 jar로 따로 배포할 수 있으면, 파생을 고쳐도 기반을 재배포하지 않아 변경 영향이 줄고 운영 중 유지보수가 쉬워진다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G8: Too Much Information — 과도한 정보
- **신호**: 간단한 일에도 여러 함수를 불러야 하는 넓고 깊은 인터페이스, 메서드·인스턴스 변수가 많은 클래스, 하위 클래스용 protected 변수·함수가 잔뜩 있다.
- **처방**: 인터페이스를 매우 작고 빡빡하게 유지한다. 데이터·유틸리티 함수·상수·임시 변수를 숨긴다. 클래스의 메서드, 함수가 아는 변수, 인스턴스 변수는 적을수록 좋다.
- **이유**: 의존할 함수가 적은 인터페이스는 결합도가 낮다. 관련: [ch10](chapter_10_classes.md), [ch16](chapter_16_refactoring_serialdate.md)

### G9: Dead Code — 죽은 코드
- **신호**: 일어날 수 없는 조건의 if 본문, 예외를 던지지 않는 try의 catch 블록, 호출되지 않는 유틸리티 메서드, 발생하지 않는 switch/case.
- **처방**: 발견하면 시스템에서 지운다.
- **이유**: 설계가 바뀔 때 죽은 코드는 같이 갱신되지 않는다. 컴파일은 되지만 새 관례를 따르지 않아 오래될수록 냄새가 심해진다. 관련: [ch15](index.md), [ch16](chapter_16_refactoring_serialdate.md)

### G10: Vertical Separation — 수직 분리
- **신호**: 지역 변수가 사용처보다 수백 줄 위에 선언되었다. private 함수가 첫 사용처에서 멀리 떨어져 있다.
- **처방**: 지역 변수는 처음 쓰기 직전에 선언해 수직 범위를 좁힌다. private 함수는 처음 쓰는 곳 바로 아래에 정의한다.
- **이유**: 첫 사용처에서 아래로 훑기만 하면 정의를 찾을 수 있다. 관련: [ch05 Vertical Distance](chapter_05_formatting.md), [ch16](chapter_16_refactoring_serialdate.md)

### G11: Inconsistency — 일관성 부족
- **신호**: 같은 타입의 객체를 함수마다 다른 변수 이름으로 받는다. 비슷한 요청을 처리하는 메서드 이름이 제각각이다.
- **처방**: 어떤 일을 한 방식으로 했다면 비슷한 일은 모두 같은 방식으로 한다. 관례는 신중히 고르고, 고른 뒤에는 계속 따른다. 예: `processRefundRequest`가 있으면 다른 요청도 `processCancelRequest`처럼 짓는다.
- **이유**: The Principle of Least Surprise에서 나온 규칙이다. 단순한 일관성만 꾸준히 지켜도 읽고 고치기가 훨씬 쉬워진다. 관련: [ch02 Pick One Word per Concept](chapter_02_meaningful_names.md), [ch15](index.md), [ch16](chapter_16_refactoring_serialdate.md)

### G12: Clutter — 잡동사니
- **신호**: 구현 없는 기본 생성자, 쓰지 않는 변수, 호출되지 않는 함수, 정보 없는 주석.
- **처방**: 모두 지우고 소스 파일을 깔끔하게 정돈한다.
- **이유**: 아무 의미 없는 인공물로 코드를 어지럽힐 뿐이다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G13: Artificial Coupling — 인위적 결합
- **신호**: 범용 enum이나 범용 static 함수가 특정 클래스 안에 선언되어, 그것을 쓰는 곳 모두가 그 특정 클래스를 알아야 한다.
- **처방**: 함수·상수·변수를 어디에 선언할지 시간을 들여 정한다. 당장 손닿는 곳에 던져 두고 내버려 두지 않는다.
- **이유**: 인위적 결합은 아무 목적 없이 두 모듈을 묶는다. 임시로 편하지만 부적절한 위치에 둔 결과다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G14: Feature Envy — 기능 욕심
- **신호**: 메서드가 다른 객체의 접근자·변경자로 그 객체의 데이터를 조작한다. 그 클래스 안에 있고 싶어 하는 셈이다(Martin Fowler의 냄새).
- **처방**: 다른 조건이 같다면 계산을 데이터를 가진 클래스로 옮긴다. 단, 보고서 형식처럼 데이터 클래스가 알면 안 되는 관심사라면 기능 욕심을 필요악으로 남긴다.
- **이유**: 기능 욕심은 한 클래스의 내부를 다른 클래스에 드러낸다. 반대로 형식을 데이터 클래스에 넣으면 SRP·OCP·CCP를 어기고 그 클래스가 형식 변경에 휘둘린다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

```java
// Bad: Printer가 Order의 데이터를 꺼내 할인 금액을 계산한다
class InvoicePrinter {
    String print(Order order) {
        long discount = order.getSubtotal() * order.getDiscountPercent() / 100;
        return String.format("합계: %,d원", order.getSubtotal() - discount);
    }
}

// Good: 계산은 데이터를 가진 Order로 옮긴다
class Order {
    private long subtotal;
    private int discountPercent;
    long discountedTotal() { return subtotal - subtotal * discountPercent / 100; }
}
class InvoicePrinter {
    // 출력 형식은 Order가 알 필요가 없으니 여기 남긴다
    String print(Order order) { return String.format("합계: %,d원", order.discountedTotal()); }
}
```

### G15: Selector Arguments — 선택자 인수
- **신호**: 호출 끝에 붙은 뜻 모를 `false`. 불리언뿐 아니라 enum·정수 등 함수 동작을 고르는 인수 전반.
- **처방**: 선택지마다 함수를 따로 만든다. 일반적으로 동작을 고르는 값을 넘기기보다 함수를 여러 개 두는 편이 낫다.
- **이유**: 뜻을 기억하기 어렵고, 여러 함수를 하나로 합쳐 놓는다. 큰 함수를 쪼개는 일을 피하는 게으른 방법이다. 관련: `F3`, [ch03 Flag Arguments](chapter_03_functions.md), [ch16](chapter_16_refactoring_serialdate.md)

### G16: Obscured Intent — 가려진 의도
- **신호**: 한 줄로 이어 붙인 긴 식, 헝가리안 표기법, 매직 넘버로 작고 빽빽하지만 꿰뚫어 보기 힘든 코드.
- **처방**: 시간을 들여 의도를 드러낸다. 이름(`N1`, `N6`), 설명 변수(`G19`), 상수(`G25`)를 쓴다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G17: Misplaced Responsibility — 잘못 놓인 책임
- **신호**: 코드가 작성자에게 편한 곳에 있지만 읽는 사람이 자연스럽게 찾을 곳에는 없다.
- **처방**: The Principle of Least Surprise에 따라 읽는 사람이 기대하는 곳에 둔다. 어디에 둘지는 관련 함수의 이름으로 판단한다. 예: 일일 매출 합계를 보고서 모듈의 `getDailySalesTotal()`과 주문 접수 모듈의 `saveOrder()` 중 어디서 계산할지 정할 때, 이름이 합계 계산을 암시하는 쪽은 앞쪽이므로 보고서 쪽에서 계산한다. 성능 때문에 접수 시점에 누적해야 한다면 접수 모듈에 `accumulateDailySales()`처럼 그 사실을 드러내는 이름의 함수를 둔다.
- **이유**: 코드를 어디에 둘지는 개발자가 내리는 가장 중요한 결정 중 하나다. 관련: `G22`, [ch16](chapter_16_refactoring_serialdate.md)

### G18: Inappropriate Static — 부적절한 static
- **신호**: 지금은 인수만으로 동작하지만, 나중에 여러 알고리즘(예: 회원 등급별 할인 계산)으로 갈라질 수 있는 함수가 static이다.
- **처방**: 신호의 예처럼 인수로 받은 객체의 데이터로 계산하는 함수는 그 데이터를 가진 클래스(예: 회원)의 non-static 메서드로 옮겨, 등급별 구현이 다형적으로 갈라질 수 있게 한다. 일반적으로 non-static 메서드를 택하고, 애매하면 non-static으로 만든다. static으로 두려면 다형적으로 동작할 가능성이 없는지 확인한다. `Math.max`처럼 소유 객체 없이 인수만 쓰고 다형성이 필요할 리 없는 함수는 static이 좋다.
- **이유**: static 함수는 다형성을 쓸 수 없다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G19: Use Explanatory Variables — 설명 변수를 써라
- **신호**: 의미를 짐작해야 하는 계산식·인덱스 접근이 한 줄에 몰려 있다.
- **처방**: 계산을 중간값으로 쪼개 의미 있는 이름의 변수에 담는다. Kent Beck이 소개한 기법이며, 저자는 설명 변수가 대개 많을수록 좋다고 본다.
- **이유**: 이름 붙은 중간값만으로 불투명한 모듈이 투명해진다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

```java
// Bad: 배열 칸이 무엇인지 읽는 사람이 추측해야 한다
String[] f = line.split(",");
if (f[2].equals("PAID")) ledger.post(f[0], Long.parseLong(f[1]));

// Good: 중간값에 이름을 붙이면 각 칸의 뜻이 드러난다
String[] fields = line.split(",");
String orderId = fields[0];
String status = fields[2];
if (status.equals("PAID")) {
    long amount = Long.parseLong(fields[1]);
    ledger.post(orderId, amount);
}
```

### G20: Function Names Should Say What They Do — 이름과 기능이 일치하는 함수
- **신호**: `reservation.extend(3)`만 봐서는 3일인지 3시간인지, 객체를 바꾸는지 새 객체를 돌려주는지 알 수 없다.
- **처방**: 객체를 바꾸면 `extendByDays(3)`, 바꾸지 않고 새 예약을 돌려주면 `withDaysAdded(3)`처럼 동작이 드러나게 짓는다. 구현이나 문서를 봐야 안다면 더 나은 이름을 찾거나, 좋은 이름을 붙일 수 있게 기능을 다시 나눈다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G21: Understand the Algorithm — 알고리즘을 이해하라
- **신호**: if 문과 플래그를 덧대 겨우 "돌아가게" 만든 코드. 떠올릴 수 있는 테스트만 통과한다.
- **처방**: 탐색하듯 이리저리 고쳐 보는 방식 자체는 괜찮고, 흔히 유일한 방법이기도 하다. 다만 끝났다고 하기 전에 함수가 어떻게 동작하는지 이해한다. 흔히 가장 좋은 방법은 동작이 뻔히 보일 만큼 깔끔하게 리팩터링하는 것이다.
- **이유**: 테스트 통과로는 부족하고, 해법이 옳다는 것을 알아야 한다. 저자는 알고리즘이 요구에 맞는지 확신하지 못하는 것은 흔한 일이지만, 자기 코드가 무엇을 하는지 모르는 것은 게으름이라고 구분한다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G22: Make Logical Dependencies Physical — 논리적 의존성은 물리적으로 드러내라
- **신호**: 의존하는 모듈이 의존 대상에 대한 가정을 품는다. 예: 주문 내보내기 모듈이 결제 대행 게이트웨이가 한 번에 받는 건수를 상수 100으로 박아 둔다.
- **처방**: 필요한 정보는 의존 대상에게 명시적으로 묻는다. 예: 게이트웨이에 `maxBatchSize()`를 두고 내보내기 모듈이 그것을 호출한다.
- **이유**: 그런 상수는 잘못 놓인 책임(`G17`)이고, 그 가정을 감당하지 못하는 구현이 들어오면 오류가 난다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### G23: Prefer Polymorphism to If/Else or Switch/Case — if/else·switch/case보다 다형성
- **신호**: 같은 종류의 선택을 하는 switch나 if/else 사슬이 여러 곳에 있다.
- **처방**: switch를 쓰기 전에 다형성을 먼저 고려한다. ONE SWITCH 규칙: 한 종류의 선택에는 switch를 하나만 두고, 그 case들은 시스템 나머지의 switch를 대신할 다형적 객체를 만든다.
- **이유**: 대부분은 상황에 맞아서가 아니라 가장 손쉬운 brute force 해법이라서 switch를 쓴다. Chapter 6에서 새 타입보다 새 함수가 더 자주 추가되는 곳에는 switch가 맞을 수 있다고 했지만, 그런 경우는 비교적 드물다. 그러니 모든 switch를 의심한다. 관련: [ch03 Switch Statements](chapter_03_functions.md)(예시), [ch06 Data/Object Anti-Symmetry](chapter_06_objects_and_data_structures.md), [ch14](chapter_14_successive_refinement.md), [ch16](chapter_16_refactoring_serialdate.md)

### G24: Follow Standard Conventions — 표준 표기법을 따르라
- **신호**: 인스턴스 변수 위치, 클래스·메서드·변수 이름 짓는 법, 중괄호 위치가 사람마다 다르다.
- **처방**: 업계 관행에 기반한 팀 코딩 표준을 정하고 모두 따른다. 표준을 설명하는 문서가 없어도 코드가 본보기가 되게 한다.
- **이유**: 중괄호를 어디 두는지는 조금도 중요하지 않다. 모두가 합의해 같은 곳에 두는 것이 중요하다. 관련: [ch05 Team Rules](chapter_05_formatting.md), [ch16](chapter_16_refactoring_serialdate.md)

### G25: Replace Magic Numbers with Named Constants — 매직 넘버는 이름 있는 상수로
- **신호**: 뜻을 설명하지 않는 날 숫자. 숫자뿐 아니라 스스로 의미를 말하지 못하는 모든 토큰이 해당한다(예: 테스트에 박힌 회원 ID·이름 문자열).
- **처방**: 잘 지은 상수 뒤로 숨긴다. 단, 아주 잘 알려졌고 주변 코드가 충분히 설명적이면 날 숫자가 나을 때도 있다(마일당 피트 5280, 하루 근무 8시간, 원 둘레 공식의 2). 8시간은 법이나 관례가 바뀔 수 있어 이견이 있을 수 있다고 저자도 인정한다. 반대로 π처럼 유명해도 오타를 알아채기 어렵고 3.14·3.14159처럼 제각각 쓰일 값은 정의된 상수(`Math.PI`)를 쓴다.
- **이유**: 날 값은 의도를 감춘다. 관련: [ch02 Use Searchable Names](chapter_02_meaningful_names.md), [ch16](chapter_16_refactoring_serialdate.md)

```java
// Bad
if (member.failedLoginCount() >= 5) member.lock();

// Good
private static final int MAX_LOGIN_ATTEMPTS = 5; // 클래스 필드

if (member.failedLoginCount() >= MAX_LOGIN_ATTEMPTS) member.lock(); // 메서드 안
```

### G26: Be Precise — 정확하라
- **신호**: 첫 조회 결과가 유일하다고 가정한다. 통화를 부동소수점으로 다룬다. 동시 갱신이 드물 거라며 잠금·트랜잭션을 생략한다. `List`면 충분한데 `ArrayList`로 선언한다(과잉 제약). 변수를 모두 기본 protected로 둔다(제약 부족).
- **처방**: 결정을 내릴 때는 이유와 예외 처리 방법을 알고 정확하게 내린다. null을 반환할 수 있는 함수를 부르면 null을 검사한다. 유일하다고 여기는 레코드를 조회하면 다른 레코드가 없는지 확인한다. 통화는 정수(더 낫게는 정수 기반 Money 클래스)로 다루고 반올림을 제대로 처리한다. 동시 갱신 가능성이 있으면 잠금을 구현한다.
- **이유**: 코드의 모호함과 부정확함은 의견 차이나 게으름에서 나온다. 어느 쪽이든 없앤다.

### G27: Structure over Convention — 관례보다 구조
- **신호**: 설계 결정을 이름 짓기 관례에만 맡긴다. 예: 이름을 잘 지은 enum으로 switch/case를 여기저기 쓴다.
- **처방**: 준수를 강제하는 구조를 쓴다. 추상 메서드를 가진 기반 클래스는 구체 클래스가 모든 추상 메서드를 구현하게 강제하지만, switch/case는 매번 같은 방식으로 구현하라고 강제하지 못한다.

### G28: Encapsulate Conditionals — 조건을 캡슐화하라
- **신호**: if나 while 안에 그대로 쓴 불리언 논리. 불리언 논리는 그 자체로도 어려운데 조건문 안에서 함께 읽어야 하면 더 어렵다.
- **처방**: 조건의 의도를 설명하는 함수로 뽑아낸다. 관련: [ch15](index.md)

```java
// Bad
if (order.isPaid() && !order.isShipped() && !order.isCanceled()) warehouse.enqueue(order);

// Good
if (isReadyToShip(order)) warehouse.enqueue(order);

private boolean isReadyToShip(Order order) {
    return order.isPaid() && !order.isShipped() && !order.isCanceled();
}
```

### G29: Avoid Negative Conditionals — 부정 조건은 피하라
- **처방**: 부정은 긍정보다 조금 더 이해하기 어렵다. 가능하면 조건을 긍정형으로 표현한다. 관련: [ch15](index.md)

```java
// Bad
if (!coupon.isNotExpired()) rejectCoupon(coupon);
// Good
if (coupon.isExpired()) rejectCoupon(coupon);
```

### G30: Functions Should Do One Thing — 함수는 한 가지만
- **신호**: 연속된 작업을 여러 구역으로 나눠 수행하는 함수. 예: 회원을 순회하고, 대상인지 검사하고, 알림까지 보내는 루프 하나.
- **처방**: 한 가지씩 하는 작은 함수로 나눈다(순회 → `notifyIfEligible` → 실제 발송). 관련: [ch03 Do One Thing](chapter_03_functions.md), [ch15](index.md)

### G31: Hidden Temporal Couplings — 숨겨진 시간적 결합
- **신호**: 정해진 순서로 불러야 하는 메서드들이 앞 단계의 결과를 인수로 받지 않고 나열되어, 순서를 바꿔 불러도 컴파일된다.
- **처방**: 시간적 결합은 필요할 때가 많지만 숨기지 않는다. 각 함수가 다음 함수에 필요한 결과를 돌려주게 해(bucket brigade) 순서를 어길 수 없게 만든다.
- **이유**: 저자는 함수가 복잡해진다는 반론을 인정하면서, 그 문법적 복잡성이 실제 시간적 복잡성을 드러낸다고 본다. 다른 private 메서드가 쓸 수 있는 인스턴스 변수는 그대로 두되 인수로 순서를 드러낸다. 관련: [ch15](index.md)

```java
// Bad: 순서가 필드에 숨어 있어 바꿔 불러도 컴파일되고 실행 중에야 실패한다
private Reservation reservation; // reserveStock()이 채우고 chargePayment()가 읽는다
private Payment payment;         // chargePayment()가 채우고 issueReceipt()가 읽는다

public void checkout(Cart cart) {
    reserveStock(cart);
    chargePayment(); // reservation이 비어 있으면 실행 중 실패
    issueReceipt();
}

// Good: 앞 단계의 결과가 다음 단계의 인수가 된다
public void checkout(Cart cart) {
    Reservation reservation = reserveStock(cart);
    Payment payment = chargePayment(reservation);
    issueReceipt(payment);
}
```

### G32: Don't Be Arbitrary — 자의적으로 짜지 마라
- **신호**: 이유 없이 정한 듯 보이는 구조. 예: 다른 클래스의 유틸리티도 아닌 public 클래스가 무관한 클래스 안에 중첩되어, 그것을 쓰는 클래스들이 바깥 클래스까지 알아야 한다.
- **처방**: 구조에 이유를 두고 그 이유가 구조에서 드러나게 한다. 다른 클래스의 유틸리티가 아닌 public 클래스는 패키지 최상위에 둔다.
- **이유**: 구조가 자의적으로 보이면 다른 사람이 마음대로 바꿔도 된다고 여긴다. 구조가 시스템 전체에 일관되게 나타나면 다른 사람도 그 구조를 따라 쓰고 관례를 지킨다. 관련: [ch15](index.md)

### G33: Encapsulate Boundary Conditions — 경계 조건을 캡슐화하라
- **신호**: `index + 1` 같은 +1·-1이 코드 여기저기 흩어져 반복된다.
- **처방**: 경계 조건 처리를 한곳에 모은다. 예: 두 번 나오는 `index + 1`을 `nextIndex` 변수에 담는다.
- **이유**: 경계 조건은 추적하기 어려우니 코드 곳곳으로 새어 나가지 않게 한다. 관련: [ch15](index.md)

### G34: Functions Should Descend Only One Level of Abstraction — 함수는 추상화 수준을 한 단계만 내려가야 한다
- **신호**: 한 함수에 개념(예: 할인율을 표시한다)과 그 표현의 세부 문법(예: 퍼센트 문자열을 손으로 조립)이 섞여 있다.
- **처방**: 함수 안 문장은 모두 같은 추상화 수준, 즉 함수 이름이 말하는 작업보다 한 단계 낮은 수준으로 쓴다. 세부 문법은 별도 모듈이나 함수에 맡긴다.
- **이유**: 생각은 단순하지만 사람은 수준을 매끄럽게 섞는 데 너무 능숙해서 가장 따르기 어려운 휴리스틱일 수 있다. 수준을 나누면 숨은 오류가 드러나기도 하고, 한 번 나누면 이전 구조에 가려 있던 새 경계가 보이므로 거듭 나눈다. 저자는 이를 리팩터링의 가장 중요하고 어려운 일 중 하나로 꼽는다. 관련: [ch03 One Level of Abstraction per Function](chapter_03_functions.md), [ch06](chapter_06_objects_and_data_structures.md)

### G35: Keep Configurable Data at High Levels — 설정 정보는 상위 수준에
- **신호**: 상위 수준에서 알고 기대하는 기본값·설정 상수가 저수준 함수에 묻혀 있다. 예: 깊은 곳의 `if (pageSize == 0) pageSize = 20; // 기본값`.
- **처방**: 그런 상수는 상위 수준(예: 명령행 인수를 파싱하는 곳)에 모으고, 저수준 함수에는 인수로 넘긴다.
- **이유**: 상위에 있으면 찾기 쉽고 바꾸기 쉽다. 저수준은 그 값의 주인이 아니다. 관련: [ch05](chapter_05_formatting.md)

### G36: Avoid Transitive Navigation — 추이적 탐색을 피하라
- **신호**: `order.getCustomer().getAddress().getZipCode()`처럼 협력자의 협력자를 따라간다.
- **처방**: 모듈은 직접 협력자만 알게 한다. 이를 디미터 법칙(Law of Demeter) 또는 Writing Shy Code라고 한다. 필요한 서비스는 직접 협력자가 제공하게 해, 한 번의 요청(`order.shippingZipCode()`)으로 끝나게 한다.
- **이유**: 많은 모듈이 `a.getB().getC()`를 쓰면 B와 C 사이에 Q를 끼우려 할 때 모든 호출을 고쳐야 한다. 모듈이 시스템 구조를 너무 많이 알면 아키텍처가 경직된다. 관련: [ch06 The Law of Demeter](chapter_06_objects_and_data_structures.md)

## Java — 자바

원서는 enum을 Java 5에 새로 생긴 기능으로 소개하는 시점에 쓰였다(J3, p. 308). 오늘날 관행과 다른 부분은 [원서 밖 보충](#원서-밖-보충)에 적었다.

### J1: Avoid Long Import Lists by Using Wildcards — 와일드카드로 긴 import 목록을 피하라
- **원서 입장**: 한 패키지에서 클래스를 둘 이상 쓰면 `import package.*;`로 패키지 전체를 가져온다. 80줄짜리 import 목록은 읽는 사람을 질리게 하고, import는 어떤 패키지와 협력하는지 간결하게 밝히면 된다.
- **이유**: 특정 클래스 import는 그 클래스가 반드시 있어야 하는 강한 의존이지만, 와일드카드는 이름 검색 경로에 패키지를 더할 뿐이라 결합을 낮춘다고 본다.
- **단서**: 레거시 코드에서 목·스텁을 만들 클래스를 찾을 때는 구체 import 목록이 쓸모 있지만 드물고, IDE가 명령 하나로 구체 목록으로 바꿔 준다. 같은 이름의 클래스가 다른 패키지에 있으면 구체 import나 정규화한 이름이 필요해 번거롭지만, 드물어서 여전히 와일드카드가 낫다고 한다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### J2: Don't Inherit Constants — 상수를 상속하지 마라
- **신호**: 인터페이스에 상수를 넣고, 그 인터페이스를 구현해 상수를 쓴다. 상수가 상속 계층 꼭대기에 숨어 어디서 왔는지 찾기 어렵다.
- **처방**: 상속으로 언어의 범위 규칙을 속이지 않는다. 대신 static import를 쓴다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### J3: Constants versus Enums — 상수 대 enum
- **신호**: Java 5에 enum이 생겼는데도 `public static final int`로 종류를 표현한다.
- **처방**: enum을 쓴다. enum은 메서드와 필드를 가질 수 있으므로 상수별 동작(예: 회원 등급별 적립률)을 enum 안에 둔다.
- **이유**: int는 의미를 잃기 쉽지만, enum은 이름 있는 열거형에 속하므로 의미를 잃지 않는다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

## Names — 이름

자세한 논의는 [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md)에 있다.

### N1: Choose Descriptive Names — 서술적인 이름
- **신호**: `d`, `tmp`, `lst` 같은 이름과 매직 넘버가 뒤섞여 무엇을 하는지 알 수 없는 코드.
- **처방**: 이름을 서둘러 정하지 않는다. 서술적인지 확인하고, 소프트웨어가 진화하며 의미가 흘러가므로 자주 다시 평가한다.
- **이유**: 저자는 이름이 가독성의 90%를 좌우한다고 본다. 잘 지은 이름은 코드 구조에 설명을 입혀 나머지 함수가 무엇을 할지 예상하게 하고, 실제 구현을 읽으면 예상대로라고 느끼게 한다. 관련: [ch15](index.md), [ch16](chapter_16_refactoring_serialdate.md)

### N2: Choose Names at the Appropriate Level of Abstraction — 적절한 추상화 수준의 이름
- **신호**: 구현을 드러내는 이름. 예: 알림 인터페이스의 `sendSms(phoneNumber)`는 이메일·푸시로 보내는 구현에는 맞지 않는다.
- **처방**: 클래스·함수의 추상화 수준을 반영하는 이름을 고른다(`send(recipientAddress)`). 코드를 다시 볼 때마다 너무 낮은 수준의 이름을 찾아 바꾼다.
- **이유**: 사람은 추상화 수준을 섞는 데 능숙해서 어렵다. 읽기 좋은 코드는 끊임없는 개선으로 얻는다. 관련: [ch16](chapter_16_refactoring_serialdate.md)

### N3: Use Standard Nomenclature Where Possible — 가능하면 표준 명명법을
- **처방**: 기존 관례를 따른다. DECORATOR 패턴이면 꾸미는 클래스 이름에 Decorator를 넣고, 문자열 변환은 Java 관례대로 `toString`이라 한다. 직접 지어내지 않는다. 팀이 프로젝트용으로 만든 이름 체계(Eric Evans의 ubiquitous language)도 표준이니 코드에서 그 용어를 적극적으로 쓴다.
- **이유**: 프로젝트에 맞는 특별한 의미를 담은 이름일수록 읽는 사람이 코드가 무엇을 말하는지 알기 쉽다. 관련: [ch02](chapter_02_meaningful_names.md), [ch16](chapter_16_refactoring_serialdate.md)

### N4: Unambiguous Names — 모호하지 않은 이름
- **신호**: 하는 일을 넓고 막연하게만 말하는 이름. 예: `doCancel()` 안에 `cancelOrder()`가 있으면 이름만으로 둘의 차이를 알 수 없다.
- **처방**: 함수·변수가 하는 일을 모호하지 않게 드러낸다(`cancelOrderAndOptionallyRefund`). 길어져도 한 곳에서만 호출된다면 설명력이 길이보다 값지다. 관련: [ch15](index.md), [ch16](chapter_16_refactoring_serialdate.md)

### N5: Use Long Names for Long Scopes — 긴 범위에는 긴 이름
- **처방**: 이름 길이를 범위 길이에 맞춘다. 5줄 남짓한 범위의 `i`, `j`는 괜찮고 오히려 긴 이름이 흐리게 만든다. 범위가 길수록 길고 정확한 이름을 쓴다.
- **이유**: 짧은 이름은 먼 거리에서 의미를 잃는다. 관련: [ch02 Use Searchable Names](chapter_02_meaningful_names.md), [ch14](chapter_14_successive_refinement.md)

### N6: Avoid Encodings — 인코딩을 피하라
- **처방**: 이름에 타입·범위 정보를 넣지 않는다. `m_`, `f` 같은 접두어도, 프로젝트·서브시스템 약어 접두어(예: 결제 모듈의 `pay_`)도 쓰지 않는다.
- **이유**: 요즘 개발 환경은 이름을 망가뜨리지 않아도 그 정보를 다 보여 주므로 쓸모없고 방해만 된다. 관련: [ch02 Avoid Encodings](chapter_02_meaningful_names.md), [ch15](index.md)

### N7: Names Should Describe Side-Effects — 부수 효과를 이름에 드러내라
- **신호**: 단순한 동사 이름인데 그 이상을 한다. 예: `getCart()`가 장바구니가 없으면 새로 만든다.
- **처방**: 함수·변수·클래스가 무엇이고 무엇을 하는지 이름에 모두 담는다(`findOrCreateCart()`). 이름으로 부수 효과를 숨기지 않는다. 관련: [ch03 Have No Side Effects](chapter_03_functions.md), [ch15](index.md)

## Tests — 테스트

테스트 코드 자체를 깨끗하게 쓰는 법(F.I.R.S.T., 테스트 코드의 중복)은 [chapter_09_unit_tests.md](chapter_09_unit_tests.md)에서 다룬다. T1–T8(T4 제외)을 실제로 적용한 사례는 [ch16](chapter_16_refactoring_serialdate.md)에 있다.

### T1: Insufficient Tests — 불충분한 테스트
- **신호**: 테스트 개수의 기준이 "이 정도면 충분해 보인다"이다.
- **처방**: 깨질 수 있는 것은 모두 테스트한다. 탐색하지 않은 조건이나 검증하지 않은 계산이 남아 있으면 불충분하다.

### T2: Use a Coverage Tool! — 커버리지 도구를 써라!
- **처방**: 커버리지 도구로 테스트가 부족한 모듈·클래스·함수를 찾는다. IDE의 초록·빨강 표시로 검증되지 않은 if·catch 본문을 빠르게 찾는다.

### T3: Don't Skip Trivial Tests — 사소한 테스트를 건너뛰지 마라
- **처방**: 사소한 테스트도 쓴다. 쓰기 쉽고, 문서로서의 가치가 작성 비용보다 크다.

### T4: An Ignored Test Is a Question about an Ambiguity — 무시한 테스트는 모호함에 대한 질문
- **처방**: 요구사항이 불분명해 동작 세부를 확신할 수 없으면, 그 질문을 주석 처리한 테스트나 `@Ignore`를 붙인 테스트로 남긴다. 둘 중 무엇을 쓸지는 모호한 부분이 컴파일되는 코드인지에 달렸다.

### T5: Test Boundary Conditions — 경계 조건을 테스트하라
- **처방**: 경계 조건을 특히 신경 써서 테스트한다(`G3`).
- **이유**: 알고리즘의 중간은 맞히고 경계에서 판단을 그르치는 일이 흔하다.

### T6: Exhaustively Test Near Bugs — 버그 주변은 철저히 테스트하라
- **처방**: 함수에서 버그를 찾으면 그 함수를 철저히 테스트한다.
- **이유**: 버그는 몰려 다닌다. 하나만 있지 않을 가능성이 크다.

### T7: Patterns of Failure Are Revealing — 실패 패턴이 원인을 드러낸다
- **처방**: 테스트 케이스를 빠짐없이 만들고 합리적인 순서로 정렬한다. "다섯 글자를 넘는 입력은 모두 실패", "두 번째 인수가 음수면 실패" 같은 패턴이 보이면 진단의 실마리가 된다.

### T8: Test Coverage Patterns Can Be Revealing — 커버리지 패턴이 원인을 드러낸다
- **처방**: 통과하는 테스트가 실행하는 코드와 실행하지 않는 코드를 보면 실패하는 테스트가 왜 실패하는지 단서를 얻는다.

### T9: Tests Should Be Fast — 테스트는 빨라야 한다
- **처방**: 무슨 수를 써서라도 테스트를 빠르게 유지한다.
- **이유**: 느린 테스트는 돌리지 않게 되고, 일정이 빠듯하면 가장 먼저 빠진다. 관련: [ch09 F.I.R.S.T.](chapter_09_unit_tests.md)

## 체크리스트

- [ ] 같은 코드, 같은 조건 분기, 비슷한 알고리즘이 되풀이되지 않는가(`G5`)?
- [ ] 인수가 셋을 넘지 않고, 셋이라면 그럴 만한 이유가 있는가(`F1`)?
- [ ] 불리언·선택자 인수나 출력 인수를 쓰지 않았는가(`F2`, `F3`, `G15`)?
- [ ] 호출만 보고 함수가 하는 일과 부수 효과를 알 수 있는가(`G20`, `N4`, `N7`)?
- [ ] 뜻을 말하지 않는 숫자·문자열 리터럴에 이름을 붙였는가(`G25`)?
- [ ] 조건식을 의도를 말하는 함수로 감쌌는가(`G28`)?
- [ ] 긍정형으로 쓸 수 있는 부정 조건(특히 `!isNotX()` 같은 이중 부정)을 그대로 두지 않았는가(`G29`)?
- [ ] null일 수 있는 반환값, 유일하다고 가정한 조회 결과, 금액 계산(부동소수점 금지)을 정확하게 다뤘는가(`G26`)?
- [ ] 함수가 한 가지 일만, 이름보다 한 단계 아래 추상화 수준에서 하는가(`G30`, `G34`)?
- [ ] 메서드가 남의 데이터를 주무르거나 협력자의 협력자를 따라가지 않는가(`G14`, `G36`)?
- [ ] 코드·상수·설정값이 읽는 사람이 찾을 위치에 있는가(`G13`, `G17`, `G35`)?
- [ ] 순서가 중요한 호출은 인수 흐름으로 순서를 강제하는가(`G31`)?
- [ ] static으로 둔 함수가 나중에 다형성이 필요해질 가능성은 없는가(`G18`)?
- [ ] 죽은 코드, 주석 처리한 코드, 쓸모없는 주석·잡동사니가 남아 있지 않은가(`C5`, `F4`, `G9`, `G12`)?
- [ ] 경고를 끄거나 실패하는 테스트를 꺼 두지 않았는가(`G4`)?
- [ ] 경계 조건마다 테스트가 있는가(`G3`, `T5`)?
- [ ] 빌드와 전체 테스트가 명령 하나로 돌고, 테스트가 빠른가(`E1`, `E2`, `T9`)?

## 관련

- [index.md](index.md) — 전체 목차. Chapter 15(JUnit Internals)에서 `G9`, `G11`, `G28`–`G33`, `N1`, `N4`, `N6`, `N7`이 쓰인다.
- [chapter_16_refactoring_serialdate.md](chapter_16_refactoring_serialdate.md) — 대부분의 휴리스틱을 실제 리팩터링에 적용한 사례
- [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) — `N1`, `N3`–`N6`과 겹치는 이름 원칙
- [chapter_03_functions.md](chapter_03_functions.md) — `F1`–`F3`, `G23`, `G30`, `G34`의 바탕, `N7`과 이어지는 Have No Side Effects
- [chapter_04_comments.md](chapter_04_comments.md) — `C1`–`C5`의 바탕
- [chapter_05_formatting.md](chapter_05_formatting.md) — `G10`, `G24`, `G35`
- [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md) — `G6`, `G23`, `G34`, `G36`
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — 깨끗한 테스트와 F.I.R.S.T.(`T9`), 테스트 코드의 `G5`
- [chapter_12_emergence.md](chapter_12_emergence.md) — `G5` 중복 제거
- [chapter_14_successive_refinement.md](chapter_14_successive_refinement.md) — `F1`, `G23`, `N5`

## 원서 밖 보충

- (원서 밖) J1: 오늘날 Google Java Style Guide 등 많은 스타일 가이드는 와일드카드 import를 금지하고, IDE가 import를 자동으로 정리해 긴 목록의 부담이 작다. 라이브러리가 같은 이름의 클래스를 새로 추가하면 와일드카드 import가 컴파일 오류를 낼 수 있다. 팀 표준(`G24`)을 따른다.
- (원서 밖) J1의 결합 논거: import 문은 컴파일 시점의 이름 해석에만 쓰이고 클래스 파일에 남지 않는다. 실제 의존은 코드가 클래스를 쓰는 곳에서 생기므로, import 형식을 바꿔도 모듈 간 결합은 그대로다. 와일드카드가 결합을 낮춘다는 원서 논거는 import한 클래스가 있어야 한다는 컴파일 검사에만 해당한다.
- (원서 밖) T4: JUnit 5에서는 `@Ignore` 대신 `@Disabled("이유")`를 쓴다.
- (원서 밖) J3·G23·G27: Java 17의 sealed 타입과 Java 21의 패턴 매칭 switch는 빠진 case를 컴파일러가 잡아 준다. switch냐 다형성이냐를 판단할 때 이 '구조로 강제' 수단도 함께 고려한다.
- (원서 밖) E1·E2: 원서 예시는 `svn`과 `ant`다. 오늘날에는 `./gradlew build`, `./mvnw test` 같은 래퍼 명령과 CI 파이프라인이 '명령 하나' 관행을 이어 간다.
- (원서 밖) G26: Java에서 금액은 최소 단위 `long`이나 `BigDecimal`(반올림 모드 명시)로 다루는 것이 일반적이다.
