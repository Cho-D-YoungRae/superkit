---
summary: 도메인 레이어를 분리하고 인터페이스와 구현을 가르는 4레이어 스타일. supporting의 기본값이며 포트 전면 도입 없이 도메인 순수성만 지킨다
read_when: [init, review, fitness, scaffold]
rules: [ld.layer-order, ld.domain-pure, ld.domain-no-framework, ld.infra-isolated]
---

## 개념

`layered-domain`은 전통적인 레이어드 구조에 **도메인 레이어를 하나 더 세우고, 바깥으로 나가는
호출만 인터페이스로 뒤집는** 스타일이다. 레이어는 넷이다.

| 레이어 | 담는 것 | 아는 것 |
|---|---|---|
| domain | 엔티티·값 객체·도메인 서비스·불변식, 그리고 **리포지터리 인터페이스** | 없음 |
| application | 유스케이스(애플리케이션 서비스), 트랜잭션 경계 | domain |
| presentation | 컨트롤러, 요청·응답 모델, 조립 지점 | application, domain, infrastructure |
| infrastructure | JPA 엔티티와 리포지터리 구현, 외부 클라이언트, 메시지 발행 | domain, application |

[[hexagonal]]과 다른 점은 **뒤집는 범위**다. 들어오는 쪽(presentation → application)은 뒤집지
않는다 — 컨트롤러가 애플리케이션 서비스를 직접 부른다. 나가는 쪽만 뒤집는다 — 인터페이스는
domain이 소유하고 구현은 infrastructure에 산다. in 포트와 포트 명명 규칙이 없는 대신, 도메인
순수성은 hexagonal과 똑같이 지킨다.

**인터페이스/구현 분리를 실제로 만드는 것은 이름이 아니라 `ld.infra-isolated`다.** domain과
application이 infrastructure를 참조할 수 없으므로, 저장·발송·조회를 부르려면 안쪽에 인터페이스를
두는 것 외에 방법이 없다. 규약이 아니라 컴파일과 테스트가 강제한다.

**영속성 스탠스 — 도메인은 순수하다.** `@Entity`가 붙은 타입은 `infrastructure` 안에서만 선언되고
참조된다(`ld.domain-pure`). 도메인 모델은 순수 Kotlin/Java이고 영속 엔티티와의 매핑은
infrastructure의 리포지터리 구현이 진다([[persistence]]). JPA 엔티티를 도메인 엔티티로 그대로
쓰고 싶다면 이 스타일이 아니라 [[layered-simple]]을 명시적으로 고르는 것이 유일한 경로다
([[domain-classification]] R2).

**도메인 문서는 필수다.** `layered-domain`을 채택한 컨텍스트는
`docs/architecture/domain/<컨텍스트>.md`를 가져야 한다. 도메인 레이어를 분리해 놓고 무엇이
불변식인지 적지 않으면, 분리된 것은 패키지뿐이고 로직은 여전히 서비스에 남는다.

## 적용 기준

[[domain-classification]]은 `supporting` 컨텍스트의 기본 스타일로 이것을 제안한다. 판정은 두
단계이며, [[hexagonal]]과 같은 판정을 쓴다.

### 1단계 — 도메인 순수성이 필요한가

이 스타일과 [[hexagonal]]은 도메인 순수성(`*.domain-pure` + 프레임워크 차단)을 강제하고 도메인
문서를 요구한다는 점에서 **완전히 같다.** 그 값이 필요 없으면 둘 다 답이 아니다. 아래 중 하나라도
해당해야 1단계를 통과한다.

- 여러 필드·엔티티에 걸친 불변식을 **두 개 이상** 이름 댈 수 있다 — "해지된 계약에는 청구를 걸 수
  없다"처럼 한 행의 제약으로 표현되지 않는 규칙
- 같은 데이터가 상태에 따라 다른 규칙을 갖는다(상태 기계가 있다)
- 분류가 `core`다

