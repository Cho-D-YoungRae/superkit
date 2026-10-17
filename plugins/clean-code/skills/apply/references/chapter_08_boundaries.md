# Chapter 8: Boundaries — 경계

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 8, pp. 113–120 · by James Grenning
> 한 줄 요약: 통제할 수 없는 외부 코드는 래퍼나 Adapter 몇 곳에서만 참조하게 하고, 학습 테스트와 경계 테스트로 기대 동작을 고정한다.

## 핵심

- `Map` 같은 경계 인터페이스는 쓰는 클래스(또는 가까운 클래스 묶음) 안에 가두고, 필요한 연산만 노출한다.
- 사용법이 분명하지 않은 서드파티 API는 프로덕션 코드에 바로 붙여 시험하기보다 학습 테스트(learning tests)로 먼저 익힌다.
- 학습 테스트와 경계 테스트(boundary tests)는 남겨 둔다. 라이브러리 새 버전이 나오면 이 테스트를 돌려 동작 차이를 곧바로 알아챈다.
- 외부 API가 아직 정해지지 않았으면 우리가 원하는 인터페이스를 먼저 정의하고, API가 정해지면 Adapter로 잇는다.
- 통제하지 못하는 것보다 통제하는 것에 의존한다. 서드파티를 아는 코드는 최소한으로 둔다.

## Using Third-Party Code — 서드파티 코드 사용하기

**어떻게**

- `Map`(또는 경계에 있는 다른 인터페이스)을 시스템 여기저기로 넘기지 않는다. 그것을 쓰는 클래스나 가까운 클래스 묶음 안에만 두고, public API에서 반환하거나 인수로 받지 않는다. 모든 `Map` 사용을 감싸라는 뜻은 아니고, 경계 인터페이스를 시스템에 퍼뜨리지 말라는 뜻이다.
- 감싼 클래스에는 애플리케이션이 실제로 필요한 연산만 연다. 형변환·타입 관리·제네릭 사용 여부는 그 클래스의 구현 세부로 숨긴다. 설계 규칙과 비즈니스 규칙(예: 특정 타입만 저장, 삭제 금지)도 이 클래스에서 강제할 수 있다.

**왜**

- 제공자는 많은 환경에서 쓰이도록 넓은 인터페이스를 만들고, 사용자는 자기 필요에 맞춘 좁은 인터페이스를 원한다. 이 긴장이 경계에서 문제를 일으킨다.
- `Map` 자체는 우리 의도(삭제 금지, 타입 제한)를 강제하지 못한다. 받은 쪽은 누구나 `clear()`로 내용을 지우거나 아무 타입이나 넣을 수 있다.
- 제네릭을 쓰면 곳곳에 반복되던 형변환이 사라져 읽기는 나아진다. 그러나 필요 이상으로 넓은 인터페이스(`clear()`, `put()` 등)를 넘긴다는 문제는 그대로 남는다. 제네릭만으로는 부족하다.
- 경계 인터페이스가 바뀌면 고칠 곳이 그만큼 많다. `Map`도 Java 5에서 제네릭이 들어오며 실제로 바뀌었고, `Map`을 마구 넘긴 탓에 변경량이 너무 커서 제네릭을 도입하지 못한 시스템도 있었다.
- 감싸면 경계 인터페이스가 숨겨져, 그 인터페이스가 바뀌어도 나머지 애플리케이션에 거의 영향 없이 감싼 클래스 안에서 대응할 수 있다. 애플리케이션에 맞춰 좁힌 인터페이스라 이해하기 쉽고 오용하기 어렵다.

```java
// Bad: 경계 인터페이스(Map)가 public API로 새어 나간다
public class ReservationBook {
    private final Map<String, Reservation> reservations = new HashMap<>();

    public Map<String, Reservation> getReservations() {
        return reservations; // 받는 쪽이 clear()·put()을 마음대로 호출할 수 있다
    }
}
// 호출부 곳곳: book.getReservations().get(id); book.getReservations().put(r.id(), r);

// Good: Map은 클래스 안에 가두고, 애플리케이션에 필요한 연산만 연다
public class ReservationBook {
    private final Map<String, Reservation> reservations = new HashMap<>();

    public Reservation findById(String id) { return reservations.get(id); }

    public void add(Reservation reservation) { reservations.put(reservation.id(), reservation); }
}
```

## Exploring and Learning Boundaries — 경계를 탐색하고 익히기

**어떻게**

- 서드파티 사용법이 분명하지 않으면 프로덕션 코드에 바로 붙여 시험하지 않는다. 대신 그 API에 대한 이해를 확인하는 테스트를 쓴다. Jim Newkirk는 이를 learning tests라 불렀다.
- 학습 테스트에서는 애플리케이션에서 쓰려는 방식 그대로 API를 호출한다. 우리가 API에서 얻고 싶은 것에 초점을 둔 통제된 실험이다.
- 진행 방식(원서의 log4j 사례): 가장 단순한 기대로 테스트를 하나 쓴다 → 돌려서 오류나 뜻밖의 결과를 본다 → 문서를 조금 더 읽고 테스트를 고친다 → 반복한다. 직관과 다른 기본 동작도 테스트로 기록해 둔다.
- 알아낸 지식은 단순한 단위 테스트 묶음으로 남기고, 그 지식을 우리 클래스(예: 자체 로거 클래스)에 캡슐화해 애플리케이션 나머지를 경계 인터페이스로부터 격리한다.

