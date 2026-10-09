# 코딩 컨벤션

도메인 로직이 드러나고 테스트하기 쉬운 코드를 쓰기 위한 규칙이다. conventions 스킬과 convention-reviewer가 함께 읽는다.

- 적용 범위: 백엔드 애플리케이션. 예시는 Kotlin·Spring·JPA로 적었지만 규칙은 언어·프레임워크와 관계없이 적용한다. 이름에 JPA가 붙은 항목은 JPA를 쓸 때만 해당한다.
- 대상 프로젝트의 지침 파일(AGENTS.md·CLAUDE.md)이나 문서에 다른 규칙이 있으면 그 규칙이 우선한다.
- `필수`는 벗어날 때 이유가 있어야 하고, `지향`은 가능한 한 따른다.
- "외부 자원"은 DB·메시지 큐처럼 우리가 운영하는 인프라까지 포함한다. "외부 API"·"외부 시스템"은 그중 우리가 모델을 정하지 못하는 시스템(DOMAIN.md의 `외부`)만 가리킨다.
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
- 조회 조건으로 상태를 걸러 가져오는 것으로 전이 검증을 대신하지 않는다. 조회 조건은 규칙의 일부만 담고, 조건이 어긋나면 '없음'으로 뭉개져 이유가 사라진다. 전이 규칙의 기준은 `canXxx()`이고, 가져온 뒤 다른 요청이 상태를 바꾸는 경우는 락으로 막는다(→ 「동시에 바뀔 수 있는 값은 동시성 제어 수단을 정한다」).

```kotlin
data class Order(val status: OrderStatus) {
    fun canCancel(): Boolean = status == OrderStatus.PAID

    fun cancel(): Order {
        check(canCancel()) { "cannot cancel order in $status" }
        return copy(status = OrderStatus.CANCELED)
    }
}
```

## 상태 값은 최소로 둔다 `지향`
상태(status) 값은 그 상태에 따라 규칙이나 흐름이 갈릴 때만 만든다. 기록만 필요하면 이력으로 남긴다(예: 결제 실패를 상태로 두지 않고 거래 이력에 남겨, 같은 주문으로 다시 결제하게 한다).
- 이유: 상태가 늘면 전이와 예외 경우가 함께 늘어 운영과 확장이 복잡해진다.

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

## 도메인 사이 의존은 한 방향으로만 둔다 `필수`
두 도메인이 서로를 부르거나 참조하지 않는다. 방향은 DOMAIN.md의 관계 표를 따르고, 반대쪽으로 알릴 일이 생기면 방향을 뒤집지 않고 이벤트나 배치·조회로 푼다.
- 이유: 서로 의존하는 두 도메인은 함께 바뀌고 따로 테스트할 수 없어 사실상 한 도메인이다. 셋 이상이 도는 순환도 같다.
- 이벤트: 의존받는 쪽이 발행하고, 의존하는 쪽이 구독한다. 발행하는 쪽은 구독자를 모른다. 발행한 트랜잭션이 커밋된 뒤 처리하고(Spring: `@TransactionalEventListener`), 구독하는 쪽의 쓰기는 리스너가 부르는 전용 리포지토리 메서드에 `REQUIRES_NEW`를 걸어 새 트랜잭션에서 한다. 다른 트랜잭션에 묶여 쓰이는 메서드와는 나눈다(묶여야 할 쓰기가 따로 커밋되지 않게).
  - 트랜잭션 밖에서 발행하면 `fallbackExecution = true`가 없는 한 처리되지 않는다. 쓰기와 같은 트랜잭션 안(리포지토리 메서드)에서 발행한다.
  - 커밋 뒤 처리는 프로세스가 죽으면 유실될 수 있다. 놓치면 안 되는 전이는 배치로 보정하거나 아웃박스를 쓴다.
- 배치·조회: 의존하는 쪽이 필요할 때 가져간다(상태 확인 배치, 조회 API).
- 순서가 필요한 흐름(외부 확인 뒤 주문 확정 등)은 어느 도메인에도 속하지 않는 위 계층(컨트롤러나 조율 컴포넌트)이 여러 도메인을 차례로 부른다. 이 호출은 도메인 사이 의존이 아니다.
- 상대를 가리켜야 하지만 알면 안 되면(여러 종류의 대상에 붙거나, 결과를 돌려주려고 상대를 기억해야 할 때) 상대의 ID 타입 대신 자기 타입(`ReviewTarget(type, id)` 등)이나 불투명한 상관 키로 들고, 그 의미를 해석하지 않는다.

