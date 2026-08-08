---
summary: controller-service-repository 3레이어. JPA 엔티티를 도메인 엔티티로 직접 쓰는 것을 허용하는 유일한 프리셋이며 generic의 기본값이다
read_when: [init, review, fitness, scaffold]
rules: [ls.layer-order, ls.controller-naming, ls.service-naming]
---

## 개념

`layered-simple`은 컨트롤러·서비스·리포지터리 3레이어 구조다.

| 레이어 | 담는 것 | 아는 것 |
|---|---|---|
| presentation | 컨트롤러, 요청·응답 모델 | application, data |
| application | 서비스, 트랜잭션 경계 | data |
| data | JPA 엔티티, 스프링 데이터 리포지터리 | 없음 |

**영속성 스탠스 — JPA 엔티티를 도메인 엔티티로 직접 쓴다.** 이 스타일에는 `domain-pure` 규칙이
없다. 그것이 빠뜨린 것이 아니라 **이 스타일을 이 스타일이게 하는 정의적 특징이다.** 프리셋 4종 중
셋은 `*.domain-pure`로 도메인 모델에서 JPA·프레임워크 타입을 몰아내지만, 여기서는 `@Entity`가
붙은 클래스가 곧 모델이고 매핑 레이어가 없다. [[domain-classification]]의 기본 매핑상 **JPA 직접
사용이 열리는 경로는 이 스타일을 명시적으로 고르는 것 하나뿐이다.**

**도메인 문서는 선택이다.** `docs/architecture/domain/<컨텍스트>.md`를 요구하지 않는다. 이
스타일을 고른다는 것은 "여기에 문서로 남길 만한 불변식이 없다"는 판단을 이미 내렸다는 뜻이기
때문이다. 그 판단이 틀렸다면 문서를 추가할 것이 아니라 스타일을 올린다.

**이 스타일은 미완성 단계가 아니다.** 분류는 등급이 아니라 설계 비용의 예산 결정이고
([[domain-classification]]), `generic` 컨텍스트에 이것을 고르는 것은 권장이다. 담을 것이 없는
도메인 레이어, 아무도 유지하지 않는 포트, 필드를 그대로 베낀 매핑 코드는 아키텍처가 아니라
비용이다. 이 플러그인이 막으려는 것은 JPA 직접 사용이 아니라 **아무도 결정하지 않았는데 그렇게
되어 있는 상태**다. 결정해서 여기에 도달했다면 그것으로 충분하다.

## 적용 기준

[[domain-classification]]은 `generic` 컨텍스트의 기본 스타일로 이것을 제안한다.

### 고르는 조건 — 넷을 모두 만족할 때

1. **분류가 `generic`이다.** Q3에서 대체 제품 이름을 실제로 댔다. 못 댔다면 분류부터 다시 한다.
2. **커맨드가 전부 한 애그리거트(사실상 한 행 묶음) 저장으로 끝난다.** 하나의 요청이 여러 엔티티의
   상태를 함께 맞춰야 하는 경우가 없다.
3. **불변식이 필드 단위다.** 널 여부·범위·유일성 수준이어서 DB 제약과 검증 애노테이션으로
   표현된다. 여러 필드에 걸친 규칙을 두 개 이상 대지 못한다.
4. **이 컨텍스트를 통째로 외부 제품으로 교체하거나 삭제하는 시나리오가 이상하지 않다.**

### 고르지 않는 조건 — 하나라도 해당하면 [[layered-domain]] 이상

- 여러 필드·엔티티에 걸친 불변식을 **두 개 이상** 이름 댈 수 있다
- 같은 데이터가 상태에 따라 다른 규칙을 갖는다(상태 기계가 있다)
- 분류가 `core`다 → 근거 ADR 없이는 고르지 않는다. [[domain-classification]] R1의 기본 매핑은
  `core → hexagonal`이다
- 실패 비용이 높은데(Q4) 자체 구현을 계속 유지할 예정이다 → 그 컨텍스트는 `generic`이 아니라
  `supporting`이다
- 엔티티 setter나 서비스 메서드에 업무 분기가 이미 쌓여 있다 → 승격 신호다. 아래 "언제 올리는가"

### 언제 올리는가 — 승격 신호

한 번 고른 스타일을 영원히 쓰는 것이 아니다. 아래 중 둘 이상이 관찰되면 [[layered-domain]]으로의
승격을 evolve·review에서 제안한다.

- 같은 상태 검사(`if (status == ...)`)가 서로 다른 서비스 세 곳 이상에 복제되어 있다
- 엔티티에 업무 판단이 담긴 메서드가 생겼고, 그 메서드가 다른 엔티티를 인자로 받는다
- 테스트를 쓰려면 매번 스프링 컨텍스트와 DB가 필요하다
- 이 컨텍스트의 버그 중 "규칙을 한 군데 고쳤는데 다른 군데는 안 고쳤다"류가 반복된다

승격 방향의 비용이 반대 방향보다 크므로([[domain-classification]] R2), 애매하면 지금 승격하는
것보다 **신호를 기록해 두고 두 번째 신호를 기다리는 편**이 낫다. 다만 신호 없이 관성으로 남아
있는 것과, 신호를 보고도 남아 있는 것은 다르다.

