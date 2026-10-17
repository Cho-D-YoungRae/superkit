# Chapter 3: Functions — 함수

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 3, pp. 31–52
> 한 줄 요약: 함수는 작게 만들어 한 가지만 하게 하고, 인수·부수 효과·오류 코드처럼 읽는 사람을 멈칫하게 하는 요소를 덜어 낸다.

## 핵심

- 함수는 작게, 그보다 더 작게 만든다. 저자는 "Functions should hardly ever be 20 lines long." (p. 34)라고 쓰고, 2~4줄짜리 함수를 본보기로 든다.
- 본문이 함수 이름 바로 아래 추상화 수준의 단계만 담으면 한 가지 일을 한다. 코드는 위에서 아래로 한 단계씩 내려가며 읽히게 둔다(The Stepdown Rule).
- 인수는 적을수록 좋다. 0개가 이상적이고, 3개는 가능하면 피하며, 그 이상은 쓰지 않는다. 플래그 인수와 출력 인수는 피한다.
- 이름이 말하지 않는 부수 효과를 숨기지 않는다. 상태를 바꾸는 명령과 값을 돌려주는 조회를 한 함수에 섞지 않는다.
- 오류 코드 대신 예외를 쓰고, try/catch 본문은 별도 함수로 뽑는다. 오류를 처리하는 함수는 오류 처리만 한다.
- 저자도 처음부터 이렇게 짜지 않으며, 그럴 수 있는 사람은 없다고 본다. 테스트로 받쳐 둔 초안을 다듬어 규칙에 맞춘다.
- 함수는 시스템을 설명하는 도메인 언어의 동사다. 진짜 목표는 함수들이 맞물려 시스템의 이야기를 정확히 들려주게 하는 것이다.

## Small! — 작게 만들어라

**어떻게**

- 함수는 작게 만들고, 다 만든 뒤에도 더 줄일 수 있는지 본다. 화면에 100줄이 들어가는 환경이라도 한 줄을 150자로, 함수를 100줄로 쓰지 않는다. 20줄에 이르는 함수도 거의 없어야 한다.
- 저자가 본보기로 드는 크기는 함수마다 2~4줄이다. 각 함수가 한눈에 이해되고, 이야기 하나를 들려주고, 다음 함수로 자연스럽게 이끈다. 저자는 긴 함수를 9줄로 줄인 뒤, 함수는 대개 이 9줄보다도 짧아야 한다며 한 번 더 줄인다.
- Blocks and Indenting: if·else·while 블록 안은 한 줄로 만든다. 그 한 줄은 아마도(probably) 서술적인 이름을 가진 함수 호출이 된다. 함수가 중첩 구조를 담을 만큼 커지지 않게 하고, 들여쓰기 수준은 한두 단계를 넘기지 않는다.

**왜**

- 추상화 수준이 여러 겹 섞이고 이상한 문자열과 플래그로 조종되는 중첩 if가 든 긴 함수는 몇 분을 들여다봐도 이해하기 어렵다. 메서드 추출·이름 변경·약간의 재구성만으로 줄인 짧은 함수는 세부를 몰라도 무엇을 하는지 짐작하게 해 준다. 작게 만드는 목적은 함수가 의도를 전달하게 하는 데 있다. 다만 저자는 아주 작은 함수가 더 낫다는 주장을 뒷받침할 연구를 댈 수 없다고 스스로 밝힌다. 근거는 3,000줄짜리부터 100~300줄, 20~30줄짜리까지 써 본 약 40년의 시행착오다.
- 블록 안을 함수 호출 하나로 두면 감싸는 함수가 작게 유지되고, 호출되는 함수의 이름이 문서 역할을 한다.

## Do One Thing — 한 가지만 해라

**어떻게**

- 함수는 한 가지를 하고, 그 일을 잘하고, 그 일만 한다. '한 가지'인지는 함수를 'TO 함수이름, …한다' 꼴의 짧은 문단(TO paragraph)으로 풀어 판단한다(TO는 LOGO 언어에서 함수 정의를 시작하던 키워드). 예: 'TO placeOrder, 주문을 검증하고 합계를 매겨 저장한 뒤 고객에게 알린다'(아래 예시). 본문 단계가 모두 함수 이름보다 딱 한 단계 낮은 추상화 수준이면, 단계가 여럿으로 보여도 한 가지 일이다.
- 구현을 되풀이할 뿐인 이름이 아니라 의미 있는 이름으로 함수를 하나 더 뽑아낼 수 있다면 여러 일을 하는 것이다. if 문 하나를 '~이면 ~한다' 식 이름으로 감싸는 것은 추상화 수준을 바꾸지 않으므로 해당하지 않는다.
- Sections within Functions: 함수가 선언·초기화·본처리처럼 구역으로 나뉜다면 여러 일을 한다는 뚜렷한 증상이다. 한 가지만 하는 함수는 무리 없이 구역으로 나눌 수 없다.

