---
summary: 애그리거트 경계를 불변식과 트랜잭션으로 긋는 절차, 크기 판단 체크리스트, 애그리거트 간 ID 참조 원칙과 INV- 불변식 연결
read_when: [model, apply, review]
---

## 개념

애그리거트는 **함께 지켜야 하는 불변식의 단위**다. 객체 그래프를 예쁘게 묶은 결과가 아니라,
"이것과 저것이 동시에 참이어야 한다"는 업무 규칙이 먼저 있고 그 규칙이 경계를 그린다.

| 역할 | 뜻 | 밖에서 보이는가 |
|---|---|---|
| 애그리거트 루트 | 경계의 유일한 입구. 모든 상태 변경이 루트의 메서드를 통과한다 | 보인다 |
| 내부 엔티티 | 루트 안에서만 식별되는 엔티티(주문 안의 품목) | 보이지 않는다 |
| 값 객체 | 식별자 없이 값으로 같음을 판정하는 구성 요소([[value-objects]]) | 보인다(복사본으로) |

경계가 결정하는 것은 셋이다 — **한 트랜잭션이 무엇을 바꾸는가**, **무엇을 ID로만 참조하는가**,
**리포지토리를 어느 단위로 두는가**([[repositories-domain-services]]).

애그리거트는 모든 컨텍스트에 필요하지 않다. [[domain-classification]]에서 `generic`으로 판정하고
[[layered-simple]]을 채택했다면 이 문서의 대부분은 비용이다 — 그 스타일에는 애그리거트 개념이
없고 `@Entity`가 곧 모델이다.

## 적용 기준

### 경계를 긋는 절차 — 불변식에서 시작한다

엔티티 목록에서 시작하면 반드시 큰 애그리거트가 나온다. 순서를 뒤집는다.

1. **불변식을 문장으로 적는다.** "확정된 주문의 합계는 0원보다 크다", "한 계좌의 잔액은 음수가
   될 수 없다". 각각 `INV-<CONTEXT>-NNN` ID를 받는다.
2. **각 불변식이 몇 개의 엔티티를 건드리는지 센다.** 한 엔티티 안에서 닫히면 그 엔티티가 곧
   경계다. 둘 이상을 걸치면 그것들이 한 애그리거트 후보다.
3. **후보들 중 겹치는 것을 합친다.** 같은 엔티티가 두 후보에 나오면 두 후보는 한 애그리거트다.
4. **합친 결과에 루트를 하나 고른다.** 밖에서 이름을 대고 찾는 것이 루트다.

불변식을 하나도 못 적으면 애그리거트를 만들 이유가 없다 — [[layered-simple]]의 적용 기준
3번(불변식이 필드 단위)에 해당하는지 먼저 확인한다.

### 크기 판단 체크리스트

아래 중 **둘 이상**에 해당하면 애그리거트를 쪼갠다.

- [ ] 루트가 소유한 컬렉션이 업무상 상한 없이 자란다(주문 100건이 아니라 고객의 전체 주문 이력).
- [ ] 한 요청이 애그리거트의 서로 다른 부분만 건드리는데 매번 전체를 로드한다.
- [ ] 두 사용자가 서로 다른 부분을 동시에 고치다 낙관적 락 충돌이 반복된다.
- [ ] 불변식 목록에서 "루트의 이 절반"과 "저 절반"을 함께 언급하는 문장이 하나도 없다.
- [ ] 애그리거트 안의 어떤 필드가 다른 컨텍스트의 소유물처럼 읽힌다 → 경계가 아니라
      [[bounded-contexts]]를 다시 본다.

반대로, 아래는 **쪼개면 안 된다는 신호**다.

- 두 부분을 항상 같은 트랜잭션에서 함께 바꾼다.
- 쪼갠 뒤 둘 사이의 정합을 애플리케이션 서비스가 손으로 맞춰야 한다 — 불변식이 코드 밖으로
  새어 나온 것이다.

### 경계 밖으로 밀 때 — 결과적 일관성

한 요청이 애그리거트 둘을 바꿔야 한다면 선택지는 둘뿐이다.