하나도 해당하지 않으면 [[layered-simple]]로 간다. 도메인 레이어를 세워도 담을 것이 없다.

### 2단계 — 두 수를 세어 hexagonal과 가른다

1단계를 통과한 뒤 남는 차이는 **뒤집기의 범위** 하나뿐이므로 그것만 센다.

| | 세는 것 |
|---|---|
| **A** | 같은 유스케이스를 부르는(또는 12개월 안에 부르게 될) 진입점의 수 — REST, 메시지 소비자, 배치, 스케줄러, 관리 콘솔 |
| **B** | **두 번째 구현의 이름을 지금 댈 수 있는** 아웃바운드 의존의 수 — 결제사 이중화, SaaS에서 자체 구현으로 전환, 상시 대체 구현이 필요한 외부 호출 |

- **A = 1 이고 B ≤ 1 → layered-domain**
- **A ≥ 2 또는 B ≥ 2 → [[hexagonal]]**

"언젠가 바뀔 수도 있다"는 B에 세지 않는다. 이름을 대야 한다. [[hexagonal]]에 같은 표와 같은
판정을 두었으므로 어느 문서에서 시작하든 결론이 같다. A는 진입점 **종류**의 수다 — REST
엔드포인트가 열 개여도 종류는 하나이고, REST와 배치가 함께 있으면 둘이다.

**이 스타일이 아끼는 것.** in 포트와 포트 명명 규율(`hex.ports-owned-inside`)을 세우지 않는다.
그 둘은 A나 B가 2 이상일 때만 값을 내고, 그렇지 않으면 새로 외울 규약만 남는다. 도메인 순수성에
아직 익숙하지 않은 팀에게 이 차이는 작지 않다 — 규칙 넷으로 같은 순수성을 얻는다.

### 고르지 않는 조건 — 하나라도 해당하면 다른 스타일

- A ≥ 2 이거나 B ≥ 2다 → [[hexagonal]]
- 1단계를 통과하지 못한다 → [[layered-simple]]
- 애플리케이션 서비스에서 프레임워크를 걷어내야 한다 → [[clean]]. 이 스타일의 application은
  `@Service`·`@Transactional`을 쓰는 것이 정상이다
- presentation → infrastructure 통로가 위험하게 느껴진다 → 아래 R4를 읽고, 그래도 기계로 막아야
  하면 [[hexagonal]]이 그 선택이다

## 규칙

아래가 이 스타일의 선언이다. `파라미터` 셀의 문법과 레이어·패키지 판별은
`references/governance/rule-vocabulary.md` §2·§2.1이 정본이며 여기서 다시 정의하지 않는다.
각 인스턴스가 어떤 테스트 코드가 되는지는 `profiles/<프로파일>/rule-mappings.md`가 정한다 —
아래 "검사 형태"는 생성될 검사의 종류만 적는다.

### 선언

- 레이어: domain, application, presentation, infrastructure (domain이 가장 안쪽)

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| ld.layer-order | layer-order | layers=domain,application,presentation |
| ld.domain-pure | confine-type | type=jpa-entity; allowed_layer=infrastructure |
| ld.domain-no-framework | forbid-import | from=domain; to=org.springframework..,jakarta.persistence.. |
| ld.infra-isolated | forbid-import | from=domain,application; to=infrastructure |

### R1. ld.layer-order — 세 레이어의 호출 방향

`layers`는 안→밖 순서다. 레이어가 넷인데 여기에는 셋만 적는다 — **빠진 레이어는 이 규칙의 제약을
받지 않으며, 그것이 의도다.** infrastructure는 R4가 따로 다룬다.

- domain은 application·presentation을 참조할 수 없다
- application은 presentation을 참조할 수 없다
- presentation → application → domain 방향은 모두 허용된다

**검사 형태**: 레이어 쌍마다 안쪽이 바깥쪽을 import하면 실패하는 검사 3건.

### R2. ld.domain-pure — @Entity는 infrastructure 안에서만

