# Chapter 10: Classes — 클래스

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 10, pp. 135–151 · with Jeff Langr
> 한 줄 요약: 클래스의 크기는 책임(변경 이유)의 수로 재어 작게 유지하고, 응집도가 떨어지면 쪼개며, 새 기능을 기존 코드 수정이 아닌 확장으로 넣을 수 있도록 추상화에 의존하게 구성한다.

## 핵심

- 클래스 크기는 줄 수가 아니라 책임(responsibility)의 수로 잰다. 메서드가 몇 개뿐이어도 변경 이유가 둘이면 너무 크다.
- 간결한 이름이 떠오르지 않거나, 25단어 남짓한 설명에 "if/and/or/but"이 필요하면 책임이 여럿이라는 신호다.
- 동작하게 만든 뒤 바로 다음 문제로 넘어가지 않는다. 돌아와서 너무 많은 것을 담은 클래스를 책임 하나짜리 단위로 나눈다.
- 인스턴스 변수는 적게 두고 메서드가 그 변수를 많이 쓰게 한다. 일부 메서드만 쓰는 변수 묶음이 생기면 거의 항상 그 안에 다른 클래스가 숨어 있다.
- 기능을 추가하려고 기존 클래스를 열고 있다면 설계를 고칠지 검토한다. 기존 코드 수정이 아니라 확장으로 기능을 넣는 구조(OCP)를 지향한다.
- 구체 세부(예: 외부 API)가 바뀌면 거기에 의존하는 클라이언트가 위험해진다. 클라이언트는 구체 구현이 아니라 그 개념을 나타내는 인터페이스·추상 클래스에 의존한다(DIP). 결합이 낮아져 테스트·재사용·이해가 쉬워진다.

## Class Organization — 클래스 체계

**어떻게**

- 표준 Java 관례에 따라 변수 목록으로 시작한다. 순서는 public static 상수(있다면) → private static 변수 → private 인스턴스 변수다. public 변수를 둘 타당한 이유는 거의 없다.
- 변수 목록 다음에 public 메서드를 둔다. 저자들은 public 메서드가 호출하는 private 유틸리티를 그 public 메서드 바로 뒤에 두는 방식을 선호한다.

**왜**

- 이 배치는 The Stepdown Rule을 따르므로 프로그램이 신문 기사처럼 위에서 아래로 읽힌다.

```java
public class CouponIssuer {
    public static final int MAX_ACTIVE_PER_MEMBER = 3;            // 1. public static 상수
    private static final Duration VALIDITY = Duration.ofDays(30);  // 2. private static 변수(여기서는 상수)
    private final CouponRepository coupons;                       // 3. private 인스턴스 변수(생성자 생략)
    public Coupon issue(MemberId memberId, Instant now) {         // 4. public 메서드
        checkLimit(memberId);
        return coupons.save(new Coupon(memberId, now.plus(VALIDITY)));
    }
    private void checkLimit(MemberId memberId) {                  // 5. 바로 아래에 그 메서드가 쓰는 private 유틸리티
        if (coupons.countActive(memberId) >= MAX_ACTIVE_PER_MEMBER)
            throw new CouponLimitExceededException(memberId);
    }
    public void revoke(CouponId couponId) { coupons.delete(couponId); }  // 6. 다음 public 메서드
}
```

### Encapsulation — 캡슐화

**어떻게**

- 변수와 유틸리티 메서드는 private으로 두는 것이 기본이지만 반드시 고집하지는 않는다. 같은 패키지의 테스트가 메서드를 호출하거나 변수에 접근해야 하면 protected나 package scope로 연다.
- 그 전에 private을 유지한 채 테스트할 방법을 먼저 찾는다. 캡슐화를 느슨하게 하는 것은 언제나 마지막 수단이다.

**왜**

- 저자들에게는 테스트가 무엇보다 우선이다. 그래도 캡슐화를 푸는 일은 다른 길이 없을 때로 미룬다.

## Classes Should Be Small! — 클래스는 작아야 한다

**어떻게**

