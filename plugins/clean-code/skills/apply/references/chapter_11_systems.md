# Chapter 11: Systems — 시스템

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 11, pp. 153–169 · by Kevin Dean Wampler
> 한 줄 요약: 시스템 수준에서도 깨끗하려면 객체 생성·연결(시작)과 런타임 로직(사용)을 분리하고, 도메인 로직은 POJO로 둔 채 횡단 관심사는 비침투적으로 붙여 점진적으로 키울 수 있는 구조를 유지한다.

## 핵심

- 생성과 사용을 분리한다. 객체 생성과 의존성 연결은 main이나 DI 컨테이너에 모으고, 나머지 코드는 필요한 객체가 이미 연결되어 있다고 가정한다. 의존성은 main → 애플리케이션 한 방향으로만 흐른다.
- 클래스는 의존성을 직접 `new`하거나 찾아 나서지 않고 생성자·setter로 받는다(Dependency Injection). 생성 시점을 애플리케이션이 정해야 하면 ABSTRACT FACTORY를 쓴다.
- 도메인 로직은 프레임워크를 모르는 POJO로 쓰고, 영속성·트랜잭션·보안 같은 횡단 관심사(cross-cutting concerns)는 aspect나 aspect류 도구(프록시, DECORATOR)로 비침투적으로 붙인다. 그래야 모든 추상화 수준에서 의도가 분명해진다.
- 처음부터 모든 것을 설계하지 않는다(BDUF). 단순하지만 잘 분리된 구조로 시작해 필요할 때 키우고, 결정은 정보가 충분해지는 가능한 마지막 순간으로 미룬다.
- 표준·프레임워크는 입증할 수 있는 가치가 있을 때 들인다. 도메인 개념은 DSL처럼 도메인 전문가의 말로 읽히게 표현한다.
- 침투적인 아키텍처는 도메인 로직을 가리고 민첩성을 해친다. 도메인 로직이 가려지면 버그가 숨기 쉽고 스토리 구현이 어려워져 품질이 떨어지며, 민첩성을 잃으면 생산성이 떨어지고 TDD의 이점도 사라진다. 시스템이든 모듈이든 "the simplest thing that can possibly work" (p. 169)를 쓴다.

## Separate Constructing a System from Using It — 시스템 생성과 사용을 분리하라

**어떻게**

- 시작 단계(애플리케이션 객체를 만들고 의존성을 연결(wiring)하는 과정)와 시작 뒤에 넘겨받는 런타임 로직을 분리한다. 사용 코드 안에 `if (x == null) x = new 구체클래스(...)` 같은 설정 관용구를 흩뿌리지 않고, 주요 의존성을 해결하는 전역적이고 일관된 전략을 둔다.
- LAZY INITIALIZATION(지연 초기화) 자체를 금지하는 것은 아니다. 실제로 쓸 때까지 생성 비용을 미루고 시작이 빨라지며 null을 돌려주지 않는 장점이 있고, 한 번 쓴 것은 심각한 문제가 아니다. 문제는 이런 작은 관용구가 쌓여 설정 전략이 곳곳에 흩어지고 중복되는 것이다.

**왜**

- 시작 과정은 모든 애플리케이션이 다뤄야 하는 관심사이고, 관심사 분리(separation of concerns)는 가장 오래되고 중요한 설계 기법 중 하나다. 사용 코드가 생성까지 맡으면 구체 클래스와 그 생성자가 요구하는 모든 것에 하드코딩된 의존이 생긴다. 런타임에 그 객체를 한 번도 쓰지 않아도 이 의존을 해결해야 컴파일된다.
- 테스트가 어렵다. 무거운 객체라면 테스트 전에 test double이나 mock을 필드에 넣어 둬야 하고, null 검사 분기까지 모든 실행 경로를 테스트해야 한다.
- 생성과 사용 두 가지를 하므로 Single Responsibility Principle을 작게나마 어긴다. 무엇보다 그 구현이 모든 맥락에 맞는 객체인지 이 클래스는 알 수 없고, 전역 맥락을 알아야 할 이유도 없다.

