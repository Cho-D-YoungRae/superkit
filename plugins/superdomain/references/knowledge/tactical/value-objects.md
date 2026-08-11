---
summary: 값 객체의 불변성·구조적 동등성 강제 방법, 원시 타입 강박 승격 기준, Kotlin data class와 value class 선택 기준
read_when: [model, apply, review]
---

## 개념

값 객체는 **식별자가 없고 값으로 같음을 판정하는 타입**이다. 1만원은 어느 1만원이든 같은 1만원
이고, "그 1만원"을 추적할 이유가 없다. 엔티티와의 차이는 하나뿐이다.

| | 엔티티 | 값 객체 |
|---|---|---|
| 같음의 기준 | 식별자가 같으면 같다 | 모든 구성 값이 같으면 같다 |
| 생애 | 상태가 바뀌며 이어진다 | 바뀌지 않는다. 바꾸려면 새로 만든다 |
| 소유 | 애그리거트 루트가 소유·관리한다 | 자유롭게 복사·공유해도 안전하다 |

값 객체가 하는 일은 셋이다 — **이름을 붙여 의미를 드러내고**, **생성 시점에 검증해 유효하지 않은
값이 도메인에 들어오지 못하게 막고**, **그 값에 딸린 연산을 한곳에 모은다.** 셋 중 하나도 해당하지
않으면 그것은 값 객체가 아니라 래퍼다.

## 적용 기준

### 원시 타입을 승격하는 신호 — 둘 이상이면 값 객체로 만든다

- [ ] 같은 원시 타입 인자가 둘 이상 나란히 있고 **순서를 바꿔도 컴파일된다**
      (`transfer(from: String, to: String, amount: Long)`).
- [ ] 그 값에 검증 규칙이 있다 — 형식·범위·길이·허용 집합.
- [ ] 그 값에 도메인 연산이 있다 — 금액 더하기, 기간 겹침 판정, 비율 적용.
- [ ] 항상 함께 다니는 필드 묶음이 있다 — 금액+통화, 시작일+종료일, 우편번호+주소.
- [ ] 같은 설명 주석을 여러 곳에 반복해서 쓰고 있다("단위는 원, 음수 불가").

**식별자는 신호를 세지 않고 무조건 승격한다.** 애그리거트 간 참조는 ID로만 하므로
([[aggregates]] R2) `String`·`Long` ID가 섞이면 다른 애그리거트의 ID를 넘겨도 컴파일된다.
`OrderId`와 `CustomerId`가 다른 타입이면 그 사고가 컴파일 오류가 된다.

### 만들지 않는 경우

- 규칙도 연산도 없는 표시용 문자열(`description`, `memo`). 이름만 늘어난다.
- 어댑터의 요청·응답 DTO 필드. 승격은 경계 **안쪽**에서 한다 — 매핑 지점에서 원시 타입을 값
  객체로 바꾸는 것이 어댑터의 일이다([[persistence]]).
- 값의 집합이 고정되어 열거 가능하다 → `enum class`가 답이다.
- 도메인 어휘에 없는 이름이 나온다(`NonEmptyString`, `PositiveLong`). 기술 래퍼는 값 객체가
  아니다. 업무 담당자가 쓰는 말이 이름이 되어야 한다.

### data class와 value class 선택

| | `data class` | `@JvmInline value class` |
|---|---|---|
| 구성 값 | 둘 이상 | **정확히 하나** |
| 전형적 용도 | 함께 다니는 값 묶음 + 연산(`Money`, `DateRange`) | 원시 타입 하나에 이름·검증을 붙임(ID·코드·수량) |
| 런타임 표현 | 객체 하나 | 대개 원시값 그대로(래퍼 없음) |
| 검증 | `init` 블록 | `init` 블록(가능하다) |
| 주의 | 자동 `equals`는 **주 생성자 프로퍼티만** 본다 | 아래 R5의 세 가지 한계 |

구성 값이 하나여도 `data class`를 쓰는 것은 틀리지 않는다. `value class`는 성능이 문제가 되거나
ID 타입처럼 대량으로 생성되는 경우의 최적화이며, R5의 한계를 감당할 수 있을 때만 고른다.