- 함수와 마찬가지로 클래스 설계에서도 첫째 규칙은 작게 만드는 것이다. 다만 함수는 물리적인 줄 수로 재지만 클래스는 책임의 수로 잰다.
- public 메서드가 수십 개인 "God class"만 문제가 아니다. 메서드가 다섯 개뿐이어도 책임이 둘 이상이면 너무 크다.
- 클래스 이름은 그 클래스가 맡은 책임을 설명해야 한다. 간결한 이름을 지을 수 없다면 아마 너무 큰 것이다. 이름이 모호할수록 책임이 많을 가능성이 크다. `Processor`, `Manager`, `Super` 같은 모호한 단어(weasel words)가 들어간 이름은 책임이 잘못 뭉쳐 있다는 암시인 경우가 많다.
- 클래스를 25단어 안팎으로 설명해 본다. "if", "and", "or", "but"을 쓰지 않고 설명할 수 있어야 한다. 설명에 "그리고"가 끼어들면 책임이 여럿이라는 힌트다.

**왜**

- 이름 짓기는 아마도 클래스 크기를 판단하는 첫 번째 수단이다. 짧은 설명도 같은 역할을 한다.

## The Single Responsibility Principle — 단일 책임 원칙

**어떻게**

- SRP는 클래스나 모듈이 "one, and only one, reason to change" (p. 138)를 가져야 한다는 원칙이다. 이것이 책임의 정의(변경 이유)이자 클래스 크기의 지침이다.
- 클래스가 바뀔 이유를 적어 본다. 두 이유가 서로 독립적으로 생길 수 있다면(한쪽을 바꿀 때 다른 쪽이 반드시 따라 바뀌지는 않는다면) 별개의 책임이므로 나눈다. 책임을 찾다 보면 더 나은 추상화가 보인다. 떼어 낸 클래스가 다른 애플리케이션에서도 재사용할 만한 구성 요소가 되기도 한다.
- 동작하는 코드를 만드는 일과 깨끗한 코드를 만드는 일은 별개의 활동이다. 먼저 동작에 집중하는 것은 전적으로 옳다. 다만 동작했다고 끝내고 다음 문제로 넘어가지 않는다. 돌아가서 너무 많은 것을 담은 클래스를 서로 결합되지 않은, 책임 하나짜리 단위로 나눈다.
- 작은 클래스가 많으면 큰 그림을 보려고 여러 클래스를 오가야 한다는 걱정이 있다. 하지만 작은 클래스 여럿으로 된 시스템이라고 큰 클래스 몇 개로 된 시스템보다 움직이는 부품이 더 많지는 않다. 배워야 할 양은 같다. 차이는 이름표가 잘 붙은 작은 서랍이 많은 공구함이냐, 아무거나 던져 넣은 서랍 몇 개냐다.

**왜**

- SRP는 OO 설계에서 중요한 개념 중 하나이고 이해하고 지키기도 비교적 쉽다. 그런데도 가장 자주 어겨지는 클래스 설계 원칙이다. 동작하면 끝났다고 보고 정리로 넘어가지 않기 때문에, 너무 많은 일을 하는 클래스가 늘 눈에 띈다.
- 먼저 동작에 집중해도 되는 것은 머릿속에 한 번에 담을 수 있는 양이 한정되어 있기 때문이다. 동작시키기와 정리하기를 따로 하는 것은 관심사 분리를 프로그램에서처럼 작업 방식에도 적용하는 일이다.
- 큰 시스템에는 어차피 많은 로직과 복잡성이 있다. 복잡성 관리의 1차 목표는 개발자가 어디를 봐야 할지 알고, 지금 직접 영향을 받는 복잡성만 이해하면 되도록 정리하는 것이다. 여러 목적을 가진 큰 클래스는 지금 알 필요 없는 것까지 헤치고 지나가게 만든다.
- 그래서 시스템은 큰 클래스 몇 개가 아니라 작은 클래스 여럿으로 이룬다. 각 클래스는 책임 하나를 캡슐화하고, 변경 이유가 하나이며, 소수의 다른 클래스와 협력해 시스템 동작을 만든다.