```java
// Bad: 사용 코드가 생성까지 맡는다 (구체 클래스 하드코딩 + 지연 초기화)
public class MembershipService {
    private PointLedger ledger;
    public void grantSignupBonus(MemberId id) {
        if (ledger == null)
            ledger = new JdbcPointLedger(DataSources.primary()); // 모든 상황에 맞는 선택일까?
        ledger.credit(id, 1_000);
    }
}

// Good: 완전히 수동적이다. 무엇을 넣을지는 main이나 DI 컨테이너가 정한다
public class MembershipService {
    private final PointLedger ledger;
    public MembershipService(PointLedger ledger) { this.ledger = ledger; }
    public void grantSignupBonus(MemberId id) { ledger.credit(id, 1_000); }
}
```

### Separation of Main · Factories

- 생성에 관한 모든 것을 main이나 main이 호출하는 모듈로 옮기고, 나머지 시스템은 모든 객체가 이미 만들어지고 연결되었다고 가정하고 설계한다.
- main과 애플리케이션 사이 경계를 넘는 의존성 화살표는 모두 main에서 멀어지는 쪽을 향한다. 애플리케이션은 main이나 생성 과정을 모르고, 모든 것이 제대로 만들어졌다고 기대할 뿐이다. 제어 흐름도 따라가기 쉽다(아래 예시의 `Application.main`).
- 객체를 *언제* 만들지는 애플리케이션이 정해야 할 때가 있다. 이때 ABSTRACT FACTORY 패턴을 쓴다. 팩토리 인터페이스는 애플리케이션 쪽에, 구현은 main 쪽에 둔다.
- 애플리케이션은 생성 시점을 완전히 통제하고 애플리케이션 고유의 생성 인수도 넘기지만, 만드는 방법의 세부는 모른다. 의존성은 여전히 main → 애플리케이션 방향이다.

```java
// 애플리케이션 쪽: 언제, 어떤 인수로 만들지는 애플리케이션이 정한다
public interface TicketFactory { Ticket issue(ReservationId reservationId, Seat seat); }
public class BookingService {
    private final TicketFactory tickets;
    public BookingService(TicketFactory tickets) { this.tickets = tickets; }
    public List<Ticket> confirm(Reservation r) {
        return r.seats().stream().map(seat -> tickets.issue(r.id(), seat)).toList();
    }
}
// main 쪽: 어떻게 만들지(서명 방식 등)는 팩토리 구현이 숨기고, 생성과 연결은 모두 main에서 한다
public class QrTicketFactory implements TicketFactory {
    private final QrSigner signer;
    public QrTicketFactory(QrSigner signer) { this.signer = signer; }
    public Ticket issue(ReservationId id, Seat seat) { return new Ticket(id, seat, signer.sign(id, seat)); }
}
public final class Application {
    public static void main(String[] args) {
        var booking = new BookingService(new QrTicketFactory(new QrSigner(QrKey.from(args))));
        new HttpServer(booking).start(); // 여기부터는 사용만 한다
    }
}
```

### Dependency Injection

- DI는 Inversion of Control(IoC)을 의존성 관리에 적용한 것이다. 객체는 의존성을 스스로 인스턴스화하지 않고, 그 책임을 전담하는 메커니즘에 넘겨 제어를 역전한다. 설정은 전역 관심사이므로 이 메커니즘은 대개 main 루틴이나 특수 목적 컨테이너다. IoC는 부차적 책임을 전담 객체로 옮겨 SRP를 돕는다.
- 진정한 DI에서 클래스는 의존성을 해결하려고 아무것도 하지 않는다. 생성자 인수나 setter(또는 둘 다)만 제공하고, 컨테이너가 필요한 객체를 (대개 필요할 때) 만들어 연결한다. 어떤 객체를 쓸지는 설정 파일이나 특수 목적 생성 모듈에서 지정한다. 반면 JNDI 같은 이름 조회(`(PointLedger) registry.lookup("pointLedger")`)는 부분적 DI다. 돌려받는 구체 타입은 호출자가 정하지 않지만 호출자가 여전히 능동적으로 의존성을 해결한다.
- 지연 초기화가 필요하면 사용 코드에 null 검사를 넣지 말고 DI 컨테이너에서 얻는다. 원서는 이 관용구가 DI에서도 가끔 쓸모 있다고 본다. 대부분의 DI 컨테이너는 필요할 때까지 객체를 만들지 않고, 많은 컨테이너가 팩토리 호출이나 프록시 생성 수단을 제공해 지연 평가 같은 최적화에 쓸 수 있다. 다만 지연 생성은 최적화일 뿐이고 때 이른 최적화일 수도 있다.