**왜**

- 함수를 만드는 이유는 큰 개념(곧 함수 이름)을 다음 추상화 수준의 단계들로 나누기 위해서다. 여러 수준의 단계가 섞여 있다면 그 분해가 덜 끝난 것이다.

## One Level of Abstraction per Function — 함수당 추상화 수준은 하나로

**어떻게**

- 한 함수 안의 문장은 모두 같은 추상화 수준에 둔다. 주문 저장·고객 알림 같은 높은 개념, 합계 계산 같은 중간 개념, 금액 뒤에 "원"과 줄바꿈을 붙이는 낮은 세부를 한 함수에 섞지 않는다.
- Reading Code from Top to Bottom: The Stepdown Rule — 각 함수 바로 뒤에 한 단계 낮은 추상화 수준의 함수가 오게 배치해, 함수 목록을 위에서 아래로 읽으면 추상화 수준이 한 단계씩 내려가게 한다. 프로그램이 TO 문단의 연속처럼, 각 문단이 현재 수준을 설명하고 한 단계 아래 문단을 참조하는 식으로 읽혀야 한다.

**왜**

- 수준이 섞이면 읽는 사람은 어느 표현이 핵심 개념이고 어느 것이 세부인지 구분하지 못할 수 있다. 깨진 창문처럼, 세부가 한번 섞이면 더 많은 세부가 함수에 쌓이는 경향이 있다. 저자는 이 규칙을 익히기가 매우 어렵다고 인정하면서도, 함수를 짧게 유지하고 한 가지만 하게 하는 열쇠라고 본다.

```java
// Bad: 검증·합계 계산·저장·메일 문구 조립이 서로 다른 수준으로 섞여 있다
public void placeOrder(Order order) {
    if (order.items().isEmpty()) throw new EmptyOrderException(order.id());
    long total = 0;
    for (OrderItem item : order.items()) total += item.price() * item.quantity();
    order.setTotal(total);
    orderRepository.save(order);
    mailer.send(order.customerEmail(), "주문 " + order.id() + " 결제 금액: " + total + "원\n");
}

// Good: 이름 한 단계 아래의 일만 나열하고, 세부는 바로 아래 함수로 내려보낸다
public void placeOrder(Order order) {
    validate(order);
    order.setTotal(totalPriceOf(order));
    orderRepository.save(order);
    notifyCustomer(order);
}
private void validate(Order order) {
    if (order.items().isEmpty()) throw new EmptyOrderException(order.id());
}
private long totalPriceOf(Order order) {
    return order.items().stream().mapToLong(i -> i.price() * i.quantity()).sum();
}
private void notifyCustomer(Order order) {
    mailer.send(order.customerEmail(), "주문 " + order.id() + " 결제 금액: " + order.total() + "원\n");
}
```

## Switch Statements — switch 문

**어떻게**

- switch 문(if/else 사슬 포함)은 작게 만들기 어렵고, 본질적으로 N가지 일을 한다. case가 둘뿐이어도 저자가 바라는 블록·함수 크기보다 크다. 늘 피할 수는 없으므로 저수준 클래스에 묻고 반복하지 않는다. 수단은 다형성이다. 타입별 switch는 팩토리(원서는 ABSTRACT FACTORY) 안에 한 번만 두어 알맞은 하위 타입 인스턴스를 만들게 하고, 타입별 동작은 인터페이스를 통해 다형적으로 호출한다.
- 저자의 일반 규칙: switch가 한 번만 나오고, 다형적 객체를 만드는 데 쓰이고, 상속 관계 뒤에 숨어 나머지 시스템에 보이지 않으면 참는다. 상황은 저마다 다르고 저자 자신도 이 규칙의 일부를 어길 때가 있다고 덧붙인다.

**왜**

