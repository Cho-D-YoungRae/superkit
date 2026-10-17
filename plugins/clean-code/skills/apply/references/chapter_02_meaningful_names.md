# Chapter 2: Meaningful Names — 의미 있는 이름

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 2, pp. 17–30 · by Tim Ottinger
> 한 줄 요약: 이름만 읽어도 존재 이유·하는 일·쓰는 법이 드러나도록 짓고, 더 나은 이름이 보이면 망설이지 말고 바꾼다.

## 핵심

- 이름에 주석이 필요하다면 의도를 드러내지 못한 이름이다. 무엇을 재는지와 단위까지 이름에 담는다.
- 거짓 단서를 남기지 않는다. 이름이 다르면 뜻도 달라야 하며, `Info`·`Data`·숫자 연번으로 구별하지 않는다.
- 발음할 수 있고 검색할 수 있는 이름을 쓴다. 이름 길이는 그 이름이 쓰이는 범위(scope)의 크기에 맞춘다.
- 타입·범위를 이름에 인코딩하지 않는다(Hungarian Notation, `m_` 접두사, 인터페이스의 `I`).
- 클래스는 명사, 메서드는 동사로 짓는다. 한 개념에는 한 단어만 쓰고, 한 단어를 두 개념에 쓰지 않는다.
- 기술 개념은 해법 영역(solution domain) 용어로, 업무 개념은 문제 영역(problem domain) 용어로 짓는다.
- 맥락은 잘 지은 클래스·함수로 주고 불필요한 접두사는 붙이지 않는다. 더 나은 이름이 보이면 다른 개발자가 반대할까 두려워하지 말고 바꾼다. 남의 코드를 유지보수할 때는 리팩터링 도구로 이름 문제를 고친다.

## Use Intention-Revealing Names — 의도를 드러내는 이름을 써라

**어떻게**
- 이름 하나로 왜 존재하는지, 무엇을 하는지, 어떻게 쓰는지에 답한다. 이름을 설명하는 주석이 필요하면 이름을 다시 짓는다.
- 측정 대상과 단위를 넣는다. Bad `int t; // 결제 요청 후 경과 시간(초)` → Good `secondsSincePaymentRequested`, `paymentWaitTimeInSeconds`.
- 배열 첨자·상태 값 같은 숨은 개념에 상수로 이름을 붙인다. 더 나아가 `int[]` 대신 클래스를 두고 `isCancelled()` 같은 의도를 드러내는 함수로 매직 넘버를 감춘다.
- 더 나은 이름을 찾으면 바꾼다. 이름은 외워 쓰기보다 도구로 다루는 세부 사항이므로, 코드가 문단과 문장처럼(또는 표와 자료구조처럼) 읽히는지에 집중한다(p. 30).

**왜**
- 코드가 단순해도 맥락이 코드에 드러나지 않으면(저자의 조어로 implicity) 독자는 목록에 무엇이 들었는지, 숫자가 무슨 뜻인지 따로 알아내야 한다. 연산자 수와 중첩 깊이가 그대로여도 이름만 바꾸면 코드가 훨씬 명시적이 된다. 좋은 이름을 고르는 데 드는 시간보다 아끼는 시간이 크다.

```java
// Bad: 무엇을 고르는지, 1과 2가 무슨 뜻인지 코드에 없다
public List<int[]> getItems() {
    List<int[]> result = new ArrayList<>();
    for (int[] r : data)
        if (r[1] == 2) result.add(r);
    return result;
}
// Good: 같은 동작. 이름만 바꿨다(data→reservations, 1→STATUS_INDEX, 2→CANCELLED 등)
public List<int[]> getCancelledReservations() {
    List<int[]> cancelled = new ArrayList<>();
    for (int[] reservation : reservations)
        if (reservation[STATUS_INDEX] == CANCELLED) cancelled.add(reservation);
    return cancelled;
}
// 더 나아가: 예약을 클래스로 두면 매직 넘버가 isCancelled() 안으로 숨는다(반환 타입도 바뀐다)
public List<Reservation> getCancelledReservations() {
    return reservations.stream().filter(Reservation::isCancelled).toList();
}
```

## Avoid Disinformation — 그릇된 정보를 피하라

