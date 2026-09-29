---
summary: 리포지토리 인터페이스의 소유 주체·참조 방향과 애그리거트 단위 규칙, 도메인 서비스와 애플리케이션 서비스를 가르는 체크리스트, 서비스 체인 금지를 팀 규약으로 채택할 때의 안내
read_when: [model, apply, review, migrate]
---

## 개념

세 이름이 섞이는 지점이다. 셋을 가르는 질문은 하나뿐이다 — **업무 규칙이 어디에 적혀 있는가.**

| 이름 | 하는 일 | 누가 소유하는가 | 상태·I/O |
|---|---|---|---|
| 리포지토리 | 애그리거트를 통째로 저장·조회한다 | 인터페이스는 **도메인이 선언**하고 구현은 영속 코드가 갖는다(R1) | I/O 담당 |
| 도메인 서비스 | 어느 한 애그리거트에 둘 수 없는 **업무 규칙**을 담는다 | 도메인이 갖는다 — 업무 규칙이 사는 자리 | 둘 다 없음 |
| 애플리케이션 서비스 | 유스케이스 한 건을 조립한다(로드 → 도메인 호출 → 저장 → 방출) | 도메인을 **부르는 쪽**이 갖는다 — 도메인은 이쪽을 참조하지 않는다 | 트랜잭션 경계 |

**「사는 곳」이 아니라 「누가 소유하는가」인 것은 의도다.** 이 플러그인은 패키지 이름을 정해 주지
않으므로(R1) 이 표가 답하는 것은 파일 경로가 아니라 **선언의 주인과 참조의 방향**이다.

가장 흔한 실패는 애플리케이션 서비스가 커지는 것이다. 규칙이 `if`로 그 안에 쌓이고, 두 번째
진입점이 생겼을 때 규칙이 복제된다. **애플리케이션 서비스에서 조건문을 지웠을 때 남는 것이 없다면
정상이고, 업무 규칙이 사라진다면 그 규칙은 원래 도메인에 있었어야 한다.**

## 적용 기준

### 리포지토리를 두는 단위

- **애그리거트 루트마다 하나.** 내부 엔티티를 위한 리포지토리를 따로 두면, 그것은 "얘는 별도
  애그리거트다"라고 선언한 것이다([[aggregates]] R3).
- 조회 대상이 애그리거트가 아니라 화면용 데이터라면 그것은 리포지토리가 아니다 → R3.

### 도메인 서비스가 필요한 조건 — 셋을 모두 만족할 때

1. **규칙이 애그리거트 둘 이상의 상태를 함께 본다.** 한 애그리거트 안에서 닫히면 그 애그리거트의
   메서드다.
2. **어느 한쪽에 두면 그쪽이 남의 내부를 알아야 한다.** `Account.canTransferTo(other)`가 상대
   계좌의 내부를 들여다봐야 한다면 규칙의 자리는 둘 사이다.
3. **계산에 I/O가 없다.** 인자로 받은 것만으로 판정이 끝난다. 무언가를 조회해야 한다면 그것은
   애플리케이션 서비스의 일이고, 조회 결과를 도메인 서비스에 **인자로 넘긴다**.

셋 중 하나라도 어긋나면 만들지 않는다. 특히 3번이 어긋난 채로 만든 "도메인 서비스"가 이 문서가
막으려는 대상이다.

### 도메인 서비스와 애플리케이션 서비스 판별 체크리스트

| 질문 | 도메인 서비스 | 애플리케이션 서비스 |
|---|---|---|
| 리포지토리·포트를 부르는가 | 아니오 | 예 |
| 트랜잭션 경계를 갖는가(`@Transactional`) | 아니오 | 예 |
| 프레임워크 타입을 import 하는가 | 아니오 | 가능 |
| 이름이 업무 용어인가 | 예(`TransferPolicy`, `RefundCalculator`) | 유스케이스 이름(`PlaceOrderUseCase`) |
| 단위 테스트에 목이 필요한가 | 아니오 — 값만 넣으면 된다 | 예 |
| 지웠을 때 사라지는 것 | 업무 규칙 | 조립 순서 |

