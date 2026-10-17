# Chapter 9: Unit Tests — 단위 테스트

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 9, pp. 121–133
> 한 줄 요약: 테스트 코드는 프로덕션 코드만큼 중요하므로 읽기 쉽고 깨끗하게 유지하고, 테스트 하나에 개념 하나만 담으며, F.I.R.S.T.를 지킨다.

## 핵심

- 테스트 코드에도 프로덕션 코드와 같은 품질 기준을 적용한다. 더러운 테스트는 테스트가 없는 것과 같거나 그보다 나쁘다. 테스트가 있어야 변경을 두려워하지 않으므로, 테스트가 곧 코드의 유연성·유지보수성·재사용성을 지킨다.
- 깨끗한 테스트의 기준은 가독성이다. BUILD-OPERATE-CHECK가 드러나게 쓰고, 무관한 세부는 테스트 언어(헬퍼 함수) 뒤로 숨긴다.
- 테스트 코드는 효율 기준을 낮춰도 되지만 깨끗함 기준은 낮추지 않는다(A Dual Standard).
- assert 수는 최소화하되 억지로 하나로 맞추지 않는다. 테스트 함수 하나에는 개념 하나만 둔다.
- 테스트는 Fast, Independent, Repeatable, Self-Validating, Timely해야 한다.

## The Three Laws of TDD — TDD의 세 가지 법칙

**어떻게**

- First Law: 실패하는 단위 테스트를 먼저 쓰기 전에는 프로덕션 코드를 쓰지 않는다.
- Second Law: 테스트는 실패할 만큼만 쓴다. 컴파일이 안 되는 것도 실패로 친다.
- Third Law: 프로덕션 코드는 지금 실패하는 테스트를 통과시킬 만큼만 쓴다.

**왜**

- 세 법칙을 따르면 테스트와 프로덕션 코드를 대략 30초 주기로 함께 쓰게 되고, 테스트가 몇 초 앞선다. 이렇게 일하면 테스트가 프로덕션 코드를 거의 전부 덮는다. 대신 테스트 양이 프로덕션 코드에 맞먹을 만큼 불어나 관리 문제가 될 수 있다. 그래서 테스트를 깨끗하게 유지해야 한다.

## Keeping Tests Clean · Tests Enable the -ilities — 테스트를 깨끗하게 지켜야 하는 이유

**어떻게**

- 테스트에서도 변수 이름을 잘 짓고, 테스트 함수를 짧고 설명적으로 쓰고, 설계와 분할에 신경 쓴다. '돌아가고 커버리지만 채우면 충분하다'는 식의 quick and dirty 테스트를 허용하지 않는다.
- 테스트는 프로덕션 코드와 같은 소스 패키지에 함께 체크인하고, 다른 사람도 쉽게 돌릴 수 있게 둔다(p. 122).

**왜**

- 프로덕션 코드가 바뀌면 테스트도 바뀌어야 한다. 테스트가 지저분할수록 고치기 어렵고, 새 프로덕션 코드를 쓰는 것보다 새 테스트를 끼워 넣는 데 시간이 더 들 가능성이 커지며, 깨진 옛 테스트를 다시 통과시키기도 어렵다. 결국 테스트가 부채가 된다.
- 테스트를 지저분하게 둔 팀은 유지 비용에 밀려 스위트를 버렸고, 결함이 늘자 변경을 두려워해 프로덕션 코드가 썩었다. "Test code is just as important as production code." (p. 124) 테스트 코드는 이등 시민이 아니며 생각과 설계와 정성이 필요하다. 저자는 결론에서 한 걸음 더 나아가, 테스트가 프로덕션 코드의 유연성·유지보수성·재사용성을 지키고 높이므로 프로덕션 코드보다 더 중요할 수도 있다고 본다(p. 133).
- 테스트가 없으면 모든 변경이 잠재적 버그다. 아키텍처가 아무리 유연하고 설계가 잘 나뉘어 있어도, 들키지 않는 버그가 두려워 코드 고치기를 망설인다. 커버리지가 높을수록 그 두려움이 줄어, 구조가 엉망인 코드도 거의 마음 놓고 고치고 개선할 수 있다.
- 그래서 프로덕션 코드를 덮는 자동화된 단위 테스트 스위트가 설계와 아키텍처를 깨끗하게 지키는 열쇠다. "Tests enable all the -ilities, because tests enable change." (p. 124) 반대로 테스트가 더러우면 변경 능력이 떨어지고 구조를 개선할 능력도 잃어 가며, 결국 테스트를 잃고 코드가 썩는다.