**어떻게**
- 이미 굳은 뜻이 있는 단어를 다른 뜻으로 쓰지 않는다. 상품 가격(item price)을 `ip`로 줄이면 IP 주소로 읽힌다.
- 실제 `List`가 아니면 `memberList`라 부르지 않는다(Good `members`, `memberGroup`). 실제 `List`여도 컨테이너 타입은 이름에 넣지 않는 편이 대개 낫다.
- 조금만 다른 이름을 피한다. `PaymentAuthorizationResultHandler`와 `PaymentAuthenticationResultHandler`는 차이가 가운데의 비슷한 단어에 묻혀 한눈에 구별되지 않는다. 비슷한 개념은 비슷한 철자로 써서 자동 완성 목록에 모이게 하고, 차이는 뚜렷하게 드러낸다.
- 소문자 `l`과 대문자 `O`를 변수 이름으로 쓰지 않는다. 숫자 1, 0과 거의 똑같아 보인다.

**왜**
- 개발자는 주석이나 메서드 목록을 보지 않고 자동 완성에 뜬 이름만 보고 고르기 쉽다. 일관된 철자는 정보이고, 어긋난 철자는 그릇된 정보다. 글꼴을 바꾸자는 식의 우회책은 모든 후임에게 따로 전해야 한다. 이름을 바꾸면 추가 산출물 없이 끝난다.

## Make Meaningful Distinctions — 의미 있게 구분하라

**어떻게**
- 같은 범위에 같은 이름을 못 쓴다고 컴파일러만 달래려 이름을 임의로 바꾸지 않는다(일부러 틀린 철자, 숫자 붙이기). 숫자 연번 대신 역할을 담는다. Bad `merge(Order o1, Order o2)` → Good `merge(Order original, Order addition)`.
- 불용어(noise word)로 구별하지 않는다. 구별 규약이 따로 없다면 `Order`/`OrderInfo`/`OrderData`, `price`/`priceAmount`, `member`/`memberObject`는 뜻이 같다. 변수 이름에 `variable`, 테이블 이름에 `table`을 넣지 않는다(Bad `nicknameString` → Good `nickname`).
- `a`·`the` 같은 접두사는 일관된 규약으로 실제 구별을 만들 때만 괜찮다(예: 지역 변수는 모두 `a`, 인수는 모두 `the`). 이미 `coupon`이 있다고 `theCoupon`을 만드는 것은 안 된다. 다만 원서 각주는 Uncle Bob도 C++에서 이렇게 하다가 현대 IDE 덕에 필요 없어져 그만두었다고 밝힌다(p. 21). 허용되는 경우일 뿐 권하는 규약은 아니다.

**왜**
- 이름이 달라야 한다면 뜻도 달라야 한다. `findMember()`, `findMembers()`, `findMemberInfo()`가 나란히 있으면 무엇을 불러야 할지 알 수 없다. 숫자 연번은 그릇된 정보는 아니지만 아무 정보도 주지 않는다(noninformative). 독자가 이름 차이만 보고 무엇이 다른지 알 수 있어야 한다.

## Use Pronounceable Names — 발음하기 쉬운 이름을 써라

**어떻게**
- 소리 내어 읽을 수 있는 단어로 짓는다. 자음만 남긴 축약어나 날짜 형식 문자를 이어 붙인 이름을 피한다.
- Bad `class RsvRcd { LocalDateTime chkindt; String rsvno; }` → Good `class Reservation { LocalDateTime checkInTime; String reservationNumber; }`.

**왜**
- 프로그래밍은 사회적 활동이다. 발음할 수 없는 이름은 동료와 토론하기 어렵고, 새로 온 개발자에게 일일이 풀어 설명해야 한다.

## Use Searchable Names — 검색하기 쉬운 이름을 써라

**어떻게**
- 숫자 상수에 이름을 붙인다. `12`를 검색하면 다른 뜻의 12까지 섞여 나오지만 `MONTHS_PER_YEAR`는 바로 찾힌다.
- 한 글자 이름은 짧은 메서드 안의 지역 변수에만 쓴다(저자의 개인적 선호). 이름 길이는 범위 크기에 비례해야 한다[N5]. 여러 곳에서 보이거나 쓰이는 이름은 반드시 검색하기 쉽게 짓는다.

**왜**
- 한 글자 이름과 숫자 상수는 코드 전체에서 찾기 어렵다. 검색 면에서는 긴 이름이 짧은 이름보다, 이름 붙은 상수가 숫자보다 낫다. 긴 숫자의 자릿수가 뒤바뀌면 버그가 생기면서 검색에도 걸리지 않는다. 이름을 붙이면 함수가 길어지지만, 같은 숫자 중 의도한 뜻의 것만 골라내는 수고보다 상수 이름 하나 찾는 편이 훨씬 쉽다.

