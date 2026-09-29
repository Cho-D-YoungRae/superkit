---
summary: 순수 도메인 모델과 영속 엔티티 분리 전략 — 매핑 위치, 영속 코드 격리, lazy loading·양방향 연관 안티패턴, JPA 직접 사용이 정당한 조건
read_when: [apply, review, migrate]
---

## 개념

도메인 모델과 영속 엔티티는 목적이 다르다. 도메인 모델은 **불변식을 지키는 것**이 일이고, 영속
엔티티는 **테이블 한 행을 표현하는 것**이 일이다. 두 목적이 충돌하기 때문에 분리가 존재한다 —
`private` 필드와 방어적 복사는 첫 번째를 돕고 두 번째를 방해하며, 기본 생성자와 가변 필드는 그
반대다.

| | 도메인 모델 | 영속 엔티티 |
|---|---|---|
| 이름 | `Order` | `OrderJpaEntity` |
| 사는 곳 | 도메인 모델 쪽 | 영속 코드 쪽 |
| 강제하는 것 | 업무 불변식 | 스키마 제약 |
| 참조 방식 | 다른 애그리거트는 ID 값([[aggregates]] R2) | FK 컬럼 |
| 아는 것 | 없음 | 도메인 모델(매핑을 위해) |

**매핑은 영속 코드의 책임이다.** 도메인은 자기가 저장된다는 사실조차 모른다. **이 플러그인은
그 두 자리에 이름을 붙이지 않는다** — 패키지 이름과 배치 관례는 프로젝트가 정하고, 이 문서가
정하는 것은 **무엇이 어느 쪽에 있어야 하는가**뿐이다.

| 무엇 | 어느 쪽 |
|---|---|
| 애그리거트 루트·엔티티·값 객체, 업무 규칙 | 도메인 모델 쪽 |
| `@Entity`·`@Table`·JPA 리포지터리 인터페이스·매핑 함수·컨버터 | 영속 코드 쪽 |
| 두 쪽을 잇는 인터페이스 | 도메인이 필요로 하는 것을 도메인 쪽이 선언하고, 구현은 영속 코드 쪽 |

**`generic`으로 분류한 컨텍스트는 이 분리를 하지 않아도 된다** — 영속 엔티티가 곧 모델인 것이
그 분류의 기본값이다([[domain-classification]]의 "분류가 정하는 것의 기본값" 절).

## 적용 기준

### 분리 여부는 이미 결정되어 있다

이 문서를 읽으며 "우리는 분리할까"를 새로 고민하는 것은 순서가 틀렸다. 분리 여부는 **분류의
결과**다([[domain-classification]]의 "분류가 정하는 것의 기본값" 절) — `core`·`supporting`은
분리가 기본값이고 `generic`은 아니다. **분리하지 않기로 하려면 이 문서가 아니라 분류를 다시 봐야 한다.**

### JPA 직접 사용이 정당한 조건

아래 넷을 모두 만족하면 분리는 비용일 뿐이며, `generic`으로 분류하고 영속 엔티티를 그대로 모델로
쓰는 것이 정직한 선택이다.

1. 분류가 `generic`이다 — 대체 제품 이름을 실제로 댈 수 있다.
2. 커맨드가 전부 한 애그리거트(사실상 한 행 묶음) 저장으로 끝난다.
3. 불변식이 필드 단위다 — 널·범위·유일성 수준이어서 DB 제약과 검증으로 표현된다.
4. 이 컨텍스트를 통째로 외부 제품으로 교체하거나 삭제하는 시나리오가 이상하지 않다.

**넷을 만족하지 못하는데 분리만 면제받는 길은 없다.** 예외 요청이 나오면 분류 선택을 다시
본다([[domain-classification]]의 "근거" 절). 되돌리는 비용이 비대칭이기 때문이다 — 순수 모델에서
JPA 직접 사용으로 내려가는 것은 매핑 코드를 지우는 기계적 작업이지만, 반대 방향은 lazy loading과
양방향 연관에 의존하는 코드가 쌓인 뒤에는 사실상 재작성이다.

### 매핑 코드를 어디에 어떻게 두는가