- 타입별 switch가 든 함수는 크고, 새 타입이 생길 때마다 커진다. 한 가지 이상을 하고, 바뀔 이유가 여럿이라 Single Responsibility Principle(SRP)을 어기며, 새 타입마다 고쳐야 하니 Open Closed Principle(OCP)을 어긴다. 아마 가장 큰 문제는 같은 구조의 switch를 가진 함수가 연산마다 끝없이 생길 수 있다는 점이다.

```java
// Bad: 결제 수단별 switch가 수수료·환불·정산일 같은 연산마다 되풀이된다
public Money feeOf(PaymentRecord r) {
    switch (r.method()) {
        case CARD:     return r.amount().percent(3);
        case TRANSFER: return Money.won(500);
        default: throw new UnknownPaymentMethodException(r.method());
    }
}

// Good: switch는 팩토리에 한 번만 두고, 연산은 다형적으로 호출한다
public interface Payment { Money fee(); }  // 환불·정산일 같은 연산도 여기에 더한다
public class TransferPayment implements Payment { public Money fee() { return Money.won(500); } }
public class PaymentFactory {
    public Payment create(PaymentRecord r) {
        switch (r.method()) {
            case CARD:     return new CardPayment(r.amount());  // fee(): 결제액의 3%
            case TRANSFER: return new TransferPayment();
            default: throw new UnknownPaymentMethodException(r.method());
        }
    }
}
Money fee = paymentFactory.create(record).fee();  // 호출부: feeOf(record)를 대체한다
```

## Use Descriptive Names — 서술적인 이름을 사용하라

**어떻게**

- 함수가 하는 일을 잘 설명하는 이름을 붙인다. 이름이 길어지는 것을 두려워하지 않는다. 길고 서술적인 이름은 짧고 수수께끼 같은 이름보다, 길고 서술적인 주석보다 낫다. 여러 단어가 잘 읽히는 명명 관례를 쓴다. 이름 고르는 데 시간을 들여, 후보를 여러 개 넣어 코드를 읽어 보고 IDE의 이름 바꾸기로 가장 서술적인 이름을 찾을 때까지 실험한다.
- 한 모듈의 함수 이름에는 같은 구문·명사·동사를 일관되게 쓴다. `reserveStock`, `reserveStockForPreorder`가 보이면 읽는 사람은 `releaseStock`, `releaseStockForPreorder`도 있으리라 예상하고, 그 예상이 맞아야 한다.

**왜**

- Ward Cunningham의 원칙([chapter_01_clean_code.md](chapter_01_clean_code.md))대로, 읽는 루틴마다 대체로 예상한 대로 동작하면 깨끗한 코드다. 이를 이루는 일의 절반이 한 가지만 하는 작은 함수에 좋은 이름을 고르는 것이고, 함수가 작고 좁을수록 이름 짓기도 쉽다. 서술적인 이름을 고르다 보면 모듈 설계가 머릿속에서 정리되고, 좋은 이름을 찾다가 코드 구조가 나아지는 일도 드물지 않다.

## Function Arguments — 함수 인수

**어떻게**