한 줄 요약: **도메인 서비스는 순수 함수에 가깝고, 애플리케이션 서비스는 순서에 가깝다.**

### 만들지 않는 경우

- 리포지토리를 한 번 호출하고 그대로 돌려주는 서비스. 유스케이스가 직접 포트를 부르면 된다.
- "자리마다 하나씩 있어야 한다"는 이유로 만드는 서비스. 규칙 없는 서비스는 호출 한 단계다.
- 도메인 서비스가 하나뿐이고 그 안에 메서드가 스무 개 있는 경우 → 그것은 서비스가 아니라
  애그리거트에 들어가지 못한 로직의 창고다. 하나씩 애그리거트로 되돌린다.

## 규칙

### R1. 인터페이스는 도메인이 소유하고, 구현은 영속 코드 쪽에 산다

**도메인이 자신이 필요로 하는 인터페이스를 선언한다.** "저장한다"·"찾아온다"는 도메인의 요구이지
저장 기술의 제안이 아니므로, 인터페이스는 요구하는 쪽이 갖고 구현이 그것에 맞춘다.

| 무엇 | 누가 소유하고, 무엇을 참조하지 않는가 |
|---|---|
| 리포지토리 인터페이스 | **도메인이 선언한다** — 도메인 타입만으로 서술되고(R2) 저장 기술을 참조하지 않는다. 그 파일이 `domain` 패키지에 있는지 `application` 패키지에 있는지는 **프로젝트 관례이지 이 규칙의 판정 대상이 아니다** |
| 그 구현 | **영속 코드가 갖는다** — JPA·드라이버·SQL이 여기서 끝나고([[persistence]] R1), 도메인은 이 타입의 존재를 모른다 |

- **이 플러그인은 두 자리에 패키지 이름을 정해 주지 않는다.** 관례는 프로젝트가 정하고, 이
  규칙이 요구하는 것은 **방향** 하나다 — 도메인이 영속 코드를 참조하지 않는다.
- **그러므로 "인터페이스가 어느 패키지에 있는가"만을 근거로 위반을 내지 않는다.** 포트를
  `application`에 두는 배치도, 리포지터리 인터페이스를 `domain`에 두는 배치도 이 규칙을 만족한다 —
  갈리는 것은 **그 인터페이스가 무엇으로 서술되어 있고 누가 누구를 참조하는가**다.
- 인터페이스 이름은 **의도**를 담는다. `SaveClaimRepository`·`SaveClaimPort`는 좋고
  `ClaimJpaGateway`는 구현이 이름으로 새어 나온 것이다.
- **`generic`으로 분류한 컨텍스트는 이 분리를 하지 않아도 된다** — 스프링 데이터 인터페이스가
  곧 리포지터리인 것이 그 분류의 기본값이다
  ([[domain-classification]]의 "분류가 정하는 것의 기본값" 절).
- **이 규칙은 기계가 보지 않는다.** 컨텍스트 안의 방향을 검사하는 규칙은 없으므로 R7이 유일한
  방어선이다.

### R2. 리포지토리는 애그리거트를 통째로, 도메인 타입으로만 주고받는다

- 시그니처의 인자와 반환 타입은 전부 도메인 타입이다. `@Entity` 타입이 나타나면 그것이
  [[persistence]] R2 표의 둘째 행(시그니처 누수)이며, 잡는 것은 기계가 아니라 리뷰다.
- 프레임워크 타입도 마찬가지다 — `Page`, `Pageable`, `Specification`이 인터페이스에 등장하면
  안쪽이 스프링 데이터를 알게 된다. 페이징이 필요하면 도메인 타입으로 감싼다.
- 애그리거트의 일부만 저장하는 메서드(`updateStatus(id, status)`)를 두지 않는다. 루트를 로드해
  루트의 메서드를 부르고 통째로 저장한다 — 그러지 않으면 불변식이 우회된다.

### R3. 조회가 쌓이면 리포지토리가 아니라 읽기 경로를 만든다

- 리포지토리에 화면 조건별 `findBy...` 메서드가 쌓이고 있는가? 그 메서드들이 반환하는 것이
  애그리거트인가, 화면용 조합인가?
