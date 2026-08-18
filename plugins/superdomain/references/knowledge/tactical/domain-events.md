---
summary: 도메인 이벤트의 발행 위치(애그리거트)와 시점(커밋 경계), 과거형 명명 규칙, 공개 이벤트를 관계 표 계약 칸에 등재하는 절차
read_when: [model, apply, review]
---

## 개념

도메인 이벤트는 **이미 일어난 업무 사실**이다. "주문이 확정되었다"는 취소할 수 없고, 듣는 쪽이
없어도 참이다. 이 점이 커맨드와의 유일하면서 결정적인 차이다 — 커맨드는 거부될 수 있고, 이벤트는
거부될 수 없다.

이벤트가 코드에서 이동하는 경로는 세 단계이고, 각 단계의 주인이 다르다.

| 단계 | 하는 일 | 주인 |
|---|---|---|
| 등록 | 상태를 바꾸면서 "무슨 일이 일어났는지" 이벤트 객체를 만든다 | 애그리거트 루트(domain) |
| 방출 | 등록된 이벤트를 커밋 경계에서 프로세스 안 구독자에게 넘긴다 | 애플리케이션 서비스 |
| 전파 | 프로세스 밖(다른 컨텍스트·시스템)으로 내보낸다 | 어댑터 + [[outbox]] |

**내부 이벤트와 공개 이벤트를 가른다.** 같은 컨텍스트 안에서만 소비되면 내부 이벤트이고 자유롭게
바꿀 수 있다. 컨텍스트 경계를 넘으면 공개 이벤트이며 그 순간 **계약**이 된다 —
[[context-mapping]] 관계 표의 `계약` 칸에 이름이 올라가고, 마음대로 바꿀 수 없게 된다.

## 적용 기준

### [[event-storming]]의 과거형 스티커를 도메인 이벤트로 승격하는 경로

이벤트 스토밍이 나열한 과거형 문장은 **후보**이지 이벤트 타입이 아니다. 전부 클래스로 만들면
아무도 구독하지 않는 타입이 수십 개 생긴다. 네 단계로 거른다.

1. **어느 애그리거트의 상태 변화인지 배정한다.** 배정할 애그리거트가 없으면 아직 모델링되지 않은
   사실이다 — 이벤트를 만들 것이 아니라 [[aggregates]]로 돌아간다.
2. **듣는 쪽이 있는지 확인한다.** 변화가 그 애그리거트 안에서 끝나면 이벤트 타입을 만들지 않는다.
   상태 필드 하나면 충분하다.
3. **듣는 쪽의 위치로 내부/공개를 가른다.** 같은 컨텍스트면 내부, 다른 컨텍스트면 공개다.
4. **공개면 관계 표에 줄이 있는지 확인한다.** 없으면 이벤트를 만들기 전에 관계부터 선언한다
   ([[context-mapping]]) — 표에 없는 쌍은 서로를 참조할 수 없다.

### 만들지 않는 경우

- **같은 트랜잭션에서 어차피 함께 바뀌는 것**을 이벤트로 잇는다 → 그것은 한 애그리거트다
  ([[aggregates]] R1의 첫 번째 선택지).
- **CRUD 감사 로그**가 목적이다(`OrderUpdated`, `CustomerChanged`) → 업무 사실이 아니라 기술 로그다.
  무엇이 왜 바뀌었는지 말하지 못하는 이름이 그 신호다.
- **구독자가 없다.** "나중에 쓸지도 모른다"로 만든 이벤트는 페이로드가 검증되지 않은 채 굳는다.
- **호출자가 결과를 즉시 알아야 한다** → 이벤트가 아니라 동기 호출이다. 이벤트로 감싸 놓고
  응답을 기다리는 구조는 두 방식의 단점만 합친 것이다.

### 결과적 일관성을 감당할 수 있는가

이벤트로 두 애그리거트를 이으면 그 사이에는 반드시 시차가 생긴다. 채택 전에 담당자에게 묻는다 —
**"두 번째 변경이 몇 초, 드물게 몇 분 늦으면 업무가 깨집니까?"** 깨진다는 답이 나오면 이벤트가
아니라 애그리거트 병합을 검토한다.

## 규칙

### R1. 이벤트는 애그리거트가 만든다 — 그리고 애그리거트는 발행하지 않는다

- 이벤트 객체를 생성하는 곳은 **상태를 바꾸는 그 메서드 안**이다. 애플리케이션 서비스가 저장한
  뒤 "그러니까 이런 일이 있었겠지"라며 만들면, 진입점이 늘어날 때마다 누락된다.
