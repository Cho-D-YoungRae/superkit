# Chapter 6: Objects and Data Structures — 객체와 자료 구조

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 6, pp. 93–101
> 한 줄 요약: 객체(데이터를 숨기고 동작을 공개)와 자료 구조(데이터를 공개하고 의미 있는 동작이 없음)를 구분해, 새 타입과 새 동작 중 무엇이 더 자주 늘어날지에 따라 하나를 고르고 둘을 섞지 않는다.

## 핵심

- 필드마다 getter/setter(접근자/변경자)를 기계적으로 붙이지 않는다. 데이터를 어떤 추상 개념으로 보여 줄지 먼저 고민한다.
- 객체는 데이터를 감추고 그 데이터를 다루는 함수를 공개한다. 자료 구조는 데이터를 공개하고 의미 있는 함수가 없다. 두 정의는 사실상 정반대다.
- 새 타입을 자주 추가할 곳은 객체(다형성)가, 새 동작을 자주 추가할 곳은 자료 구조와 절차적 함수가 맞다. 모든 것을 객체로 만들 필요는 없다.
- 객체에는 디미터 법칙(Law of Demeter)을 지킨다. 돌려받은 객체의 메서드를 다시 호출하며 내부를 따라가지 말고, 그 값을 원했던 의도를 객체에게 시킨다.
- 반은 객체, 반은 자료 구조인 하이브리드(hybrid)를 만들지 않는다. DTO와 Active Record는 자료 구조로 다루고, 업무 규칙은 별도 객체에 둔다.

## Data Abstraction — 자료 추상화

**어떻게**

- 구현을 숨기려면 변수와 호출자 사이에 함수 한 겹을 끼우는 것만으로는 부족하다. 사용자가 구현을 몰라도 데이터의 본질을 다룰 수 있는 추상 인터페이스를 공개한다. 저장 형태를 드러내는 구체적인 용어(갤런 단위 용량, 남은 갤런) 대신 호출자가 알고 싶은 추상적인 용어(남은 연료 비율)로 표현한다.
- 인터페이스를 도입하거나 getter/setter를 두는 것만으로 추상화가 되지는 않는다. 변수가 private이어도 변수 하나당 getter/setter를 하나씩 두면 구현이 그대로 드러나고, 인터페이스라도 저장된 값을 그대로 내보내면 구체적인 표현이다(아래 Stock의 Bad도 인터페이스다). 데이터를 어떻게 표현하는 것이 가장 좋을지 진지하게 고민한다. getter/setter를 생각 없이 추가하는 것이 가장 나쁜 선택이다.
- 메서드로 접근 정책을 강제한다. 예를 들어 값은 하나씩 읽게 하되, 함께 바뀌어야 하는 값은 한 번의 원자적(atomic) 연산으로만 바꾸게 한다.

**왜**

- 변수를 private으로 두는 이유는 남이 거기에 의존하지 않게 해 타입이나 구현을 언제든 바꿀 자유를 지키는 것이다. getter/setter를 다 열면 그 이유가 사라진다. 잘 추상화된 인터페이스는 내부가 어떤 표현(예: 직교 좌표인지 극좌표인지)인지조차 알 수 없게 하면서도 여전히 데이터를 나타낸다.

```java
// Bad: private이지만 필드마다 getter/setter를 달아 "날짜 두 개"라는 구현을 그대로 노출한다
public class StayPeriod {
    private LocalDate checkIn;
    private LocalDate checkOut;
    public LocalDate getCheckIn() { return checkIn; }
    public void setCheckIn(LocalDate checkIn) { this.checkIn = checkIn; }
    public LocalDate getCheckOut() { return checkOut; }
    public void setCheckOut(LocalDate checkOut) { this.checkOut = checkOut; }
}

// Good: 종료일과 박 수를 모두 읽을 수 있어 어느 쪽으로 저장했는지 알 수 없다. 변경은 한 번에 한다
public interface StayPeriod {
    LocalDate getCheckIn();
    LocalDate getCheckOut();
    int getNights();
    void reschedule(LocalDate checkIn, LocalDate checkOut);
}
// Bad: 호출자가 저장된 수량 두 개를 꺼내 직접 계산해야 한다
public interface Stock { int getQuantityOnHand(); int getQuantityReserved(); }
// Good: 호출자가 실제로 알고 싶은 개념으로 표현한다
public interface Stock { int getAvailableQuantity(); }
```

## Data/Object Anti-Symmetry — 자료/객체 비대칭

**어떻게**