## 규칙

아래가 이 스타일의 선언이다. `파라미터` 셀의 문법과 레이어·패키지 판별은
`references/governance/rule-vocabulary.md` §2·§2.1이 정본이며 여기서 다시 정의하지 않는다.
각 인스턴스가 어떤 테스트 코드가 되는지는 `profiles/<프로파일>/rule-mappings.md`가 정한다 —
아래 "검사 형태"는 생성될 검사의 종류만 적는다.

### 선언

- 레이어: presentation, application, data (위 → 아래 호출 방향. 안→밖 순서가 **아니다**)

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| ls.layer-order | layer-order | layers=data,application,presentation |
| ls.controller-naming | naming-suffix | scope=presentation; suffixes=Controller |
| ls.service-naming | naming-suffix | scope=application; suffixes=Service |

### R1. ls.layer-order — 레이어 라벨과 파라미터가 정확히 뒤집혀 있다

`layers`는 **언제나 안→밖 순서**이고, 이 스타일은 레이어 라벨이 호출 방향(위→아래)으로 적혀 있어
두 줄이 글자 그대로 반대가 된다. 프리셋 4종 중 유일한 경우이므로 여기서 한 번 더 못 박는다.

| | 순서 |
|---|---|
| 레이어 라벨 | presentation → application → data (호출 방향) |
| `layers` 파라미터 | data → application → presentation (안→밖 = 의존 방향) |

가장 안쪽은 `data`다. 아무것에도 의존하지 않는 것이 데이터 모델이라는 뜻이고, 그것이 이 스타일의
솔직한 자기 서술이다 — 다른 셋은 가장 안쪽에 도메인 모델을 둔다.

강제되는 내용:

- data는 application·presentation을 참조할 수 없다
- application은 presentation을 참조할 수 없다
- presentation·application → data는 허용된다. **이 허용이 JPA 엔티티 직접 사용을 성립시킨다** —
  `data`에서 선언된 `@Entity` 타입을 서비스와 컨트롤러가 그대로 다룰 수 있다

**검사 형태**: 레이어 쌍마다 안쪽이 바깥쪽을 import하면 실패하는 검사 3건
(data↛application, data↛presentation, application↛presentation).

### R2. ls.controller-naming / R3. ls.service-naming

`scope`가 레이어 전체이므로 **그 레이어의 모든 최상위 public 타입**이 해당 접미사로 끝나야 한다.
값은 대소문자를 구분한다.

요청·응답 DTO를 어디에 둘지가 곧바로 문제가 된다. `ClaimRequest`를 presentation에 최상위로 두면
R2 위반이고, application에 두면 R3 위반이다. 해법은 셋이며 이 순서로 검토한다.

1. **컨트롤러의 중첩 타입으로 둔다.** 중첩 타입은 검사 대상이 아니다(`rule-vocabulary.md` §3.4).
   요청·응답 모델은 그 엔드포인트에만 쓰이므로 대개 이것이 맞다.
2. **`internal`로 둔다.** 최상위 public 타입만 대상이다.
3. **스코프를 패키지 패턴으로 좁힌 커스텀 스타일을 선언한다.** 프리셋 문서를 고치는 것이 아니다.

`data` 레이어에는 명명 규칙이 없다. 엔티티와 리포지터리 이름은 자유다.

**검사 형태**: presentation 패턴의 최상위 public 타입 이름이 `Controller`로 끝나는지 확인하는
검사 1건, application 패턴에 대해 `Service`로 같은 검사 1건.

### R4. 없는 규칙 — domain-pure가 없다는 것이 선언이다

다른 세 프리셋에 있는 `confine-type`(`*.domain-pure`) 인스턴스가 여기에는 **없다.** 표에서 빠진
것이 아니라 이 스타일의 내용이다.

| | layered-simple | 나머지 셋 |
|---|---|---|
| `@Entity` 선언 위치 | 제약 없음(관례상 data) | 지정 레이어 안에서만 |
| 서비스·컨트롤러가 엔티티를 직접 다루기 | **허용** | 위반 |
| 도메인 모델 ↔ 영속 엔티티 매핑 코드 | 없음 | 필수 |
| 도메인 문서 | 선택 | 필수 |

따라서 이 스타일에서는 `@Entity` 타입이 컨트롤러 응답으로 그대로 나가도 아키텍처 규칙 위반이
아니다. 직렬화 사고·지연 로딩 누수는 여전히 실무 문제이므로 R5의 체크리스트로 사람이 본다
([[persistence]]).

프레임워크 차단 `forbid-import` 인스턴스도 없다. 막을 도메인 레이어가 없기 때문이다.

### R5. 리뷰 체크리스트 (기계가 보지 않는 것)

- [ ] 엔티티를 응답으로 그대로 내보내고 있는가? 규칙 위반은 아니지만, 스키마 변경이 곧 API 변경이
      된다. 최소한 목록·상세 응답은 별도 타입으로 뽑는다
