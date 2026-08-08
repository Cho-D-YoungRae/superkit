---
summary: 4개 동심원(domain, usecase, interface-adapter, framework) 스타일. usecase 레이어까지 프레임워크를 금지하므로 트랜잭션 경계가 바깥으로 나간다
read_when: [init, review, fitness, scaffold]
rules: [cl.deps-inward, cl.domain-pure, cl.domain-no-framework]
---

## 개념

클린 아키텍처는 레이어를 넷으로 두고 의존을 안쪽으로만 흐르게 한다.

| 레이어 | 담는 것 | 아는 것 |
|---|---|---|
| domain | 엔티티·값 객체·불변식 (기업 업무 규칙) | 없음 |
| usecase | 인터랙터, 입출력 경계(boundary) 인터페이스, 게이트웨이 인터페이스 | domain |
| interface-adapter | 컨트롤러, 프레젠터, 요청·응답 모델 | usecase, domain |
| framework | 스프링 설정, JPA 엔티티, 게이트웨이 구현, 트랜잭션 데코레이터 | 안쪽 전부 |

[[hexagonal]]과 겹치는 부분이 많다. 실질적인 차이는 **선언 표에 하나 있고, 그것이 전부를
바꾼다** — `cl.domain-no-framework`의 `from`에 `usecase`가 들어간다.

> hexagonal의 `application`은 `@Service`·`@Transactional`을 쓸 수 있다.
> clean의 `usecase`는 **쓸 수 없다.** 인터랙터에는 프레임워크 애노테이션이 한 개도 붙지 않는다.

따라서 트랜잭션 경계가 유스케이스 안에 있을 수 없고, 바깥 레이어의 데코레이터로 나간다. 이것이
clean을 고르는 실제 비용이자 유일한 실질적 이득이다. 이 교환을 받아들일 이유가 없다면 clean은
hexagonal보다 나은 선택이 아니다.

**영속성 스탠스 — 도메인은 순수하다.** `@Entity`가 붙은 타입은 `framework` 안에서만 선언되고
참조된다(`cl.domain-pure`). `interface-adapter`는 `framework`를 참조할 수 없으므로(`cl.deps-inward`)
**게이트웨이 구현체도 `framework`에 산다.** interface-adapter에 남는 것은 전달 메커니즘 쪽
번역(컨트롤러·프레젠터·요청 응답 모델)뿐이고, 영속 기술은 가장 바깥 원에서 끝난다
([[persistence]]).

**도메인 문서는 필수다.** `clean`을 채택한 컨텍스트는 `docs/architecture/domain/<컨텍스트>.md`를
가져야 한다.

## 적용 기준

[[domain-classification]]의 기본 매핑에는 clean이 없다. 즉 **clean은 기본값을 벗어나는 선택이며
언제나 근거 ADR을 동반한다.** 아래 조건은 그 근거로 쓸 수 있는 형태로 적는다.

### 고르는 조건 — 셋을 모두 만족할 때만

1. **usecase 레이어를 프레임워크 없이 굴려야 할 구체적 이유가 있다.** 프레임워크 교체가 로드맵에
   있거나, 같은 인터랙터를 웹·CLI·배치 등 성격이 다른 전달 메커니즘 둘 이상에서 재사용하거나,
   유스케이스 레이어를 별도 산출물로 배포한다. "결합도를 낮추고 싶다"는 이유가 아니다.
2. **트랜잭션 경계를 바깥에서 선언할 설계가 이미 있다.** 데코레이터·프록시·인터셉터 중 무엇으로
   감쌀지 지금 말할 수 있어야 한다. 이 답이 없으면 3개월 뒤 인터랙터에 `@Transactional`이 붙고,
   `cl.domain-no-framework`는 예외로 빠지며, 남는 것은 이름만 clean인 hexagonal이다.
3. **팀이 clean 어휘를 실제로 쓴다.** Interactor·Boundary·Gateway·Presenter가 리뷰에서 통용되는
   말인가. 아니면 [[hexagonal]]의 Port·UseCase 쪽이 더 적은 마찰로 같은 결과를 준다.