- 객체는 추상화 뒤로 데이터를 숨기고 그 데이터를 다루는 함수만 공개한다. 자료 구조는 데이터를 그대로 공개하고 의미 있는 함수를 갖지 않는다. 설계할 때 지금 만드는 것이 어느 쪽인지 정한다.
- 앞으로 새 타입이 더 자주 추가될 부분은 객체와 다형성으로, 새 동작(함수)이 더 자주 추가될 부분은 자료 구조와 그것을 다루는 절차적 함수로 짠다. 절차적 코드를 객체지향이 아니라는 이유만으로 고치지 않는다. 경우에 따라서는 정말로 단순한 자료 구조와 그 위에서 도는 절차가 필요하다.

**왜**

- 절차적 코드(자료 구조를 쓰는 코드): 기존 자료 구조를 건드리지 않고 새 함수를 추가하기 쉽다. 대신 새 자료 구조를 추가하면 모든 함수를 고쳐야 한다.
- 객체지향 코드: 기존 함수를 건드리지 않고 새 클래스를 추가하기 쉽다. 대신 새 함수를 추가하면 모든 클래스를 고쳐야 한다.
- 원서 각주: 객체지향에서 새 함수를 추가하면 모든 클래스를 고쳐야 하는 제약은 Visitor나 이중 디스패치(dual-dispatch)로 우회할 수 있다. 하지만 그 기법에도 비용이 따르고, 대개 구조가 다시 절차적 프로그램 모양으로 돌아간다.

```java
// 절차적: 자료 구조는 데이터만, 동작은 한 곳에 모은다
public class CardPayment     { public long amount; }
public class TransferPayment { public boolean sameBank; }
public class PaymentFees {
    public long fee(Object payment) {
        if (payment instanceof CardPayment c) return c.amount * 3 / 100;
        if (payment instanceof TransferPayment t) return t.sameBank ? 0 : 500;
        throw new IllegalArgumentException("unknown payment type");
    }
}
// refundFee() 추가: PaymentFees에 함수 하나만 넣으면 된다(자료 구조는 그대로)
// 새 결제 수단 추가: PaymentFees의 모든 함수를 고쳐야 한다
```

```java
// 객체지향: 데이터를 숨기고 동작을 다형적으로 공개한다
public interface Payment { long fee(); }
public class CardPayment implements Payment {
    private final long amount;
    public CardPayment(long amount) { this.amount = amount; }
    public long fee() { return amount * 3 / 100; }
}
public class TransferPayment implements Payment {
    private final boolean sameBank;
    public TransferPayment(boolean sameBank) { this.sameBank = sameBank; }
    public long fee() { return sameBank ? 0 : 500; }
}
// 새 결제 수단 추가: 클래스 하나만 만들면 된다(기존 함수는 그대로)
// refundFee() 추가: 모든 Payment 구현 클래스를 고쳐야 한다
```

## The Law of Demeter — 디미터 법칙

**어떻게**

- 모듈은 자신이 다루는 객체의 내부 사정을 몰라야 하고, 따라서 객체는 접근자로 내부 구조를 드러내지 않는다. 더 정확히는, 클래스 C의 메서드 f는 다음의 메서드만 호출한다: C 자신, f가 생성한 객체, f에 인수로 전달된 객체, C의 인스턴스 변수가 가리키는 객체. 이 대상의 메서드가 돌려준 객체에 대해서는 다시 메서드를 호출하지 않는다. 원서의 표현으로 "talk to friends, not to strangers" (p. 98).

**왜**

- 객체는 데이터를 숨기고 연산을 공개한다(앞 절의 정의). 접근자로 내부 구조를 내보내면 구조를 숨기는 것이 아니라 드러내는 셈이 된다.
- 사슬을 따라가는 함수는 여러 객체가 서로 어떻게 들어 있는지까지 알아야 한다. 한 함수가 지기에는 지식이 지나치게 많다.
- 할 일을 객체에 시키면 객체는 내부를 계속 숨길 수 있고, 호출하는 함수는 몰라야 할 객체들을 거쳐 갈 필요가 없다.

### Train Wrecks — 기차 충돌

- `a.getB().getC().getD()`처럼 줄줄이 이어진 호출을 기차 충돌(train wreck)이라 부른다. 이런 사슬은 일반적으로 조잡한 스타일로 여겨지므로 피한다 [G36]. 대개는 지역 변수로 한 단계씩 나누는 편이 낫다. 다만 나누어 쓴다고 디미터 법칙 위반 여부가 바뀌지는 않는다. 호출하는 함수가 여러 객체를 거쳐 가는 길을 안다는 사실은 그대로다.
- 위반인지 아닌지는 사슬에 나온 것들이 객체인지 자료 구조인지에 달렸다. 객체라면 내부를 아는 것 자체가 명백한 위반이다. 동작 없는 자료 구조라면 내부 구조를 드러내는 것이 본래 역할이므로 디미터 법칙이 적용되지 않는다.
- 자료 구조에 접근자를 다는 바람에 이 구분이 흐려진다. 자료 구조는 공개 변수만 갖고 함수가 없으며, 객체는 비공개 변수와 공개 함수를 갖는 식으로 갈라 두면 덜 헷갈린다. 단, beans처럼 단순한 자료 구조에도 getter/setter를 요구하는 프레임워크와 표준이 있다.