## 계층은 한 방향으로만 참조한다 `필수`
presentation(컨트롤러, 요청·응답 DTO) → application(서비스, application 리포지토리) → domain 방향으로만 참조한다. 아래 계층은 위 계층을 모른다. application은 요청 DTO나 HTTP 타입처럼 presentation의 타입을 받거나 돌려주지 않고, domain은 application을 모른다.
- 예: 컨트롤러가 요청 DTO를 도메인 입력 타입(`NewOrder`)으로 바꿔 서비스에 넘기고, 서비스가 돌려준 결과로 응답 DTO를 만든다. 입력 경로가 여럿이면(바로 주문, 장바구니 주문) 같은 입력 타입으로 맞춰 뒷단을 하나로 둔다.
- 요청 값으로 값 타입을 만들다 실패하면(`IllegalArgumentException`) 그 변환 단계에서 400으로 바꾼다. 도메인 로직 안에서 난 표준 예외는 선검증을 빠뜨린 프로그래밍 오류이므로 그대로 둔다.
- infrastructure(JPA 엔티티, 외부 자원의 구현)는 이 방향 밖에 둔다. application은 인터페이스나 감싼 클래스로 infrastructure를 쓰고(→ 「외부 자원은 인터페이스 뒤에 둔다」), infrastructure는 application의 인터페이스를 구현하려고 application·domain을 참조할 수 있다.
- 이유: 화면이나 API가 바뀌어도 application과 domain은 그대로 두고, 같은 유스케이스를 배치·워커 같은 다른 입구에서도 쓸 수 있다.

## 자명하지 않은 규칙은 KDoc으로 남긴다 `지향`
집계 규칙, 정합성 제약, "왜 이렇게 하지 않았는지" 같은 결정은 클래스·메서드 KDoc에 이유와 함께 남긴다. 코드가 무엇을 하는지는 쓰지 않는다.

## 도메인은 표준 예외만 던진다 `필수`
도메인 객체는 `require`·`check`·`error` 같은 표준 예외만 쓴다. 에러 코드를 담은 비즈니스 예외(`CoreException` 등)는 application 계층(서비스, application 리포지토리)이 `canXxx()`로 먼저 확인한 뒤 던진다.
- 이유: 도메인은 응답 규칙을 몰라도 되고, 도메인 안의 예외는 "확인 없이 호출했다"는 프로그래밍 오류 신호로 남는다.
- 확인과 쓰기 사이에 다른 요청이 끼어들 수 있으면 둘을 리포지토리 메서드 하나에서 한다(→ 「트랜잭션은 서비스가 아니라 리포지토리에 건다」).

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
- 예외: 감사용 생성·수정 시각(`@CreationTimestamp` 등). 다만 감사용 시각을 기간 규칙(예: 작성 후 7일 안에만 수정)에 쓰지 않는다. 규칙이 기대는 시각은 Clock으로 채운 전용 필드로 둔다.

```kotlin
fun canRenew(now: Instant): Boolean = ...     // 도메인
renewal.canRenew(clock.instant())             // application
```

## 정적 호출은 컴포넌트로 감싼다 `필수`
`UUID.randomUUID()`나 `Random`처럼 결과가 매번 달라지는 정적 호출은 컴포넌트로 감싸 주입받는다. 반환값은 문자열보다 타입(`UUID`)으로 둔다.
- 이유: 정적 메서드는 테스트에서 모킹하기 어렵다. 일반 모킹이나 상속으로는 대체할 수 없어 정적 모킹 같은 별도 도구가 필요하고, 그마저 막히는 경우가 있다. 컴포넌트로 감싸면 테스트에서 값을 고정할 수 있다.
- 테스트: 감싼 컴포넌트를 모킹하거나, 상속해 고정 값을 돌려주는 가짜로 바꿔 끼운다(Kotlin은 `kotlin("plugin.spring")`이 `@Component` 클래스를 열어 두므로 상속할 수 있다).

```kotlin
@Component
class UuidHolder {
    fun random(): UUID = UUID.randomUUID()
}
```