## Scaling Up — 확장

**어떻게**

- 시스템을 처음부터 '제대로' 만들 수 있다는 생각을 버린다. 오늘의 스토리만 구현하고, 내일의 새 스토리에 맞춰 리팩터링하고 확장한다. 코드 수준에서는 TDD·리팩터링·클린 코드가 이를 가능하게 한다.
- 시스템 수준에서도 이 방식이 통하도록 관심사 분리를 유지한다. 비즈니스 로직이 컨테이너 타입을 상속하거나 컨테이너가 요구하는 생명주기 메서드를 줄줄이 구현해야 하는 침투적 구조를 만들지 않는다.

**왜**

- 도시도 작은 마을에 미래를 대비한 6차선 도로를 미리 놓지 않고, 인구가 늘 때 길을 넓히며 자란다. 물리 시스템과 달리 소프트웨어는 관심사를 적절히 분리해 두면 아키텍처 수준에서도 점진적으로 자랄 수 있다.
- 원서의 반례는 EJB2다. 비즈니스 로직이 무거운 컨테이너에 강하게 묶여 격리된 단위 테스트가 어렵고 EJB2 밖 재사용은 사실상 불가능했으며, 행위 없는 DTO와 데이터 복사용 보일러플레이트가 늘었다.

### Cross-Cutting Concerns

- 영속성·트랜잭션·보안처럼 도메인 객체의 자연스러운 경계를 가로지르는 관심사를 횡단 관심사라 한다. 보통 모든 객체에 대체로 같은 전략(같은 DBMS, 테이블·컬럼 명명 규칙, 일관된 트랜잭션 의미)을 쓰려 한다. 원리상 이 전략은 한 모듈로 다룰 수 있지만, 실제로는 거의 같은 코드를 많은 객체에 퍼뜨리게 된다. 영속성 프레임워크도 도메인 로직도 따로 보면 모듈이고, 문제는 둘이 세밀하게 교차하는 지점이다.
- EJB2도 트랜잭션·보안·일부 영속성 동작을 소스 코드가 아닌 배포 서술자(deployment descriptor)에 선언했다는 점에서는 관심사 분리에 가까웠고, 원서는 이를 aspect-oriented programming(AOP)을 '예견'한 방식으로 본다. 문제는 선언이 아니라 비즈니스 로직을 컨테이너에 묶는 침투성이었다.
- AOP는 횡단 관심사의 모듈성을 되찾는 범용 접근이다. aspect라는 모듈 단위가 시스템의 어떤 지점들의 동작을 일관되게 바꿀지를 간결한 선언적·프로그램적 방식으로 지정한다. 예를 들어 어떤 객체·속성을 저장할지만 선언하고 실제 작업은 영속성 프레임워크에 맡긴다. 대상 소스는 손으로 고치지 않는다(noninvasive).

## Java Proxies · Pure Java AOP Frameworks · AspectJ Aspects — 횡단 관심사를 붙이는 수단

**어떻게**

- 도메인 로직은 POJO(Plain Old Java Object)로 쓴다. POJO는 자기 도메인에만 집중하고 엔터프라이즈 프레임워크나 다른 어떤 도메인에도 의존하지 않는다.
- 영속성·트랜잭션·보안·캐시·장애 조치(failover) 같은 인프라는 선언적 설정이나 API로 붙이고, 그 선언이 DI 컨테이너를 움직여 주요 객체를 만들고 연결하게 한다. 컨테이너에 의존하는 코드는 최상위 객체를 요청하는 몇 줄로 줄여, 애플리케이션을 프레임워크와 거의 완전히 떼어 놓는다.
- 프레임워크 메타데이터는 어노테이션 안에 가두고 로직에 섞지 않는다. 원하면 XML로 옮겨 순수 POJO로 만들 수 있다. 매핑이 자주 바뀌지 않으면 많은 팀이 어노테이션을 그대로 두는 쪽을 택할 수 있다. 그래도 EJB2식 침투보다 해가 훨씬 적다(원서의 EJB3 사례).
- AOP를 그 구현 기법(메서드 가로채기, 프록시로 감싸기)과 혼동하지 않는다. 도구는 다음처럼 고른다.
  - JDK dynamic proxy: 개별 객체·클래스의 메서드 호출을 감싸는 단순한 경우. 인터페이스에만 동작하고, 클래스를 감싸려면 CGLIB·ASM·Javassist 같은 바이트코드 라이브러리가 필요하다.
  - Spring AOP·JBoss AOP 같은 pure Java AOP 프레임워크: 프록시 보일러플레이트 대부분을 대신 처리하며, aspect가 가장 쓸모 있는 경우의 80~90%에 충분하다.
  - AspectJ: aspect를 일급 모듈 단위로 지원하는 가장 강력한 도구지만 새 도구와 언어 구성·관용구를 익혀야 한다. 어노테이션 형식이 이 부담을 일부 덜었다.