| 선택 | 조건 | 대가 |
|---|---|---|
| 하나로 합친다 | 두 쪽의 불변식이 실제로 얽혀 있다 | 애그리거트가 커진다 |
| 도메인 이벤트로 잇는다 | 두 번째 변경이 "잠깐 늦어도 되는" 것이다 | 결과적 일관성([[domain-events]]) |

"잠깐 늦으면 업무가 깨지는가"를 담당자에게 물어 답이 나오지 않으면 늦어도 되는 것이다.

## 규칙

기계로 판정할 수 있는 것이 거의 없는 영역이다 — 애그리거트 경계의 적정성은
`rule-vocabulary.md` §6의 마지막 항목("판정 기준이 사람의 해석에 달려 있으면 규칙이 아니다")에
해당한다. 따라서 아래는 대부분 리뷰 체크리스트이며, 기계에 닿는 지점은 R5 하나다.

### R1. 트랜잭션 1개 = 애그리거트 1개

하나의 트랜잭션은 **하나의 애그리거트 인스턴스만** 생성·변경한다. 조회는 이 제한을 받지 않는다.

- [ ] 애플리케이션 서비스 하나가 두 개 이상의 리포지토리에 `save`를 호출하는가?
- [ ] 그렇다면 둘이 한 애그리거트여야 하는가, 아니면 두 번째는 이벤트로 미뤄야 하는가?
- [ ] 예외로 남긴다면 근거가 ADR에 있는가? (초기 데이터 적재·마이그레이션은 정상적인 예외다)

### R2. 애그리거트 간 참조는 ID로만

다른 애그리거트를 객체 참조로 들지 않는다. `Order`는 `Customer`가 아니라 `CustomerId`를 갖는다.

- 지키면 얻는 것: 트랜잭션 경계가 타입으로 드러나고, 로딩 범위가 고정되며, 애그리거트를 나중에
  다른 컨텍스트로 옮길 수 있다.
- ID 타입은 원시 타입이 아니라 값 객체다(`CustomerId`, `OrderId`) — [[value-objects]] R4.
- 이 규칙을 어기면 영속 계층에서 양방향 연관과 lazy 프록시로 번져 나간다([[persistence]] R5).

### R3. 루트만 공개한다

- [ ] 내부 엔티티 타입이 애그리거트 밖(애플리케이션·어댑터)에서 참조되는가?
- [ ] 루트가 내부 컬렉션을 그대로 반환하는가? 방어적 복사(`toList()`) 또는 읽기 전용 뷰여야 한다.
- [ ] 내부 엔티티를 위한 리포지토리가 따로 있는가? 있으면 그것은 별도 애그리거트라는 선언이다
      ([[repositories-domain-services]] R2).

### R4. 불변식은 루트 안에서 강제된다

- [ ] 각 `INV-` 항목마다 그것을 깨려는 호출을 거부하는 코드가 루트에 있는가?
- [ ] 검증이 애플리케이션 서비스나 컨트롤러에 있는가? → 다른 진입점이 생기면 우회된다.
- [ ] 상태를 바꾸는 public setter가 있는가? setter는 불변식을 우회하는 가장 흔한 경로다.
- [ ] `proposed` 상태의 불변식을 이미 구현했는가? 확정 전에는 구현하지 않는다.

`scripts/check_invariants.py`가 이 체크리스트를 두 지점에서 거든다 — `docs/architecture/domain/`의
`INV-<CONTEXT>-NNN`과 테스트의 `@Tag("INV-...")`를 대조해 **confirmed인데 태그가 없으면 위반**,
**`proposed`인데 태그가 있으면 경고**(넷째 항목)를 낸다. 문서에 그 항목을 채우는 것은
`/superarchitect:model`이고 구현·태깅은 `/superarchitect:apply`다.

**나머지 셋은 기계가 판정하지 못한다.** 태그가 달렸다는 것은 그 테스트가 불변식을 실제로
검증한다는 뜻도, 강제가 **루트 안**에 있다는 뜻도 아니기 때문이다. 그 대조는 리뷰의 의미론
판정으로 남는다(`agents/domain-reviewer.md` C3).

### R5. 애그리거트는 도메인 레이어에 산다