```java
// Bad: 메서드는 셋뿐이지만 변경 이유가 둘이다(재고 규칙, 알림 문구). 설명에도 "그리고"가 필요하다
public class InventoryManager {
    private final Map<String, Integer> stock = new HashMap<>();
    public void decrease(String sku, int qty) { stock.merge(sku, -qty, Integer::sum); }
    public boolean isLow(String sku) { return stock.getOrDefault(sku, 0) < 5; }
    public String lowStockMessage(String sku) {
        return "[재고 부족] " + sku + " 남은 수량 " + stock.getOrDefault(sku, 0);
    }
}

// Good: 책임마다 클래스 하나. 이름이 책임을 그대로 말한다
public class Inventory {
    private final Map<String, Integer> stock = new HashMap<>();
    public void decrease(String sku, int qty) { stock.merge(sku, -qty, Integer::sum); }
    public boolean isLow(String sku) { return quantityOf(sku) < 5; }
    public int quantityOf(String sku) { return stock.getOrDefault(sku, 0); }
}
public class LowStockNotice {
    public String message(String sku, int quantity) { return "[재고 부족] " + sku + " 남은 수량 " + quantity; }
}
```

## Cohesion — 응집도

**어떻게**

- 인스턴스 변수의 수를 적게 유지한다. 각 메서드는 인스턴스 변수를 하나 이상 다뤄야 한다. 일반적으로 메서드가 다루는 인스턴스 변수가 많을수록 그 메서드는 클래스에 더 응집되어 있다. 모든 메서드가 모든 변수를 쓰는 클래스가 응집도가 최대인 클래스다. 다만 그런 클래스는 일반적으로 바람직하지도 가능하지도 않다. 목표는 응집도를 높게 유지하는 것이다.
- 함수를 작게, 매개변수 목록을 짧게 하는 전략을 따르다 보면 일부 메서드만 쓰는 인스턴스 변수가 늘어날 때가 있다. 이는 거의 항상 큰 클래스 안에 적어도 하나의 다른 클래스가 숨어 있다는 뜻이다. 변수와 메서드를 둘 이상의 클래스로 나눠 새 클래스들의 응집도를 높인다.

**왜**

- 응집도가 높다는 것은 클래스의 메서드와 변수가 서로 의존하며 논리적인 한 덩어리로 묶여 있다는 뜻이다.

### Maintaining Cohesion Results in Many Small Classes — 응집도를 유지하면 작은 클래스가 많아진다

**어떻게**

- 큰 함수에서 일부를 떼어 낼 때, 그 부분이 함수 안 지역 변수 넷을 쓴다고 넷을 다 인수로 넘길 필요는 없다. 그 변수들을 인스턴스 변수로 승격하면 인수 없이 떼어 낼 수 있다.
- 그 대가로 몇몇 함수끼리 공유하려고 만든 인스턴스 변수가 쌓여 클래스의 응집도가 떨어진다. 그 몇몇 함수와 공유 변수는 그 자체로 하나의 클래스다. 응집도를 잃으면 클래스를 쪼갠다. 그래서 큰 함수를 작은 함수로 나누는 일은 종종 작은 클래스 여럿을 떼어 낼 기회가 된다. 프로그램 구조가 더 잘 정리되고 투명해진다.
- 나눈 클래스마다 무엇이 바뀌면 그 클래스가 바뀌는지 하나로 말할 수 있어야 한다. 원서 예에서는 함수 하나로 된 프로그램이 실행 환경 처리, 출력 형식, 계산 알고리즘을 맡는 세 클래스로 나뉘고, 각 클래스는 자기 영역(호출 방식, 출력 형식, 알고리즘)이 바뀔 때만 바뀐다.
- 이런 리팩터링은 재작성이 아니다. 먼저 원래 프로그램의 정확한 동작을 검증하는 테스트 묶음을 쓴다. 그다음 아주 작은 변경을 하나씩 하고, 변경할 때마다 실행해 동작이 그대로인지 확인한다. 알고리즘과 동작 방식은 그대로 유지된다.
- 나눈 뒤 코드가 길어지는 것(원서 예: 한 쪽 남짓 → 거의 세 쪽)은 걱정하지 않는다. 늘어난 분량은 더 길고 서술적인 이름, 주석 역할을 하는 함수·클래스 선언, 가독성을 위한 공백과 서식에서 온다.