**왜**

- POJO는 개념적으로 단순하고 test drive하기 쉽다. 스토리를 올바르게 구현했는지 확인하기 쉽고, 다음 스토리에 맞춰 유지하고 발전시키기도 쉽다.
- 클라이언트는 POJO를 부른다고 믿지만 실제로는 기본 동작을 넓히는 중첩 DECORATOR('러시아 인형')의 바깥 껍질을 호출한다. 그래서 트랜잭션·캐시 같은 동작을 도메인 코드를 고치지 않고 더할 수 있다.
- 프록시를 직접 쓰면 단순한 경우에도 코드가 많고 복잡해 깨끗하게 유지하기 어렵다. 또 프록시만으로는 시스템 전반의 적용 지점을 지정할 수 없어 진정한 AOP가 되지 못한다. AOP의 가치는 시스템 전반의 동작을 간결하고 모듈화된 방식으로 지정하는 데 있다. 설정 파일이 장황해도 거기 적힌 '정책'은 그 뒤에서 자동으로 생기는 프록시·aspect 로직보다 단순하다.

```java
// Bad: 도메인 로직에 트랜잭션 처리가 섞이고, 같은 틀이 클래스마다 반복된다
public class StockInventory implements Inventory {
    private final StockRepository stocks; private final TxManager tx; // 생성자 생략
    public void reserve(Sku sku, int qty) {
        tx.begin();
        try { stocks.find(sku).decrease(qty); tx.commit(); }
        catch (RuntimeException e) { tx.rollback(); throw e; }
    }
}

// Good: 도메인은 POJO로 두고, 조립(main·DI 설정)에서 같은 Inventory를 구현한 바깥 껍질(DECORATOR)로 감싼다
public class StockInventory implements Inventory {
    private final StockRepository stocks; // 생성자 생략
    public void reserve(Sku sku, int qty) { stocks.find(sku).decrease(qty); }
}
public class TransactionalInventory implements Inventory { // 조립: new TransactionalInventory(new StockInventory(stocks), tx)
    private final Inventory target; private final TxManager tx; // 생성자 생략
    public void reserve(Sku sku, int qty) {
        tx.begin();
        try { target.reserve(sku, qty); tx.commit(); }
        catch (RuntimeException e) { tx.rollback(); throw e; }
    }
}
// 손으로 쓰든 JDK 동적 프록시로 만들든 이런 껍질은 코드가 많고 복잡하며 시스템 전반의 적용 지점을 지정할 수 없다. 그래서 AOP 선언으로 붙인다
```

## Test Drive the System Architecture — 시스템 아키텍처를 테스트 주도로 키워라

**어떻게**

- 관심사별로 모듈화한 영역을 각각 아키텍처 관심사와 떨어진 POJO로 구현하고, 침투를 최소화한 aspect(또는 aspect류 도구)로 통합한다. 원서는 이것을 최적의 아키텍처로 보며, 이런 아키텍처는 코드처럼 test drive할 수 있다. 순진할 만큼 단순하지만 결합도가 낮은 구조로 시작해 동작하는 스토리를 빨리 내놓고, 규모가 커질 때 필요한 기술·인프라를 그때 들인다.
- Big Design Up Front(BDUF), 즉 무엇이든 구현하기 전에 모든 것을 설계하는 방식을 피한다. 원서는 이것을 바람직한 사전 설계(up-front design)와 구분한다. 방향 없이 시작하라는 뜻도 아니다. 범위·목표·일정과 시스템의 대략적 구조에 대한 기대는 갖되, 상황이 바뀌면 방향을 틀 능력을 지킨다.
- 필요하지 않은 API는 잘 설계되었더라도 과할 수 있다. "A good API should largely disappear from view most of the time" (p. 167). 팀의 창의적 노력 대부분은 구현 중인 스토리에 쓰여야 한다.