**왜**

- 서드파티 코드를 검증할 책임은 우리에게 없지만, 우리가 쓰려는 방식대로 동작하는지 테스트로 확인해 두면 이득이 될 수 있다.
- 익히기와 통합을 한꺼번에 하면 버그 원인이 우리 쪽인지 라이브러리 쪽인지 가리기 어려워 긴 디버깅에 빠지기 쉽다.

```java
// 결제 금액 계산에 BigDecimal을 쓰기 전에, 기대하는 동작을 학습 테스트로 확인한다
class BigDecimalLearningTest {
    @Test
    void equals는_scale까지_비교한다() {
        assertNotEquals(new BigDecimal("10.0"), new BigDecimal("10.00"));
        assertEquals(0, new BigDecimal("10.0").compareTo(new BigDecimal("10.00")));
    }

    @Test
    void HALF_UP으로_소수점_둘째_자리까지_반올림한다() {
        assertEquals(new BigDecimal("1.01"), new BigDecimal("1.005").setScale(2, RoundingMode.HALF_UP));
    }

    @Test
    void 몫이_무한소수면_반올림_규칙_없는_divide는_예외를_던진다() {
        assertEquals(new BigDecimal("2.5"), new BigDecimal("10").divide(new BigDecimal("4")));
        assertThrows(ArithmeticException.class, () -> new BigDecimal("10").divide(new BigDecimal("3")));
    }
}
```

## Learning Tests Are Better Than Free — 학습 테스트는 공짜 이상이다

**어떻게**

- 학습 테스트를 버리지 말고 남겨 둔다. 서드파티 새 버전이 나오면 학습 테스트를 돌려 동작 차이가 있는지 확인한다.
- 학습 테스트가 필요했든 아니든, 깔끔한 경계에는 프로덕션 코드와 같은 방식으로 인터페이스를 호출하는 경계 테스트(원서: outbound tests)를 둔다.

**왜**

- API는 어차피 익혀야 하므로 학습 테스트에 드는 추가 비용은 없다. 남겨 두면 새 버전마다 다시 돌릴 수 있어 투자 수익까지 생긴다.
- 서드파티는 작성자의 사정에 따라 계속 바뀌므로, 한번 통합했다고 우리 기대와 계속 맞는다는 보장이 없다. 남겨 둔 테스트가 비호환 변경을 즉시 드러낸다.
- 경계 테스트는 새 버전으로 옮겨 가는 일을 쉽게 해 준다. 이것이 없으면 옛 버전에 필요 이상으로 오래 머물고 싶은 유혹에 빠질 수 있다.

## Using Code That Does Not Yet Exist — 아직 존재하지 않는 코드 사용하기

**어떻게**

- 아는 것과 모르는 것을 가르는 경계도 있다. 경계 너머를 아직 알 수 없거나 일부러 보지 않기로 했다면, 막히지 않도록 미지의 부분에서 먼 곳부터 작업한다(원서 사례: 인터페이스가 미정인 무선 송신 서브시스템).
- 작업하다 경계에 닿으면 경계 너머에 무엇을 요청하고 싶은지가 드러난다. 그 요청이 어떻게 처리될지는 나중으로 미루고, 드러난 필요대로 우리가 원하는 인터페이스를 직접 정의한다. 원서는 이것을 "the interface we wish we had" (p. 119)라고 표현한다.
- 클라이언트 코드는 그 인터페이스에만 의존하게 하고, 외부 API가 정해지면 Adapter 패턴(GoF, 『Design Patterns』)으로 둘 사이를 잇는다.
- 테스트에서는 fake 구현을 끼워 클라이언트를 검증한다. 외부 API가 생기면 그 API를 올바르게 쓰는지 확인하는 경계 테스트를 만든다.

**왜**

- 원하는 인터페이스는 우리 통제 아래 있다. 그래서 클라이언트 코드가 읽기 쉽고 하려는 일에 집중한다.
- Adapter가 API와의 상호작용을 캡슐화하므로 API가 바뀔 때 고칠 곳이 한 곳이다. 이 구조는 fake를 끼워 테스트하기 편한 seam도 만든다(원서가 참조하는 『Working Effectively with Legacy Code』의 용어, '원서 밖 보충' 참고).

```java
// Good 1) 결제 대행사 API가 정해지기 전: 우리가 원하는 인터페이스를 먼저 정의한다
public interface PaymentGateway {
    PaymentResult charge(String orderId, Money amount);
}

public class CheckoutService { // 클라이언트는 우리 인터페이스만 안다
    private final PaymentGateway gateway;
    public CheckoutService(PaymentGateway gateway) { this.gateway = gateway; }
    public PaymentResult checkout(Order order) { return gateway.charge(order.id(), order.total()); }
}
// 테스트에서는 FakePaymentGateway를 주입해 CheckoutService를 검증한다
```