```java
// Bad
int s = 0;
for (int j = 0; j < 12; j++) s += f[j] * 110 / 100;
// Good: 같은 동작 (상수는 클래스 필드)
private static final int MONTHS_PER_YEAR = 12;
private static final int VAT_PERCENT = 10;
int yearlyTotalWithVat = 0;
for (int month = 0; month < MONTHS_PER_YEAR; month++)
    yearlyTotalWithVat += monthlyFees[month] * (100 + VAT_PERCENT) / 100;
```

## Avoid Encodings — 인코딩을 피하라

**어떻게**
- 타입이나 범위 정보를 부호로 바꿔 이름에 넣지 않는다.

**왜**
- 해독할 짐이 늘어난다. 새로 온 사람은 방대한 코드에 더해 별도의 인코딩 "언어"까지 익혀야 한다. 인코딩된 이름은 발음하기 어렵고 오타 나기 쉽다.

### Hungarian Notation — 헝가리식 표기법

**어떻게**
- 이름에 타입 표시를 붙이지 않는다. Bad `strCouponCode`, `iQty` → Good `couponCode`, `quantity`.

**왜**
- 컴파일러가 타입을 검사하지 않던 시절(Windows C API 등)에는 타입을 기억하는 버팀목이었다. 지금 Java는 컴파일러와 편집기가 타입을 강제하고 오류를 먼저 잡으며, 클래스·함수가 작아져 선언부도 대개 바로 보인다. 그래서 이제는 방해물이다. 이름이나 타입을 바꾸기 어렵게 하고 읽기 어렵게 하며, 타입만 바뀌고 이름이 남으면 독자를 속인다. 예: `Money priceStr; // 타입을 바꿨는데 이름은 그대로`.

### Member Prefixes — 멤버 변수 접두사

**어떻게**
- 멤버 변수에 `m_`를 붙이지 않는다. 클래스와 함수를 접두사가 필요 없을 만큼 작게 유지하고, 멤버를 색으로 구별해 주는 편집기를 쓴다. Bad `private String m_cd; // 쿠폰 코드` → Good `private String code;`(세터에서는 `this.code = code`).

**왜**
- 사람들은 금세 접두사(또는 접미사)를 건너뛰고 의미 있는 부분만 읽는다. 결국 접두사는 보이지 않는 잡동사니이자 옛 코드의 표식이 된다.

### Interfaces and Implementations — 인터페이스 클래스와 구현 클래스

**어떻게**
- 저자는 인터페이스 이름을 꾸미지 않는 쪽을 선호한다. Bad `IPaymentGateway` → Good `PaymentGateway`. 둘 중 하나를 꼭 표시해야 한다면 구현 쪽에 표시한다. `PaymentGatewayImp`, 보기 흉한 `CPaymentGateway`조차 인터페이스에 `I`를 붙이는 것보다 낫다고 본다.

**왜**
- 사용자가 알아야 할 것은 그것이 `PaymentGateway`라는 사실이지, 인터페이스를 건네받는다는 사실이 아니다. 앞에 붙인 `I`는 잘해야 주의를 흩뜨리고, 나쁘면 과한 정보다.

## Avoid Mental Mapping — 머릿속 변환을 강요하지 마라

**어떻게**
- 독자가 이름을 자기가 아는 다른 이름으로 바꿔 읽게 하지 않는다. 문제 영역이나 해법 영역의 용어를 쓴다. Bad `int p = q * POINTS_PER_ITEM; m.addPoints(p);` → Good `int earnedPoints = quantity * POINTS_PER_ITEM; member.addPoints(earnedPoints);`.
- 반복문 카운터는 범위가 아주 작고 충돌할 이름이 없으면 `i`, `j`, `k`로 써도 된다(단 `l`은 절대 안 된다). 그 밖의 대부분 맥락에서 한 글자 이름은 나쁜 선택이며, `a`, `b`가 이미 있어서 `c`를 쓰는 것이 가장 나쁜 이유다.

**왜**
- 반복문 카운터의 한 글자 이름은 관례라 통한다. 그 밖의 한 글자 이름은 독자가 실제 개념으로 매핑해야 하는 자리표시자일 뿐이다. 똑똑한 프로그래머와 전문가 프로그래머의 차이 중 하나는, 전문가가 "clarity is king" (p. 25)임을 안다는 점이다. 재주를 자랑하지 말고 남이 이해하는 코드를 쓴다.

## Class Names — 클래스 이름