```java
// Bad: statement() 헬퍼끼리 값을 나누려고 승격한 필드(out, total). cancel()은 쓰지 않는다
public class OrderService {
    private final OrderRepository orders;   // 생성자 생략
    private StringBuilder out;
    private long total;
    public void cancel(OrderId id) { orders.find(id).cancel(); }   // orders만 쓴다
    public String statement(OrderId id) {
        out = new StringBuilder(); total = 0;
        orders.find(id).lines().forEach(this::appendLine);
        return out.append("합계 ").append(total).toString();
    }
    private void appendLine(OrderLine line) {
        out.append(line.name()).append(' ').append(line.amount()).append('\n');
        total += line.amount();
    }
}

// Good: 변수를 공유하던 메서드를 그 변수와 함께 새 클래스로 뗀다. OrderService.statement(id)는 new OrderStatement(orders.find(id)).text()를 반환한다
public class OrderStatement {
    private final StringBuilder out = new StringBuilder();
    private long total;
    public OrderStatement(Order order) { order.lines().forEach(this::appendLine); }
    private void appendLine(OrderLine line) { /* Bad와 같다: out에 한 줄 추가, total 누적 */ }
    public String text() { return out + "합계 " + total; }
}
```

## Organizing for Change — 변경하기 쉬운 클래스

**어떻게**

- 대부분의 시스템은 계속 바뀌고, 변경할 때마다 나머지가 의도대로 동작하지 않을 위험이 따른다. 클래스를 그 위험이 줄어들도록 구성한다. 기능을 추가하려고 클래스를 "열어" 고치면 위험이 생긴다. 같은 클래스의 다른 코드가 깨질 수 있고, 클래스 전체를 다시 테스트해야 한다.
- 한 클래스가 새 종류의 기능을 추가할 때도 바뀌고, 기존 한 종류의 세부를 바꿀 때도 바뀐다면 변경 이유가 둘이므로 SRP 위반이다.
- 클래스의 일부 기능에만 관련된 private 메서드가 보이면 개선할 곳의 후보로 본다. 다만 이것은 찾아내는 데 쓰는 휴리스틱일 뿐이고, 손을 대는 1차 계기는 시스템 변경 자체다. 클래스가 논리적으로 완결되었다고 판단되면 책임을 나눌 걱정은 하지 않아도 된다. 아직 완결되지 않은 클래스라도 가까운 미래에 그 기능을 추가할 일이 없다면 그대로 둔다. 하지만 클래스를 열어 고치고 있는 자신을 발견하는 즉시 설계를 고칠지 검토한다.
- 원서의 해법은 public 메서드(기능 종류) 하나하나를 공통 추상 클래스의 하위 클래스로 빼는 것이다. 특정 종류에만 쓰이던 private 메서드는 그것이 필요한 클래스로 옮기고, 여럿이 공유하는 private 동작은 작은 유틸리티 클래스로 분리한다.
- 기능을 추가하거나 바꿀 때 건드리는 코드가 최소가 되도록 시스템을 구조화한다. 이상적인 시스템에서는 기존 코드를 고치지 않고 시스템을 확장해서 새 기능을 넣는다.

**왜**

- 이렇게 나누면 각 클래스의 코드가 극도로 단순해져 이해하는 데 드는 시간이 거의 없어지고, 한 함수가 다른 함수를 깨뜨릴 위험도 아주 작아진다. 클래스끼리 격리되어 있어 모든 로직을 테스트로 증명하기도 쉽다. 새 종류는 새 클래스로 추가하므로 기존 클래스는 하나도 바뀌지 않고, 다른 코드가 이 변경 때문에 깨지지 않는다.
- 이 구조는 SRP와 함께 OCP(Open-Closed Principle)도 지킨다. 클래스는 "open for extension but closed for modification" (p. 149)이어야 한다.