- 화면용이라면 애그리거트 리포지토리에 넣지 않는다. 별도의 조회 전용 포트를 두고 도메인 모델을
  거치지 않는다 — 적용 판단은 [[cqrs]]가 갖는다.
- 이 구분을 하지 않으면 애그리거트가 조회 요구에 맞춰 커진다([[aggregates]] 크기 체크리스트).

### R4. 도메인 서비스는 상태도 I/O도 프레임워크도 갖지 않는다

- 리포지토리·포트를 주입받지 않는다. 필요한 애그리거트는 **인자로 받는다.**
- **기계는 이것을 막지 않는다.** R1이 인터페이스를 도메인 쪽에 두므로 도메인 서비스가 그것을
  주입받아도 어떤 검사에도 걸리지 않는다. R4는 처음부터 끝까지 리뷰 항목이다.
- `@Service`·`@Component`를 붙이지 않는다 — 도메인 서비스가 프레임워크를 알기 시작하면 그것을
  단독으로 테스트할 수 없게 된다.

### R5. 애플리케이션 서비스가 하는 일과 하지 않는 일

한다: 입력 검증(형식 수준), 애그리거트 로드, 도메인 호출, 저장, 이벤트 방출([[domain-events]] R2),
트랜잭션 경계, 권한 확인, 어댑터 타입 ↔ 도메인 타입 변환.

하지 않는다: 업무 조건 판정, 상태 전이 결정, 금액·기간 계산. 이것들이 보이면 애그리거트나 도메인
서비스로 내린다.

- [ ] 유스케이스 하나가 애그리거트 둘을 저장하는가? → [[aggregates]] R1로 되돌아간다.
- [ ] `if`가 세 개 이상 있는가? → 그 조건들의 이름을 도메인에 물어본다.

### R6. "서비스끼리 참조 금지"가 필요할 때

기본값은 이 금지를 두지 않는 것이다. 아래 신호가 실제로 있을 때만 팀 규약으로 채택한다.

- 서비스 호출 체인이 셋 이상 이어지거나 순환한다.
- 트랜잭션이 중첩되어 어디서 시작했는지 추적할 수 없다.
- 같은 업무 규칙이 두 서비스에 복제되어 있다.

**이 플러그인에는 그런 규칙을 선언할 자리가 없다.** 기계 강제 규칙은 관계 표에서 파생되는
`derived.context-isolation` 하나뿐이므로, 채택한다면 `docs/superdomain/conventions/<key>.md`의 리뷰
체크리스트로 적고 근거를 ADR에 남긴다.

**켜기 전에 대안 배치를 먼저 정한다.** 금지를 세우면 서비스 간 공통 로직이 갈 곳이 필요해진다 —
도메인 서비스로 내리거나(R4의 세 조건을 만족할 때), 협력자 타입으로 뺀다. 그 자리를 정해 두지
않고 켜면 다음 날 예외가 생기고, 예외로 사는 규약은 규약이 아니다.

### R7. 리뷰 체크리스트

- [ ] **도메인이 영속 코드를 참조하는가?** (리포지토리 인터페이스가 저장 기술 타입으로 서술돼
      있거나, 도메인 파일이 구현 쪽을 import한다 — **패키지 이름은 근거가 아니다**, R1)
- [ ] 리포지토리 시그니처에 `@Entity`·`Page`·`Pageable`·`Specification`이 있는가?
- [ ] 내부 엔티티를 대상으로 하는 리포지토리가 있는가?
- [ ] 도메인 서비스가 리포지토리를 주입받는가? (기계는 잡지 않는다 — R4)
- [ ] 이름이 `...DomainService`인데 `@Transactional`이 붙어 있는가?
- [ ] 애플리케이션 서비스에 업무 조건 판정이 들어 있는가?
- [ ] 서비스가 서비스를 부르는 체인이 셋 이상인가? → R6 검토

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.transfer.domain — 도메인 서비스: 상태도 I/O도 없다 (R4)
package com.acme.transfer.domain