### 고르지 않는 조건 — 하나라도 해당하면 clean이 아니다

- 인터랙터에 `@Transactional`을 붙일 생각이다 → [[hexagonal]]. 같은 도메인 순수성을 더 싸게 얻는다
- 전달 메커니즘이 HTTP 하나뿐이고 프레임워크 교체 계획이 없다 → [[hexagonal]] 또는
  [[layered-domain]]
- 분류가 `supporting`·`generic`이다 → 기본 매핑([[layered-domain]]·[[layered-simple]])을 벗어날
  근거가 위 세 조건으로 서지 않으면 고르지 않는다
- 레이어 이름을 소스 패키지와 맞출 수 없거나 맞출 생각이 없다 → 아래 R0을 먼저 읽는다. 맞추지
  않으면 규칙 전체가 위반 0건으로 통과한다

### hexagonal과 가르는 한 문항

> **트랜잭션 경계를 유스케이스 코드 밖으로 옮길 수 있는가, 그리고 그렇게 할 이유가 있는가?**
>
> - 둘 다 예 → clean
> - 하나라도 아니오 → hexagonal

이 문항이 전부다. 원의 개수(3개냐 4개냐)는 판단 근거가 아니다 — hexagonal의 adapter를 in/out
패키지로 나누면 실무상 원은 이미 넷이다. 갈리는 것은 프레임워크가 어디까지 들어올 수 있느냐뿐이다.

## 규칙

아래가 이 스타일의 선언이다. `파라미터` 셀의 문법과 레이어·패키지 판별은
`references/governance/rule-vocabulary.md` §2·§2.1이 정본이며 여기서 다시 정의하지 않는다.
각 인스턴스가 어떤 테스트 코드가 되는지는 `profiles/<프로파일>/rule-mappings.md`가 정한다 —
아래 "검사 형태"는 생성될 검사의 종류만 적는다.

### 선언

- 레이어: domain, usecase, interface-adapter, framework (안 → 밖 순서)

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| cl.deps-inward | layer-order | layers=domain,usecase,interface-adapter,framework |
| cl.domain-pure | confine-type | type=jpa-entity; allowed_layer=framework |
| cl.domain-no-framework | forbid-import | from=domain,usecase; to=org.springframework..,jakarta.persistence.. |

### R0. 채택 전 준비 — 패키지 규약 표가 필수다

`interface-adapter`는 하이픈을 포함하므로 패키지 세그먼트가 될 수 없다. 기본 관례
(`{기본 패키지}.{컨텍스트}.{레이어}..`)를 그대로 두면 실재하지 않는 패키지를 가리키게 되고, 그
레이어에 걸린 규칙은 **오류 없이 위반 0건으로 통과한다**([[package-conventions]] R1·R4).
`clean`을 채택하는 컨텍스트는 규약 표를 반드시 함께 선언한다.

```markdown
### 패키지 규약
| 레이어 | 패턴 |
|---|---|
| domain | com.acme.{컨텍스트}.domain.. |
| usecase | com.acme.{컨텍스트}.usecase.. |
| interface-adapter | com.acme.{컨텍스트}.adapter.. |
| framework | com.acme.{컨텍스트}.framework.. |
```

레이어 이름은 선언 표와 글자 그대로 같아야 하고, 패턴 쪽은 실제 소스와 같아야 한다. 이것은 규칙이
아니라 규칙이 작동하기 위한 전제이므로 기계가 잡아 주지 않는다.

### R1. cl.deps-inward — 네 원의 의존 방향

`layers`는 안→밖 순서이고 레이어 라벨의 순서와 같다. `strict`를 쓰지 않았으므로 건너뛴 의존
(framework → domain 등)은 허용된다 — 매핑 코드가 도메인 타입을 알아야 하기 때문이다.

가장 자주 놓치는 귀결 하나: **interface-adapter는 framework를 참조할 수 없다.** 따라서 JPA를
만지는 게이트웨이 구현은 interface-adapter가 아니라 framework에 둔다. 컨트롤러가
`@RestController`를 쓰는 것은 위반이 아니다 — 그것은 `org.springframework..` import이고,
`cl.domain-no-framework`의 `from`에 interface-adapter는 없다.