## 규칙

### R1. 불변 — 모든 프로퍼티는 `val`

- 프로퍼티는 전부 `val`. `var`가 하나라도 있으면 값 객체가 아니다.
- 컬렉션을 담으면 읽기 전용 타입(`List`)으로 선언하고 **생성자에서 방어적으로 복사한다**.
  `List`로 선언해도 호출자가 넘긴 것이 `MutableList`면 밖에서 바뀐다.
- 상태를 바꾸는 메서드는 자기를 고치지 않고 **새 인스턴스를 반환한다**(`plus`, `withCurrency`).

### R2. 동등성은 구조적 동등성이다

- `data class`가 생성하는 `equals`/`hashCode`에 맡긴다. 손으로 쓰지 않는다.
- **주 생성자에 없는 프로퍼티는 `equals`에서 빠진다.** 본문에 선언한 프로퍼티가 값의 일부라면
  그것은 주 생성자로 올라가야 한다 — 조용히 무시되는 흔한 함정이다.
- `Array`를 프로퍼티로 두지 않는다. `Array`의 `equals`는 참조 비교라 구조적 동등성이 깨진다.
- 값 객체를 `Set`의 원소나 `Map`의 키로 쓰는 코드가 있으면 R1·R2 위반은 즉시 데이터 유실이 된다.

### R3. 유효하지 않은 인스턴스는 존재할 수 없다

- 검증은 `init` 블록에서 하고, 실패는 예외로 즉시 끝낸다. `isValid()` 같은 사후 검사 메서드를
  두지 않는다 — 부르지 않으면 그만이다.
- `copy()`도 주 생성자를 호출하므로 `init` 검증을 통과한다. 검증을 `init`에 두어야 하는 이유가
  이것이다(팩토리 함수에만 두면 `copy()`로 우회된다).
- 입력이 신뢰할 수 없는 곳에서 온다면 예외 대신 `Result`나 팩토리를 함께 제공한다. 다만
  **생성자 검증을 없애는 것이 아니라 추가하는 것**이다.

### R4. 원시 타입 강박 — 시그니처에서 잡는다

- [ ] public 메서드 시그니처에 같은 원시 타입이 둘 이상 연달아 있는가?
- [ ] 애그리거트 간 참조가 `String`·`Long`인가? → 무조건 승격(위 적용 기준).
- [ ] 금액이 `Long`·`BigDecimal` 단독인가? 통화가 어디에 있는지 물어본다.
- [ ] 같은 검증 코드(`require(x > 0)`)가 두 곳 이상에 있는가? → 그 값이 값 객체를 요구하고 있다.

### R5. value class를 고르기 전에 확인할 세 가지

`@JvmInline value class`는 다음 상황에서 **박싱되어 최적화가 사라진다** — 성능이 채택 이유였다면
먼저 확인한다.

1. **nullable로 쓸 때**(`ClaimId?`), **제네릭 타입 인자로 쓸 때**(`List<ClaimId>`),
   인터페이스 타입으로 취급될 때.
2. **JVM 함수 이름 맹글링** — value class를 파라미터로 받는 함수는 JVM 시그니처 이름이 바뀐다.
   Java 코드나 리플렉션 기반 도구에서 그 함수를 직접 부르는 경로가 있으면 영향을 받는다.
3. **프레임워크 지원** — JPA·직렬화 라이브러리는 value class를 그대로 매핑하지 못하는 경우가
   있어 컨버터가 필요하다. 그 컨버터는 도메인이 아니라 **어댑터에 둔다**([[persistence]] R1).

### R6. 값 객체는 도메인 레이어의 순수 타입이다

`@Entity`·`@Embeddable`·`jakarta.persistence.*`·검증 프레임워크 애노테이션을 값 객체에 붙이지
않는다. `*.domain-pure`(`confine-type`)와 `*.domain-no-framework`(`forbid-import`)가 기계로
막는 지점이다([[hexagonal]] R2·R3). 값 객체를 컬럼으로 펼치는 일은 어댑터의 매핑 코드가 한다.

