---
summary: 포트와 어댑터 — domain·application을 안쪽에 두고 바깥과의 모든 상호작용을 포트로 뒤집는 스타일. core의 기본값이며 도메인은 순수하게 유지한다
read_when: [init, review, fitness, scaffold, migrate]
rules: [hex.deps-inward, hex.domain-pure, hex.domain-no-framework, hex.ports-owned-inside]
---

## 개념

헥사고날(포트와 어댑터)은 레이어를 셋으로 두고, **바깥 세계와의 모든 상호작용을 안쪽이 소유한
인터페이스(포트)로 뒤집는** 스타일이다.

| 레이어 | 담는 것 | 아는 것 |
|---|---|---|
| domain | 엔티티·값 객체·도메인 서비스·불변식 | 없음 |
| application | 유스케이스와 포트 인터페이스(in/out) | domain |
| adapter | 웹 컨트롤러, JPA 영속, 외부 API 클라이언트, 메시지 소비자 | application, domain |

핵심은 레이어 개수가 아니라 **방향**이다. 실행 시점의 흐름은 HTTP 요청 → 유스케이스 → DB로
바깥에서 안으로, 다시 안에서 바깥으로 흐르지만, 컴파일 시점의 의존은 언제나 안쪽을 향한다.
그 방향이 뒤집히는 지점이 out 포트다 — `ClaimPersistenceAdapter`(adapter)가 `SaveClaimPort`
(application)를 구현하고, application은 그 구현이 JPA인지 파일인지 모른다.

**영속성 스탠스 — 도메인은 순수하다.** `@Entity`가 붙은 타입은 `adapter` 안에서만 선언되고
참조된다(`hex.domain-pure`). 도메인 모델은 JPA·스프링 타입을 모르는 순수 Kotlin/Java이고, 도메인
모델과 영속 엔티티 사이의 매핑은 out 어댑터의 책임이다([[persistence]]). 이 스타일에는 JPA
엔티티를 도메인 엔티티로 그대로 쓰는 경로가 없다. 그 경로가 필요하면 규칙 예외가 아니라 스타일
선택을 다시 본다 — 답은 대개 [[layered-simple]]이다([[domain-classification]] R2).

**도메인 문서는 필수다.** `hexagonal`을 채택한 컨텍스트는 `docs/architecture/domain/<컨텍스트>.md`를
가져야 한다. 포트가 뒤집어 주는 것은 의존 방향뿐이고, 무엇이 불변식인지는 문서가 없으면 다음
세션에 다시 추측된다.

## 적용 기준

[[domain-classification]]은 `core` 컨텍스트의 기본 스타일로 이것을 제안한다. 아래는 그 기본값을
확정하거나 뒤집기 위한 판정이며 두 단계로 나뉜다.

### 1단계 — 도메인 순수성이 필요한가

hexagonal과 [[layered-domain]]은 도메인 순수성(`*.domain-pure` + 프레임워크 차단)을 강제하고
도메인 문서를 요구한다는 점에서 **완전히 같다.** 그 값이 필요 없으면 둘 다 답이 아니다. 아래 중
하나라도 해당해야 1단계를 통과한다.

- 여러 필드·엔티티에 걸친 불변식을 **두 개 이상** 이름 댈 수 있다
- 같은 데이터가 상태에 따라 다른 규칙을 갖는다(상태 기계가 있다)
- 분류가 `core`다

통과하지 못하면 [[layered-simple]]로 간다. 분류는 `core`인데 앞의 두 항목을 하나도 못 채운다면
분류부터 다시 본다([[domain-classification]] Q1).

### 2단계 — 두 수를 세어 layered-domain과 가른다

1단계를 통과한 뒤 남는 차이는 **뒤집기의 범위** 하나뿐이므로 그것만 센다.

| | 세는 것 |
|---|---|
| **A** | 같은 유스케이스를 부르는(또는 12개월 안에 부르게 될) 진입점의 수 — REST, 메시지 소비자, 배치, 스케줄러, 관리 콘솔 |
| **B** | **두 번째 구현의 이름을 지금 댈 수 있는** 아웃바운드 의존의 수 — 결제사 이중화, SaaS에서 자체 구현으로 전환, 상시 대체 구현이 필요한 외부 호출 |

- **A ≥ 2 또는 B ≥ 2 → hexagonal**
- **A = 1 이고 B ≤ 1 → [[layered-domain]]**