- 인수 개수는 0개(niladic)가 이상적이고, 다음이 1개(monadic), 바로 뒤가 2개(dyadic)다. 3개(triadic)는 가능하면 피한다. 4개 이상(polyadic)은 아주 특별한 이유가 있어야 하고, 그래도 쓰지 않는 편이 낫다. 여러 함수가 함께 쓰는 값은 인수로 넘겨 다니기보다 인스턴스 변수로 두는 것을 고려한다.
- Common Monadic Forms: 단항 함수는 인수에 대해 질문하거나(`boolean isExpired(Coupon c)`) 인수를 변환해 반환하는(`Money toKrw(Money usd)`) 경우가 흔하다. 이름으로 둘을 구별하고 일관된 맥락에서 쓴다. 입력만 받아 시스템 상태를 바꾸는 이벤트 형식(`void paymentDeclined(int declineCount)`)은 이벤트임이 분명하도록 이름과 맥락을 골라 조심해서 쓴다. 이 밖의 형식은 피한다. 변환 결과는 출력 인수가 아니라 반환값으로 내보낸다(구현이 입력을 그대로 돌려줄 뿐이어도 그렇다).
- Flag Arguments: boolean 인수를 넘기지 않는다. 플래그 값에 따라 하는 일이 갈린다면 함수를 둘로 나눈다. 저자도 기존 호출부가 이미 플래그를 넘기고 있어 리팩터링 범위를 그 함수와 그 아래 함수로 제한했을 때는 플래그를 남겼지만, 그래도 둘로 나눴어야 한다고 말한다.
- Dyadic Functions: 이항 함수는 단항보다 이해하기 어렵다. 나쁜 것은 아니고 반드시 쓰게 되지만 비용이 있다. `new Point(x, y)`처럼 두 인수가 한 값의 순서 있는 구성 요소라면 자연스럽지만, `assertEquals(expected, actual)`처럼 순서가 관례일 뿐이면 자주 뒤바뀐다. 함수를 인수 중 하나(쓰기 대상처럼 함수가 작용하는 객체)의 메서드로 옮기거나, 그 인수를 현재 클래스의 멤버 변수로 만들거나, 그 인수를 생성자로 받는 새 클래스를 뽑아 단항으로 바꿀 수 있다.
- Triads: 삼항은 순서 혼동, 읽다 멈칫하는 일, 인수를 무시하게 되는 문제가 두 배 이상이므로 만들기 전에 매우 신중히 생각한다. 다만 오차 범위를 받는 부동소수점 단언처럼 멈칫할 가치가 있는 삼항도 있다.
- Argument Objects: 인수가 두세 개보다 많이 필요해 보이면 일부를 클래스로 묶을 때일 가능성이 크다. 함께 넘어가는 변수 묶음은 대개 따로 이름을 붙일 만한 개념의 일부이므로 묶는 것은 속임수가 아니다(`reserve(room, checkIn, checkOut)` 대신 숙박 기간에 이름을 붙인 `reserve(room, stayPeriod)`).
- Argument Lists: 똑같이 취급되는 가변 인수는 `List` 하나와 같다(`String.format(String, Object...)`는 사실상 이항). 같은 규칙이 적용되므로 가변 인수 함수도 삼항까지만 쓴다.
- Verbs and Keywords: 단항 함수는 이름과 인수가 동사/명사 쌍을 이루게 한다(`charge(amount)`보다 금액의 정체까지 알리는 `chargeDeposit(amount)`). 키워드 형식은 인수 이름을 함수 이름에 넣어 순서를 기억할 부담을 던다(`transferPointsFromSenderToReceiver(sender, receiver)`).

**왜**

- 인수는 개념적으로 큰 부담이다. 넘겨 다니는 버퍼처럼 함수 이름과 다른 추상화 수준에 있는 인수는 그 지점에서 중요하지 않은 세부를 알도록 강요하고, 읽는 사람이 볼 때마다 다시 해석하게 만든다. 또 인수가 늘수록 테스트할 값 조합이 벅차게 늘어난다. 사람은 정보가 인수로 들어가 반환값으로 나온다고 기대하므로 출력 인수는 다시 읽게 만든다. 읽다가 무시하는 법을 배운 인수에는 버그가 숨는다.
- 플래그 인수는 시그니처를 복잡하게 만들고, 참일 때와 거짓일 때 다른 일을 한다고, 곧 여러 일을 한다고 대놓고 알린다. 호출부의 `reserve(room, true)`는 선언을 찾아봐도 크게 나아지지 않는다.

```java
// Bad(Flag Arguments): reserve(room, true)만 봐서는 true의 뜻을 알 수 없다
public Reservation reserve(Room room, boolean withBreakfast) {
    Reservation r = new Reservation(room);
    if (withBreakfast) r.addOption(Option.BREAKFAST);
    return repository.save(r);
}

// Good: 하는 일이 둘이면 함수도 둘이다
public Reservation reserveRoomOnly(Room room) { return repository.save(new Reservation(room)); }
public Reservation reserveWithBreakfast(Room room) {
    Reservation r = new Reservation(room);
    r.addOption(Option.BREAKFAST);
    return repository.save(r);
}
```

## Have No Side Effects — 부수 효과를 일으키지 마라

**어떻게**

- 함수가 이름으로 약속한 일 외에 숨은 일을 하지 않게 한다. 자기 클래스의 변수, 넘겨받은 인수, 시스템 전역 상태를 이름이 말하지 않는 방식으로 바꾸지 않는다. 시간적 결합(temporal coupling)이 꼭 필요하다면 원래 하던 일과 숨어 있던 일을 모두 이름에 드러낸다(`checkPaymentApprovedAndClearCart`). 다만 저자도 인정하듯 이런 이름은 Do One Thing을 어긴다.
- Output Arguments: 일반적으로 출력 인수는 피한다. 상태를 바꿔야 한다면 그 상태를 가진 객체가 바꾸게 한다(`applyDiscount(cart)` 대신 `cart.applyDiscount()`). 객체지향 이전에는 출력 인수가 필요할 때가 있었지만, 객체지향 언어에서는 `this`가 그 역할을 한다.

