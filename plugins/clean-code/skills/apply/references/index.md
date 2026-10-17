# Clean Code 레퍼런스 색인

> 원서: Robert C. Martin, *Clean Code: A Handbook of Agile Software Craftsmanship*, Prentice Hall, 2008.
> 이 폴더의 파일은 원서를 대신하지 않는 요약 노트다. 원칙 이름·절 제목·휴리스틱 코드는 원서 영어 표기를 그대로 쓰고, 본문은 한국어로 다시 썼으며, 코드 예시는 새로 작성했다. 각 파일의 `원서 밖 보충` 절은 원서 이후의 관행과 작성자 의견을 덧붙인 것이다.

필요한 챕터 파일만 연다. 파일 링크가 없는 항목은 코드 작성 지침이 없거나 그 내용이 다른 파일(주로 17장)에 이미 있어 파일을 만들지 않았고, 이유는 항목마다 적었다. 쪽 번호는 원서 기준이다.

## 한눈에 보기

| 장 | 제목 | 쪽 | 파일 |
|---|---|---|---|
| — | Foreword · Introduction · On the Cover — 추천사·들어가며·표지 | xix–xxx | — |
| 1 | Clean Code — 깨끗한 코드 | 1–15 | [chapter_01_clean_code.md](chapter_01_clean_code.md) |
| 2 | Meaningful Names — 의미 있는 이름 | 17–30 | [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) |
| 3 | Functions — 함수 | 31–52 | [chapter_03_functions.md](chapter_03_functions.md) |
| 4 | Comments — 주석 | 53–74 | [chapter_04_comments.md](chapter_04_comments.md) |
| 5 | Formatting — 형식 맞추기 | 75–92 | [chapter_05_formatting.md](chapter_05_formatting.md) |
| 6 | Objects and Data Structures — 객체와 자료 구조 | 93–101 | [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md) |
| 7 | Error Handling — 오류 처리 | 103–112 | [chapter_07_error_handling.md](chapter_07_error_handling.md) |
| 8 | Boundaries — 경계 | 113–120 | [chapter_08_boundaries.md](chapter_08_boundaries.md) |
| 9 | Unit Tests — 단위 테스트 | 121–133 | [chapter_09_unit_tests.md](chapter_09_unit_tests.md) |
| 10 | Classes — 클래스 | 135–151 | [chapter_10_classes.md](chapter_10_classes.md) |
| 11 | Systems — 시스템 | 153–169 | [chapter_11_systems.md](chapter_11_systems.md) |
| 12 | Emergence — 창발성 | 171–176 | [chapter_12_emergence.md](chapter_12_emergence.md) |
| 13 | Concurrency — 동시성 | 177–191 | [chapter_13_concurrency.md](chapter_13_concurrency.md) |
| 14 | Successive Refinement — 점진적인 개선 | 193–250 | [chapter_14_successive_refinement.md](chapter_14_successive_refinement.md) |
| 15 | JUnit Internals — JUnit 들여다보기 | 251–265 | — |
| 16 | Refactoring SerialDate — SerialDate 리팩터링 | 267–284 | [chapter_16_refactoring_serialdate.md](chapter_16_refactoring_serialdate.md) |
| 17 | Smells and Heuristics — 냄새와 휴리스틱 | 285–315 | [chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md) |
| 부록 A | Concurrency II — 동시성 II | 317–348 | [chapter_13_concurrency.md](chapter_13_concurrency.md) 안에 합침 |
| 부록 B | org.jfree.date.SerialDate | 349–408 | — |
| 부록 C | Cross References of Heuristics — 휴리스틱 교차 참조 | 409–410 | — |
| — | Epilogue — 에필로그 | 411 | — |
| — | Index — 찾아보기 | 413– | — |

## 챕터별 목차와 요약

### Foreword · Introduction · On the Cover — 추천사·들어가며·표지 (pp. xix–xxx) · 파일 없음