- 그러나 애그리거트는 **방출하지 않는다.** 도메인이 발행자(`ApplicationEventPublisher`,
  메시지 템플릿)를 주입받는 순간 도메인 테스트가 프레임워크를 필요로 하게 된다
  ([[persistence]] R2 표의 넷째 행과 같은 성질의 누수다 — 기계는 잡지 않는다).
- 전달 형태는 둘 다 좋다 — 루트가 이벤트를 **반환**하거나([[aggregates]]의 `place()` 예),
  루트가 내부 목록에 **등록**하고 애플리케이션이 꺼내 간다. 이벤트가 여럿이면 후자가 편하다.

### R2. 방출 시점은 커밋 경계다

- 프로세스 **밖으로 나가는** 이벤트는 트랜잭션 커밋 후에만 나간다. 커밋 전에 내보내면 롤백된
  사실을 남에게 알린 것이 되고, 되돌릴 방법이 없다.
- "커밋 후 발행"과 "발행 성공"은 다르다. 커밋과 발행 사이에서 프로세스가 죽으면 이벤트는
  사라진다. 유실이 업무상 허용되지 않으면 [[outbox]]를 쓴다 — 이벤트 저장을 **같은 트랜잭션에**
  넣는 것이 그 패턴의 전부다.
- 같은 트랜잭션 안에서 처리하는 내부 이벤트는 허용된다. 다만 그 핸들러가 다른 애그리거트를
  저장하면 [[aggregates]] R1을 어긴 것이므로, "이벤트를 썼으니 괜찮다"고 넘어가지 않는다.

### R3. 명명 — 애그리거트 + 과거형

- 형식은 `<애그리거트><과거분사>`다: `OrderPlaced`, `ClaimApproved`, `PaymentFailed`.
- **현재형·명령형은 이벤트가 아니라 커맨드다.** `SendEmail`, `ApproveClaim`은 이벤트 이름이 될 수
  없다. 이 한 줄이 실무에서 가장 자주 어겨진다.
- 컨텍스트 이름을 타입 접두사로 붙이지 않는다 — 패키지가 이미 컨텍스트다. 컨텍스트와 버전은
  **스키마 이름**에 들어간다(R4).
- `Event` 접미사는 중복이다(과거분사가 이미 이벤트임을 말한다). 붙이기로 정했으면 전부 붙인다.
- 이벤트 타입은 domain에 선언하므로 `hex.ports-owned-inside`(`naming-suffix`, scope=application)의
  대상이 아니다 — application에 두면 `Port`·`UseCase`로 끝나지 않아 위반이 된다.

### R4. 공개 이벤트는 관계 표의 `계약` 칸에 등재한다

- 컨텍스트 경계를 넘는 이벤트는 [[context-mapping]] 관계 표에 한 줄이 있어야 하고, `계약` 칸에
  **버전을 포함한 스키마 이름**을 적는다(`claim-events-v1`).
- `계약` 칸의 이름은 코드에서 grep 하면 나와야 한다([[context-mapping]] R2). 문서에만 있는
  이름은 계약이 아니다.
- 필드를 지우거나 의미를 바꾸는 것은 버전 올림이다. 소비자 하나가 필요하다고 필드를 계속
  덧붙이면 스키마가 특정 소비자에게 종속된다 — `published-language`의 대표 안티패턴이다.

### R5. 페이로드는 최소한의 도메인 타입

- 담는 것: 애그리거트 ID, 발생 시각, **그 사실을 설명하는 데 필요한 값**.
- 담지 않는 것: 애그리거트 전체 직렬화(내부 구조가 계약이 된다), 영속 엔티티·전송 DTO
  (영속 관심사가 이벤트를 타고 새어 나간다 — [[persistence]] R2), 소비자별 편의 필드.
- 이벤트는 불변 값 객체다 — `val`만, 구조적 동등성([[value-objects]] R1·R2).
- 소비자가 더 필요하다고 하면 먼저 되묻는다: 그 데이터는 소비자가 자기 컨텍스트에서 조회할 수
  있는가? 조회할 수 있으면 페이로드가 아니라 ID만 준다.

### R6. 리뷰 체크리스트