**왜**

- 저자는 숨은 부수 효과를 "Side effects are lies." (p. 44)라고 표현한다. 숨은 변경은 이상한 시간적 결합과 순서 의존성을 낳는 경우가 많다. 이름을 믿고 호출한 사람이 기존 데이터를 잃을 수 있고, 함수를 안전한 시점에만 호출할 수 있게 된다. 출력 인수도 마찬가지로 `applyDiscount(cart)`만 보고는 cart가 입력인지 출력인지 몰라 선언을 확인하게 된다. 시그니처를 확인하게 만드는 것은 다시 읽기와 같은 인지적 단절이다.

```java
// Bad: 이름은 '승인 여부 확인'인데 장바구니를 비우는 숨은 부수 효과가 있다
public boolean isPaymentApproved(String paymentId, long memberId) {
    boolean approved = gateway.statusOf(paymentId) == PaymentStatus.APPROVED;
    if (approved) cartService.clear(memberId);
    return approved;
}
if (payments.isPaymentApproved(paymentId, memberId)) shipOrder();  // 호출부

// Good: 조회는 답만 하고, 상태 변경은 호출부에 드러낸다
public boolean isPaymentApproved(String paymentId) {
    return gateway.statusOf(paymentId) == PaymentStatus.APPROVED;
}
if (payments.isPaymentApproved(paymentId)) {  // 호출부
    cartService.clear(memberId);
    shipOrder();
}
```

## Command Query Separation — 명령과 조회를 분리하라

**어떻게**

- 함수는 무언가를 하거나(객체 상태 변경) 무언가에 답하거나(객체 정보 반환) 둘 중 하나만 한다. 상태를 바꾸고 성공 여부를 boolean으로 돌려주지 않는다. 이름에 '하고 확인한다'는 뜻을 덧붙여도 if 문은 별로 읽기 쉬워지지 않으므로, 명령과 조회를 나눠 모호함이 생길 수 없게 한다(`if (hasPreference(memberId, "language")) setPreference(memberId, "language", "ko");`처럼 조회 뒤에 반환값 없는 명령).

**왜**

- 설정을 바꾸고 성공 여부를 돌려주게 하면 `if (setPreference(memberId, "language", "ko"))` 같은 문장이 생긴다. if 조건 안의 명령은 질문처럼 읽히고, set이 동사인지 '이미 설정된'을 뜻하는 형용사인지 갈린다. 이미 그 값으로 설정돼 있느냐고 묻는지, 방금 바꾸는 데 성공했다는 뜻인지 호출부만으로는 알 수 없다.

## Prefer Exceptions to Returning Error Codes — 오류 코드보다 예외를 사용하라

**어떻게**

- 명령 함수에서 오류 코드를 반환하지 않고 예외를 던진다. 오류 코드 반환은 명령을 if 문의 조건식으로 쓰게 부추기는, 명령과 조회 분리의 미묘한 위반이다.
- Extract Try/Catch Blocks: try 블록과 catch 블록의 본문을 각각 별도 함수로 뽑는다. 바깥 함수는 오류 처리만, 뽑아낸 함수는 정상 처리만 다룬다.
- Error Handling Is One Thing: 오류를 처리하는 함수는 그 외에 아무것도 하지 않는다. 함수에 try가 있다면 try가 함수의 첫 단어이고, catch/finally 블록 뒤에는 아무것도 없어야 한다.
- The Error.java Dependency Magnet: 모든 오류 코드를 클래스나 enum 하나에 모으는 구조를 만들지 않는다. 새 오류는 예외 클래스의 파생 클래스로 추가한다.

**왜**