```java
// Bad: 새 형식(XML)을 넣으려면 이 클래스를 열어야 한다. csvCell은 CSV에만 쓰인다
public class OrderExporter {
    private final List<Order> orders;
    public OrderExporter(List<Order> orders) { this.orders = orders; }
    public String toCsv()  { /* ... csvCell(...) ... */ }
    public String toJson() { /* ... */ }
    private String csvCell(String value) { /* 쉼표·따옴표 이스케이프 */ }
}

// Good: 형식마다 클래스 하나. XML은 XmlOrderExport를 추가할 뿐 기존 클래스는 닫혀 있다
public interface OrderExport { String render(List<Order> orders); }
public class CsvOrderExport implements OrderExport {
    @Override public String render(List<Order> orders) { /* ... csvCell(...) ... */ }
    private String csvCell(String value) { /* CSV 전용 private 메서드는 여기로 */ }
}
public class JsonOrderExport implements OrderExport {
    @Override public String render(List<Order> orders) { /* ... */ }
}
```

## Isolating from Change — 변경으로부터 격리

**어떻게**

- 요구사항이 바뀌면 코드도 바뀐다. 구체 클래스는 구현 세부(코드)를 담고, 추상 클래스는 개념만 나타낸다. 구체 세부에 의존하는 클라이언트 클래스는 그 세부가 바뀔 때 위험해진다. 인터페이스와 추상 클래스를 도입해 구체 세부가 미치는 영향을 격리한다.
- 외부 API처럼 결과가 수시로 바뀌는 구체 클래스에 클라이언트가 직접 의존하게 하지 않는다. 클라이언트에 필요한 개념을 인터페이스로 선언하고(원서 예는 메서드 하나짜리), 구체 클래스가 그것을 구현하게 하며, 클라이언트는 생성자 인수로 그 인터페이스 참조를 받는다.
- 테스트에서는 그 인터페이스의 테스트용 구현을 만들어 값을 고정한다. 테스트용 구현은 단순한 조회 표 수준으로 줄어든다.

**왜**

- 구체 세부에 의존하면 테스트가 어렵다. 몇 분마다 답이 달라지는 대상으로는 테스트를 쓰기 힘들다.
- 이렇게 테스트할 수 있을 만큼 결합이 낮은 시스템은 더 유연하고 재사용하기도 쉽다. 결합이 낮으면 각 요소가 서로로부터, 그리고 변경으로부터 잘 격리되어 각 요소를 이해하기도 쉬워진다.
- 이렇게 결합을 최소화하면 DIP(Dependency Inversion Principle)를 지키게 된다. 요지는 클래스가 구체 세부가 아니라 추상화에 의존해야 한다는 것이다. 인터페이스는 "현재 값을 묻는다"는 추상 개념만 나타내고, 그 값을 어디서 어떻게 얻는지 같은 세부는 모두 감춘다.

```java
// Bad: 실시간 환율 API 클라이언트를 직접 만든다. 테스트할 때마다 결과가 달라진다
public class ForeignOrder {
    private final LiveExchangeRateClient rates = new LiveExchangeRateClient();
    private final List<Item> items = new ArrayList<>();
    public void add(Item item) { items.add(item); }
    public long totalInKrw() {
        return items.stream().mapToLong(i -> i.usdCents() * rates.krwPerUsd() / 100).sum();
    }
}

// Good: "환율을 묻는다"는 개념에만 의존하고, 구현은 생성자로 받는다
public interface ExchangeRates { long krwPerUsd(); }
public class LiveExchangeRateClient implements ExchangeRates { @Override public long krwPerUsd() { /* 외부 API 호출 */ } }
public class ForeignOrder {
    private final ExchangeRates rates;
    public ForeignOrder(ExchangeRates rates) { this.rates = rates; }
    // items, add(), totalInKrw()는 Bad와 같다
}
@Test public void twoTenDollarItemsCost26000WonAtFixedRate() {  // ForeignOrderTest 안. 람다가 환율을 고정한 테스트용 구현이다
    ForeignOrder order = new ForeignOrder(() -> 1300);
    order.add(new Item(1000)); order.add(new Item(1000));
    assertEquals(26_000, order.totalInKrw());
}
```

## 체크리스트

