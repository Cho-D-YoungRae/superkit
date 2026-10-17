# Chapter 7: Error Handling — 오류 처리

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 7, pp. 103–112 · by Michael Feathers
> 한 줄 요약: 오류 처리를 주 로직과 분리된 관심사로 보고 예외·API 감싸기·특수 사례 객체로 다루며, null은 반환하지도 넘기지도 않는다.

## 핵심

- 오류 처리는 중요하지만 로직을 가리면 잘못된 것이다. 원문 표현은 "if it obscures logic, it's wrong" (p. 103)이다. 견고함과 가독성은 상충하지 않는다.
- 오류는 반환 코드·오류 플래그가 아니라 예외로 알린다. 예외가 날 수 있는 코드는 try-catch-finally부터 쓰고 try 블록을 트랜잭션처럼 다룬다.
- 일반 애플리케이션 코드에서는 unchecked 예외를 쓴다. 호출자가 반드시 잡아야 하는 핵심 라이브러리라면 checked 예외가 유용할 수 있다.
- 예외 메시지에는 실패한 연산과 실패 유형을 담고, 예외 클래스는 호출자가 어떻게 잡을지를 기준으로 정한다. 서드파티 API는 감싸서 공통 예외로 번역한다.
- 중단할 필요가 없는 특수 상황은 특수 사례 객체(SPECIAL CASE object)로 처리하고, null은 반환하지도 넘기지도 않는다.

## Use Exceptions Rather Than Return Codes — 반환 코드 대신 예외를 쓴다

**어떻게**

- 오류를 감지한 메서드는 오류 플래그를 세우거나 오류 코드를 반환하지 않고 예외를 던진다. 호출부의 로직이 오류 검사에 가려지지 않게 한다. 예외를 잡는 코드와 본래 업무의 알고리즘은 서로 다른 메서드로 나눠 각각 따로 읽히게 한다.

**왜**

- 반환 코드는 호출 직후 매번 검사해야 해서 호출부가 어수선해지고, 검사를 빠뜨리기 쉽다.
- 얽혀 있던 두 관심사, 즉 본래 업무의 알고리즘과 오류 처리가 분리되어 각각을 따로 이해할 수 있다. 보기 좋아지는 것 이상의 이점이다.

```java
// Bad: 호출할 때마다 결과를 확인하느라 취소 로직이 묻힌다
public void cancelOrder(OrderId id) {
    Order order = orderRepository.find(id);
    if (order != null) {
        if (refundGateway.refund(order.paymentId()) == REFUND_OK) {
            order.markCancelled();
            orderRepository.save(order);
        } else { logger.warn("환불 실패: " + id); }
    } else { logger.warn("주문 없음: " + id); }
}
// Good: catch와 취소 알고리즘을 나눈다. loadOrder·refund는 실패하면 같은 메시지로 예외를 던진다
public void cancelOrder(OrderId id) {
    try { performCancellation(id); }
    catch (OrderCancelException e) { logger.warn(e.getMessage(), e); }
}
private void performCancellation(OrderId id) {
    Order order = loadOrder(id);
    refund(order);
    order.markCancelled();
    orderRepository.save(order);
}
```

## Write Your Try-Catch-Finally Statement First — try-catch-finally 문부터 쓴다

**어떻게**

- 예외를 던질 수 있는 코드는 try-catch-finally 구조부터 잡는다. 실행은 try 안 어디서든 끊겨 catch로 넘어올 수 있으므로 try 블록을 트랜잭션처럼 다루고, catch는 어떤 경우에도 프로그램을 일관된 상태로 남기게 한다.
- TDD 순서: 예외를 강제하는 테스트 → 통과시키는 try-catch → 잡는 타입을 실제로 던져지는 타입으로 좁히기 → 나머지 로직은 그 범위 안에서 실패가 없다고 여기고 채우기.

**왜**

- 이 구조가 try 안에서 무엇이 잘못되든 호출자가 무엇을 기대하면 되는지를 정한다. 범위를 먼저 세워 두면 로직을 붙여 나가도 트랜잭션 성격이 유지된다.