## JPA는 인프라에 둔다 `필수`
도메인 모델은 JPA에 의존하지 않는 순수 Kotlin·Java 클래스로 둔다. JPA 엔티티와 도메인 모델 사이의 변환은 application 계층의 리포지토리가 맡고, 서비스는 JPA 리포지토리를 직접 쓰지 않는다.
- 이유: 도메인 로직이 영속 기술의 제약(기본 생성자, 가변 필드, 지연 로딩)에 끌려가지 않는다.
- application 리포지토리는 이름이 아니라 역할(엔티티↔도메인 변환, JPA 접근)로 정한다. 이름은 프로젝트 관례를 따른다(`XxxRepository`, `XxxReader` 등).
- 예외: 도메인 로직이 얇은 곳(분류가 generic인 도메인, 어드민·워커·배치)은 JPA 엔티티를 직접 써도 된다.

## JPA 클래스 이름 `필수`

| 대상 | 이름 |
|---|---|
| 엔티티 | `XxxEntity` |
| Spring Data 리포지토리 | `XxxJpaRepository` (커스텀: `XxxJpaRepositoryCustom`, 구현: `XxxJpaRepositoryCustomImpl`) |
| `@Embeddable` 값 | `XxxEmbeddable` |
| 조회 전용 결과 | `XxxProjection` |

## JPA 엔티티 매핑 `필수`
- 연관관계는 같은 도메인 안에서만 쓰고, `@ManyToOne(fetch = LAZY)`만 쓴다. `@OneToMany`는 되도록 쓰지 않고, 자식 목록은 리포지토리로 조회한다.
- 다른 도메인의 엔티티는 연관관계 대신 ID 칼럼으로 잇는다.
- enum 칼럼은 `@Enumerated(EnumType.STRING)`으로 저장한다. 기본값(ORDINAL)은 enum 순서가 바뀌면 저장된 값의 뜻이 바뀐다.
- 변경 가능한 필드는 `protected set`으로 막고, 의미 있는 메서드로만 바꾼다.
- `spring.jpa.open-in-view`는 끈다.
- 이유: 연관관계가 도메인을 넘으면 경계가 코드에서 무너지고, `@OneToMany`는 지연 로딩·N+1·컬렉션 변경 추적 문제를 부른다.

## 트랜잭션은 서비스가 아니라 리포지토리에 건다 `필수`
트랜잭션은 인프라의 일이므로 서비스에 걸지 않고, DB와 닿는 application 리포지토리의 메서드에 건다. 함께 성공해야 하는 쓰기는 그 리포지토리 메서드 하나에 모은다.
- 동시 쓰기를 막으려고 검증과 쓰기를 한 트랜잭션에서 해야 하면, 리포지토리 메서드 안에서 도메인 모델의 검증(`canXxx()`)을 부르고 비즈니스 예외를 던져도 된다. 검증 로직은 여전히 도메인 모델에 있다.
- 동시 쓰기를 실제로 막는 것은 락이다(「동시에 바뀔 수 있는 값은 동시성 제어 수단을 정한다」). 트랜잭션은 검증과 쓰기를 한 단위로 묶는다.
- 여러 도메인을 한 트랜잭션에 묶어야 하면(도메인 가이드의 허용 조건), 흐름의 뒤 단계 도메인의 리포지토리 메서드가 앞 단계 도메인의 리포지토리를 불러 묶는다.
- 조회도 리포지토리 메서드 안에서 엔티티를 도메인 모델로 바꾸는 데까지 끝낸다(`@Transactional(readOnly = true)`, 필요하면 fetch join). OSIV를 끄고 LAZY만 쓰므로 트랜잭션 밖에서는 지연 로딩이 안 된다.
- 이유: 서비스가 인프라에 묶이지 않고, 트랜잭션이 DB 작업만큼 짧아지며, 외부 호출이 트랜잭션에 섞이지 않는다(「외부 호출은 DB 트랜잭션 밖에서 한다」).
- 예외: application 리포지토리 없이 JPA 엔티티를 직접 쓰는 얇은 곳(「JPA는 인프라에 둔다」의 예외)은 서비스에 트랜잭션을 걸어도 된다.

```kotlin
@Repository
class XxxRepository(private val xxxJpaRepository: XxxJpaRepository) {
    @Transactional
    fun execute(id: XxxId) {
        val entity = xxxJpaRepository.findByIdOrNull(id.value) ?: throw CoreException(ErrorType.XXX_NOT_FOUND)
        val xxx = entity.toXxx()                    // XxxEntity의 @Version(낙관적 락)이 동시 쓰기를 막는다
        if (!xxx.canExecute()) {
            throw CoreException(ErrorType.XXX_CANNOT_EXECUTE)
        }
        entity.update(xxx.execute())
    }
}
```