이 규칙이 `layered-simple`과 이 스타일을 가르는 유일한 선언 차이다. 격리는 **양방향**이다 —
`@Entity` 타입은 infrastructure 밖에서 선언될 수 없고, infrastructure 밖에서 참조될 수도 없다.
application이 리포지터리 구현에서 JPA 엔티티를 그대로 받아 쓰는 흔한 누수가 두 번째 절반에
걸린다.

**검사 형태**: `@Entity` 타입의 선언 위치 검사 1건 + infrastructure 밖에서 그 타입을 참조하지
않는지 확인하는 검사 1건.

`presentation`도 예외가 아니다. 컨트롤러가 JPA 엔티티를 그대로 응답으로 내보내는 코드는 이
규칙 위반이고, 그것이 이 스타일에서 가장 자주 잡히는 위반이다.

### R3. ld.domain-no-framework — 도메인에 프레임워크 import 금지

`from=domain`은 레이어 참조, `to`의 두 항목은 패키지 패턴이다. R2가 `@Entity` 타입 집합을 막고
R3은 import 자체를 막으므로 둘은 겹치지 않는다 — `@Component`가 붙은 도메인 서비스,
`jakarta.persistence.Embeddable`만 붙은 값 객체는 R3에서만 잡힌다.

`application`은 `from`에 없다. 애플리케이션 서비스에 `@Service`·`@Transactional`을 붙이는 것은
이 스타일에서 정상이다.

**검사 형태**: domain 패턴의 파일이 두 패키지 패턴을 import하면 실패하는 검사 2건.

### R4. ld.infra-isolated — 안쪽은 구현을 모른다

`from`은 레이어 두 개, `to`도 레이어다. 이 규칙이 "인터페이스/구현 분리"를 기계 검증으로 만든다.
리포지터리 인터페이스는 domain에, 구현은 infrastructure에 두는 배치가 규약이 아니라 강제가 된다.

**presentation은 `from`에 없다 — 의도된 통로다.** 스프링 설정, 컴포넌트 스캔, 빈 조립처럼
구현체를 알아야만 하는 코드가 어딘가에는 있어야 하고, 그 자리가 presentation(또는 애플리케이션
모듈)이다. 여기까지 막으면 조립할 방법이 사라진다.

대신 이 통로는 남용되기 쉽다. 컨트롤러가 인프라 클라이언트를 직접 호출하는 코드는 **규칙 위반이
아니며 기계가 잡지 않는다.** R5의 체크리스트 항목으로 사람이 본다. 이것이 기계로 막히지 않는
것이 불편하다면, 그 불편이 [[hexagonal]]을 고를 이유다.

**검사 형태**: domain·application 패턴의 파일이 infrastructure 패턴을 import하면 실패하는
검사 2건.

### R5. 리뷰 체크리스트 (기계가 보지 않는 것)

- [ ] presentation이 infrastructure를 조립 목적 외로 부르는가? 컨트롤러에서 인프라 클라이언트를
      직접 호출하고 있다면 그 호출은 application으로 내린다
- [ ] domain에 인터페이스가 하나도 없는가? → 도메인 레이어가 데이터 홀더만 담고 있을 가능성.
      로직이 application에 남아 있으면 분리한 것은 패키지뿐이다
- [ ] application 서비스 하나가 여러 컨텍스트의 도메인을 조율하는가? → 경계 문제다
      ([[bounded-contexts]])
- [ ] 도메인 문서에 이 컨텍스트의 불변식이 있는가? 이 스타일은 도메인 문서가 필수다
- [ ] 네 레이어의 패키지 패턴이 각각 실제 소스를 잡는가? 어긋난 패턴은 위반 0건으로 보인다
      ([[package-conventions]])

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.policy.domain — 순수. 인터페이스도 여기서 소유한다
package com.acme.policy.domain