"언젠가 바뀔 수도 있다"는 B에 세지 않는다. 이름을 대야 한다. A는 진입점 **종류**의 수다 — REST
엔드포인트가 열 개여도 종류는 하나이고, REST와 배치가 함께 있으면 둘이다. [[layered-domain]]에
같은 표와 같은 판정을 두었으므로 어느 문서에서 시작하든 결론이 같다.

**왜 A와 B만 세는가.** hexagonal이 layered-domain보다 더 요구하는 것은 정확히 둘이다 — in 포트를
세우는 일과 `hex.ports-owned-inside`가 강제하는 명명 규율. 이 비용이 값을 내는 경우도 정확히
둘이다. 진입점이 여럿이라 유스케이스 의미가 복제될 위험이 있을 때(A), 어댑터를 실제로 갈아 끼울
때(B). 둘 다 아니면 layered-domain이 같은 도메인 순수성을 더 적은 규칙으로 준다.

### 고르지 않는 조건

- A = 1이고 B ≤ 1이다 → [[layered-domain]]
- 1단계를 통과하지 못한다 → [[layered-simple]]. 유스케이스가 전부 한 애그리거트 저장으로 끝나면
  포트는 값을 만들지 않고 이름만 늘린다
- 유스케이스 레이어에서 프레임워크를 완전히 걷어내야 한다(트랜잭션 경계까지 바깥으로) → [[clean]].
  hexagonal의 `application`은 `@Transactional`·`@Service`를 쓸 수 있다
- 컨텍스트 경계가 아직 정해지지 않았다 → [[bounded-contexts]]를 먼저 끝낸다. 경계가 흔들리는
  상태에서 포트를 그으면 포트가 잘못된 경계를 고정한다

분류 기본값을 벗어나는 선택(예: `supporting`인데 hexagonal)은 가능하며, 그때는 2단계의 A·B 값을
근거로 ADR을 남긴다.

## 선언

- 레이어: domain, application, adapter (안 → 밖 순서)

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| hex.deps-inward | layer-order | layers=domain,application,adapter |
| hex.domain-pure | confine-type | type=jpa-entity; allowed_layer=adapter |
| hex.domain-no-framework | forbid-import | from=domain; to=org.springframework..,jakarta.persistence.. |
| hex.ports-owned-inside | naming-suffix | scope=application; suffixes=Port,UseCase |

`파라미터` 셀의 문법과 레이어·패키지 판별은 `references/governance/rule-vocabulary.md` §2·§2.1이
정본이며 여기서 다시 정의하지 않는다. 각 인스턴스의 해설은 아래 `## 규칙`에 있다.

## 규칙

각 인스턴스가 어떤 테스트 코드가 되는지는 `profiles/<프로파일>/rule-mappings.md`가 정한다 —
아래 "검사 형태"는 생성될 검사의 종류만 적는다.

### R1. hex.deps-inward — 의존은 안으로만

`layers`는 안→밖 순서이고, 이 스타일에서는 레이어 라벨의 순서와 같다.

- domain은 application·adapter를 참조할 수 없다
- application은 adapter를 참조할 수 없다. adapter → application·domain은 허용된다
- `strict`를 쓰지 않았으므로 adapter → domain 직접 참조는 정상이다. 어댑터가 도메인 모델을
  매핑해야 하므로 여기서 막으면 매핑할 방법이 사라진다

**검사 형태**: 레이어 쌍마다 "안쪽 패턴의 파일이 바깥쪽 패턴을 import하면 실패"하는 검사 3건
(domain↛application, domain↛adapter, application↛adapter).

### R2. hex.domain-pure — @Entity는 adapter 안에서만

이 규칙이 스타일의 정체성이다. 격리는 **양방향**이다 — `@Entity` 타입은 adapter 밖에서 선언될 수
없고, adapter 밖에서 참조될 수도 없다. 두 번째 절반이 실질이다. 엔티티를 어댑터에 두고
application이 그것을 그대로 꺼내 쓰면 포트는 형식만 남는다.

**검사 형태**: `@Entity` 타입의 선언 위치가 adapter 패턴 안인지 확인하는 검사 1건 +
adapter 밖의 파일이 그 타입들을 참조하지 않는지 확인하는 검사 1건.

이 규칙을 예외로 빼려는 요구가 나오면 예외가 아니라 스타일 선택을 먼저 검토한다
(`rule-vocabulary.md` §4).

### R3. hex.domain-no-framework — 도메인에 프레임워크 import 금지