```java
@Test // 1) 실패를 강제하는 테스트부터
void loadThrowsWhenSnapshotFileIsMissing() {
    assertThrows(InventoryLoadException.class, () -> loader.load(Path.of("missing.dat")));
}
// 2~3) 범위를 먼저 정하고, Exception이 아니라 실제로 던져지는 타입으로 잡는다
public List<StockItem> load(Path file) {
    try (InputStream in = Files.newInputStream(file)) {
        return new ArrayList<>(); // 4) 읽기 로직은 여기에 TDD로 채운다
    } catch (IOException e) {
        throw new InventoryLoadException("재고 스냅샷 로드 실패: " + file, e);
    }
}
```

## Use Unchecked Exceptions — unchecked 예외를 쓴다

**어떻게**

- 일반 애플리케이션 코드에서는 unchecked 예외(Java에서는 `RuntimeException` 계열)를 쓴다. 하위 메서드가 새 예외를 던지게 되었다고 호출 경로 전체에 `throws`를 붙이게 만들지 않는다.
- 단서: 저자는 checked 예외 논쟁이 끝났다고 보면서도 checked 예외에 어느 정도 이점이 있다고 인정한다. 호출자가 반드시 잡아야 하는 핵심 라이브러리(critical library)를 작성할 때는 때때로 유용하다.

**왜**

- 비용은 OCP(Open/Closed Principle) 위반이다. catch가 세 단계 위에 있으면 그 사이 메서드 모두가 예외를 선언해야 하고, 하위 한 곳의 변경이 상위 여러 단계의 시그니처 변경·재빌드·재배포로 번진다. 그 모듈들이 신경 쓰는 것은 바뀌지 않았는데도 그렇다.
- 캡슐화도 깨진다. throw 경로의 모든 함수가 하위 예외의 세부를 알아야 하므로, 오류를 멀리서 처리하려는 예외의 목적과 어긋난다. C#·C++·Python·Ruby에는 checked 예외가 없지만 견고한 소프트웨어를 만들 수 있다. checked 예외는 견고함의 필수 조건이 아니며, 일반 애플리케이션 개발에서는 의존성 비용이 이점보다 크다.

## Provide Context with Exceptions — 예외에 맥락을 담는다

**어떻게**

- 던지는 예외마다 오류의 출처와 위치를 알아낼 만한 맥락을 담는다. 메시지에 실패한 연산과 실패 유형을 적는다.
- 애플리케이션이 로그를 남긴다면, catch에서 오류를 기록할 수 있을 만큼의 정보를 예외에 실어 보낸다.

**왜**

- Java 스택 트레이스는 어디서 났는지는 보여 주지만, 실패한 연산이 무엇을 하려던 것인지는 알려 주지 않는다.

```java
// Bad: 무엇을 하다 왜 실패했는지 알 수 없다
throw new ReservationException("error", e);
// Good: 실패한 연산·실패 유형·식별자를 담는다
throw new ReservationException("객실 예약 실패(기간 중복): roomId=" + roomId + ", 기간=" + stay, e);
```

## Define Exception Classes in Terms of a Caller's Needs — 호출자 관점에서 예외 클래스를 정의한다

**어떻게**

- 오류는 출처(어느 컴포넌트)나 종류(장치·네트워크·프로그래밍 오류)로도 나눌 수 있지만, 예외 클래스를 정할 때 가장 중요한 기준은 그 예외를 어떻게 잡느냐다. 서드파티 API가 여러 예외를 던지는데 호출부의 처리가 사실상 같다면, API를 감싸는 클래스를 만들어 공통 예외 하나로 번역한다.
- 한 코드 영역에는 예외 클래스 하나로 충분한 경우가 많다. 오류 구분은 예외에 담는 정보로 하고, 어떤 예외는 잡고 다른 예외는 통과시켜야 할 때만 클래스를 나눈다.

**왜**

- 대부분의 예외 처리는 원인과 상관없이 비슷하다. 대개 할 일은 오류를 기록하고 계속 진행할 수 있게 하는 정도다. 벤더 예외마다 catch를 나누면 같은 코드가 반복된다.
- 서드파티 API 감싸기는 모범 관행(best practice)이다. 의존성이 줄어 다른 라이브러리로 바꾸기 쉽고, 테스트에서 외부 호출을 mock하기 쉬우며, 벤더의 API 설계에 묶이지 않고 쓰기 편한 API를 직접 정할 수 있다.