- [ ] 서비스가 다른 서비스를 호출하는 사슬이 3단 이상인가? 필요하면
      `forbid-sibling-dependency`(`layer=application; suffix=Service`)를 이 컨텍스트에 추가로
      채택하는 것을 검토한다 — 프리셋에는 없다
- [ ] 트랜잭션 밖에서 지연 로딩 프로퍼티에 접근하는 코드가 있는가?
- [ ] 위 "승격 신호" 넷 중 몇 개가 관찰되는가? 둘 이상이면 [[layered-domain]] 승격을 제안한다
- [ ] 세 레이어의 패키지 패턴이 각각 실제 소스를 잡는가? 어긋난 패턴은 위반 0건으로 보인다
      ([[package-conventions]])

## 사례

### 올바른 예 — Kotlin

```kotlin
// com.acme.notification.data — 엔티티가 곧 모델이다. 매핑 레이어가 없다
package com.acme.notification.data

@Entity
class NotificationTemplate(
    @Id @GeneratedValue val id: Long = 0,
    var channel: String,
    var body: String,
)

interface NotificationTemplateRepository : JpaRepository<NotificationTemplate, Long>

// com.acme.notification.application — 타입 이름이 Service로 끝난다
package com.acme.notification.application

@Service
class NotificationTemplateService(private val repository: NotificationTemplateRepository) {
    @Transactional
    fun updateBody(id: Long, body: String) {
        val template = repository.findByIdOrNull(id) ?: throw TemplateNotFound(id)
        template.body = body                       // 엔티티를 그대로 다룬다 — 이 스타일에서는 정상
    }
}

// com.acme.notification.presentation — 타입 이름이 Controller로 끝난다
package com.acme.notification.presentation

@RestController
class NotificationTemplateController(private val service: NotificationTemplateService) {
    data class UpdateRequest(val body: String)     // 중첩 타입 — 명명 규칙 대상 아님

    @PutMapping("/templates/{id}")
    fun update(@PathVariable id: Long, @RequestBody request: UpdateRequest) =
        service.updateBody(id, request.body)
}
```

### 안티패턴 1 — 파라미터 순서를 레이어 라벨에서 베낌

레이어 라벨은 `presentation, application, data`로 옳게 적었는데, `ls.layer-order`의 파라미터를
`layers=presentation,application,data`로 — 즉 라벨을 그대로 복사해 — 적은 선언이다.
(이 문서의 유일한 정본 선언은 위 `### 선언`의 표이며, 여기 적은 것은 틀린 값이다.)

`layers`가 안→밖이라는 것을 잊었을 때 나오는 결과다. 파서는 오류를 내지 않는다 — 세
항목 모두 선언된 레이어이므로 문법적으로 완전히 정상이다. 대신 강제되는 내용이 정반대가 된다.

- 컨트롤러가 서비스를 부르는 정상 코드가 **전부 위반으로** 뜬다
- 엔티티가 컨트롤러를 참조하는 진짜 문제는 **통과한다**

전자 때문에 팀은 하루 안에 알아차리고 규칙을 꺼 버리기 쉽다. 그러면 후자가 영구히 열린다. 선언을
쓸 때 라벨을 복사하지 말고 의존 방향으로 다시 판단한다(`rule-vocabulary.md` §3.1).

### 안티패턴 2 — 승격 신호를 지나친 코드

```kotlin
// com.acme.notification.data.NotificationTemplate
import com.acme.notification.application.TemplatePolicyService   // R1 위반: data → application

@Entity
class NotificationTemplate(...) {
    fun canSend(now: LocalDateTime): Boolean {                   // 업무 판단이 엔티티로 들어왔다
        if (status == "PAUSED") return false
        if (channel == "SMS" && quietHours(now)) return false    // 같은 분기가 서비스 두 곳에도 있다
        return TemplatePolicyService.isAllowed(this)
    }
}
```

R1은 import 한 줄만 잡는다. 진짜 문제는 규칙이 잡지 못하는 쪽이다 — 이 컨텍스트는 이미 상태
기계를 갖고 있고, 같은 분기가 세 곳에 복제되어 있다. 승격 신호 둘이 동시에 켜진 상태이므로
import를 지우는 것이 아니라 [[layered-domain]]으로 올릴 시점이다. `layered-simple`이 틀린 선택이
되는 것은 이렇게 조건이 변할 때이지, 처음 고른 순간이 아니다.

## 관련 문서

- [[domain-classification]] — `generic`의 기본 스타일이 여기인 이유, JPA 직접 사용이 이 선택으로만
  열리는 이유(R2)
- [[layered-domain]] — 승격의 첫 목적지. 도메인 순수성이 여기서 시작된다
- [[hexagonal]] — 분류가 `core`로 바뀌었을 때의 기본값
- [[clean]] — 프레임워크를 유스케이스 밖으로까지 밀어야 할 때
- [[persistence]] — JPA 직접 사용이 정당한 조건과 지연 로딩·양방향 연관 안티패턴
- [[package-conventions]] — 세 레이어가 패키지 패턴이 되는 방식
- [[module-composition]] — 이 스타일도 모듈 구성 3형 어디에나 올릴 수 있다