- [ ] 이벤트 이름이 전부 과거형인가? 하나라도 명령형이면 커맨드가 섞여 있다.
- [ ] 도메인 코드가 발행자·메시지 브로커 타입을 참조하는가?
- [ ] 커밋 전에 외부로 나가는 경로가 있는가?
- [ ] 컨텍스트를 넘는 이벤트 중 관계 표에 없는 것이 있는가?
- [ ] 구독자가 0인 이벤트 타입이 있는가?
- [ ] 이벤트 페이로드에 어댑터 타입·엔티티가 들어 있는가?
- [ ] 유실이 허용되지 않는 이벤트인데 [[outbox]] 없이 커밋 후 발행만 하는가?

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.order.domain — 순수. 발행자를 모른다 (R1)
package com.acme.order.domain

interface DomainEvent { val occurredAt: Instant }

data class OrderPlaced(                            // R3: 애그리거트 + 과거분사
    val orderId: OrderId,                          // R5: ID와 최소 사실만
    val customerId: CustomerId,
    val total: Money,
    override val occurredAt: Instant,
) : DomainEvent

class Order(/* ... */) {
    private val events = mutableListOf<DomainEvent>()

    fun place(now: Instant) {
        require(status == OrderStatus.DRAFT) { "이미 확정된 주문이다" }
        status = OrderStatus.PLACED
        events += OrderPlaced(id, customerId, total, now)   // 등록만 한다
    }

    fun pullEvents(): List<DomainEvent> = events.toList().also { events.clear() }
}

// com.acme.order.application — 방출은 여기서, 커밋 경계에 맞춰 (R2)
package com.acme.order.application

@Service
class DefaultPlaceOrderUseCase(
    private val loadOrder: LoadOrderPort,
    private val saveOrder: SaveOrderPort,
    private val publishEvents: PublishEventsPort,   // out 포트 — 구현은 어댑터
) : PlaceOrderUseCase {
    @Transactional
    override fun handle(command: PlaceOrderUseCase.Command) {
        val order = loadOrder.findById(command.orderId) ?: throw OrderNotFound(command.orderId)
        order.place(command.now)
        saveOrder.save(order)
        publishEvents.publish(order.pullEvents())   // 어댑터가 outbox 행으로 기록한다
    }
}
```

`PublishEventsPort`의 어댑터 구현이 같은 트랜잭션에서 outbox 테이블에 기록하고, 릴레이가 커밋된
행만 밖으로 보낸다([[outbox]]). 애플리케이션은 그 방식을 모른다.

### 안티패턴 1 — 도메인이 직접 발행한다

```kotlin
// com.acme.order.domain.Order
class Order(private val publisher: ApplicationEventPublisher) {   // R1 위반
    fun place() {
        status = OrderStatus.PLACED
        publisher.publishEvent(OrderPlaced(id))     // R2 위반: 커밋 전에 나간다
    }
}
```

`org.springframework..` import가 도메인에 들어와 `*.domain-no-framework`가 잡는다. 기계가 잡지
못하는 쪽이 더 아프다 — 이후 트랜잭션이 롤백되어도 이미 나간 이벤트는 돌아오지 않는다.

### 안티패턴 2 — 커맨드를 이벤트라 부르고, 애그리거트를 통째로 실었다

```kotlin
data class SendWelcomeEmail(val order: Order)      // R3 위반(명령형) + R5 위반(애그리거트 전체)
```

이름이 명령형이라는 것은 발행자가 **수신자에게 무엇을 하라고 지시하고 있다**는 뜻이다. 그 순간
"메일을 보낼지"는 주문 컨텍스트의 결정이 되고, 알림 컨텍스트는 자기 규칙을 가질 수 없다. 이름을
`OrderPlaced`로 되돌리고 메일 발송 여부는 구독자가 정하게 하면 결합이 사라진다. 페이로드도
마찬가지다 — `Order`를 통째로 실으면 내부 구조가 계약이 되어 애그리거트를 리팩터링할 수 없다.

## 관련 문서

- [[aggregates]] — 이벤트를 만드는 주체와 "트랜잭션 1개 = 애그리거트 1개"를 지키는 경로
- [[value-objects]] — 이벤트 페이로드가 따르는 불변·동등성 규칙
- [[context-mapping]] — 공개 이벤트가 등재되는 관계 표와 `계약` 칸 규약
- [[outbox]] — 커밋과 전파 사이의 유실을 막는 방법
- [[event-storming]] — 과거형 스티커를 뽑아내는 앞 단계
- [[repositories-domain-services]] — 도메인이 발행자를 모르게 만드는 인터페이스 소유 방향
- [[cqrs]] — 이벤트로 읽기 모델을 갱신하는 경우의 판단 기준