Foreword(James O. Coplien)는 5S 같은 작은 규율이 품질을 만든다는 비유로 디테일에 대한 관심을 강조하고, Introduction은 이 책이 원칙 → 사례 연구 → 휴리스틱 목록의 세 부분으로 이루어지며 사례 연구에서 휴리스틱을 대괄호 표기(예: [G5])로 참조한다고 안내한다. On the Cover는 표지 사진 설명이다. 코드 작성 지침이 없어 파일을 만들지 않았다.

### Chapter 1: Clean Code — 깨끗한 코드 (pp. 1–15)

엉망인 코드는 팀을 반드시 느리게 만들므로 빨리 가는 유일한 길은 코드를 늘 깨끗하게 유지하는 것이며, 그 책임은 프로그래머에게 있다.

- 파일: [chapter_01_clean_code.md](chapter_01_clean_code.md)
- 절: There Will Be Code · Bad Code · The Total Cost of Owning a Mess (The Grand Redesign in the Sky · Attitude · The Primal Conundrum · The Art of Clean Code? · What Is Clean Code?) · Schools of Thought · We Are Authors · The Boy Scout Rule · Prequel and Principles

### Chapter 2: Meaningful Names — 의미 있는 이름 (pp. 17–30)

이름만 읽어도 존재 이유·하는 일·쓰는 법이 드러나도록 짓고, 더 나은 이름이 보이면 망설이지 말고 바꾼다.

- 파일: [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md)
- 절: Use Intention-Revealing Names · Avoid Disinformation · Make Meaningful Distinctions · Use Pronounceable Names · Use Searchable Names · Avoid Encodings (Hungarian Notation · Member Prefixes · Interfaces and Implementations) · Avoid Mental Mapping · Class Names · Method Names · Don't Be Cute · Pick One Word per Concept · Don't Pun · Use Solution Domain Names · Use Problem Domain Names · Add Meaningful Context · Don't Add Gratuitous Context

### Chapter 3: Functions — 함수 (pp. 31–52)

함수는 작게 만들어 한 가지만 하게 하고, 인수·부수 효과·오류 코드처럼 읽는 사람을 멈칫하게 하는 요소를 덜어 낸다.

- 파일: [chapter_03_functions.md](chapter_03_functions.md)
- 절: Small! (Blocks and Indenting) · Do One Thing (Sections within Functions) · One Level of Abstraction per Function (The Stepdown Rule) · Switch Statements · Use Descriptive Names · Function Arguments (Common Monadic Forms · Flag Arguments · Dyadic Functions · Triads · Argument Objects · Argument Lists · Verbs and Keywords) · Have No Side Effects (Output Arguments) · Command Query Separation · Prefer Exceptions to Returning Error Codes (Extract Try/Catch Blocks · Error Handling Is One Thing · The Error.java Dependency Magnet) · Don't Repeat Yourself · Structured Programming · How Do You Write Functions Like This?

### Chapter 4: Comments — 주석 (pp. 53–74)

주석은 코드로 의도를 표현하지 못한 부분을 메우는 차선책이므로, 먼저 코드로 말하게 하고 꼭 필요한 주석만 정확하게 남긴다.