- [ ] 이 클래스를 간결한 이름으로 부를 수 있는가? `Manager`, `Processor`, `Super` 같은 모호한 단어에 기대고 있지 않은가? "if/and/or/but" 없이 25단어 남짓으로 설명할 수 있는가?
- [ ] 이 클래스가 바뀔 이유를 하나만 댈 수 있는가? 서로 독립적으로 생기는 변경 이유가 둘 이상이지 않은가?
- [ ] 일부 메서드만 쓰는 인스턴스 변수 묶음 없이 응집도가 높은가? 함수를 쪼개느라 승격한 필드가 그런 묶음을 만들었다면 그 변수와 메서드를 새 클래스로 뗐는가?
- [ ] 변수 목록 → public 메서드 → 그 메서드가 쓰는 private 유틸리티 순으로 위에서 아래로 읽히는가? public 변수는 없는가?
- [ ] 테스트를 위해 private을 package scope나 protected로 넓혔다면, private을 유지할 다른 방법을 먼저 찾아봤는가?
- [ ] 새 기능을 넣으려고 기존 클래스를 열고 있다면, 새 클래스를 추가하는 것만으로 기능을 넣을 수 있게 설계를 고칠지 검토했는가(논리적으로 완결되었거나 가까운 미래에 바꿀 계획이 없는 클래스는 그대로 둔다)?
- [ ] 외부 API처럼 바뀌기 쉬운 구체 클래스에 직접 의존하지 않고 인터페이스를 생성자로 받는가? 테스트에서 고정값 구현으로 바꿔 끼울 수 있는가?
- [ ] 클래스를 나누는 리팩터링 전에 현재 동작을 고정하는 테스트를 쓰고, 작은 변경마다 테스트를 돌렸는가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)): `G8` Too Much Information, `G10` Vertical Separation, `G17` Misplaced Responsibility, `G23` Prefer Polymorphism to If/Else or Switch/Case, `N1` Choose Descriptive Names
- [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) — 클래스 이름은 명사로, `Manager`·`Processor` 같은 단어는 피한다
- [chapter_03_functions.md](chapter_03_functions.md) — 함수를 작게 만들기, The Stepdown Rule
- [chapter_05_formatting.md](chapter_05_formatting.md) — 신문 기사처럼 위에서 아래로 읽히는 배치, 수직 거리
- [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md) — 새 타입 추가와 새 동작 추가의 비대칭, 다형성이 유리한 경우
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — 테스트를 코드만큼 중요하게 다루는 이유
- [chapter_11_systems.md](chapter_11_systems.md) — 의존성 주입과 시스템 수준의 관심사 분리
- [chapter_12_emergence.md](chapter_12_emergence.md) — Minimal Classes and Methods: SRP를 지나치게 적용해 클래스를 너무 잘게 쪼개지 말라는 원서 자체의 균형추
- [chapter_14_successive_refinement.md](chapter_14_successive_refinement.md) — 테스트로 동작을 고정하고 작은 단계로 리팩터링하기

## 원서 밖 보충

- SRP·OCP·DIP는 LSP·ISP와 함께 SOLID로 묶여 불린다. 다섯 원칙은 이 장이 출처로 드는 Martin의 『Agile Software Development: Principles, Patterns, and Practices』(2002)에 정리되어 있고, SOLID라는 약어는 2004년 무렵 Michael Feathers가 붙였다. Martin은 『Clean Architecture』(2017)에서 SRP를 하나의 actor(같은 변경을 요구하는 이해관계자 집단)에 대해서만 책임지는 것으로 다시 설명한다.
- 인터페이스를 생성자로 받는 방식은 Spring 같은 DI 프레임워크의 생성자 주입과 그대로 맞물린다. 현재 시각에 따라 결과가 달라지는 코드도 `java.time.Clock`을 주입받으면 같은 방법으로 테스트할 수 있다.
- 확장 지점은 추상 클래스보다 인터페이스로 두는 편이 많다(『Effective Java』 3판 아이템 20 "추상 클래스보다는 인터페이스를 우선하라"). 아이템 18 "상속보다는 컴포지션을 사용하라"가 경계하는 것은 다른 패키지의 일반 구체 클래스를 상속하는 경우다. 원서의 예처럼 확장용으로 설계한 추상 클래스를 상속하는 것은 문제 삼지 않는다. 위 OCP 예시는 인터페이스로 썼다.