- 오류 코드를 반환하면 호출자가 그 자리에서 오류를 처리해야 해서 중첩이 깊어진다. 예외를 쓰면 오류 처리를 정상 경로(happy path)에서 떼어 내 단순하게 만들 수 있다. try/catch는 그 자체로 코드 구조를 흐리고 오류 처리와 정상 처리를 섞는다. 나눠 두면 오류 처리 함수는 한번 이해하고 넘어가면 되고, 정상 처리 함수에서는 오류 처리를 잊어도 된다.
- 오류 코드 enum은 많은 클래스가 import하는 의존성 자석이다. 바뀌면 그 클래스들을 모두 다시 컴파일·배포해야 하므로, 개발자는 새 코드를 추가하지 않고 옛 코드를 재사용하게 된다. 예외는 재컴파일·재배포 없이 추가할 수 있다(OCP의 예).

```java
// Bad: 오류 코드를 단계마다 즉시 확인해야 해서 중첩이 깊어진다
if (inventory.release(order) == Result.OK) {
    if (payments.refund(order) == Result.OK) log.info("order cancelled");
    else log.warn("refund failed");
} else {
    log.warn("stock release failed");
}

// Good: 각 단계는 실패하면 위 메시지를 담은 CancelFailedException(RuntimeException 하위)을 던진다
public void cancel(Order order) {
    try {
        releaseStockAndRefund(order);
    } catch (CancelFailedException e) {
        logCancelFailure(e);
    }
}
private void releaseStockAndRefund(Order order) {
    inventory.release(order);
    payments.refund(order);
    log.info("order cancelled");
}
private void logCancelFailure(CancelFailedException e) {
    log.warn(e.getMessage());
}
```

## Don't Repeat Yourself — 반복하지 마라

**어떻게**

- 같은 알고리즘이 여러 곳에 되풀이되면 함수 하나로 모은다. 다른 코드와 섞여 있고 모양이 조금씩 달라 눈에 잘 띄지 않는 중복도 찾는다.

**왜**

- 중복은 코드를 부풀리고, 알고리즘이 바뀌면 여러 곳을 고치게 하며, 그 수만큼 한 곳을 빠뜨리는 실수의 기회를 만든다. 반대로 중복을 함수 하나로 모으면 모듈 전체가 읽기 쉬워진다. 저자는 중복이 소프트웨어에서 모든 악의 근원일 수 있다고 보며, 많은 원칙과 기법이 중복을 통제하거나 없애려고 생겼다고 본다.

## Structured Programming — 구조적 프로그래밍

**어떻게**

- Dijkstra의 규칙(모든 함수와 블록은 입구와 출구가 하나: return 하나, 루프 안 break·continue 금지, goto 절대 금지)을 작은 함수에 엄격히 적용하지 않는다. 함수를 작게 유지한다면 가끔 여러 return·break·continue를 써도 된다. goto는 피한다.

**왜**

- 저자는 그 목표와 규율에 공감하지만, 규칙이 큰 이득을 주는 것은 큰 함수에서뿐이라고 본다. 작은 함수에서는 여러 return·break·continue가 해가 없고, 때로는 단일 입출구보다 의도를 더 잘 드러낸다. goto는 큰 함수에서나 의미가 있다.

## How Do You Write Functions Like This? — 함수를 어떻게 짜죠?

**어떻게**

- 처음부터 규칙에 맞게 쓰려 하지 않는다. 먼저 생각을 코드로 옮긴다. 초안은 길고, 중첩이 깊고, 인수 목록이 길고, 이름이 제멋대로이고, 중복이 있어도 된다. 다만 그 서툰 코드의 모든 줄을 덮는 단위 테스트를 갖춘다. 그다음 테스트를 계속 통과시키면서 함수를 쪼개고, 이름을 바꾸고, 중복을 없애고, 메서드를 줄이고 순서를 바꾼다. 때로는 클래스를 통째로 떼어 낸다.

**왜**

- 코드를 쓰는 일도 다른 글쓰기처럼 초안을 고쳐 쓰는 과정이다. 저자도 처음부터 이렇게 쓰지 않으며, 그럴 수 있는 사람은 없다고 본다.

## 체크리스트