### Hybrids — 하이브리드

- 의미 있는 일을 하는 함수가 있는 클래스에 공개 변수를 두거나, 비공개 변수를 사실상 공개하는 getter/setter를 두지 않는다. 이런 하이브리드는 외부 함수가 그 변수를 절차적 프로그램처럼 꺼내 쓰도록 유혹한다(원서 각주: Martin Fowler의 『Refactoring』에서는 이를 Feature Envy라고도 부른다).
- 새 함수를 추가하기도, 새 자료 구조를 추가하기도 어렵다. 원서는 이를 두고 "They are the worst of both worlds." (p. 99)라고 한다. 앞으로 늘어날 것이 새 함수인지(→ 자료 구조 + 절차) 새 타입인지(→ 객체 + 다형성) 설계자가 정하지 못했거나, 더 나쁘게는 이 문제를 아예 모른다는 신호다.

### Hiding Structure — 구조 숨기기

- 사슬에 나온 것들이 실제 동작을 가진 객체라면 내부를 따라 내려가지 않는다. 내부를 묻지 말고, 내부를 꺼내려던 이유(그 값으로 결국 무엇을 하려 했는지)를 찾아 그 일을 객체에게 시킨다.
- 사슬 전체를 감싸는 위임 getter(`getZipCodeOfCustomerAddress()` 같은 것)를 늘리면 객체의 메서드 수가 폭증할 수 있다. 중간 객체를 돌려주는 getter 위에서 다시 호출하는 방식은 그 반환값이 자료 구조라고 가정하는 셈이다. 둘 다 좋은 해법이 아니다.
- 원서 예에서 꺼낸 경로를 쓰는 코드는 경로 구분자, 확장자, 파일 객체처럼 수준이 다른 세부를 주변 코드와 뒤섞고 있었다 [G34][G6]. 원서는 이것도 조금 거슬린다고 짚지만 디미터 논의와는 떼어 두고, 그 경로로 임시 파일을 만들려 했다는 의도를 찾는 데 집중한다.

```java
// Bad: 객체(Order, Customer)의 내부 구조를 따라 내려가 값을 꺼낸 뒤 바깥에서 계산한다
Money fee = rateTable.feeFor(
        order.getCustomer().getShippingAddress().getZipCode(), order.getTotalWeight());

// Good: 값이 필요했던 의도(배송비 계산)를 객체에게 시킨다
Money fee = order.shippingFee(rateTable);
public class Order {
    private Customer customer;     // 인스턴스 변수: 호출해도 되는 대상
    private Weight totalWeight;
    public Money shippingFee(ShippingRateTable rateTable) {  // 인수: 호출해도 되는 대상
        return customer.shippingFee(rateTable, totalWeight);
    }
}
public class Customer {
    private ShippingAddress address;  // 공개 필드만 있는 자료 구조
    Money shippingFee(ShippingRateTable rateTable, Weight weight) {
        return rateTable.feeFor(address.zipCode, weight);  // 인수의 메서드 호출, 자료 구조의 필드 읽기: 위반 아님
    }
}
```

## Data Transfer Objects — 자료 전달 객체

**어떻게**

- 공개 변수만 있고 함수가 없는 클래스가 자료 구조의 전형인 DTO다. 데이터베이스와 통신하거나 소켓에서 받은 메시지를 파싱할 때 특히 유용하다. 이보다 조금 더 흔한 것은 비공개 변수를 getter/setter로 다루는 bean 형태다. bean이어도 자료 구조로 취급한다.

**왜**

- DTO는 데이터베이스의 원시 데이터를 애플리케이션 객체로 바꾸는 여러 변환 단계 중 첫 단계를 맡는 경우가 많다.
- bean의 준캡슐화(quasi-encapsulation)는 일부 객체지향 순수주의자의 마음을 편하게 해 주는 듯하지만, 대개 다른 이점은 없다.

### Active Record