## Clean Tests · Domain-Specific Testing Language — 깨끗한 테스트와 테스트 언어

**어떻게**

- 깨끗한 테스트의 기준은 첫째도 둘째도 셋째도 가독성(readability)이다. 명료함, 단순함, 표현의 밀도를 갖춰 적은 표현으로 많은 것을 말한다.
- BUILD-OPERATE-CHECK 세 부분으로 나눈다. 테스트 데이터를 만들고(build), 그 데이터로 동작을 실행하고(operate), 결과가 기대와 같은지 확인한다(check).
- 테스트 의도와 무관한 세부(문자열을 도메인 객체로 바꾸기, 처리기 생성, 응답 꺼내기와 캐스팅, 요청 조립)는 본문에서 걷어 내고, 테스트에 정말 필요한 타입과 함수만 쓴다. 테스트 의도를 이루는 입력값·실행할 동작·기대값(아래 예의 "m-1", 10_000, 쿠폰, 18_000)은 본문에 남긴다. 반복되는 준비·검증 호출의 중복(G5)은 없앤다.
- Domain-Specific Testing Language: 시스템을 조작하는 프로그래머용 API를 본문에서 바로 부르지 않고, 그 API를 감싼 함수와 유틸리티를 테스트 언어로 삼는다(원서는 testing API라고도 부른다. 아래 예의 `givenMember`, `submitOrder`, `assertOrderCreatedWithTotal`).
- 이 테스트 언어는 미리 설계하지 않는다. 세부로 흐려진 테스트 코드를 계속 리팩터링하면서 자라게 한다.

**왜**

- 가독성은 아마 프로덕션 코드보다 테스트에서 더 중요하다. 세부가 쏟아지는 테스트는 읽는 사람을 고려하지 않은 코드다. 독자는 세부를 모두 이해한 뒤에야 테스트의 뜻을 안다. 정리한 테스트는 같은 일을 하면서도 오해나 압도 없이 금방 읽힌다.
- 테스트 언어는 테스트를 쓰기 편하고 읽기 쉽게 만든다. 지금 쓰는 사람과 나중에 읽는 사람을 함께 돕는다.

```java
// Bad: 테스트와 무관한 변환·조립·캐스팅이 의도를 가린다
@Test
void placesOrderWithCoupon() {
    memberRepository.save(new Member(MemberId.parse("m-1")));
    productRepository.save(new Product(Sku.parse("SKU-1"), Money.parse("10000")));
    OrderRequest request = new OrderRequest("m-1", "WELCOME10");
    request.addLine("SKU-1", 2);
    HttpResult result = (HttpResult) new OrderHandler(context).handle(request);
    assertEquals(201, result.status());
    assertEquals("18000", result.body().get("total"));
}

// Good: 같은 검증을 테스트 언어로. BUILD → OPERATE → CHECK
@Test
void placesOrderWithCoupon() {
    givenMember("m-1");
    givenProduct("SKU-1", 10_000);
    submitOrder("m-1", line("SKU-1", 2), coupon("WELCOME10"));
    assertOrderCreatedWithTotal(18_000);
}
```

## A Dual Standard — 이중 표준

**어떻게**

- 테스트 언어 코드도 단순하고 간결하고 표현력 있게 쓴다. 다만 프로덕션 코드만큼 효율적일 필요는 없다. 프로덕션에서라면 피할 비효율(대개 메모리나 CPU 문제)은 테스트에서 허용할 수 있다. 깨끗함에 관한 기준은 결코 낮추지 않는다.
- 같은 상태 묶음을 여러 테스트에서 확인할 때는, 상태를 순서가 고정된 문자열(대문자=켜짐, 소문자=꺼짐)로 인코딩해 `assertEquals` 한 번으로 비교한다. 상태를 `assertTrue`/`assertFalse`로 하나씩 확인하면 상태 이름과 기대값 사이를 눈이 오가야 해서 지루하고 틀리기 쉽다.