- 위치는 **영속 코드가 사는 자리 안**이다. 거기서 한 줄도 나가지 않는다.
- 형태는 자유다. Kotlin 확장 함수(`internal fun OrderJpaEntity.toDomain()`)든 매퍼 클래스든
  상관없다. 다만 **확장 함수를 도메인 패키지에 선언하지 않는다** — 파일이 도메인에 있으면 도메인이
  엔티티 타입을 참조하는 것이 되어 분리가 그 자리에서 무너진다.
- 도메인 모델에 `toEntity()`를 두지 않는다. 매핑 방향은 언제나 바깥 → 안쪽 소유다.
- 매핑 라이브러리를 도입하기 전에 생각한다. 리플렉션 기반 자동 매핑은 필드 이름이 같아야 동작하고,
  그 요구가 도메인 모델을 스키마 모양으로 끌어당긴다. 손으로 쓴 매핑이 길다는 것은 대개 도메인
  모델이 아직 스키마의 복사본이라는 신호다.

### 분리가 값을 못 하고 있다는 신호

- 매핑 함수가 필드를 1:1로 옮기기만 하고, 도메인 모델에 메서드가 하나도 없다.
- 스키마를 바꿀 때마다 도메인 모델도 같이 바뀐다(반대 방향으로도 마찬가지다).
- 값 객체가 하나도 없고 도메인 모델의 필드가 전부 원시 타입이다([[value-objects]] R4).

셋 다 해당하면 위 "정당한 조건" 넷을 다시 세어 본다.

## 규칙

**아래는 전부 리뷰 판정 도구다.** 이 플러그인의 유일한 기계 강제 규칙
(`derived.context-isolation`)은 컨텍스트 **사이**의 참조만 보므로, 한 컨텍스트 안에서 영속 코드가
도메인으로 새는 것은 **어떤 검사도 잡지 못한다.** 그 사실이 이 문서의 규칙이 존재하는 이유다.

### R1. 영속 관심사는 영속 코드 안에서 끝난다

- `@Entity`·`@Table`·JPA 리포지터리 인터페이스·매핑 함수·컨버터가 전부 그 자리 안에 있다.
- 값 객체를 컬럼으로 펼치는 일, `@JvmInline value class`용 `AttributeConverter`를 두는 일도
  여기다([[value-objects]] R5).
- 영속 코드가 반환하는 것은 완성된 도메인 객체다. 도메인 객체를 만드는 데 필요한 복원 생성자·팩토리
  (`Order.restore(...)`)는 도메인이 제공한다 — 영속 코드가 `private` 필드를 리플렉션으로 채우지 않는다.

### R2. 누수 형태 아홉 — 전부 리뷰가 본다

아래 아홉은 위쪽 다섯(선언·import·시그니처·파일 위치처럼 **눈에 보이는 배치**)과 아래쪽 넷(배치는
맞는데 분리를 무력화하는 것)으로 나뉜다. **어느 쪽도 기계가 잡지 않으므로 리뷰가 아홉 전부를 본다.**

| 누수 형태 | 어디를 보면 드러나는가 | 근거 |
|---|---|---|
| 도메인·유스케이스 코드에서 `@Entity` 선언 | 선언 위치 — 파일 경로와 패키지 | R1 |
| 도메인이 필요로 하는 인터페이스 시그니처에 `OrderJpaEntity` | 시그니처의 타입 | R1 |
| 매핑 확장 함수를 도메인 패키지에 선언 | 파일 위치(도메인이 엔티티를 참조하게 된다) | R1 |
| 도메인이 `jakarta.persistence.*`를 import(`@Id` 등) | 도메인 파일의 import 목록 | R1 |
| 영속 코드가 `Map<String, Any>`·`Any`로 감싸 반환 | 반환 타입 | R1 |
| lazy 프록시가 영속 코드 밖에서 초기화됨 | 트랜잭션 밖 접근·런타임 예외 | R4 |
| 양방향 연관으로 애그리거트 둘이 묶임 | 엔티티의 연관 매핑 | R5 |
| 도메인 모델에 `version`·`createdAt`이 올라옴 | 도메인 필드 목록 | R3 |
| 도메인 필드가 테이블 컬럼과 1:1(값 객체 0개) | 도메인 모델의 행위 유무 | 위 "값 못 하는 신호" |

**위쪽 다섯이 아래쪽 넷보다 싸게 잡힌다.** 앞의 것들은 파일 하나를 열어 선언과 import를 보면
판정이 서고, 뒤의 것들은 실행 시점의 현상이거나 여러 파일을 함께 봐야 한다. 리뷰의 시간을 그
순서로 쓴다 — 다만 **어느 것도 생략하지 않는다.** 여기서 빠지면 아무도 보지 않는다.