**왜**

- BDUF는 변화에 적응하지 못하게 한다. 이미 들인 노력을 버리기 싫은 심리적 저항이 생기고, 먼저 고른 아키텍처가 이후의 설계 사고를 끌고 간다.
- 건물은 공사가 한참 진행되면 근본적 구조 변경이 불가능해 BDUF를 할 수밖에 없다. 소프트웨어는 구조가 관심사를 효과적으로 분리하고 있으면 근본적 변경도 경제적으로 가능하다.

## Optimize Decision Making · Use Standards Wisely, When They Add Demonstrable Value — 결정은 늦게, 표준은 가치가 입증될 때

**어떻게**

- 영속성·캐시·보안 같은 기술 결정이 도메인 코드에 새지 않도록 관심사를 모듈로 나누고 도메인은 POJO로 유지한다. 그래야 그 결정을 가능한 마지막 순간까지 미루고, 규모가 커질 때 필요한 인프라를 그때 고를 수 있다.
- 표준이라는 이유만으로 채택하지 않는다. 더 가볍고 단순한 설계로 충분한지 먼저 따진다(원서의 예: 표준이라서 EJB2를 고른 팀들). 과대 선전된 표준에 매달려 고객 가치 구현을 놓치지 않는다.

**왜**

- 충분히 큰 시스템에서는 한 사람이 모든 결정을 내릴 수 없다. 모듈성과 관심사 분리가 분산된 결정을 가능하게 해, 각 결정을 가장 적합한 사람에게 맡길 수 있다.
- 미루는 것은 게으름이 아니라 최선의 정보로 고르려는 것이다. 이른 결정은 고객 피드백·숙고·구현 경험이 그만큼 모자란 상태에서 내린 결정이다. 모듈화된 POJO 시스템은 최신 지식에 근거한 just-in-time 결정을 가능하게 하고 결정의 복잡도도 줄인다.
- 표준은 아이디어와 컴포넌트 재사용, 경험자 채용, 좋은 아이디어의 캡슐화, 컴포넌트 연결을 쉽게 한다. 그러나 표준을 만드는 데 업계가 기다리기 힘들 만큼 오래 걸릴 때가 있고, 어떤 표준은 채택자의 실제 필요와 동떨어진다.

## Systems Need Domain-Specific Languages — 시스템에는 도메인 특화 언어가 필요하다

**어떻게**

- 도메인 전문가가 쓸 법한 구조화된 산문처럼 읽히는 Domain-Specific Language(DSL)로 도메인 로직을 표현한다. DSL은 별도의 작은 스크립트 언어일 수도, 표준 언어 안의 API일 수도 있다(원서는 JMock을 DSL을 만드는 Java API의 예로 든다).

**왜**

- 좋은 DSL은 도메인 개념과 그것을 구현한 코드 사이의 의사소통 간극을 줄여, 도메인을 구현으로 잘못 옮길 위험을 낮춘다. 효과적으로 쓴 DSL은 추상화 수준을 코드 관용구와 디자인 패턴 위로 올리고 알맞은 수준에서 의도를 드러낸다. 고수준 정책부터 저수준 세부까지 모든 추상화 수준과 도메인을 POJO로 표현하게 해 준다.

```java
// Bad: 할인 규칙이 비교 연산과 날짜 계산에 묻혀 있다
boolean eligible = member.grade() == Grade.GOLD
        && member.joinedAt().isBefore(today.minusYears(1))
        && order.total().compareTo(Money.won(50_000)) >= 0;
if (eligible) order.applyDiscount(Percent.of(10));

// Good: 마케팅 담당자가 규칙을 말하는 방식대로 읽히는 내부 DSL
DiscountPolicy loyalGoldDiscount = discount(Percent.of(10))
        .when(gradeIs(GOLD))
        .and(memberLongerThan(Period.ofYears(1)))
        .and(orderTotalAtLeast(Money.won(50_000)));
loyalGoldDiscount.applyTo(order, member, today);
```

## 체크리스트