class TransferPolicy {
    fun check(source: Account, target: Account, amount: Money) {
        require(source.id != target.id) { "같은 계좌로는 이체할 수 없다" }
        require(source.currency == target.currency) { "통화가 다른 계좌 간 이체는 지원하지 않는다" }
        require(source.withdrawable() >= amount) { "출금 가능 금액을 초과했다" }
    }
}

// com.acme.transfer.application — 인터페이스는 요구하는 쪽이 소유하고 도메인 타입만 오간다 (R1·R2)
package com.acme.transfer.application

interface LoadAccountPort { fun findById(id: AccountId): Account? }
interface SaveAccountPort { fun save(account: Account) }

@Service
class DefaultTransferUseCase(
    private val loadAccount: LoadAccountPort,
    private val saveAccount: SaveAccountPort,
    private val policy: TransferPolicy,          // 순수 도메인 서비스
) : TransferUseCase {
    @Transactional                               // 트랜잭션 경계는 여기 (R5)
    override fun handle(command: TransferUseCase.Command) {
        val source = loadAccount.findById(command.from) ?: throw AccountNotFound(command.from)
        val target = loadAccount.findById(command.to) ?: throw AccountNotFound(command.to)
        policy.check(source, target, command.amount)   // 판정은 도메인이 한다
        source.withdraw(command.amount)                // 상태 전이도 도메인이 한다
        saveAccount.save(source)                       // 입금은 이벤트로 — aggregates R1
    }
}
```

애플리케이션 서비스에 남은 것은 순서뿐이고, 지워도 업무 규칙은 사라지지 않는다.

### 안티패턴 1 — 리포지토리가 구현을 흘린다

```kotlin
interface LoadOrderPort {
    fun findById(id: OrderId): OrderJpaEntity?                       // R2 위반: 영속 타입 노출
    fun search(spec: Specification<OrderJpaEntity>, page: Pageable)  // R2 위반: 프레임워크 타입
    fun updateStatus(id: OrderId, status: String)                    // R2 위반: 부분 갱신
}

interface LoadOrderLinePort { fun findByOrderId(id: OrderId): List<OrderLine> }  // R1/aggregates R3
```

**넷 다 기계는 잡지 못한다.** 앞의 둘은 시그니처만 열면 드러나지만, 세 번째와 네 번째는 시그니처가
멀쩡해 보인다 — `updateStatus`는 루트의 상태 전이 규칙을 통째로 우회하고, `LoadOrderLinePort`는
내부 엔티티를 밖으로 꺼내 애그리거트 경계를 없앤다. 리뷰 체크리스트가 필요한 이유가 이것이다.

### 안티패턴 2 — 이름만 도메인 서비스

```kotlin
// com.acme.order.domain.OrderDomainService
@Service                                              // R4 위반: 프레임워크 애노테이션
class OrderDomainService(
    private val orderRepository: OrderRepository,     // R4 위반: I/O
    private val paymentService: PaymentService,       // 서비스 → 서비스 (R6 신호)
) {
    @Transactional                                    // R4 위반: 도메인이 트랜잭션을 갖는다
    fun placeOrder(command: PlaceOrderCommand) { /* if 열두 개 */ }
}
```

이것은 도메인 서비스가 아니라 애플리케이션 서비스이며, 이름에 `Domain`이 붙어 있을 뿐이다.
증상은 테스트에서 먼저 나타난다 — 업무 규칙 하나를 검증하려고 목 두 개와 트랜잭션이 필요해진다.
**어떤 검사도 이 배치를 거부하지 않으므로**, 이 안티패턴을 잡는 유일한 방어선은 R7의
체크리스트다.

## 관련 문서

- [[aggregates]] — 리포지토리의 단위와 "트랜잭션 1개 = 애그리거트 1개"
- [[persistence]] — 리포지토리 구현이 하는 매핑과 영속 코드 격리
- [[domain-events]] — 애플리케이션 서비스가 커밋 경계에서 하는 마지막 일
- [[domain-classification]] — 인터페이스/구현을 분리하지 않는 것이 정답인 `generic` 컨텍스트
- [[cqrs]] — 조회가 리포지토리를 밀어낼 때의 판단