**어떻게**
- 클래스와 객체에는 명사나 명사구를 쓴다. Good `Order`, `Member`, `Coupon`, `InvoiceParser`.
- `Manager`, `Processor`, `Data`, `Info` 같은 단어를 클래스 이름에 쓰지 않는다. 동사도 쓰지 않는다. Bad `OrderManager`, `MemberInfo`, `ProcessRefund`.

**왜**
- 원서는 이 절에서 규칙만 제시하고 이유를 따로 밝히지 않는다. `Data`·`Info`는 Make Meaningful Distinctions에서 본 불용어(noise word)라 구별을 만들지 못한다(p. 21). `Manager`·`Processor` 같은 모호한 단어가 책임이 너무 많이 모였다는 신호라는 설명은 Chapter 10에 있다([chapter_10_classes.md](chapter_10_classes.md)).

## Method Names — 메서드 이름

**어떻게**
- 메서드에는 동사나 동사구를 쓴다. Good `cancelOrder`, `reserveSeat`, `save`.
- 접근자(accessor)·변경자(mutator)·조건자(predicate)는 값을 기준으로 이름 짓고 javabean 표준에 따라 `get`·`set`·`is`를 붙인다: `order.getTotal()`, `member.setNickname("kim")`, `if (payment.isRefunded())`.
- 생성자를 오버로드할 때는 인수를 설명하는 이름의 정적 팩터리 메서드(static factory method)가 대개 낫다. Bad `new Weight(2.5)`·`new Weight(250L)`(킬로그램 `double`, 그램 `long` 생성자 오버로드) → Good `Weight.ofKilograms(2.5)`·`Weight.ofGrams(250)`. 해당 생성자를 `private`으로 막아 사용을 강제하는 것도 고려한다.

**왜**
- 오버로드된 생성자는 인수가 무엇을 뜻하는지 말해 주지 않는다. 팩터리 메서드 이름이 그 정보를 준다.

## Don't Be Cute — 기발한 이름은 피하라

**어떻게**
- 재미보다 명확함을 고른다. Bad `kaboom()` → Good `deleteExpiredCarts()`. 속어·은어나 특정 문화에 기댄 농담도 이름에 쓰지 않는다. Bad `sayonara()` → Good `withdrawMembership()`.

**왜**
- 기발한 이름은 저자와 유머 감각이 같은 사람에게만, 그것도 그 농담을 기억하는 동안만 통한다. "Say what you mean. Mean what you say." (p. 26)

## Pick One Word per Concept — 한 개념에 한 단어를 사용하라

**어떻게**
- 추상 개념 하나에 단어 하나를 골라 끝까지 쓴다. 저장소에서 하나를 읽는 동작을 클래스마다 `findById`, `loadById`, `lookupById`로 다르게 부르지 않는다. 역할 이름도 맞춘다. 한 코드베이스에 `OrderService`, `PaymentHandler`, `RefundProcessor`가 섞여 있으면 셋이 본질적으로 무엇이 다른지 묻게 된다.

**왜**
- 단어가 다르면 독자는 타입도 클래스도 전혀 다른 객체를 기대한다. 어느 클래스에 어느 단어를 썼는지 기억하려면 누가 만들었는지까지 떠올려야 한다. 편집기의 메서드 목록은 대개 함수 이름 주변의 주석을 보여 주지 않고 매개변수 이름조차 빠질 때가 있다. 함수 이름은 홀로 서야 하고 일관되어야 한다. 일관된 어휘(lexicon)는 내 코드를 가져다 써야 하는 프로그래머에게 큰 도움이 된다.

## Don't Pun — 말장난을 하지 마라

**어떻게**
- 한 단어를 두 목적에 쓰지 않는다. 같은 이름의 메서드들은 매개변수와 반환값의 의미가 같을 때만 그 이름을 공유한다.
- "일관성"을 핑계로 의미가 다른 동작에 기존 단어를 재사용하지 않는다. 예: 코드베이스의 `merge`가 모두 "두 값을 합쳐 새 값을 돌려준다"(`itemPrice.merge(shippingFee)`)는 뜻이라면, 대기열 끝에 하나를 넣는 메서드는 `waitingList.merge(reservation)`이 아니라 `waitingList.enqueue(reservation)`로 짓는다.

**왜**
- 같은 용어로 다른 개념을 가리키면 말장난(pun)이 된다. 코드는 정독이 아니라 훑어보는 것만으로 이해되어야 하며, 뜻을 분명히 할 책임은 독자가 아니라 작성자에게 있다.