- [ ] 비즈니스 로직이 협력 객체(서비스·저장소·외부 연동)의 구현체를 직접 `new`하거나 이름으로 조회하거나 `if (x == null) x = new ...`로 지연 초기화하지 않는가? 의존성을 생성자(또는 setter)로 받아 테스트에서 test double을 바로 넣을 수 있는가?
- [ ] 객체 생성과 연결이 main(또는 그것이 부르는 구성 모듈·DI 설정)에 모여 있고 애플리케이션 코드는 그쪽을 참조하지 않는가? 생성 시점을 애플리케이션이 정해야 하는 객체는 팩토리 인터페이스로 만들고 구현을 main 쪽에 두었는가?
- [ ] 도메인 클래스가 프레임워크 타입을 상속하거나 프레임워크 생명주기 메서드를 구현하지 않는가? 컨테이너 없이 단위 테스트할 수 있는가?
- [ ] 트랜잭션·보안·영속성·캐시 코드가 여러 도메인 메서드에 반복되지 않는가? 그런 횡단 관심사는 한 곳(aspect·DECORATOR·선언적 설정)에서 붙였는가?
- [ ] 지금 스토리에 필요하지 않은 인프라·표준·프레임워크를 미리 들이고 있지 않은가? 미뤄도 되는 결정을 지금 굳히고 있지 않은가?
- [ ] 도메인 규칙이 도메인 전문가의 말로 읽히는가?

## 관련

- Chapter 17 휴리스틱: `G35` Keep Configurable Data at High Levels — 설정값은 main처럼 높은 수준에서 읽어 아래로 넘긴다. `G6` Code at Wrong Level of Abstraction — 생성 세부와 도메인 로직을 섞지 않는다. `G5` Duplication — 흩어진 설정 관용구와 반복되는 횡단 관심사 코드. `G30` Functions Should Do One Thing — 생성과 사용을 함께 하는 메서드.
- [chapter_10_classes.md](chapter_10_classes.md) — SRP, 구체 클래스 대신 추상화에 의존해 변경으로부터 격리하기
- [chapter_08_boundaries.md](chapter_08_boundaries.md) — 서드파티 프레임워크를 경계 뒤에 가두기
- [chapter_12_emergence.md](chapter_12_emergence.md) — 단순한 설계 규칙과 점진적으로 드러나는 설계
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — 테스트 코드에서 쓰는 도메인 특화 언어

## 원서 밖 보충

- 원서의 Spring XML 설정과 `XmlBeanFactory`는 낡았다(`XmlBeanFactory`는 Spring 3.1부터 deprecated). 지금은 `@Configuration`·`@Bean` Java 설정과 component scan을 주로 쓰고, 필수 의존성은 생성자 주입이 권장된다. 필드 주입은 의존성을 감추고 컨테이너 없이 테스트하기 어렵게 한다. 비즈니스 코드에서 `ApplicationContext.getBean(...)`을 부르면 이름 조회(부분적 DI)로 되돌아간다.
- 원서 예제의 `XmlBeanFactory` 같은 순수 `BeanFactory`는 `getBean` 시점에 객체를 만들지만, 오늘날 주로 쓰는 `ApplicationContext`(Spring Boot 포함)는 singleton bean을 시작 시점에 미리 만든다. 지연 생성은 `@Lazy`(Spring Boot는 `spring.main.lazy-initialization`)로 따로 지정한다.
- Spring AOP는 프록시 기반이라 같은 클래스 안에서 `this`로 부르는 자기 호출(self-invocation)에는 `@Transactional` 같은 aspect가 적용되지 않는다. Spring Boot 2.0부터는 기본으로 CGLIB 클래스 프록시를 쓴다. JBoss AOP는 더 이상 유지되지 않으므로, 지금 pure Java 방식의 선택지는 사실상 Spring AOP이고 그 밖에는 AspectJ 위빙을 쓴다.
- main 쪽의 조립 지점을 요즘은 Composition Root라 부르기도 한다. 의존성이 도메인 쪽으로만 향하게 하는 생각은 Hexagonal Architecture·Clean Architecture로 이어진다. EJB3·JPA 어노테이션은 Jakarta EE 9부터 `jakarta.*` 패키지로 옮겨졌다.
- 체크리스트 1번의 대상은 협력 객체다. 값 객체·엔티티처럼 협력 객체가 아닌 것은 사용 코드에서 직접 생성해도 된다.