**검사 형태**: 레이어 쌍마다 안쪽이 바깥쪽을 import하면 실패하는 검사 6건.

### R2. cl.domain-pure — @Entity는 framework 안에서만

격리는 **양방향**이다. `@Entity` 타입은 framework 밖에서 선언될 수 없고, framework 밖에서
참조될 수도 없다. 인터랙터가 게이트웨이에서 받은 엔티티를 그대로 다루는 누수가 두 번째 절반에
걸린다.

**검사 형태**: `@Entity` 타입의 선언 위치 검사 1건 + framework 밖에서 그 타입을 참조하지 않는지
확인하는 검사 1건.

### R3. cl.domain-no-framework — domain과 usecase 모두 프레임워크 금지

`from`이 레이어 두 개라는 점이 이 스타일의 정의적 선언이다. `to`의 두 항목은 패키지 패턴이다.

인터랙터에서 금지되는 것: `@Service`, `@Component`, `@Transactional`, `@Autowired`,
`jakarta.persistence`의 모든 타입. 인터랙터는 생성자 주입만 받는 평범한 클래스이고, 빈 등록은
framework의 설정 클래스가 한다.

트랜잭션 경계는 다음 중 하나로 옮긴다.

- framework에 입력 경계를 구현한 데코레이터를 두고 `@Transactional`을 거기에 붙인다(아래 사례)
- 게이트웨이 구현 단위로 트랜잭션을 닫는다 — 유스케이스 하나가 쓰기 한 번으로 끝날 때만 성립한다
- 인터셉터·AOP로 입력 경계 구현체 전체를 감싼다

세 방법 모두 인터랙터 코드에는 흔적이 남지 않아야 한다. 흔적이 남기 시작하면 적용 기준의 조건 2가
실제로는 충족되지 않았다는 신호다.

**검사 형태**: domain·usecase 패턴의 파일이 두 패키지 패턴을 import하면 실패하는 검사 4건.

### R4. 명명 규칙을 두지 않은 이유

프리셋에 `naming-suffix` 인스턴스가 없다. Interactor·Boundary·Gateway·Presenter는 관례로 쓰되
강제하지 않는다 — usecase 레이어에는 성격이 다른 타입(인터랙터, 입력 경계, 출력 경계, 게이트웨이
인터페이스)이 함께 살아서 접미사 하나로 묶으면 반드시 예외가 필요해지기 때문이다
(`rule-vocabulary.md` §3.4). 특정 접미사를 강제하고 싶다면 프리셋을 고치는 것이 아니라 커스텀
스타일을 선언한다(`rule-vocabulary.md` §5).

### R5. 리뷰 체크리스트 (기계가 보지 않는 것)

- [ ] 인터랙터가 트랜잭션을 "가정"하고 있는가? 애노테이션은 없지만 두 번의 쓰기가 한 트랜잭션이라고
      전제하는 코드는 규칙에 걸리지 않고 깨진다
- [ ] 출력 경계(프레젠터)가 실제로 쓰이는가, 아니면 인터랙터가 반환값을 그대로 돌려주는가?
      후자라면 원 하나가 형식만 남은 것이다
- [ ] framework에만 있어야 할 설정이 interface-adapter로 새어 나왔는가?
- [ ] 규약 표의 네 패턴이 각각 실제 소스를 잡는가? R0의 실패 모드는 초록불로 나타난다
- [ ] 도메인 문서에 이 컨텍스트의 불변식이 있는가? 이 스타일은 도메인 문서가 필수다

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.billing.domain — 순수
package com.acme.billing.domain

class Invoice(val id: InvoiceId, private var issued: Boolean) {
    fun issue() {
        check(!issued) { "이미 발행된 청구서다" }
        issued = true
    }
}

// com.acme.billing.usecase — 프레임워크 애노테이션 없음. 트랜잭션 경계도 없다
package com.acme.billing.usecase