## Use Solution Domain Names — 해법 영역에서 가져온 이름을 써라

**어떻게**
- 코드를 읽는 사람은 프로그래머다. 전산 용어, 알고리즘·패턴 이름, 수학 용어를 쓴다. 기술적인 일에는 기술적인 이름이 대개 가장 알맞다. Good `ReservationBuilder`, `PaymentRetryQueue`, `InventoryEventListener`.

**왜**
- 모든 이름을 문제 영역에서 가져오면 동료가 이미 다른 이름으로 아는 개념을 두고 이름마다 고객에게 뜻을 물으러 다녀야 한다.

## Use Problem Domain Names — 문제 영역에서 가져온 이름을 써라

**어떻게**
- 알맞은 프로그래머 용어가 없으면 문제 영역의 이름을 쓴다. Good `settlementCutoffDate`(정산 마감일), `noShowPenalty`(노쇼 위약금), `backorder`(입고 대기 주문). 해법 영역 개념과 문제 영역 개념을 가르고, 문제 영역 개념과 더 관련된 코드는 문제 영역에서 이름을 가져온다.

**왜**
- 코드를 유지보수하는 프로그래머가 적어도 도메인 전문가에게 뜻을 물어볼 수 있다. 두 영역을 가르는 일은 좋은 프로그래머이자 설계자의 몫이다.

## Add Meaningful Context — 의미 있는 맥락을 추가하라

**어떻게**
- 스스로 뜻이 분명한 이름은 드물다. 잘 지은 클래스·함수·네임스페이스에 넣어 맥락을 준다. 접두사로 맥락을 붙이는 것은 다른 방법이 모두 안 될 때의 마지막 수단이다. Bad 흩어진 `String number, holder; int expiryMonth;` → 차선 `cardNumber`, `cardHolder`, `cardExpiryMonth` → Good 필드 `number`, `holder`, `expiryMonth`를 가진 `PaymentCard` 클래스.
- 긴 함수 곳곳에서 쓰이는 변수들의 맥락을 알고리즘을 끝까지 읽어야 짐작할 수 있다면, 그 변수들을 필드로 갖는 클래스를 만든다. 변수를 클래스 필드로 올리면 맥락이 분명해지고, 그 덕에 알고리즘을 작은 함수로 나눌 수 있다.

**왜**
- `number`, `holder`, `expiryMonth`가 함께 있으면 카드 정보임을 알지만, 메서드에서 `number` 하나만 보면 주문 번호인지 카드 번호인지 알 수 없다. 클래스로 묶으면 독자뿐 아니라 컴파일러도 그 변수들이 더 큰 개념에 속함을 안다.

```java
// Bad: 실제로는 더 긴 메서드라고 하자. 세 변수가 영수증 금액의 일부라는 맥락을 끝까지 읽어야 안다
public String receiptLine(Order order) {
    int subtotal = order.itemsTotal(), discount = 0, shippingFee = BASE_SHIPPING_FEE;
    if (order.isByMember()) discount = subtotal * MEMBER_DISCOUNT_PERCENT / 100;
    if (subtotal - discount >= FREE_SHIPPING_MIN) shippingFee = 0;
    return String.format("%d - %d + %d", subtotal, discount, shippingFee);
}
// Good: 같은 동작. 세 변수가 ReceiptBreakdown의 필드가 되고, 단계마다 작은 메서드로 나뉜다
public class ReceiptBreakdown {
    private int subtotal, discount, shippingFee;
    public String make(Order order) {
        subtotal = order.itemsTotal();
        applyMemberDiscount(order);
        applyFreeShipping();
        return String.format("%d - %d + %d", subtotal, discount, shippingFee);
    }
    private void applyMemberDiscount(Order order) {
        discount = order.isByMember() ? subtotal * MEMBER_DISCOUNT_PERCENT / 100 : 0;
    }
    private void applyFreeShipping() {
        shippingFee = subtotal - discount >= FREE_SHIPPING_MIN ? 0 : BASE_SHIPPING_FEE;
    }
}
```

## Don't Add Gratuitous Context — 불필요한 맥락을 없애라

**어떻게**
- 모든 클래스 앞에 애플리케이션·모듈 약어를 붙이지 않는다. 가상의 "Happy Booking" 앱이라고 `HBReservation`, `HBMember`처럼 짓지 않는다. 이름에는 필요한 만큼만 맥락을 넣는다. 명확하기만 하면 짧은 이름이 대개 긴 이름보다 낫다.
- `orderTotal`, `refundAmount`는 `Money` 클래스의 인스턴스 이름으로는 좋지만 클래스 이름으로는 나쁠 수 있다. `Money`는 좋은 클래스 이름이다. 같은 단어가 실제로 다른 개념을 가리킬 때는 더 정확한 클래스 이름으로 나눈다. "코드"가 쿠폰 코드·우편번호·상품 코드를 뜻한다면 `CouponCode`, `PostalCode`, `Sku`처럼 짓는다.