- Active Record는 DTO의 특수한 형태다. 공개 변수(또는 bean 방식의 getter/setter)를 가지면서 보통 `save`, `find` 같은 탐색 메서드도 가진다. 대개 데이터베이스 테이블 같은 데이터 원천을 그대로 옮긴 것이다.
- 여기에 업무 규칙 메서드를 넣어 객체처럼 다루지 않는다. 그러면 자료 구조와 객체의 하이브리드가 된다. Active Record는 자료 구조로 두고, 업무 규칙을 담으면서 내부 데이터(아마도 Active Record 인스턴스)를 숨기는 별도 객체를 만든다.

```java
// Bad: 테이블을 옮긴 Active Record에 업무 규칙까지 넣는다(하이브리드)
public class MemberRecord {
    public long id;
    public int points;
    public String grade;
    public void save() { /* UPDATE member ... */ }
    public void upgradeIfEligible() { if (points >= 10_000) grade = "GOLD"; }
}

// Good: MemberRecord에서 upgradeIfEligible()만 빼 자료 구조로 두고, 업무 규칙은 감싼 객체가 맡는다
public class Membership {
    private final MemberRecord record;   // 내부 데이터(Active Record)를 숨긴다
    public Membership(MemberRecord record) { this.record = record; }
    public void upgradeIfEligible() { if (record.points >= 10_000) record.grade = "GOLD"; }
}
```

## 체크리스트

- [ ] 이 클래스를 객체(데이터를 숨기고 동작을 공개)로 쓸지 자료 구조(데이터를 공개하고 의미 있는 동작 없음)로 쓸지 정했는가? 의미 있는 동작과 공개 필드(또는 모든 필드의 getter/setter)가 한 클래스에 섞인 하이브리드를 피했는가?
- [ ] 필드마다 getter/setter를 자동으로 붙이지 않았는가? 공개한 메서드가 저장된 값이 아니라 호출자에게 필요한 개념을 드러내는가? 함께 바뀌어야 하는 값은 한 번의 연산으로만 바꾸게 했는가?
- [ ] 앞으로 더 자주 늘어날 것이 타입인지 동작인지 따져, 타입이면 객체와 다형성을, 동작이면 자료 구조와 절차적 함수를 골랐는가?
- [ ] 객체가 돌려준 객체에 다시 메서드를 호출하며 내부를 따라 내려가지 않고, 값을 꺼내려던 의도를 객체에게 시키는가?
- [ ] DTO나 Active Record에 업무 규칙을 넣지 않았는가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)): `G36` Avoid Transitive Navigation, `G14` Feature Envy, `G8` Too Much Information, `G23` Prefer Polymorphism to If/Else or Switch/Case, `G34` Functions Should Descend Only One Level of Abstraction, `G6` Code at Wrong Level of Abstraction
- [chapter_10_classes.md](chapter_10_classes.md) — 캡슐화, 응집도, 변경에 대비한 클래스 구성
- [chapter_03_functions.md](chapter_03_functions.md) — switch 문을 다형성 뒤로 숨기기, 함수당 추상화 수준 하나

## 원서 밖 보충

- Java 16 이후의 `record`는 DTO나 값 자료 구조를 짧게 표현한다(필드는 final이지만 참조하는 객체까지 불변인 것은 아니다). 업무 동작 없이 데이터만 담는 record라면 접근자 메서드가 있어도 자료 구조이므로 위 기준으로는 디미터 법칙의 대상이 아니다. record에 업무 규칙 메서드를 넣으면 하이브리드가 되므로 동작은 별도 객체에 둔다.
- Java 17의 sealed 인터페이스와 Java 21의 switch 패턴 매칭을 쓰면 절차적 방식에서 새 타입을 추가했을 때 그 타입을 처리하지 않은 switch(default 없이 쓴 경우)를 컴파일러가 알려 준다. 고칠 곳이 많다는 비용은 그대로지만 빠뜨릴 위험은 줄어든다. 위 PaymentFees처럼 `Object`를 받는 `instanceof` 사슬에는 이 검사가 적용되지 않는다.
- 내부를 묻지 말고 할 일을 시키라는 생각은 흔히 Tell, Don't Ask라고 부른다(Andy Hunt와 Dave Thomas가 널리 알렸다). 원서는 이 이름을 쓰지 않는다.
- `stream().filter(...).map(...)`나 빌더처럼 같은 추상화를 계속 돌려주는 fluent API 사슬은 내부 구조를 따라가는 것이 아니므로 보통 기차 충돌로 보지 않는다.
- Lombok `@Data`는 모든 필드에 getter/setter를 생성한다. JPA 엔티티는 관례상 접근자를 두는 경우가 많지만, 필드 접근 방식이면 JPA 자체는 접근자를 요구하지 않는다. 원서의 bean 논의와 같은 상황이므로, 그 클래스를 자료 구조로 쓸지 업무 규칙을 가진 객체로 쓸지 먼저 정하고 필요한 접근자만 둔다.