- [ ] 함수가 20줄보다 훨씬 짧고, if·else·while 블록 안은 한 줄(대개 함수 호출)이며, 들여쓰기가 두 단계를 넘지 않는가?
- [ ] 본문이 이름 바로 아래 추상화 수준의 단계만 담고 있어, 구현을 되풀이하지 않는 이름으로 더 뽑아낼 부분이 없는가?
- [ ] 함수를 선언·초기화·본처리 같은 구역으로 나눌 수 없을 만큼 한 가지 일만 하는가?
- [ ] 호출되는 함수가 호출하는 함수 가까이 아래에 있어, 위에서 아래로 추상화 수준이 한 단계씩 내려가는가?
- [ ] 타입을 판별하는 switch나 if/else 사슬이 팩토리 한 곳에만 있고, 타입별 동작은 다형성으로 호출하는가?
- [ ] 함수가 이름이 말하는 일만 하고, 이름이 말하지 않는 필드·인수·전역 상태 변경이 없는가?
- [ ] 인수가 셋을 넘지 않고(셋이면 그럴 만한 이유가 있고), 함께 다니는 인수는 객체로 묶었으며, boolean 플래그 인수와 출력 인수가 없는가?
- [ ] 함수마다 상태를 바꾸는 명령과 값(성공 여부 포함)을 돌려주는 조회 중 하나만 하는가?
- [ ] 명령 함수가 오류 코드 대신 예외를 던지고, try가 있는 함수는 try로 시작해 catch/finally로 끝나는가?
- [ ] 같은 알고리즘이 모양만 바꿔 여러 곳에 흩어지지 않고 함수 하나로 모여 있는가?
- [ ] 다듬는 코드를 덮는 테스트를 먼저 갖춘 뒤 리팩터링하는가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)): `F1` Too Many Arguments, `F2` Output Arguments, `F3` Flag Arguments, `G5` Duplication, `G15` Selector Arguments, `G20` Function Names Should Say What They Do, `G23` Prefer Polymorphism to If/Else or Switch/Case, `G30` Functions Should Do One Thing, `G31` Hidden Temporal Couplings, `G34` Functions Should Descend Only One Level of Abstraction, `N1` Choose Descriptive Names, `N7` Names Should Describe Side-Effects
- [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) — 함수 이름을 포함한 이름 짓기 전반
- [chapter_04_comments.md](chapter_04_comments.md) — 서술적인 이름이 주석을 대신하는 이유
- [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md) — switch(절차적 코드)와 다형성(객체) 사이의 트레이드오프
- [chapter_07_error_handling.md](chapter_07_error_handling.md) — 예외를 쓰는 오류 처리의 세부. Use Unchecked Exceptions 절은 checked 예외가 시그니처 변경을 퍼뜨려 OCP를 어긴다고 보므로, 이 장의 '예외는 재배포 없이 추가할 수 있다'는 기존 예외 계층의 파생으로 추가하는 경우의 이야기다.
- [chapter_10_classes.md](chapter_10_classes.md) — SRP·OCP, 함수를 쪼개다 생긴 필드로 클래스를 나누는 과정
- [chapter_12_emergence.md](chapter_12_emergence.md) — 중복 제거를 단순한 설계 규칙으로 다룸
- [chapter_14_successive_refinement.md](chapter_14_successive_refinement.md) — 테스트를 받쳐 두고 초안을 다듬는 실제 과정

## 원서 밖 보충

- Java 17의 sealed 인터페이스와 Java 21의 switch 패턴 매칭을 함께 쓰고 default 분기를 두지 않으면, 하위 타입이 추가될 때 컴파일러가 빠진 case를 잡아 준다(enum을 대상으로 한 Java 14+ switch 식도 마찬가지다). 타입 집합이 닫혀 있고 연산이 자주 늘어나는 경우에는 팩토리 + 다형성 대신 고려할 만한 선택지다(트레이드오프는 [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md) 참고).
- 원서는 오류 코드가 명령을 if 조건식으로 쓰게 만들고(CQS 위반), 호출자가 그 자리에서 처리해야 해서 중첩을 깊게 하며, 공용 오류 enum이 의존성 자석이 된다고 비판한다. 요즘은 예상 가능한 실패를 Result 계열 타입으로 반환 타입에 드러내는 관행도 있고, 호출자가 처리를 건너뛰기 어렵다는 점이 정수 오류 코드와 다르다(`Optional`은 실패 원인 없이 값의 부재만 나타낸다). 다만 map/flatMap 같은 조합 수단 없이 단계마다 분기하면 원서가 지적한 중첩이 그대로 생기고, 모든 실패를 공용 enum 하나에 모으면 의존성 자석 문제도 남는다.
- 조회와 명령을 나누면 동시성 환경에서 둘 사이에 상태가 바뀌는 check-then-act 경쟁이 생길 수 있다. 원자성이 필요하면 명령 하나로 처리하고 실패는 예외로 알린다.