**왜**

- 테스트는 운영 환경이 아니라 테스트 환경에서 돌고, 두 환경의 요구는 매우 다르다. 저자는 비용이 작으면 프로덕션 코드에서도 `StringBuffer` 같은 보기 흉한 효율 장치를 피한다. 이중 표준은 원서 예(임베디드 실시간 시스템)처럼 운영 환경의 메모리·CPU는 빠듯하고 테스트 환경은 그렇지 않을 때 갈린다.
- 대문자=켜짐/소문자=꺼짐 같은 인코딩은 Avoid Mental Mapping 규칙을 거의 어기는 셈이다. 저자는 그래도 이 경우에는 적절하다고 본다. 뜻을 한 번 알면 결과를 빠르게 읽을 수 있기 때문이다.

```java
// Bad: 상태 이름과 assertTrue/assertFalse 사이를 눈이 오간다
@Test
void holdsSuspiciousPayment() {
    paySuspiciousAmount();
    assertFalse(gateway.approved());
    assertTrue(gateway.fraudAlert());
    assertTrue(gateway.manualReview());
}

// Good: 대문자=켜짐, 소문자=꺼짐. 순서는 {approved, fraudAlert, manualReview}
@Test
void holdsSuspiciousPayment() {
    paySuspiciousAmount();
    assertEquals("aFM", gateway.state());
}

// 테스트용 mock 게이트웨이의 메서드. 효율은 낮아도 읽기 쉽다
String state() {
    String s = "";
    s += approved ? "A" : "a";
    s += fraudAlert ? "F" : "f";
    s += manualReview ? "M" : "m";
    return s;
}
```

## One Assert per Test — 테스트당 assert 하나

**어떻게**

- 테스트의 assert 수를 최소화한다. 테스트 함수마다 assert를 하나만 두라는 학파의 규칙은 좋은 가이드라인이지 절대 규칙이 아니다. 여러 확인을 assert 하나로 모을 수 있으면 그것을 뒷받침하는 테스트 언어를 만든다(위 상태 문자열 예처럼).
- 형식 확인과 내용 확인(예: 응답이 특정 형식인지, 특정 내용을 담는지)처럼 assert 하나로 합치기 어려우면 두 테스트로 나눌 수 있다. 이때 테스트 언어 함수 이름을 given…/when…/then…으로 시작하는 given-when-then 규약을 쓰면 더 읽기 쉽다. 다만 나누면 준비·실행 코드가 중복된다.
- 그 중복은 TEMPLATE METHOD 패턴(given/when은 기반 클래스, then은 파생 클래스)이나 별도 테스트 클래스의 `@Before`(given/when을 몰아넣기)로 없앨 수 있다. 저자는 이 사소한 문제에 비해 장치가 너무 크다고 보고 assert 여러 개를 둔 원래 테스트를 택한다. 이런 경우에는 assert 여러 개를 그대로 둔다.

**왜**

- assert가 하나인 테스트는 결론이 하나라 빠르고 쉽게 이해된다. 그러나 assert 하나를 지키려고 들이는 구조가 얻는 것보다 클 수 있다. 저자는 대개 단일 assert를 돕는 테스트 언어를 만들려 하지만, assert를 둘 이상 넣는 것도 두려워하지 않는다.

## Single Concept per Test — 테스트당 개념 하나

**어떻게**

- 아마 더 나은 규칙은 테스트 함수 하나에서 개념 하나만 테스트하는 것이다. 잡다한 것을 차례로 확인하는 긴 테스트 함수를 만들지 않는다. 서로 독립된 것을 확인하는 테스트는 개념마다 독립된 테스트로 나눈다. 정리하면 개념당 assert 수를 최소화하고, 테스트 함수당 개념은 하나만 둔다.