```java
// Bad: 클라이언트가 대행사 SDK를 직접 다룬다. 이런 호출이 여러 서비스에 흩어지면 SDK가 바뀔 때 모두 고쳐야 한다
public PaymentResult checkout(Order order) {
    VendorChargeResponse res = client.requestCharge(order.id(), order.total().minorUnits(), order.total().currency());
    return res.approved() ? PaymentResult.approved(res.txId()) : PaymentResult.declined(res.code());
}

// Good 2) API가 정해진 뒤: Adapter 한 곳에서만 대행사 SDK를 다룬다. CheckoutService는 그대로다
public class VendorPayAdapter implements PaymentGateway {
    private final VendorPayClient client; // 서드파티 SDK
    public VendorPayAdapter(VendorPayClient client) { this.client = client; }

    @Override
    public PaymentResult charge(String orderId, Money amount) {
        VendorChargeResponse res = client.requestCharge(orderId, amount.minorUnits(), amount.currency());
        return res.approved() ? PaymentResult.approved(res.txId()) : PaymentResult.declined(res.code());
    }
}
```

## Clean Boundaries — 깨끗한 경계

**어떻게**

- 서드파티를 참조하는 코드를 래퍼(`Map` 예)나 Adapter 몇 곳에 모으고, 그 경계에 기대 동작을 정의하는 테스트를 붙인다. 나머지 코드는 서드파티 세부를 모르게 한다.

**왜**

- 경계에서는 변경이 일어난다. 서드파티를 아는 코드가 적을수록 그 변경에 드는 비용이 작고, 코드가 의도를 더 잘 드러내며, 경계 너머를 일관된 방식으로 쓰게 된다.
- 통제하지 못하는 것에 기대면 결국 그것이 우리를 좌우하게 될 수 있다. 우리가 통제하는 인터페이스에 기대야 외부 변경으로부터 투자를 지킬 수 있다.

## 체크리스트

- [ ] `Map` 같은 경계 인터페이스나 서드파티 타입, 그 호출이 래퍼·Adapter(또는 가까운 클래스 묶음) 안에만 있는가? 그 밖의 public API 시그니처에서 경계 인터페이스·서드파티 타입을 없앴는가?
- [ ] 감싼 클래스가 애플리케이션에 필요한 연산만 노출하는가(`clear()` 같은 불필요한 권한은 감췄는가)?
- [ ] 사용법을 확신하지 못하는 라이브러리는 프로덕션 코드에 붙이기 전에 학습 테스트로 동작을 확인했는가?
- [ ] 라이브러리 버전을 올릴 때 돌릴 학습 테스트·경계 테스트가 있는가?
- [ ] 정해지지 않은 외부 API 때문에 막혀 있다면, 우리가 원하는 인터페이스를 먼저 정의했는가?
- [ ] 외부 API가 바뀌면 고칠 곳이 Adapter(또는 래퍼) 한 곳뿐인가? 클라이언트 코드를 fake 구현으로 테스트할 수 있는가?

## 관련

- Chapter 17 휴리스틱: `G8` Too Much Information — 감싼 클래스는 작은 인터페이스만 노출한다. (`G3`·`G33`·`T5`의 boundary는 경계 조건(edge case)을 뜻하므로 이 장의 '경계'와 다르다.)
- [chapter_07_error_handling.md](chapter_07_error_handling.md) — 서드파티 API를 감싸 예외 타입을 호출자 필요에 맞게 바꾸는 방법
- [chapter_10_classes.md](chapter_10_classes.md) — 구체 구현 대신 추상화에 의존해 변경으로부터 격리하기
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — 테스트 코드를 깨끗하게 유지하는 원칙(학습 테스트·경계 테스트에도 그대로 적용한다)
- [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md) — 구현을 감추고 추상 인터페이스를 노출하기

## 원서 밖 보충

- `Collections.unmodifiableMap`이나 `Map.copyOf`(Java 10+)로 읽기 전용 `Map`을 돌려줘도 `Map` 인터페이스는 그대로 노출되고, `put` 호출은 컴파일되지만 실행 중에 `UnsupportedOperationException`을 던진다. 경계 인터페이스를 감추는 래퍼를 대신하지 못한다.
- log4j 1.x는 2015년에 지원이 끝났다. 요즘 Java에서는 SLF4J 같은 로깅 facade가 '자체 로거 클래스' 역할을 대신하는 경우가 많다. 다만 SLF4J API 자체도 서드파티 경계다. API가 매우 안정적이고 사실상 표준이라 코드 곳곳에서 직접 쓰는 것을 감수하는 절충이며, 안정성이 낮은 라이브러리에는 같은 판단을 적용하지 않는다.
- seam은 Michael Feathers가 『Working Effectively with Legacy Code』에서 쓴 용어로, 그 자리의 코드를 고치지 않고도 프로그램 동작을 바꿔 끼울 수 있는 지점을 뜻한다.
- 원하는 인터페이스를 정의하고 Adapter로 잇는 구조를 시스템 전체로 넓힌 것이 Ports and Adapters(Hexagonal Architecture)다.
