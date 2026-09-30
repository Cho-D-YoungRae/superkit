# 코딩 컨벤션

도메인 로직이 드러나고 테스트하기 쉬운 코드를 쓰기 위한 규칙이다. conventions 스킬과 convention-reviewer가 함께 읽는다.

- 적용 범위: Kotlin·Java, Spring, JPA.
- 대상 프로젝트의 CLAUDE.md나 문서에 다른 규칙이 있으면 그 규칙이 우선한다.
- `필수`는 벗어날 때 이유가 있어야 하고, `지향`은 가능한 한 따른다.
- 도메인 로직이 중요한 곳(DOMAIN.md 분류 core·supporting)에는 전부 적용한다. 분류가 generic인 도메인, 그리고 어드민·워커·배치처럼 도메인 로직이 얇은 곳은 「JPA는 인프라에 둔다」의 예외를 쓸 수 있다.

## 값은 타입으로 표현한다 `지향`
문자열·원시 타입 대신 의미 있는 타입을 쓴다. 단일 값은 `value class`로 감싸고 생성할 때 검증한다. 여러 값과 행위가 함께 다니면 data class로, 컬렉션에 붙는 로직은 일급 컬렉션으로 모은다.
- 이유: 잘못된 값이 생성 시점에 막히고, 타입이 곧 문서가 된다.

```kotlin
@JvmInline
value class Email(val value: String) {
    init { require("@" in value) { "invalid email: $value" } }
}
```

## 도메인 행위는 canXxx()로 실행 조건을 드러낸다 `지향`
실행 조건이 있는 행위는 그 조건을 `canXxx(): Boolean`으로 공개하고, `xxx()`는 시작할 때 `check(canXxx())`로 스스로를 지킨다. `Xxx`에는 도메인 동사를 쓴다(`canCancel()`/`cancel()`).
- 이유: 검증 로직이 도메인 안에 있으면서도 밖에서 물어볼 수 있다. application은 `canXxx()`로 먼저 확인하고 비즈니스 예외를 던진다(→ 「도메인은 표준 예외만 던진다」).

```kotlin
data class Order(val status: OrderStatus) {
    fun canCancel(): Boolean = status == OrderStatus.PAID

    fun cancel(): Order {
        check(canCancel()) { "cannot cancel order in $status" }
        return copy(status = OrderStatus.CANCELED)
    }
}
```

## 도메인 모델은 불변을 기본으로 한다 `지향`
도메인 모델의 필드는 `val`로 두고, 상태를 바꾸는 행위는 새 객체를 반환한다(`copy`).
- 예외: JPA 엔티티를 도메인으로 직접 쓰는 곳(→ 「JPA는 인프라에 둔다」).

## 계산은 도메인, 조회는 리포지토리 `필수`
DB에서 가져오는 일은 리포지토리가 맡고, 가져온 값으로 계산·집계·판단하는 일은 도메인 객체(`create()` 같은 팩토리 포함)가 맡는다. 서비스는 둘을 잇기만 한다.
- 이유: 도메인 로직이 한곳에 모이고, DB 없이 단위 테스트할 수 있다.

```kotlin
val rows = matchRepository.findAll(period)      // 조회
val stats = WinRateStatistics.create(rows)      // 계산
```

## 다른 도메인은 ID로 참조한다 `필수`
도메인 객체는 다른 도메인의 객체를 필드로 들지 않고 ID(가능하면 값 타입)로 참조한다. 여러 도메인의 데이터를 조합해야 하면 application 계층에서 조합한다.
- 이유: 도메인 경계가 코드에서도 유지되고, 한 도메인의 변경이 다른 도메인 모델로 번지지 않는다.

## 자명하지 않은 규칙은 KDoc으로 남긴다 `지향`
집계 규칙, 정합성 제약, "왜 이렇게 하지 않았는지" 같은 결정은 클래스·메서드 KDoc에 이유와 함께 남긴다. 코드가 무엇을 하는지는 쓰지 않는다.

## 도메인은 표준 예외만 던진다 `필수`
도메인 객체는 `require`·`check`·`error` 같은 표준 예외만 쓴다. 에러 코드를 담은 비즈니스 예외(`CoreException` 등)는 application 계층(서비스, application 리포지토리)이 `canXxx()`로 먼저 확인한 뒤 던진다.
- 이유: 도메인은 응답 규칙을 몰라도 되고, 도메인 안의 예외는 "확인 없이 호출했다"는 프로그래밍 오류 신호로 남는다.

```kotlin
// application
if (!order.canCancel()) throw CoreException(ErrorType.ORDER_NOT_CANCELABLE)
orderRepository.save(order.cancel())
```