- 파일: [chapter_04_comments.md](chapter_04_comments.md)
- 절: Comments Do Not Make Up for Bad Code · Explain Yourself in Code · Good Comments (Legal · Informative · Explanation of Intent · Clarification · Warning of Consequences · TODO · Amplification · Javadocs in Public APIs) · Bad Comments (Mumbling · Redundant · Misleading · Mandated · Journal · Noise · Scary Noise · Don't Use a Comment When You Can Use a Function or a Variable · Position Markers · Closing Brace Comments · Attributions and Bylines · Commented-Out Code · HTML Comments · Nonlocal Information · Too Much Information · Inobvious Connection · Function Headers · Javadocs in Nonpublic Code)

### Chapter 5: Formatting — 형식 맞추기 (pp. 75–92)

형식은 의사소통 수단이므로, 팀이 합의한 단순한 규칙을 일관되게 적용해 소스 파일이 신문 기사처럼 위에서 아래로 읽히게 한다.

- 파일: [chapter_05_formatting.md](chapter_05_formatting.md)
- 절: The Purpose of Formatting · Vertical Formatting (The Newspaper Metaphor · Vertical Openness Between Concepts · Vertical Density · Vertical Distance · Vertical Ordering) · Horizontal Formatting (Horizontal Openness and Density · Horizontal Alignment · Indentation · Dummy Scopes) · Team Rules · Uncle Bob's Formatting Rules

### Chapter 6: Objects and Data Structures — 객체와 자료 구조 (pp. 93–101)

객체(데이터를 숨기고 동작을 공개)와 자료 구조(데이터를 공개하고 의미 있는 동작이 없음)를 구분해, 새 타입과 새 동작 중 무엇이 더 자주 늘어날지에 따라 하나를 고르고 둘을 섞지 않는다.

- 파일: [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md)
- 절: Data Abstraction · Data/Object Anti-Symmetry · The Law of Demeter (Train Wrecks · Hybrids · Hiding Structure) · Data Transfer Objects (Active Record)

### Chapter 7: Error Handling — 오류 처리 (pp. 103–112)

오류 처리를 주 로직과 분리된 관심사로 보고 예외·API 감싸기·특수 사례 객체로 다루며, null은 반환하지도 넘기지도 않는다.

- 파일: [chapter_07_error_handling.md](chapter_07_error_handling.md)
- 절: Use Exceptions Rather Than Return Codes · Write Your Try-Catch-Finally Statement First · Use Unchecked Exceptions · Provide Context with Exceptions · Define Exception Classes in Terms of a Caller's Needs · Define the Normal Flow · Don't Return Null · Don't Pass Null

### Chapter 8: Boundaries — 경계 (pp. 113–120)

통제할 수 없는 외부 코드는 래퍼나 Adapter 몇 곳에서만 참조하게 하고, 학습 테스트와 경계 테스트로 기대 동작을 고정한다.

- 파일: [chapter_08_boundaries.md](chapter_08_boundaries.md)
- 절: Using Third-Party Code · Exploring and Learning Boundaries · Learning log4j · Learning Tests Are Better Than Free · Using Code That Does Not Yet Exist · Clean Boundaries

### Chapter 9: Unit Tests — 단위 테스트 (pp. 121–133)

테스트 코드는 프로덕션 코드만큼 중요하므로 읽기 쉽고 깨끗하게 유지하고, 테스트 하나에 개념 하나만 담으며, F.I.R.S.T.를 지킨다.

- 파일: [chapter_09_unit_tests.md](chapter_09_unit_tests.md)
- 절: The Three Laws of TDD · Keeping Tests Clean (Tests Enable the -ilities) · Clean Tests (Domain-Specific Testing Language · A Dual Standard) · One Assert per Test (Single Concept per Test) · F.I.R.S.T.

### Chapter 10: Classes — 클래스 (pp. 135–151)

클래스의 크기는 책임(변경 이유)의 수로 재어 작게 유지하고, 응집도가 떨어지면 쪼개며, 새 기능을 기존 코드 수정이 아닌 확장으로 넣을 수 있도록 추상화에 의존하게 구성한다.

- 파일: [chapter_10_classes.md](chapter_10_classes.md)
- 절: Class Organization (Encapsulation) · Classes Should Be Small! (The Single Responsibility Principle · Cohesion · Maintaining Cohesion Results in Many Small Classes) · Organizing for Change (Isolating from Change)

### Chapter 11: Systems — 시스템 (pp. 153–169)

시스템 수준에서도 깨끗하려면 객체 생성·연결(시작)과 런타임 로직(사용)을 분리하고, 도메인 로직은 POJO로 둔 채 횡단 관심사는 비침투적으로 붙여 점진적으로 키울 수 있는 구조를 유지한다.

- 파일: [chapter_11_systems.md](chapter_11_systems.md)
- 절: How Would You Build a City? · Separate Constructing a System from Using It (Separation of Main · Factories · Dependency Injection) · Scaling Up (Cross-Cutting Concerns) · Java Proxies · Pure Java AOP Frameworks · AspectJ Aspects · Test Drive the System Architecture · Optimize Decision Making · Use Standards Wisely, When They Add Demonstrable Value · Systems Need Domain-Specific Languages

### Chapter 12: Emergence — 창발성 (pp. 171–176)

Kent Beck의 Simple Design 네 규칙(테스트 통과, 중복 제거, 의도 표현, 클래스·메서드 최소화)을 중요도 순으로 지키면 좋은 설계가 드러나기 쉬워진다.

- 파일: [chapter_12_emergence.md](chapter_12_emergence.md)
- 절: Getting Clean via Emergent Design · Simple Design Rule 1: Runs All the Tests · Simple Design Rules 2–4: Refactoring · No Duplication · Expressive · Minimal Classes and Methods

### Chapter 13: Concurrency — 동시성 (pp. 177–191)

동시성은 '무엇을'과 '언제'를 떼어 내는 전략이지만 올바르게 짜기 어려우므로, 동시성 코드는 따로 두고 공유 데이터와 임계 영역을 최소로 줄이며 라이브러리를 알고 간헐적 실패를 끝까지 추적한다.

- 파일: [chapter_13_concurrency.md](chapter_13_concurrency.md) (부록 A를 함께 담는다)
- 절: Why Concurrency? (Myths and Misconceptions) · Challenges · Concurrency Defense Principles (Single Responsibility Principle · Corollary: Limit the Scope of Data · Corollary: Use Copies of Data · Corollary: Threads Should Be as Independent as Possible) · Know Your Library (Thread-Safe Collections) · Know Your Execution Models (Producer-Consumer · Readers-Writers · Dining Philosophers) · Beware Dependencies Between Synchronized Methods · Keep Synchronized Sections Small · Writing Correct Shut-Down Code Is Hard · Testing Threaded Code (Treat Spurious Failures as Candidate Threading Issues · Get Your Nonthreaded Code Working First · Make Your Threaded Code Pluggable · Make Your Threaded Code Tunable · Run with More Threads Than Processors · Run on Different Platforms · Instrument Your Code to Try and Force Failures)

### Chapter 14: Successive Refinement — 점진적인 개선 (pp. 193–250)

명령행 인수 파서 사례로, 깨끗한 코드는 동작하는 초안을 테스트가 통과하는 작은 단계로 다듬어 얻으며, 같은 종류의 기능이 한 클래스 곳곳에 흩어져 엉망이 커지기 시작하면 기능 추가를 멈추고 구조부터 고쳐야 함을 보여 준다.

- 파일: [chapter_14_successive_refinement.md](chapter_14_successive_refinement.md) (사례 연구의 교훈과 변환 패턴만)
- 절: Args Implementation (How Did I Do This?) · Args: The Rough Draft (So I Stopped · On Incrementalism) · String Arguments

### Chapter 15: JUnit Internals — JUnit 들여다보기 (pp. 251–265) · 파일 없음

JUnit의 문자열 비교 결과를 압축해 보여 주는 모듈을 The Boy Scout Rule에 따라 조금씩 다듬는 사례 연구다. 적용한 원칙은 모두 17장 휴리스틱에 있어 파일을 만들지 않고 교훈만 남긴다.

- 커버리지가 높고 이미 깔끔한 코드도 더 다듬을 수 있다. 필요 없어 보이는 조건문은 빼고 테스트를 돌려 확인한 뒤 지운다. 테스트가 이런 과감한 정리를 안전하게 만든다.
- 복합 조건은 의도를 드러내는 이름의 메서드로 추출하고 긍정형으로 바꾼다. 함수 이름은 실제로 하는 일(부수 효과 포함)을 말해야 한다.
- 호출 순서에 기대는 숨은 시간적 결합은 앞 단계를 반드시 먼저 부르는 구조로 드러낸다. 순서를 강제하려고 의미 없는 인수를 넘기지 않는다.
- 곳곳에 흩어진 +1/-1 보정은 한 곳으로 모으고, 변수 이름을 실제 의미(인덱스인지 길이인지)에 맞춘다. 그러면 쓸모없는 조건이나 숨은 버그가 드러난다.
- 리팩터링은 앞서 내린 결정을 되돌리기도 하며 수렴해 가는 반복 과정이다.
- 적용된 휴리스틱: `N6` `G28` `N4` `G29` `N7` `G30` `G11` `N1` `G31` `G32` `G33` `G9` → [chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)

- 절: The JUnit Framework

### Chapter 16: Refactoring SerialDate — SerialDate 리팩터링 (pp. 267–284)

잘 짜인 남의 코드라도 커버리지로 테스트 빈틈을 찾아 빠진 테스트와 버그 수정부터 하고(Make It Work), 작은 단계마다 전체 테스트를 돌리며 Chapter 17 휴리스틱으로 다듬는(Make It Right) 사례 연구다.

- 파일: [chapter_16_refactoring_serialdate.md](chapter_16_refactoring_serialdate.md) (사례 연구의 교훈과 변환 패턴만)
- 절: First, Make It Work · Then Make It Right

### Chapter 17: Smells and Heuristics — 냄새와 휴리스틱 (pp. 285–315)

저자가 여러 프로그램을 리팩터링하며 고친 이유를 모은 냄새·휴리스틱 66개 목록으로, 리뷰·리팩터링 중에 `G5` 같은 코드로 찾아 쓴다.

- 파일: [chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)
- 절: Comments (C1–C5) · Environment (E1–E2) · Functions (F1–F4) · General (G1–G36) · Java (J1–J3) · Names (N1–N7) · Tests (T1–T9)

### Appendix A: Concurrency II — 동시성 II (pp. 317–348)

13장을 보강하는 부록이다. 단순한 클라이언트/서버 예시로 스레드를 도입할 때의 고려 사항을 보이고, 한 줄짜리 코드도 실행 경로가 매우 많다는 점, Executor·nonblocking 클래스·스레드에 안전하지 않은 클래스, 메서드 사이의 의존이 동시성 코드를 깨뜨리는 경우와 클라이언트·서버 기반 잠금, 처리량 계산, 데드락의 네 조건과 각 조건을 깨는 방법, 멀티스레드 코드 테스트를 다룬다.

- 파일: [chapter_13_concurrency.md](chapter_13_concurrency.md)의 `보강: Appendix A — Concurrency II` 절
- 절: Client/Server Example · Possible Paths of Execution · Knowing Your Library (Executor Framework · Nonblocking Solutions · Nonthread-Safe Classes) · Dependencies Between Methods Can Break Concurrent Code (Tolerate the Failure · Client-Based Locking · Server-Based Locking) · Increasing Throughput · Deadlock (Mutual Exclusion · Lock & Wait · No Preemption · Circular Wait와 각각을 깨는 방법) · Testing Multithreaded Code · Tool Support for Testing Thread-Based Code · Tutorial: Full Code Examples

### Appendix B: org.jfree.date.SerialDate (pp. 349–408) · 파일 없음

16장에서 리팩터링한 SerialDate 관련 코드 전체 목록(원본, 테스트, 리팩터링 결과)이다. 새 원칙 없이 코드만 실려 있고 판단 근거는 16·17장에 있어 파일을 만들지 않았다.

### Appendix C: Cross References of Heuristics — 휴리스틱 교차 참조 (pp. 409–410) · 파일 없음

17장 휴리스틱 코드마다 본문에서 쓰인 위치(장-쪽)를 나열한 표다. 휴리스틱 내용과 관련 챕터 링크는 17장 파일에 있어 파일을 만들지 않았다.

### Epilogue — 에필로그 (p. 411) · 파일 없음

TDD에 대한 개인적 다짐을 담은 한 쪽짜리 맺음말이다. 코드 작성 지침이 없어 파일을 만들지 않았다.

### Index — 찾아보기 (pp. 413–) · 파일 없음

원서 용어별 쪽 번호 색인이다. 이 레퍼런스에서는 쓰지 않는다.