class Policy(val id: PolicyId, private var status: PolicyStatus) {
    fun renew(today: LocalDate) {
        require(status == PolicyStatus.ACTIVE) { "해지된 계약은 갱신할 수 없다" }
        status = PolicyStatus.RENEWED
    }
}

interface PolicyRepository {
    fun findById(id: PolicyId): Policy?
    fun save(policy: Policy)
}

// com.acme.policy.application — 유스케이스와 트랜잭션 경계
package com.acme.policy.application

@Service
class PolicyRenewalService(private val policies: PolicyRepository) {   // 인터페이스에만 의존
    @Transactional
    fun renew(id: PolicyId) {
        val policy = policies.findById(id) ?: throw PolicyNotFound(id)
        policy.renew(LocalDate.now())
        policies.save(policy)
    }
}

// com.acme.policy.infrastructure — JPA는 여기서 끝난다
package com.acme.policy.infrastructure

@Entity
class PolicyJpaEntity(@Id val id: Long, var status: String)

@Repository
class PolicyJpaRepositoryAdapter(private val jpa: PolicyJpaRepository) : PolicyRepository {
    override fun findById(id: PolicyId): Policy? = jpa.findByIdOrNull(id.value)?.toDomain()
    override fun save(policy: Policy) { jpa.save(policy.toJpaEntity()) }
}
```

infrastructure → domain 방향은 정상이다. 구현이 인터페이스를 알아야 하므로 이 방향까지 막으면
분리 자체가 성립하지 않는다.

### 안티패턴 1 — 도메인이 곧 JPA 엔티티

```kotlin
// com.acme.policy.domain.Policy
@Entity                                              // R2 위반: infrastructure 밖에서 @Entity 선언
class Policy(@Id val id: Long, var status: String)   // R3 위반: jakarta.persistence.. import
```

도메인 레이어가 생겼지만 안에 있는 것은 테이블이다. 이 상태를 유지할 생각이면 스타일 이름을
정직하게 [[layered-simple]]로 바꾸는 편이 낫다 — 규칙이 지켜지지 않는 선언보다 규칙이 적은
선언이 낫다.

### 안티패턴 2 — 서비스가 구현을 직접 잡음

```kotlin
// com.acme.policy.application.PolicyRenewalService
import com.acme.policy.infrastructure.PolicyJpaRepository   // R4 위반: application → infrastructure

@Service
class PolicyRenewalService(private val jpa: PolicyJpaRepository) {
    @Transactional
    fun renew(id: Long) {
        val entity = jpa.findByIdOrNull(id)!!                // R2 위반 B: 엔티티를 밖에서 참조
        entity.status = "RENEWED"                            // 갱신 규칙이 서비스로 새어 나왔다
    }
}
```

인터페이스는 domain에 그대로 있지만 아무도 쓰지 않는다. 도메인 순수성이 무너지는 실제 경로는
대개 이쪽이지 안티패턴 1이 아니다 — 엔티티에 `@Entity`를 붙이는 것은 눈에 띄지만, 서비스가
구현을 직접 잡는 것은 리뷰에서 잘 보이지 않는다. R4와 R2가 함께 잡는다.

## 관련 문서

- [[domain-classification]] — `supporting`의 기본 스타일이 여기인 이유
- [[hexagonal]] — 뒤집기를 인바운드까지 넓혀야 할 때. 판정 문항은 양쪽이 같다
- [[layered-simple]] — 도메인 레이어에 담을 것이 없을 때의 정직한 선택
- [[clean]] — application에서까지 프레임워크를 걷어내야 할 때
- [[persistence]] — 도메인 모델 ↔ 영속 엔티티 매핑을 어디에 두는가
- [[repositories-domain-services]] — 리포지터리 인터페이스를 domain에 두는 근거와 책임 경계
- [[package-conventions]] — 네 레이어가 패키지 패턴이 되는 방식
- [[module-composition]] — 레이어를 모듈로 나눌지 패키지로 나눌지는 이 선택과 직교한다