### R7. 리뷰 체크리스트

- [ ] `var` 프로퍼티나 setter를 가진 값 객체가 있는가?
- [ ] 주 생성자 밖에 선언된 프로퍼티가 값의 일부인가?
- [ ] 검증이 `init`이 아니라 호출부에 흩어져 있는가?
- [ ] 값 객체 이름이 업무 용어인가, 기술 용어인가?
- [ ] 어댑터 DTO를 값 객체로 승격해 도메인 어휘를 오염시키고 있지 않은가?

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.order.domain — 순수. 프레임워크 애노테이션 없음 (R6)
package com.acme.order.domain

@JvmInline
value class OrderId(val value: String) {          // 구성 값 하나 → value class
    init { require(value.isNotBlank()) { "OrderId는 빈 값일 수 없다" } }   // R3
}

@JvmInline
value class CustomerId(val value: String)         // OrderId와 다른 타입 — 뒤바꾸면 컴파일 오류

data class Money(                                  // 함께 다니는 두 값 → data class
    val amount: BigDecimal,
    val currency: Currency,
) : Comparable<Money> {
    init {                                         // R3: copy()도 이 검증을 통과한다
        require(amount.scale() <= currency.defaultFractionDigits) { "허용 소수 자리를 넘었다" }
    }

    operator fun plus(other: Money): Money {       // R1: 새 인스턴스를 반환한다
        require(currency == other.currency) { "통화가 다르면 더할 수 없다" }
        return copy(amount = amount + other.amount)
    }

    fun isPositive(): Boolean = amount > BigDecimal.ZERO

    override fun compareTo(other: Money): Int {
        require(currency == other.currency) { "통화가 다르면 비교할 수 없다" }
        return amount.compareTo(other.amount)
    }

    companion object { val ZERO = Money(BigDecimal.ZERO, Currency.getInstance("KRW")) }
}
```

`Money`가 통화를 함께 들기 때문에 "원화 합계에 달러를 더하는" 사고가 런타임 예외가 아니라
애초에 표현될 수 없는 상태가 된다.

### 안티패턴 1 — 가변 값 객체

```kotlin
data class Money(var amount: BigDecimal, val currency: Currency)   // R1 위반: var

val price = Money(BigDecimal("1000"), KRW)
val basket = mutableSetOf(price)
price.amount = BigDecimal("2000")        // 해시가 바뀐다
basket.contains(price)                   // false — 방금 넣은 원소를 못 찾는다
```

`var` 하나가 `Set`·`Map`에서 원소를 잃어버리게 만든다. 값 객체를 컬렉션 키로 쓰는 코드는 거의
항상 존재하므로, 이 버그는 발견될 때쯤 원인에서 멀리 떨어진 곳에서 터진다.

### 안티패턴 2 — 원시 타입 강박

```kotlin
fun transfer(from: String, to: String, amount: Long, currency: String)
```

인자 넷 중 셋이 `String`·`Long`이라 순서를 바꿔도 컴파일된다. `amount`의 단위(원인가 전인가),
`currency`의 표기(`KRW`인가 `krw`인가)는 호출부마다 다르게 가정되고 검증은 어디에도 없다.
승격 후에는 시그니처 자체가 문서가 된다.

```kotlin
fun transfer(from: AccountId, to: AccountId, amount: Money)
```

`from`과 `to`는 여전히 같은 타입이라 뒤바뀔 수 있다 — 이것은 값 객체가 풀어 주지 못하는 부분이며,
이름 있는 인자나 커맨드 타입으로 다룬다.

## 관련 문서

- [[aggregates]] — 값 객체가 구성 요소로 들어가는 단위, ID 타입 승격의 근거
- [[persistence]] — 값 객체를 컬럼으로 펼치는 매핑과 value class 컨버터의 위치
- [[domain-events]] — 이벤트 페이로드도 값 객체다(불변·구조적 동등성)
- [[hexagonal]] — 값 객체를 순수하게 유지하는 규칙(R2·R3)의 정의
- [[layered-simple]] — 값 객체 승격 없이 원시 타입으로 가는 것이 정당한 경우