**왜**

- 여러 개념을 한 함수에 섞으면 독자가 각 부분이 왜 있고 무엇을 확인하는지 스스로 알아내야 한다. 문제는 assert가 여러 개라는 점이 아니라 개념이 여러 개라는 점이다.
- 개념별로 Given/When/Then 문장으로 풀어 보면 잡다한 테스트 속에 숨은 일반 규칙이 보이고, 빠진 테스트가 드러난다. 원서 예에서는 '월을 더해도 날짜는 그 달의 말일을 넘지 않는다'는 규칙이 드러나 2월 28일 사례가 빠졌음을 알게 된다. 아래 예에서도 '잔액을 넘게 쓸 수 없다'는 규칙이 드러나면 '잔액 전부 사용' 테스트가 빠졌음이 보인다.

```java
// Bad: 독립된 개념 셋을 한 함수에 몰았다
@Test
void points() {
    PointAccount account = PointAccount.open();
    account.earn(1_000);
    assertEquals(1_000, account.balance());
    account.redeem(300);
    assertEquals(700, account.balance());
    assertThrows(InsufficientPointsException.class, () -> account.redeem(800));
}

// Good: 테스트 하나에 개념 하나
@Test
void earningIncreasesBalance() {
    PointAccount account = PointAccount.open();
    account.earn(1_000);
    assertEquals(1_000, account.balance());
}

@Test
void redeemingDecreasesBalance() {
    PointAccount account = accountWith(1_000);
    account.redeem(300);
    assertEquals(700, account.balance());
}

@Test
void cannotRedeemMoreThanBalance() {
    assertThrows(InsufficientPointsException.class, () -> accountWith(700).redeem(800));
}
```

## F.I.R.S.T. — 깨끗한 테스트의 다섯 규칙

**어떻게**

- Fast: 테스트는 빨리 돌아야 한다.
- Independent: 테스트끼리 의존하지 않는다. 한 테스트가 다음 테스트의 조건을 준비하지 않는다. 각 테스트를 따로, 어떤 순서로든 돌릴 수 있어야 한다.
- Repeatable: 운영 환경, QA 환경, 네트워크 없는 노트북 등 어떤 환경에서든 반복해 돌 수 있어야 한다.
- Self-Validating: 결과는 통과 아니면 실패인 불리언이다. 로그 파일을 읽거나 텍스트 파일 두 개를 손으로 비교해야 판정되면 안 된다.
- Timely: 단위 테스트는 그것을 통과시킬 프로덕션 코드 직전에 쓴다.
- 시간에 기대는 코드는 표준 시간 함수를 직접 부르지 않도록 떼어 내고, 테스트에서 시간 함수를 mock으로 바꿔 시간을 완전히 통제한다. 그리고 시간을 직접 앞으로 돌리며 상태가 바뀌는지 확인한다(p. 122, 저자가 지금이라면 택할 방식).

**왜**

- Fast: 느리면 자주 돌리지 않는다. 그러면 문제를 일찍 못 찾고, 코드를 마음 놓고 정리하지 못해 결국 코드가 썩는다.
- Independent: 의존하면 첫 실패가 연쇄 실패를 일으켜 진단을 어렵게 하고 뒤쪽 결함을 가린다.
- Repeatable: 그렇지 않으면 실패할 때마다 핑계가 생기고, 환경이 없을 때는 테스트를 돌리지 못한다.
- Self-Validating: 그렇지 않으면 실패 판정이 주관적이 되고, 테스트를 돌릴 때마다 긴 수작업 평가가 필요하다.
- Timely: 나중에 쓰면 프로덕션 코드가 테스트하기 어려울 수 있고, 너무 어렵다며 일부를 테스트하지 않기로 하거나, 테스트할 수 있게 설계하지 않을 수 있다.