### R3. 영속 관심사는 도메인 모델로 올라오지 않는다

- 감사 컬럼(`createdAt`, `updatedAt`, `createdBy`)은 영속 엔티티에만 둔다. 업무 규칙이 그 시각을
  쓴다면 그것은 감사 컬럼이 아니라 도메인 값이므로 이름을 업무 용어로 바꾼다(`placedAt`).
- **식별자는 저장 전에 정해진다.** DB 자동 채번에 의존하면 저장 전 도메인 객체의 ID가 `null`이
  되고, 그 널 가능성이 도메인 전체로 번진다. UUID나 채번 포트로 애플리케이션에서 먼저 발급한다.
- **낙관적 락 `version`은 영속 엔티티의 것이다.** 분리 구조에서는 로드한 버전을 저장 시점까지
  옮길 방법이 필요한데, 영속 코드가 트랜잭션 스코프에 (id → version)을 보관하는 것이 도메인을 깨끗이
  두는 방법이다. 도메인이 불투명한 정수 하나를 들고 다니는 타협도 가능하지만, **그 값을 업무
  규칙에 쓰지 않는다**는 조건이 붙는다.

### R4. lazy loading은 영속 코드 밖으로 나가지 않는다

- 매핑은 영속 코드 안에서 **완결**한다. 필요한 연관은 명시적으로 페치(fetch join·엔티티 그래프)하고
  도메인 값으로 **복사**한다. 도메인 모델에는 지연 로딩 개념이 없다.
- 프록시가 밖으로 나가는 경로는 둘뿐이다 — 엔티티를 그대로 반환하거나(R2 표의 둘째 행), 매핑
  함수가 지연 컬렉션을 복사하지 않고 참조만 옮기는 경우다.
- **OSIV(`spring.jpa.open-in-view`)는 끄는 것을 기본으로 한다.** 켜져 있으면 누수가 예외로
  드러나지 않고 컨트롤러 렌더링 중에 쿼리가 나가 조용히 N+1이 된다. 예외가 나는 편이 낫다.
- 영속 코드 밖에서 도메인 객체를 다룰 때 추가 쿼리가 나가면 안 된다 — 리뷰에서 확인할 항목이다.

### R5. 양방향 연관은 애그리거트 경계를 지운다

- 애그리거트 경계를 넘는 연관은 영속 엔티티에서도 **FK 값 컬럼**이다. `@ManyToOne CustomerJpaEntity`가
  아니라 `customerId: String`이다([[aggregates]] R2).
- 애그리거트 **내부**(루트 → 내부 엔티티)의 `@OneToMany`는 정상이며, 단방향 소유
  (`@JoinColumn` + `cascade` + `orphanRemoval`)로 둔다.
- 양방향은 언제나 편의로 추가되고, 그 편의가 경계를 지운다 — 어느 쪽이 연관의 주인인지 흐려지고,
  동기화 편의 메서드를 빠뜨리면 상태가 갈라지며, 연쇄 저장이 트랜잭션 범위를 넓힌다.
- 양방향이 필요하다고 느끼면 대개 **조회 요구**다. 조회 전용 경로로 해결한다
  ([[repositories-domain-services]] R3, [[cqrs]]).

### R6. 리뷰 체크리스트

- [ ] 매핑이 영속 코드 안에서 **완결**되는가? 지연 컬렉션을 도메인 값으로 복사했는가, 참조만
      옮겼는가? (매핑 코드의 **위치**는 R2 표의 위쪽 다섯에서 이미 본다)
- [ ] 도메인 객체를 다루는 코드가 트랜잭션 밖에서 추가 쿼리를 유발하는가?
- [ ] `spring.jpa.open-in-view`가 꺼져 있는가?
- [ ] 애그리거트 경계를 넘는 `@ManyToOne`·양방향 `@OneToMany`가 있는가?
- [ ] 도메인 모델에 `version`·감사 컬럼·널 가능 ID가 있는가?
- [ ] 매핑이 1:1 복사뿐이고 도메인 모델에 행위가 없는가? → 분류 선택을 다시 본다

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.order.adapter.out.persistence — JPA는 여기서 끝난다 (R1)
package com.acme.order.adapter.out.persistence