## 동시에 바뀔 수 있는 값은 동시성 제어 수단을 정한다 `필수`
같은 데이터를 여러 곳에서 동시에 바꿀 수 있으면 제어 수단(낙관적 락 `@Version`, 조건부 UPDATE, 비관적 락)을 정한다. 동시 수정은 여러 사용자의 요청에서만 생기지 않는다. 여러 도메인의 흐름이 같은 데이터를 바꾸거나(결제와 리뷰가 각각 포인트 도메인을 불러 같은 잔액을 바꾼다), API 서버·워커·배치처럼 여러 애플리케이션이 같은 데이터를 바꿀 때도 생긴다.
- 한 프로세스 안의 락(`synchronized` 등)은 서버가 여럿이거나 애플리케이션이 다르면 막지 못한다. DB(락·유니크 제약·조건부 UPDATE)나 분산 락으로 막는다.
- 중복이 안 되는 규칙(1인 1장, 주문 항목당 리뷰 하나 등)은 애플리케이션의 확인에 더해 DB 유니크 제약으로 보장한다. 확인하고 저장하는 사이에 다른 요청이 끼어들 수 있다.
- 제약 위반과 락 충돌은 비즈니스 예외로 바꾸거나 재시도한다. 처리하지 않은 채 500으로 흘리지 않는다.
- 이유: 잔액·수량·사용 상태가 동시에 바뀌면 갱신이 사라지거나 중복이 생긴다. 재화라면 곧 돈 문제다.

## 돈·재화의 기록은 고치지 않고 쌓는다 `지향`
결제·취소·정산·포인트처럼 대사가 필요한 기록은 행을 고치지 않고 새 기록(취소·환불·변동 이력)으로 쌓는다.
- 잔액을 바꾸면 같은 트랜잭션에서 변동 이력(금액, 변동 후 잔액, 원인 ID)을 남긴다. 잔액이 틀어져도 이력으로 다시 계산해 바로잡을 수 있다.
- 확정된 기록이 틀렸거나 뒤집혀야 하면 고치지 않고 반대 기록(차감·상계)을 더한다(예: 정산 뒤 취소된 금액은 다음 정산금에서 뺀다).
- 이유: 무엇이 언제 왜 바뀌었는지 남아 추적·정산·분쟁 대응이 쉽다. 저장만 하므로 수정 이력을 따로 둘 필요도 없다.

## 외부 자원은 인터페이스 뒤에 둔다 `지향`
외부 API, 메시지 큐, 파일 저장소, 알림 같은 외부 자원은 application 계층에 인터페이스를 두고, 구현은 infrastructure에 두는 것을 지향한다. 단순하게 가려면 인터페이스 없이 구체 클래스로 감싸도 된다(예: `XxxJpaRepository`를 쓰는 application의 `XxxRepository`).
- 이유: application 코드가 특정 기술에 묶이지 않고, 테스트에서는 이 인터페이스만 대역으로 바꾸면 된다.
- 구현이 둘 이상이거나 바뀔 가능성이 크면(메시지 큐, 알림 채널 등) 인터페이스를 둔다.
- 인터페이스가 없어도 테스트에서는 감싼 클래스를 모킹하거나 실제 자원으로 검증할 수 있다.

```kotlin
interface OrderEventPublisher { fun publish(event: OrderPaid) }     // application
class SqsOrderEventPublisher(...) : OrderEventPublisher { ... }     // infrastructure
```

## 외부 응답과 오류는 경계에서 우리 타입으로 바꾼다 `필수`
외부 API·SDK를 감싼 클래스는 외부의 응답 타입과 오류(HTTP 오류, 타임아웃, 외부 예외)를 밖으로 내보내지 않는다. 우리 타입(결과 객체, 우리가 정한 예외)으로 바꿔 돌려준다. 재시도·타임아웃 같은 연동 정책도 감싼 클래스 쪽에 둔다. 외부에서 받는 호출·웹훅의 페이로드도 받는 곳에서 우리 타입으로 바꿔 넘긴다.
- 이유: 외부 도메인의 복잡성(모델·용어·상태 코드)과 외부 시스템의 복잡성(타임아웃·실패·장애)을 경계 안에 가둔다. 외부가 바뀌어도 고칠 곳이 한곳이다.
- 외부에서 받은 콜백·웹훅의 값(금액·식별자)은 우리 기록과 대조한 뒤 처리한다.