`from=domain`은 레이어 참조, `to`의 두 항목은 패키지 패턴이다. R2가 타입 집합(`@Entity`)을 막고,
R3은 import 자체를 막는다. 둘은 겹치지 않는다 — `@Component`가 붙은 도메인 서비스나
`jakarta.persistence.Id`만 슬쩍 쓰는 값 객체는 R2로는 잡히지 않고 R3으로 잡힌다.

`application`은 이 규칙의 `from`에 없다. hexagonal에서 유스케이스에 `@Service`·`@Transactional`을
붙이는 것은 허용이며, 그것을 막고 싶으면 [[clean]]이 그 선택이다.

**검사 형태**: domain 패턴의 파일이 두 패키지 패턴을 import하면 실패하는 검사 2건.

### R4. hex.ports-owned-inside — application의 공개 표면은 포트뿐

`scope=application`은 레이어 전체이므로 **application의 모든 최상위 public 타입**이 `Port` 또는
`UseCase`로 끝나야 한다. 강한 규칙이고, 프리셋 4종에서 예외가 가장 자주 필요해지는 규칙이다
(`rule-vocabulary.md` §3.4).

걸리는 것은 대개 하나다. 흔한 관례에서 in 포트 인터페이스는 이미 `ApproveClaimUseCase`인데
**구현 클래스 이름만** `ApproveClaimService`여서 위반이 된다. 규칙을 켠 채로 사는 방법은 넷이며,
이 순서로 검토한다.

1. **구현에 접두사를 붙여 `DefaultApproveClaimUseCase`로 짓는다.** 인터페이스와 구현이 모두
   `UseCase`로 끝나 통과한다. **포기하는 것이 없고 한 단어면 된다** — in 포트도 그대로 두고 명명
   규율도 그대로 지킨다. 관례에서 바꾸는 것은 구현 클래스 이름 하나뿐이다.
2. **in 포트 인터페이스를 두지 않고 유스케이스 클래스 자체를 `...UseCase`로 짓는다.** 커맨드·결과
   타입은 그 클래스의 중첩 타입으로 둔다(중첩 타입은 검사 대상이 아니다). 다만 이것은 in 포트를
   포기하는 선택이고, in 포트는 이 스타일을 [[layered-domain]] 대신 고른 이유의 절반이다 —
   적용 기준 2단계의 A가 1이었다면 애초에 layered-domain이 맞았을 수 있다.
3. **구현을 `internal`로 둔다.** 최상위 public 타입만 대상이므로 `internal class ApproveClaimService`는
   위반이 아니다. 단 **Kotlin 전용 답이며 java-spring 프로파일에는 대응물이 없다**(Java의
   package-private은 같은 패키지 안에서만 보인다). 컨텍스트가 모듈 하나일 때만 유효하다.
4. **스코프를 좁힌 커스텀 스타일을 선언하거나, 컨텍스트에서 규칙 예외로 뺀다** —
   `- 규칙 예외: -hex.ports-owned-inside (ADR-XXXX)`. 근거 ADR이 반드시 따른다.

**애노테이션은 검사 대상이 아니다** — `@Service`가 붙은 `ApproveClaimUseCase`는 정상이다.
검사하는 것은 타입 이름뿐이다.

**예외 타입은 domain에 선언한다.** application에 최상위 public으로 두면 `Port`·`UseCase`로 끝나지
않아 위반이다. domain에는 명명 규칙이 없고, "청구를 찾을 수 없다"는 업무 사실이므로 도메인에
속하는 것이 자연스럽다. 순수성 규칙(R2·R3)도 걸리지 않는다 — 예외는 프레임워크 타입도
`@Entity`도 아니다.

**검사 형태**: application 패턴의 최상위 public 타입 이름이 `Port`·`UseCase` 중 하나로 끝나는지
확인하는 검사 1건.

### R5. 리뷰 체크리스트 (기계가 보지 않는 것)

- [ ] out 포트가 도메인 타입만 주고받는가? 시그니처에 어댑터 DTO가 있으면 R2를 우회한 누수다
- [ ] 포트 이름이 기술이 아니라 의도인가? `SaveClaimPort`는 좋고 `ClaimJpaPort`는 어댑터가
      이름으로 새어 나온 것이다