@Entity
@Table(name = "orders")
class OrderJpaEntity(
    @Id val id: String,
    @Column(name = "customer_id") val customerId: String,       // R5: FK 값, 객체 참조 아님
    @Enumerated(EnumType.STRING) var status: OrderStatus,
    @OneToMany(cascade = [CascadeType.ALL], orphanRemoval = true)
    @JoinColumn(name = "order_id")                              // 애그리거트 내부 — 단방향 소유
    val lines: MutableList<OrderLineJpaEntity> = mutableListOf(),
    @Version var version: Long = 0,                             // R3: 영속 관심사는 여기 산다
)

internal fun OrderJpaEntity.toDomain(): Order = Order.restore(  // R1: 복원 팩토리는 도메인이 제공
    id = OrderId(id),
    customerId = CustomerId(customerId),
    lines = lines.map { it.toDomain() },                        // R4: 여기서 복사한다
    status = status,
)

@Repository
class OrderPersistenceAdapter(
    private val jpa: OrderJpaRepository,
) : LoadOrderPort, SaveOrderPort {
    override fun findById(id: OrderId): Order? =
        jpa.findWithLinesById(id.value)?.toDomain()             // R4: 연관을 명시적으로 페치
    override fun save(order: Order) { jpa.save(order.toJpaEntity()) }
}
```

인터페이스 시그니처에 도메인 타입만 있으므로 도메인·유스케이스 코드는 JPA가 있는지도 모른다.
매핑을 영속 코드 안에서 완결했기 때문에 프록시가 밖으로 나갈 경로 자체가 없다.

### 안티패턴 1 — 엔티티가 새고, 프록시가 따라 나간다

```kotlin
// com.acme.order.application.LoadOrderPort
interface LoadOrderPort { fun findById(id: OrderId): OrderJpaEntity? }   // R2: 시그니처 누수

// com.acme.order.adapter.in.web.OrderController
@GetMapping("/orders/{id}")
fun get(@PathVariable id: String): OrderResponse {
    val entity = loadOrder.findById(OrderId(id)) ?: throw OrderNotFound(OrderId(id))
    return OrderResponse(entity.lines.map { it.name })   // 트랜잭션 밖에서 프록시 초기화
}
```

첫 줄은 시그니처만 봐도 드러난다(R2 표 둘째 행). 그것을 놓치면 두 번째 문제가 남는다 — OSIV가 꺼져
있으면 `LazyInitializationException`이 나고, 켜져 있으면 예외 대신 렌더링 중에 쿼리가 나가
목록 화면에서 N+1이 된다. **후자가 더 나쁘다.** 성능 문제로만 보여서 원인이 설계라는 사실이
가려지기 때문이다.

### 안티패턴 2 — 양방향 연관으로 애그리거트 둘을 묶는다

```kotlin
@Entity
class OrderJpaEntity(
    @ManyToOne(fetch = FetchType.LAZY) var customer: CustomerJpaEntity,   // 경계를 넘는 객체 참조
)

@Entity
class CustomerJpaEntity(
    @OneToMany(mappedBy = "customer", cascade = [CascadeType.ALL])
    val orders: MutableList<OrderJpaEntity> = mutableListOf(),            // 상한 없는 컬렉션
)
```

이 코드는 영속 코드 안에 있으므로 배치만 보면 아무 문제가 없다. 그런데도 분리는 무효가 된다 — 주문
하나를 저장하려고 고객 전체를 로드하고, 고객을 저장하면 주문 전부가 flush 대상이 되며, 락 범위가
고객 단위로 넓어진다. 도메인 모델에서 `CustomerId`로 잘라 놓은 경계를 스키마가 다시 붙여 버린
것이고, 이것이 R2 표의 아래쪽에 양방향 연관이 있는 이유다.

## 관련 문서

- [[aggregates]] — 경계를 넘는 참조를 ID로 두는 원칙, 영속 연관 설계의 근거
- [[value-objects]] — 값 객체를 컬럼으로 펼치는 매핑과 value class 컨버터
- [[repositories-domain-services]] — 매핑을 수행하는 리포지토리 구현의 책임 범위
- [[domain-classification]] — 분리 여부가 결정되는 상류. `generic`은 분리하지 않는 것이 정답인 경우의 종착지다
- [[cqrs]] — 조회 요구가 연관 설계를 밀어낼 때