**왜**
- 공통 접두사는 도구를 거스른다. `HB`를 치고 자동 완성을 누르면 시스템의 모든 클래스가 길게 쏟아진다. 예약 모듈에서 만든 일반 우편 주소 클래스를 `HBReservationAddress`로 지으면, 굿즈 배송 모듈에서 주소가 필요할 때 맞지 않는 이름이 된다. 이름 짓기의 목적은 정확성이다.

## 체크리스트

- [ ] 이름만 보고 존재 이유·하는 일·쓰는 법을 알 수 있는가? 이름을 설명하는 주석이 붙어 있지 않은가?
- [ ] 수치를 담은 이름에 측정 대상과 단위가 드러나는가? 매직 넘버와 숨은 첨자에 이름을 붙였는가?
- [ ] 실제와 어긋나는 이름(`List`가 아닌데 `...List`), 한눈에 구별되지 않는 이름, `l`·`O` 같은 이름은 없는가?
- [ ] `Info`·`Data`·`the`·숫자 연번으로만 구별되는 이름은 없는가?
- [ ] 소리 내어 읽고 grep으로 찾을 수 있는가? 이름 길이가 범위 크기에 맞는가? 타입 표시, `m_`, 인터페이스의 `I` 같은 인코딩이 남아 있지 않은가?
- [ ] 클래스는 명사(구), 메서드는 동사(구)인가? 생성자 오버로드가 필요한 곳에는 인수를 설명하는 이름의 정적 팩터리 메서드를 썼는가?
- [ ] 농담·속어·문화 의존 표현 없이 하는 일을 그대로 말하는 이름인가?
- [ ] 같은 개념에 같은 단어를 쓰고, 같은 단어를 다른 개념에 쓰지 않았는가?
- [ ] 기술 개념은 CS·알고리즘·패턴 용어로, 업무 개념은 도메인 용어로 지었는가? 독자가 머릿속으로 다른 이름으로 바꿔 읽어야 하는 이름은 없는가?
- [ ] 맥락은 클래스·함수가 주고 있는가? 앱·모듈 접두사 같은 불필요한 맥락은 없는가?

## 관련

- Chapter 17 휴리스틱: `N1` Choose Descriptive Names, `N2` Choose Names at the Appropriate Level of Abstraction, `N3` Use Standard Nomenclature Where Possible, `N4` Unambiguous Names, `N5` Use Long Names for Long Scopes, `N6` Avoid Encodings, `G11` Inconsistency, `G16` Obscured Intent, `G24` Follow Standard Conventions, `G25` Replace Magic Numbers with Named Constants
- [chapter_03_functions.md](chapter_03_functions.md) — 함수 이름 짓기(Use Descriptive Names): 함수가 작고 한 가지 일만 할수록 서술적인 이름을 고르기 쉽고, 길고 서술적인 이름이 짧고 모호한 이름보다 낫다
- [chapter_04_comments.md](chapter_04_comments.md) — 주석 대신 이름으로 의도를 표현하기
- [chapter_10_classes.md](chapter_10_classes.md) — 작은 클래스와 클래스 이름이 드러내는 책임, `Manager`·`Processor` 같은 모호한 단어
- [chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md) — 이름 관련 휴리스틱(N1–N7) 전체. 범위 길이와 이름 길이의 관계는 N5

## 원서 밖 보충

- 요즘 Java에서는 구현 클래스에 `Imp`보다 `Impl` 접미사가 흔하다. 구현이 여럿이면 접미사보다 구현 방식을 드러내는 이름(`CardPaymentGateway`, `InMemoryOrderRepository`)이 더 많은 정보를 준다.
- 이름 변경은 IDE의 Rename 리팩터링으로 하면 코드 안의 참조가 함께 바뀐다. 리플렉션, 설정 파일의 프로퍼티 키, JPQL·XML 매퍼 같은 문자열 참조는 IDE가 놓칠 수 있으니 따로 검색한다. 공개 API·직렬화 필드·DB 컬럼처럼 코드 밖에서 참조되는 이름은 바꿀 때 호환성을 따로 확인한다.