애그리거트 루트·내부 엔티티·값 객체는 전부 도메인 레이어의 순수 타입이다. 이 한 가지는 기계가
본다 — `*.domain-pure`(primitive: `confine-type`)와 `*.domain-no-framework`(`forbid-import`)가
`@Entity`와 프레임워크 import를 도메인 밖으로 밀어낸다([[hexagonal]] R2·R3). 애그리거트를 JPA
엔티티로 직접 쓰고 싶다면 규칙 예외가 아니라 스타일 선택을 다시 본다([[persistence]]).

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.order.domain — 순수. 프레임워크 import 없음
package com.acme.order.domain

class Order private constructor(
    val id: OrderId,
    val customerId: CustomerId,                  // R2: 다른 애그리거트는 ID로만
    private val lines: MutableList<OrderLine>,   // R3: 내부 엔티티는 감춘다
    private var status: OrderStatus,
) {
    val total: Money get() = lines.fold(Money.ZERO) { acc, line -> acc + line.amount }

    fun addLine(line: OrderLine) {
        require(status == OrderStatus.DRAFT) { "확정된 주문은 품목을 바꿀 수 없다" }
        require(lines.size < MAX_LINES) { "품목은 최대 ${MAX_LINES}개다" }   // INV-ORDER-002
        lines += line
    }

    fun place(): OrderPlaced {                                              // R4: 루트가 강제한다
        require(status == OrderStatus.DRAFT) { "이미 확정된 주문이다" }
        require(total.isPositive()) { "합계가 0원인 주문은 확정할 수 없다" } // INV-ORDER-001
        status = OrderStatus.PLACED
        return OrderPlaced(id, total)            // 적립은 이벤트로 미룬다 — R1
    }

    fun lines(): List<OrderLine> = lines.toList()   // R3: 방어적 복사

    companion object {
        const val MAX_LINES = 100
        fun draft(id: OrderId, customerId: CustomerId) =
            Order(id, customerId, mutableListOf(), OrderStatus.DRAFT)
    }
}
```

`OrderPlaced`를 커밋 경계에서 방출하면 적립 애그리거트는 별도 트랜잭션에서 바뀐다
([[domain-events]] R2).

### 안티패턴 1 — 한 트랜잭션이 두 애그리거트를 바꾼다

```kotlin
class Order(
    val customer: Customer,                     // R2 위반: 객체 참조
    val lines: MutableList<OrderLine>,          // R3 위반: 밖에서 바꿀 수 있다
) {
    fun place() {
        status = OrderStatus.PLACED
        customer.addPoint(total)                // R1 위반: 두 번째 애그리거트를 함께 바꾼다
    }
}
```

증상은 코드가 아니라 운영에서 나타난다. 적립 로직이 실패하면 주문 확정까지 롤백되고, 락 범위가
고객 단위로 넓어져 같은 고객의 주문이 서로를 기다린다. `Customer`를 `CustomerId`로 바꾸는 순간
이 두 문제가 함께 사라진다.

### 안티패턴 2 — 상한 없는 컬렉션

```kotlin
class Customer(
    val id: CustomerId,
    val orders: MutableList<Order>,             // 3년 차 고객이면 수천 건
) {
    fun place(order: Order) { orders += order }
}
```

주문 하나를 추가하려고 고객의 전체 주문을 로드한다. 크기 체크리스트의 첫 항목이 이것이고, 답은
언제나 같다 — `Order`를 별도 애그리거트로 분리하고 `Order.customerId`로 잇는다. "고객의 주문
목록"이 필요하면 그것은 조회이지 애그리거트가 아니다([[cqrs]]).

## 관련 문서

- [[value-objects]] — 애그리거트를 구성하는 값 타입과 ID 타입
- [[domain-events]] — R1을 어기지 않고 두 애그리거트를 잇는 방법
- [[repositories-domain-services]] — 리포지토리는 애그리거트 단위로 하나
- [[persistence]] — 애그리거트를 영속 엔티티로 옮기는 매핑의 위치
- [[bounded-contexts]] — 애그리거트가 아니라 컨텍스트를 다시 그어야 하는 경우
- [[domain-classification]] — 애그리거트를 모델링할 가치가 있는 컨텍스트를 가린다
- [[layered-simple]] — 애그리거트 개념 없이 가는 것이 정답인 경우
- [[cqrs]] — 조회 요구가 애그리거트 경계를 밀어낼 때