- [ ] 구현이 하나뿐인 포트가 대부분인가? → 적용 기준 2단계의 A·B를 다시 센다
- [ ] 도메인 문서에 이 컨텍스트의 불변식이 있는가? hexagonal은 도메인 문서가 필수다
- [ ] adapter 패턴이 실제 소스를 잡는가? 어긋난 패턴은 위반 0건으로 보인다([[package-conventions]])

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.claim.domain — 순수. 프레임워크 import 없음
package com.acme.claim.domain

class Claim(val id: ClaimId, private var status: ClaimStatus) {
    fun approve(approver: UserId) {
        require(status == ClaimStatus.REVIEWING) { "심사 중인 청구만 승인할 수 있다" }
        status = ClaimStatus.APPROVED
    }
}

// 예외는 domain에 둔다 — domain에는 명명 규칙이 없고, 업무 사실이다 (R4)
class ClaimNotFound(id: ClaimId) : RuntimeException("청구 없음: $id")

// com.acme.claim.application — 포트는 안쪽이 소유한다
package com.acme.claim.application

interface LoadClaimPort { fun findById(id: ClaimId): Claim? }
interface SaveClaimPort { fun save(claim: Claim) }

interface ApproveClaimUseCase {                        // in 포트 — UseCase로 끝난다
    fun handle(command: Command)
    data class Command(val claimId: ClaimId, val approver: UserId)   // 중첩 타입 — R4 대상 아님
}

@Service                                               // 애노테이션은 검사 대상이 아니다
class DefaultApproveClaimUseCase(                      // 구현도 UseCase로 끝난다 — R4의 1번
    private val loadClaim: LoadClaimPort,
    private val saveClaim: SaveClaimPort,
) : ApproveClaimUseCase {
    @Transactional
    override fun handle(command: ApproveClaimUseCase.Command) {
        val claim = loadClaim.findById(command.claimId) ?: throw ClaimNotFound(command.claimId)
        claim.approve(command.approver)
        saveClaim.save(claim)
    }
}

// com.acme.claim.adapter.out.persistence — JPA는 여기서 끝난다
package com.acme.claim.adapter.out.persistence

@Entity
class ClaimJpaEntity(@Id val id: Long, var status: String)

@Repository
class ClaimPersistenceAdapter(private val jpa: ClaimJpaRepository) : LoadClaimPort, SaveClaimPort {
    override fun findById(id: ClaimId): Claim? = jpa.findByIdOrNull(id.value)?.toDomain()
    override fun save(claim: Claim) { jpa.save(claim.toJpaEntity()) }
}
```

### 안티패턴 1 — 도메인이 영속 엔티티가 됨

```kotlin
// com.acme.claim.domain.Claim
@Entity                                            // R2 위반: adapter 밖에서 @Entity 선언
class Claim(@Id val id: Long, var status: String)  // R3 위반: jakarta.persistence.. import
```

포트와 어댑터 디렉터리는 그대로 있는데 안쪽이 스키마에 묶였다. 어댑터를 갈아 끼울 수 없으므로
헥사고날이라고 부를 근거가 사라진다. 이 상태가 편하다면 [[layered-simple]]이 정직한 선택이다.

### 안티패턴 2 — 포트는 있는데 엔티티가 샌다

```kotlin
// com.acme.claim.application.LoadClaimPort
interface LoadClaimPort {
    fun findById(id: ClaimId): ClaimJpaEntity?     // R2 위반 B: 격리 범위 밖에서 참조
}
```

선언 위치만 검사하는 규칙이었다면 통과했을 코드다. 포트 시그니처에 어댑터 타입이 들어간 순간
application이 JPA 스키마를 알게 되고, 뒤집기는 이름만 남는다. `confine-type`이 참조까지 막는
이유가 이것이다.

## 관련 문서

- [[domain-classification]] — `core`의 기본 스타일이 여기인 이유와 기본값을 벗어날 때의 절차
- [[layered-domain]] — 도메인 순수성은 같고 뒤집기 범위만 작은 선택지
- [[clean]] — usecase 레이어에서까지 프레임워크를 걷어내야 할 때
- [[layered-simple]] — 도메인 순수성을 포기하는 것이 정답인 경우
- [[persistence]] — 도메인 모델 ↔ 영속 엔티티 매핑을 어디에 두는가
- [[package-conventions]] — 레이어 이름이 패키지 패턴이 되는 방식, 위반 0건 실패 모드
- [[module-composition]] — 세 레이어를 모듈로 나눌지 패키지로 나눌지는 직교한다
- [[repositories-domain-services]] — 포트와 리포지터리의 책임 경계