```java
// Bad: 벤더 예외마다 같은 처리가 반복되고, 호출부가 벤더 예외 타입을 안다
try {
    smsVendorClient.send(message);
} catch (VendorConnectionException e) {
    markFailed(message); logger.error("connection failure", e);
} catch (VendorAuthException e) {
    markFailed(message); logger.error("auth failure", e);
}
// Good: 호출부는 벤더 예외 타입을 모른다 → 라이브러리 교체·테스트 mock이 쉽다
public class SmsSender {
    private final SmsVendorClient client; // 생성자 생략
    public void send(SmsMessage message) {
        try { client.send(message); }
        catch (VendorConnectionException | VendorAuthException e) {
            String type = e.getClass().getSimpleName(); // 실패 유형을 메시지에 싣는다
            throw new SmsSendException("SMS 발송 실패(" + type + "): id=" + message.id(), e);
        }
    }
}
try { smsSender.send(message); } // 호출부는 하나만 잡는다
catch (SmsSendException e) { markFailed(message); logger.error(e.getMessage(), e); }
```

## Define the Normal Flow — 정상 흐름을 정의한다

**어떻게**

- 예외가 중단이 아니라 업무상 특수 상황(데이터가 없으면 기본값 적용 등)을 나타낸다면 catch로 처리하지 말고 Fowler의 SPECIAL CASE PATTERN으로 바꾼다. 특수 상황을 처리하는 클래스를 만들거나 객체를 그렇게 구성해 반환한다.

**왜**

- 앞 절들을 따르면 오류 감지가 프로그램 가장자리로 밀려난다(외부 API는 감싸서 자기 예외를 던지고, 중단된 계산은 위쪽 handler가 처리한다). 대개는 훌륭한 방식이지만 중단하지 않는 편이 나은 경우가 있다. catch에 업무 규칙이 들어가면 예외가 로직을 어지럽힌다. 특수 상황을 객체 안에 캡슐화하면 클라이언트 코드는 예외적 동작을 다루지 않아도 된다.

```java
// Bad: "지역 요금이 없으면 기본 배송비"라는 규칙이 catch에 숨어 있다
try {
    ShippingRate rate = rateRepository.findByRegion(order.region());
    total += rate.feeFor(order);
} catch (ShippingRateNotFoundException e) { total += DEFAULT_SHIPPING_FEE; }
// Good: 지역 요금이 없으면 저장소가 특수 사례 객체를 준다
ShippingRate rate = rateRepository.findByRegion(order.region());
total += rate.feeFor(order);
// 저장소 findByRegion: return rates.getOrDefault(region, new DefaultShippingRate());
public class DefaultShippingRate implements ShippingRate {
    public long feeFor(Order order) { return DEFAULT_SHIPPING_FEE; }
}
```

## Don't Return Null — null을 반환하지 않는다

**어떻게**

- null을 반환하고 싶어지면 예외를 던지거나 특수 사례 객체를 반환하는 쪽을 검토한다. 컬렉션이라면 빈 컬렉션(예: 불변 빈 리스트 `Collections.emptyList()`)이 손쉬운 해법이다.
- null을 반환하는 서드파티 API를 불러야 한다면, 예외를 던지거나 특수 사례 객체를 반환하는 메서드로 감싸는 것을 검토한다.

**왜**

- null 반환은 일을 만들고 문제를 호출자에게 떠넘긴다. null 검사 하나만 빠져도 애플리케이션이 통제를 벗어나고, 깊은 곳에서 터진 NullPointerException(NPE)에는 마땅한 대응이 없다.
- 진짜 문제는 null 검사가 빠진 것이 아니라 너무 많다는 것이다. null을 없애면 NPE 가능성이 줄고 코드도 깔끔해진다.

```java
// Bad: 예약이 없으면 null → 모든 호출부가 검사해야 한다
List<Reservation> reservations = reservationService.findByMember(memberId);
if (reservations != null)
    for (Reservation r : reservations) { points += r.earnedPoints(); }
// Good: 없으면 빈 리스트를 반환한다. null을 줄 수 있는 외부 API는 여기서 감싼다
public List<Reservation> findByMember(MemberId memberId) {
    List<Reservation> found = vendorBookingClient.fetch(memberId);
    return found != null ? found : Collections.emptyList();
}
for (Reservation r : reservationService.findByMember(memberId)) { points += r.earnedPoints(); }
```