interface IssueInvoiceInput { fun issue(invoiceId: InvoiceId) }
interface InvoiceGateway {
    fun load(id: InvoiceId): Invoice?
    fun save(invoice: Invoice)
}

class IssueInvoiceInteractor(private val gateway: InvoiceGateway) : IssueInvoiceInput {
    override fun issue(invoiceId: InvoiceId) {
        val invoice = gateway.load(invoiceId) ?: throw InvoiceNotFound(invoiceId)
        invoice.issue()
        gateway.save(invoice)
    }
}

// com.acme.billing.adapter — 전달 메커니즘 번역. 스프링 웹은 허용, 영속 타입은 금지
package com.acme.billing.adapter

@RestController
class InvoiceController(private val input: IssueInvoiceInput) {
    data class IssueRequest(val invoiceId: Long)                    // 중첩 타입

    @PostMapping("/invoices/issue")
    fun issue(@RequestBody request: IssueRequest) = input.issue(InvoiceId(request.invoiceId))
}

// com.acme.billing.framework — JPA와 트랜잭션 경계가 여기서 끝난다
package com.acme.billing.framework

@Entity
class InvoiceJpaEntity(@Id val id: Long, var issued: Boolean)

@Repository
class JpaInvoiceGateway(private val jpa: InvoiceJpaRepository) : InvoiceGateway {
    override fun load(id: InvoiceId): Invoice? = jpa.findByIdOrNull(id.value)?.toDomain()
    override fun save(invoice: Invoice) { jpa.save(invoice.toJpaEntity()) }
}

@Component
@Primary
class TransactionalIssueInvoice(private val delegate: IssueInvoiceInteractor) : IssueInvoiceInput {
    @Transactional
    override fun issue(invoiceId: InvoiceId) = delegate.issue(invoiceId)   // 경계는 바깥에 있다
}
```

### 안티패턴 1 — 인터랙터에 트랜잭션

```kotlin
// com.acme.billing.usecase.IssueInvoiceInteractor
import org.springframework.transaction.annotation.Transactional   // R3 위반: from에 usecase 포함

class IssueInvoiceInteractor(private val gateway: InvoiceGateway) : IssueInvoiceInput {
    @Transactional
    override fun issue(invoiceId: InvoiceId) { ... }
}
```

hexagonal이었다면 정상인 코드다. clean에서 이것을 예외로 빼면 남는 것은 hexagonal과 같은 강제에
레이어 이름만 다른 상태이므로, 예외를 다는 대신 스타일을 [[hexagonal]]로 바꾸는 것이 정직하다.

### 안티패턴 2 — 게이트웨이 구현을 interface-adapter에 둠

```kotlin
// com.acme.billing.adapter.JpaInvoiceGateway
import com.acme.billing.framework.InvoiceJpaEntity   // R1 위반 + R2 위반 B

@Repository
class JpaInvoiceGateway(...) : InvoiceGateway { ... }
```

hexagonal 감각(어댑터에 영속 구현을 둔다)을 그대로 가져오면 나오는 배치다. clean의
`allowed_layer=framework`는 영속 기술을 한 원 더 바깥으로 밀어 두므로, 게이트웨이 구현은
framework에 있어야 한다. 두 규칙이 동시에 걸린다.

## 관련 문서

- [[hexagonal]] — 대부분의 경우 더 싸게 같은 결과를 준다. 갈림 문항은 트랜잭션 경계 하나다
- [[layered-domain]] — 인바운드 뒤집기가 필요 없을 때
- [[layered-simple]] — 도메인 순수성 자체가 필요 없을 때
- [[domain-classification]] — 기본 매핑에 clean이 없는 이유와 기본값을 벗어날 때의 절차
- [[package-conventions]] — R0의 규약 표를 쓰는 법과 위반 0건 실패 모드
- [[persistence]] — 도메인 모델 ↔ 영속 엔티티 매핑 위치
- [[module-composition]] — 네 원을 모듈로 나눌지 패키지로 나눌지는 직교한다