```kotlin
@Component
class PgPaymentClient(private val api: PgApi) {                    // RestClient 기준 — 예외 타입은 클라이언트마다 다르다
    fun approve(approval: PaymentApproval): ApprovalResult =
        try {
            api.confirm(approval.toPgRequest()).toApprovalResult()  // 외부 응답 → 우리 타입
        } catch (e: HttpClientErrorException) {                      // 4xx: 거절·잘못된 요청
            ApprovalResult.Rejected
        } catch (e: RestClientException) {                           // 5xx·타임아웃·연결 실패
            ApprovalResult.Unknown                                   // 외부 장애 → 우리 상태("확인 중")
        }
}
```

## 외부 호출은 DB 트랜잭션 밖에서 한다 `필수`
외부 API 호출을 DB 트랜잭션 안에 넣지 않는다. 외부 호출과 DB 반영이 함께 필요하면 호출을 트랜잭션 밖에서 끝내고, 그 결과를 짧은 트랜잭션으로 반영한다.
- 이유: 느리거나 멈춘 외부 호출이 DB 커넥션과 잠금을 붙잡아 장애가 번진다. 롤백해도 이미 나간 외부 호출은 되돌릴 수 없다.
- 되돌릴 수 없는 외부 작업(결제 승인·이체)이 성공한 뒤 우리 쪽 반영이 실패할 때의 처리(재처리, 보상 취소, 대사)를 미리 정한다. 외부 작업은 이미 끝났으므로, 뒤따르는 반영은 실패할 일이 적게 짧고 단순하게 둔다.
- 외부 호출 전에 무엇을 요청하는지 먼저 기록해 두는 것을 지향한다(예: 결제 승인을 요청하기 전에 거래 이력에 요청을 남긴다). 외부가 실패하거나 응답이 없어도 무엇을 요청했는지 남는다.

## 모킹은 외부 자원에만 쓴다 `필수`
외부 자원(HTTP 클라이언트, DB, 메시지 큐 등)만 모킹한다. 도메인 객체와 내부 컴포넌트는 실제 객체를 쓰고, 시간은 `Clock.fixed`로 고정한다.
- 이유: 모킹이 많을수록 테스트가 구현에 묶여 리팩터링 때 깨지고, 실제 동작은 검증하지 못한다.
- DB는 모킹할 수 있지만, application 리포지토리는 실제 DB로 검증하는 것을 지향한다. 모킹(stub-and-verify)은 호출만 검증하므로 실제 동작과 어긋날 수 있다.
- 조건을 직접 쓴 조회(`@Query`, QueryDSL 등)는 실제 DB로 테스트하고, 걸러져야 할 데이터(삭제·만료·다른 사용자·다른 상태)를 함께 넣어 포함과 제외를 모두 검증한다. 쿼리 메서드 이름에서 만들어지는 조회는 테스트하지 않아도 된다(→ 「라이브러리·DB가 이미 구현한 기능은 테스트하지 않는다」).
- 예외: 정적 호출을 감싼 컴포넌트는 모킹하거나 상속한 가짜로 바꿔 끼워도 된다(「정적 호출은 컴포넌트로 감싼다」). 컨트롤러 슬라이스 테스트는 application 계층을 모킹해도 된다.

## 라이브러리·DB가 이미 구현한 기능은 테스트하지 않는다 `지향`
테스트는 우리가 쓴 로직을 검증한다. 라이브러리·프레임워크·DB(PostgreSQL·MySQL 등)가 이미 구현해 제공하는 기능이 제대로 동작하는지는 따로 테스트하지 않는다.
- 예: Spring Data JPA 쿼리 메서드(`findByUserIdAndStatus`)가 이름대로 쿼리를 만드는지, `@Lock`을 붙인 리포지토리 메서드나 DB의 락(`SELECT ... FOR UPDATE`, PostgreSQL advisory lock, MySQL `GET_LOCK`)이 실제로 잠그는지.
- 이유: 그 동작은 만든 쪽이 이미 검증했다. 다시 확인해도 우리 코드의 결함은 잡지 못하고, 느리고 깨지기 쉬운 테스트만 는다(락을 확인하려면 여러 스레드와 실제 DB가 필요하다).
- 우리가 직접 쓴 쿼리(`@Query`의 JPQL·네이티브 SQL, QueryDSL 같은 동적 쿼리)는 우리 코드이므로 테스트한다(→ 「모킹은 외부 자원에만 쓴다」).