```java
// Bad: 실제 시간 30분을 기다린다 (Fast 위반, 시간을 테스트가 통제하지 못한다)
@Test
void expiresAfterThirtyMinutes() throws InterruptedException {
    Reservation reservation = new Reservation();
    reservation.hold(seat("A1"));
    Thread.sleep(Duration.ofMinutes(30).toMillis());
    assertTrue(reservation.isExpired());
}

// Good: 시계를 주입하고 테스트가 시간을 앞으로 돌린다
@Test
void expiresAfterThirtyMinutes() {
    MutableClock clock = MutableClock.at("2024-05-01T10:00:00Z");
    Reservation reservation = new Reservation(clock);
    reservation.hold(seat("A1"));
    clock.advance(Duration.ofMinutes(30));
    assertTrue(reservation.isExpired());
}
```

## 체크리스트

- [ ] 테스트 본문이 BUILD-OPERATE-CHECK(given-when-then) 세 부분으로 바로 읽히는가?
- [ ] 의도와 무관한 세부(변환, 생성, 캐스팅, 요청 조립)와 반복되는 준비·검증 코드를 테스트 언어(헬퍼 함수)로 뽑았는가?
- [ ] 테스트 코드에도 프로덕션 코드와 같은 깨끗함 기준을 적용했는가(효율은 양보해도 된다)?
- [ ] 테스트 함수 하나가 개념 하나만 검증하는가? 개념당 assert 수는 최소인가?
- [ ] 각 테스트를 Given/When/Then 문장으로 적었을 때 드러나는 규칙의 경계 사례(말일, 잔액 전부 사용 등)를 테스트했는가?
- [ ] 테스트가 다른 테스트가 남긴 상태에 기대지 않아, 하나만 따로 돌려도 어떤 순서로 돌려도 통과하는가?
- [ ] 실제 시간 대기나 네트워크, 특정 환경 없이 빠르게 돌고, 결과가 통과/실패로만 나오는가?
- [ ] 테스트를 프로덕션 코드보다 먼저(직전에) 썼는가?

## 관련

- Chapter 17 휴리스틱: `T1` Insufficient Tests, `T2` Use a Coverage Tool!, `T5` Test Boundary Conditions(개념별로 나누면 드러나는 경계 사례), `T9` Tests Should Be Fast, `G5` Duplication
- [chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md) — 테스트 휴리스틱 T1~T9 전체
- [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) — Avoid Mental Mapping: 상태 문자열 인코딩이 부딪히는 규칙
- [chapter_08_boundaries.md](chapter_08_boundaries.md) — 서드파티 API를 학습 테스트로 익히고 경계를 테스트로 지키기
- [chapter_12_emergence.md](chapter_12_emergence.md) — Simple Design Rule 1: Runs All the Tests, 테스트가 리팩터링을 가능하게 한다
- [chapter_16_refactoring_serialdate.md](chapter_16_refactoring_serialdate.md) — 커버리지로 빈틈을 찾아 테스트를 먼저 보강한 뒤 리팩터링하는 사례

## 원서 밖 보충

- 원서는 JUnit 3/4 기준이다. JUnit 5에서는 `@Before`가 `@BeforeEach`가 됐다. `@Nested` 클래스마다 `@BeforeEach`에 given/when을 두면, 원서가 장치가 너무 크다고 본 테스트 분리 방식을 비교적 가볍게 쓸 수 있다. `assertAll`은 여러 assert를 묶어 실패를 한꺼번에 보고한다. 한 개념을 여러 측면에서 확인할 때 유용하다. `@DisplayName`으로 given-when-then 문장을 테스트 이름으로 달 수 있고, `@ParameterizedTest`로 한 개념의 여러 입력 사례를 표현할 수 있다. AssertJ 같은 fluent assertion 라이브러리도 테스트 언어 역할을 일부 맡는다.
- 원서는 효율을 높이려면 아마 `StringBuffer`를 썼어야 했다고 말한다. 오늘날 단일 스레드 문자열 조립에는 동기화 비용이 없는 `StringBuilder`를 쓴다.
- 시간 통제는 `java.time.Clock`을 주입하고 테스트에서 `Clock.fixed`·`Clock.offset`이나 직접 만든 가변 Clock을 쓰는 방식이 흔하다. 위 예의 `MutableClock`은 그런 테스트용 클래스를 가정했다.