## DB가 필요한 검증은 판정 객체로 모은다 `지향`
검증에 DB의 사실(데이터가 있는지 등)이 필요할 때는 이렇게 한다.
- 사실 하나면 리포지토리의 boolean 조회로 충분하다(`isDeleted(id)`).
- 여러 사실이 조합된 규칙이면, 리포지토리가 사실을 담은 도메인 객체 `XxxEligibility`를 만들어 돌려주고 판정은 그 객체가 한다. application은 판정 결과를 보고 비즈니스 예외를 던진다.
- 이유: 규칙이 도메인 객체에 남아 DB 없이 테스트할 수 있다.
- 이름: `Condition`(Spring·검색 조건), `Validation`(Bean Validation), `Specification`(Spring Data JPA)은 기존 개념과 겹치므로 쓰지 않는다.

```kotlin
class PublishEligibility(
    private val hasActiveListing: Boolean,
    private val isSellerBlocked: Boolean,
) {
    fun isEligible(): Boolean = !hasActiveListing && !isSellerBlocked
}
```

## 현재 시각은 Clock에서 얻는다 `필수`
인자 없는 `now()`를 쓰지 않고, 주입받은 `Clock`에서 얻는다(`clock.instant()`, `LocalDateTime.now(clock)`). 도메인 메서드는 `Clock` 대신 `now`를 인자로 받는 것을 지향한다.
- 이유: 테스트에서 시간을 고정할 수 있고, 도메인이 시간의 출처에 의존하지 않는다.
- 테스트: `Clock`은 모킹하지 않고 `Clock.fixed(...)`를 쓴다.
- 예외: 감사용 생성·수정 시각(`@CreationTimestamp` 등).

```kotlin
fun canRenew(now: Instant): Boolean = ...     // 도메인
renewal.canRenew(clock.instant())             // application
```

## 정적 호출은 컴포넌트로 감싼다 `필수`
`UUID.randomUUID()`나 `Random`처럼 결과가 매번 달라지는 정적 호출은 컴포넌트로 감싸 주입받는다. 반환값은 문자열보다 타입(`UUID`)으로 둔다.
- 이유: 테스트에서 값을 고정할 수 있다.
- 테스트: 모킹하지 않고, 감싼 컴포넌트를 상속해 고정 값을 돌려주는 가짜로 바꿔 끼운다(Kotlin은 `kotlin("plugin.spring")`이 `@Component` 클래스를 열어 두므로 상속할 수 있다).

```kotlin
@Component
class UuidHolder {
    fun random(): UUID = UUID.randomUUID()
}
```

## JPA는 인프라에 둔다 `필수`
도메인 모델은 JPA에 의존하지 않는 순수 Kotlin·Java 클래스로 둔다. JPA 엔티티와 도메인 모델 사이의 변환은 application 계층의 리포지토리가 맡고, 서비스는 JPA 리포지토리를 직접 쓰지 않는다.
- 이유: 도메인 로직이 영속 기술의 제약(기본 생성자, 가변 필드, 지연 로딩)에 끌려가지 않는다.
- 예외: 도메인 로직이 얇은 곳(분류가 generic인 도메인, 어드민·워커·배치)은 JPA 엔티티를 직접 써도 된다.

## JPA 클래스 이름 `필수`

| 대상 | 이름 |
|---|---|
| 엔티티 | `XxxEntity` |
| Spring Data 리포지토리 | `XxxJpaRepository` (커스텀: `XxxJpaRepositoryCustom`, 구현: `XxxJpaRepositoryCustomImpl`) |
| `@Embeddable` 값 | `XxxEmbedded` |
| 조회 전용 결과 | `XxxProjection` |

## 외부 자원은 인터페이스 뒤에 둔다 `필수`
외부 API, 메시지 큐, 파일 저장소, 알림 같은 외부 자원은 application 계층에 인터페이스를 두고, 구현은 infrastructure에 둔다.
- 이유: application 코드가 특정 기술에 묶이지 않고, 테스트에서는 이 인터페이스만 대역으로 바꾸면 된다.

```kotlin
interface OrderEventPublisher { fun publish(event: OrderPaid) }     // application
class SqsOrderEventPublisher(...) : OrderEventPublisher { ... }     // infrastructure
```

## 모킹은 외부 자원에만 쓴다 `필수`
외부 자원(HTTP 클라이언트, DB, 메시지 큐 등)만 모킹한다. 도메인 객체와 내부 컴포넌트는 실제 객체를 쓰고, 값을 고정해야 하는 컴포넌트는 `Clock.fixed`나 상속한 가짜로 바꿔 끼운다.
- 이유: 모킹이 많을수록 테스트가 구현에 묶여 리팩터링 때 깨지고, 실제 동작은 검증하지 못한다.
- DB는 모킹할 수 있지만, application 리포지토리는 실제 DB로 검증하는 것을 지향한다. 모킹(stub-and-verify)은 호출만 검증하므로 실제 동작과 어긋날 수 있다.
- 예외: 컨트롤러 슬라이스 테스트는 application 계층을 모킹해도 된다.