## Don't Pass Null — null을 넘기지 않는다

**어떻게**

- 메서드에 null을 가능한 한 넘기지 않는다(null을 받도록 설계된 API는 예외). 기본 규칙으로 금지하고, 인수 목록의 null은 문제의 신호로 읽는다.

**왜**

- null 반환보다 null 전달이 더 나쁘다. 메서드 안에서 null을 검사해 새 예외를 던지면 NPE보다 조금 나을 수는 있지만 그 예외의 handler가 할 수 있는 좋은 조치가 마땅치 않다. assert는 좋은 문서가 되지만 null이 들어오면 여전히 런타임 오류가 난다. 대부분의 언어에는 호출자가 실수로 넘긴 null을 잘 처리할 방법이 없다. 그래서 기본적으로 금지하는 것이 합리적이고, 그러면 부주의한 실수가 훨씬 줄어든다.

## 체크리스트

- [ ] 호출 직후 반환 코드·오류 플래그를 검사하는 코드가 본 로직을 가리고 있지 않은가?
- [ ] 무엇이 실패하든 catch가 프로그램을 일관된 상태로 남기는가? 예외 경로를 강제하는 테스트가 있는가?
- [ ] 하위 메서드의 checked 예외 때문에 여러 계층의 시그니처에 `throws`가 번지고 있지 않은가?
- [ ] 예외 메시지만 보고 어떤 연산이 어떤 이유로 실패했는지 알 수 있는가?
- [ ] 처리가 같은 catch를 반복하지 않고 공통 예외 하나로 번역해 잡는가? 예외 클래스는 호출자가 다르게 잡아야 할 때만 나눴는가?
- [ ] 기본값 적용 같은 업무 규칙을 catch에 숨기지 않고 특수 사례 객체로 처리했는가?
- [ ] null을 반환하지도 넘기지도 않고, 그 자리에 빈 컬렉션·특수 사례 객체·예외를 쓰는가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)): `G5` Duplication(반복되는 catch), `G23` Prefer Polymorphism to If/Else or Switch/Case(특수 사례 객체로 분기 제거), `G26` Be Precise(null을 반환할 수 있는 함수를 부른다면 검사한다. 이 장에서는 그 검사를 감싸는 메서드 한 곳에 모은다)
- [chapter_03_functions.md](chapter_03_functions.md) — 오류 코드보다 예외, try/catch 블록 추출, 오류 처리도 한 가지 작업
- [chapter_08_boundaries.md](chapter_08_boundaries.md) — 서드파티 API를 감싸 경계를 관리한다
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — TDD 세 가지 법칙과 깨끗한 테스트. 이 장에서 예외를 강제하는 테스트부터 쓰는 절차도 그 법칙을 따른다

## 원서 밖 보충

- 원서 이후 Java 8의 `Optional`이 생겨 "값이 없을 수 있음"을 반환 타입으로 드러낼 수 있다(필드·매개변수에는 쓰지 않는 것이 흔한 권고다). `@Nullable`/`@NonNull` 애너테이션과 정적 분석(NullAway 등)을 쓰면 "null 전달 금지"를 컴파일 단계에서 기계적으로 강제할 수 있다. `Objects.requireNonNull`은 진입 지점에서 바로 실패하게(fail-fast) 하는 런타임 검사여서, 원서가 조금 나을 뿐이라고 본 방식(검사 후 예외 던지기)과 성격이 같다.
- try-with-resources(Java 7)가 finally에서 자원을 닫는 코드를 대신하고, multi-catch(`catch (A | B e)`)가 같은 처리의 catch 반복을 줄인다. 예외를 번역할 때는 원인 예외를 cause로 넘겨 스택 트레이스를 보존한다. 원서는 checked 예외 논쟁이 끝났다고 보지만 지금도 의견이 갈린다. Java 표준 API는 여전히 checked 예외를 쓰고, 람다·스트림 안에서 특히 불편해 `UncheckedIOException` 같은 래퍼가 추가되었다.
