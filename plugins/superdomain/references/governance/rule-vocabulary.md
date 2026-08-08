# 규칙 어휘 (rule vocabulary) — 정본

스타일이 선언할 수 있는 규칙의 **닫힌 집합**을 정의한다. 이 문서에 없는 규칙은 존재하지 않는다.

**목차 — 무엇을 판단하러 왔는가**

| 하려는 일 | 읽을 곳 |
|---|---|
| 왜 어휘를 마음대로 늘릴 수 없는지 알기 | [§1 폐쇄 원칙](#1-폐쇄-원칙) |
| 파라미터 셀을 정확히 쓰기·읽기 | [§2 파라미터 문법](#2-파라미터-문법) |
| 쓸 수 있는 규칙과 그 파라미터 확인 | [§3 primitive 5종](#3-primitive-5종) |
| 규칙 id 짓기, 예외 선언 검토 | [§4 규칙 id 규약](#4-규칙-id-규약) |
| 선언부터 강제까지 전체 흐름 보기 | [§5 워크드 예제](#5-워크드-예제--hexagonal-전체-체인) |
| 새 규칙이 필요한 것 같을 때 | [§6 먼저 이것부터](#6-새-규칙이-필요할-때--먼저-이것부터) → [§7 확장 절차](#7-어휘-확장-절차) |

---

## 1. 폐쇄 원칙

**스타일은 열려 있고, 규칙 어휘는 닫혀 있다.**

프로젝트는 어떤 아키텍처 스타일이든 선언할 수 있다 — 3계층, 4계층, 헥사고날, 자기만의 변형. 그러나 모든 스타일은 아래 5종 primitive의 **조합**으로 표현되어야 한다.

이 폐쇄가 없으면 성립하지 않는 것:

| 폐쇄가 주는 것 | 열린 어휘였다면 |
|---|---|
| 프로파일은 스타일이 아니라 primitive 5종만 매핑하면 된다 | 스타일이 늘 때마다 두 프로파일을 고쳐야 한다 |
| 아무도 예상하지 않은 커스텀 스타일도 테스트가 자동 생성된다 | 선언은 되는데 생성은 안 되는 스타일이 생긴다 |
| "선언된 것은 강제된다"가 참이다 | 선언만 되고 조용히 강제되지 않는 규칙이 생긴다 |

마지막 줄이 핵심이다. 생성할 수 없는 규칙은 **없는 규칙보다 나쁘다** — 지켜지고 있다고 믿게 만들기 때문이다.

따라서: **어휘 밖의 임시 검사(ad-hoc check)는 금지한다.** "이번만 스크립트로 확인하자", "리뷰에서 눈으로 보자"는 규칙이 아니라 관행이다. 기계 검증이 필요하면 어휘에 정식 등록하는 것이 유일한 경로다(§7). 기계 검증이 불가능한 판단이면 규칙이 아니라 `knowledge/`·`conventions/` 문서의 리뷰 체크리스트로 쓴다.

---

## 2. 파라미터 문법

스타일 선언 표의 `파라미터` 셀은 이 문법으로 파싱된다. 두 사람이 같은 셀을 읽으면 반드시 같은 결과가 나와야 한다.

```
파라미터셀 ::= 파라미터 ( ";" 파라미터 )*
파라미터   ::= 키 "=" 값
키         ::= [a-z][a-z0-9_]*          (소문자 snake_case)
값         ::= 항목 ( "," 항목 )*
항목       ::= ";" "," "=" 와 공백을 포함하지 않는 문자열
```

**파싱 절차** (이 순서대로)

1. 셀을 `;`로 분할한다.
2. 각 조각을 `=`에서 키와 값으로 나눈다. 조각에 `=`가 0개거나 2개 이상이면 오류.
3. 키와 값의 앞뒤 공백을 제거한다.
4. 값을 `,`로 분할하고 각 항목의 앞뒤 공백을 제거한다 → **모든 값은 목록이다**. 항목이 하나면 길이 1의 목록.

**규칙**

- 키 순서는 의미가 없다. `a=1; b=2`와 `b=2; a=1`은 같다.
- 키 중복은 오류다. 목록을 넣으려면 `,`를 쓴다.
- 해당 primitive가 정의하지 않은 키는 오류다 — 오타가 조용히 무시되면 규칙이 사라진다.
- 빈 키·빈 값·빈 항목은 오류다. 따라서 후행 `;`(`a=1;`)도 오류다.
- **trim 후에도 키나 항목 안에 공백이 남으면 오류다**(`suffixes=Use Case`). 3·4단계의 trim은 구분자 주변 여백만 제거하며, 항목 내부 공백을 허용하지 않는다(BNF의 항목 정의와 같다).
- **형식이 목록이 아닌 키에 항목이 2개 이상이면 오류다.** §3의 형식 열에 "목록"이 없는 키(`type`, `layer`, `suffix`, `scope`, `strict`)가 여기 해당한다 — `suffix=Service,Component`는 OR로 해석되지 않고 거부된다.
- 키는 소문자만. 값은 **대소문자를 구분한다**(`suffixes=Controller`는 `controller`와 다르다).
- 인용 부호는 없다. 값에 `;` `,` `=` 공백을 넣을 수 없다 — 필요한 값이 생기면 문법이 아니라 파라미터 설계를 다시 본다.

**해석 결과 예시**

| 파라미터 셀 | 파싱 결과 |
|---|---|
| `layers=domain,application,adapter` | `layers = [domain, application, adapter]` |
| `type=jpa-entity; allowed_layer=adapter` | `type = [jpa-entity]`, `allowed_layer = [adapter]` |
| `from=domain; to=org.springframework..,jakarta.persistence..` | `from = [domain]`, `to = [org.springframework.., jakarta.persistence..]` |
| `layer=application; suffix=Service` | `layer = [application]`, `suffix = [Service]` |

세 번째 행이 목록 값의 표준형이다: `;`가 파라미터를 가르고, `,`가 한 파라미터 안의 항목을 가른다.

**패키지 패턴 표기**: `..`로 끝나면 그 패키지와 모든 하위 패키지를 뜻한다(`org.springframework..`). `..` 없이 쓰면 정확히 그 패키지·타입만 뜻한다. Konsist·ArchUnit이 공유하는 표기이며 프로파일이 그대로 번역한다.

### 2.1 레이어 이름과 패키지 패턴의 판별

§3의 형식 열이 "레이어 이름 또는 패키지 패턴"인 **모든 파라미터**에 적용된다 — 현재 `forbid-import`의 `from`·`to`, `naming-suffix`의 `scope`. 한 파라미터 안에 두 종류가 섞일 수 있으므로 판별 규칙이 필요하다.

1. 항목이 스타일의 `레이어` 라벨에 선언된 이름과 **정확히 일치**하면 → 레이어 참조. fitness가 정규화 결과(컨텍스트 × 레이어 → 패키지 패턴 집합, 스펙 §4.3 규칙 3)로 치환한다.
2. 그 외에는 → 패키지 패턴 그대로.
3. **레이어 이름이 우선한다.** 따라서 레이어 이름과 동명인 최상위 패키지는 그대로 쓸 수 없고, `..`를 붙여 완전한 패턴(`com.acme.domain..`)으로 써야 한다.

이 판별에는 조용한 실패 모드가 하나 있다: 레이어로 의도한 값이 오타 등으로 레이어 목록에 없으면 규칙 2에 따라 패키지 패턴으로 해석되고, **매칭 대상이 0개가 되어 규칙이 아무것도 검사하지 않은 채 통과한다.** 이는 §1이 "없는 규칙보다 나쁘다"고 부른 상태이므로, 파서는 `.`을 포함하지 않으면서 레이어 목록에도 없는 항목을 오류로 보고한다.

---

## 3. primitive 5종

### 3.1 `layer-order`

**강제 내용** — 선언된 레이어 순서에서 안쪽 레이어는 바깥쪽 레이어에 의존할 수 없다. 바깥쪽 → 안쪽 의존은 허용한다.

| 키 | 필수 | 형식 | 기본값 | 설명 |
|---|---|---|---|---|
| `layers` | 필수 | 레이어 이름 목록 | — | **항상 안 → 밖 순서.** 스타일의 `레이어` 라벨에 적힌 순서와 무관하다 |
| `strict` | 선택 | `true` \| `false` | `false` | `true`면 인접 레이어에만 의존 가능(건너뛴 의존 금지) |

**선언 예**

```
| hex.deps-inward | layer-order | layers=domain,application,adapter |
```

`domain`은 아무것에도 의존하지 않고, `application`은 `domain`에, `adapter`는 `application`·`domain`에 의존할 수 있다. `strict=true`였다면 `adapter → domain` 직접 의존도 위반이 된다.

**위반 예**

```kotlin
// com.acme.claim.domain.Claim  (domain 레이어)
import com.acme.claim.adapter.out.persistence.ClaimJpaEntity   // 위반: domain → adapter
```

**주의**

- `layers`의 순서는 **언제나 안→밖**이다. `layered-simple`은 `레이어: presentation, application, data`(위→아래 호출 방향)로 선언하지만 파라미터는 `layers=data,application,presentation`이다. 두 순서가 반대일 수 있으므로, 파라미터 순서를 레이어 라벨에서 복사하지 말고 의존 방향으로 다시 판단한다.
- `layers`에 스타일의 모든 레이어가 들어갈 필요는 없다. 빠진 레이어는 이 규칙의 제약을 받지 않는다. 예: `layered-domain`은 레이어가 4개지만 `ld.layer-order`는 3개만 나열하고, `infrastructure`는 별도의 `ld.infra-isolated`가 다룬다(presentation → infrastructure는 조립 지점이라 허용해야 하므로).
- 레이어 이름은 스타일의 `레이어` 라벨에 선언된 이름과 정확히 일치해야 한다.

### 3.2 `forbid-import`

**강제 내용** — `from`에 해당하는 코드가 `to`에 해당하는 패키지·타입을 import(참조)하는 것을 금지한다.

| 키 | 필수 | 형식 | 기본값 | 설명 |
|---|---|---|---|---|
| `from` | 필수 | 레이어 이름 또는 패키지 패턴의 **목록** | — | 금지 대상이 되는 쪽 |
| `to` | 필수 | 레이어 이름 또는 패키지 패턴의 **목록** | — | 참조가 금지되는 쪽 |

`from`·`to`의 각 항목이 레이어인지 패키지 패턴인지는 **§2.1의 판별 규칙**을 따른다.

**선언 예**

```
| ld.domain-no-framework | forbid-import | from=domain; to=org.springframework..,jakarta.persistence.. |
| ld.infra-isolated      | forbid-import | from=domain,application; to=infrastructure |
```

첫 줄은 레이어 → 외부 패키지 패턴, 둘째 줄은 레이어 목록 → 레이어다. 두 형태 모두 같은 문법으로 표현된다.

**위반 예**

```kotlin
// com.acme.claim.domain.ClaimPolicy  (domain 레이어)
import org.springframework.stereotype.Component   // 위반: from=domain, to=org.springframework..

@Component
class ClaimPolicy
```

**주의**

- `to`가 레이어면 그 레이어의 **모든** 패키지가 금지된다. 일부만 열려면 `to`를 패키지 패턴으로 좁혀 쓴다.
- 스펙 §4.3 규칙 5의 파생 규칙(공용 모듈 의존 방향, 애플리케이션 봉쇄, 컨텍스트 간 직접 참조 금지)도 전부 `forbid-import` 인스턴스다. 다만 이들은 스타일 문서에 쓰지 않고 fitness가 선언에서 직접 생성한다 — 형식과 id 규약의 정본은 `architecture-template.md`다.

### 3.3 `confine-type`

**강제 내용** — 셀렉터로 지정한 타입 집합을 특정 레이어·패키지 안으로 격리한다. 격리는 두 방향 모두를 뜻한다: 해당 타입은 지정 범위 **안에서만 선언**될 수 있고, 지정 범위 **밖에서 참조**될 수 없다.

| 키 | 필수 | 형식 | 기본값 | 설명 |
|---|---|---|---|---|
| `type` | 필수 | 셀렉터 이름 | — | 등록된 셀렉터만 허용(아래 표) |
| `allowed_layer` | 택1 필수 | 레이어 이름 목록 | — | 격리 범위를 레이어로 지정 |
| `allowed_package` | 택1 필수 | 패키지 패턴 목록 | — | 격리 범위를 패키지 패턴으로 지정 |

`allowed_layer`와 `allowed_package`는 **정확히 하나만** 있어야 한다. 둘 다 있거나 둘 다 없으면 오류다.

**등록된 셀렉터** (v1)

| 셀렉터 | 선택하는 타입 |
|---|---|
| `jpa-entity` | `@Entity`가 붙은 타입 |

셀렉터 추가도 어휘 확장이다 — §7의 절차를 따른다.

**선언 예**

```
| hex.domain-pure | confine-type | type=jpa-entity; allowed_layer=adapter |
```

**위반 예**

```kotlin
// com.acme.claim.domain.Claim  (domain 레이어)
@Entity                       // 위반 A: jpa-entity가 adapter 밖에서 선언됨
class Claim(...)

// com.acme.claim.application.ClaimService  (application 레이어)
import com.acme.claim.adapter.out.persistence.ClaimJpaEntity   // 위반 B: 격리 범위 밖에서 참조
```

**주의**

- 위반 B가 이 primitive의 진짜 가치다. 선언 위치만 검사하면 "엔티티는 어댑터에 두고 서비스에서 그대로 꺼내 쓰는" 흔한 누수를 잡지 못한다.
- `*.domain-pure`는 이 primitive의 대표 인스턴스이며 `layered-domain`·`hexagonal`·`clean`의 정체성이다. `layered-simple`만 이 규칙이 없다 — JPA 엔티티 직접 사용 허용이 그 스타일의 정의적 특징이기 때문이다.

### 3.4 `naming-suffix`

**강제 내용** — 지정 스코프 안의 공개 타입 이름은 `suffixes` 중 하나로 끝나야 한다.

| 키 | 필수 | 형식 | 기본값 | 설명 |
|---|---|---|---|---|
| `scope` | 필수 | 레이어 이름 또는 패키지 패턴 | — | 검사 대상 범위 |
| `suffixes` | 필수 | 접미사 목록 | — | 하나라도 만족하면 통과 |

`scope`가 레이어인지 패키지 패턴인지는 **§2.1의 판별 규칙**을 따른다 — `forbid-import`의 `from`·`to`와 같은 규칙이다. 프리셋의 `scope=presentation`·`scope=application`은 모두 레이어 참조로 해석된다(해당 스타일이 그 이름의 레이어를 선언하고 있으므로).

**공개 타입**: 프로덕션 소스의 최상위(top-level) public 타입. 중첩 타입, private·internal 타입, 테스트 소스는 대상이 아니다.

**선언 예**

```
| ls.controller-naming   | naming-suffix | scope=presentation; suffixes=Controller |
| hex.ports-owned-inside | naming-suffix | scope=application; suffixes=Port,UseCase |
```

**위반 예**

```kotlin
// com.acme.claim.presentation.ClaimApi   (presentation 레이어)
class ClaimApi                            // 위반: 접미사가 Controller가 아님
```

**주의**

- 이 규칙은 스코프 안의 **모든** 공개 타입에 적용된다. `hex.ports-owned-inside`처럼 스코프가 레이어 전체면 강한 규칙이 된다 — 예외가 가장 자주 필요해지는 규칙이므로, 선언 전에 스코프를 패키지 패턴으로 좁히는 편이 나은지 검토한다.
- 접미사에는 언어 규약을 따르는 대문자 표기를 쓴다. 값은 대소문자를 구분한다.

### 3.5 `forbid-sibling-dependency`

**강제 내용** — 같은 레이어 안에서, 같은 접미사를 가진 타입끼리의 의존을 금지한다. "서비스가 다른 서비스를 부르지 않는다"를 표현하는 규칙이다.

| 키 | 필수 | 형식 | 기본값 | 설명 |
|---|---|---|---|---|
| `layer` | 필수 | 레이어 이름 | — | 검사 대상 레이어 |
| `suffix` | 필수 | 접미사 | — | 이 접미사로 끝나는 타입끼리의 의존을 금지 |

**선언 예**

```
| acme.no-service-chain | forbid-sibling-dependency | layer=application; suffix=Service |
```

**위반 예**

```kotlin
// com.acme.claim.application.ClaimService
class ClaimService(
    private val paymentService: PaymentService,   // 위반: Service → Service
)
```

**주의**

- 자기 자신에 대한 참조(재귀)는 두 타입 간 의존이 아니므로 위반이 아니다.
- 프리셋 4종은 이 규칙을 쓰지 않는다. 서비스 간 호출이 실제로 문제를 일으키는 프로젝트가 선택적으로 채택한다.

---

## 4. 규칙 id 규약

형식: `<스타일 접두사>.<하이픈-이름>` — 예: `hex.domain-pure`, `ld.layer-order`, `ls.controller-naming`.

- 접두사는 스타일마다 하나씩 정한다(프리셋: `ls`, `ld`, `hex`, `cl`). 커스텀 스타일은 짧고 겹치지 않는 접두사를 쓴다.
- **뒷이름은 스타일-로컬이며 각 스타일의 문헌 관용을 따른다.** 헥사고날·클린 아키텍처 문헌이 "의존은 안으로 향한다"고 말하므로 `hex.deps-inward`·`cl.deps-inward`가 맞고, 레이어드 문헌의 어휘를 쓰는 `ls.layer-order`·`ld.layer-order`도 맞다. 스타일 간 이름 통일은 **요구사항이 아니다** — 각 스타일을 쓰는 사람이 아는 말로 부르는 것이 우선이다.
- 여러 스타일이 같은 뒷이름을 공유하게 되면(`*.domain-pure`) 스타일을 가로질러 규칙을 지칭할 수 있어 편리하지만, 그건 결과이지 지켜야 할 규범이 아니다. 이미 쓰이는 id를 통일하겠다고 개명하는 것은 아래 안정성 계약 위반이다.
- id는 primitive 이름과 같을 필요가 없다. `hex.deps-inward`도 `ld.layer-order`도 primitive는 똑같이 `layer-order`다.

**id는 공개 표면이다.** 컨텍스트가 예외를 선언하는 유일한 수단이 id이기 때문이다:

```markdown
- 규칙 예외: -hex.ports-owned-inside (ADR-0002)
```

id를 바꾸면 이 선언이 조용히 아무것도 가리키지 않게 된다 — 예외가 사라지는 것이 아니라, **예외로 막고 있던 규칙이 갑자기 되살아난다**. 그래서:

- 한 번 배포된 id는 이름을 바꾸지 않는다. 의미가 달라졌으면 새 id를 만들고 옛 id를 폐기(제거)한다.
- id를 제거·변경할 때는 그 id를 예외로 참조하는 선언을 모두 찾아 함께 고친다.
- 예외에는 근거 ADR이 반드시 따른다. `*.domain-pure`처럼 스타일의 정체성에 해당하는 규칙을 예외로 빼려 한다면, 예외가 아니라 **스타일 선택 자체가 틀린 것은 아닌지** 먼저 검토한다(그 경우 답은 대개 `layered-simple`이다).

---

## 5. 워크드 예제 — hexagonal 전체 체인

스타일 선언에서 실제 강제까지의 사슬 전체를 한눈에 본다.

**① 스타일 선언** (`references/knowledge/styles/hexagonal.md`)

```markdown
## 선언
- 레이어: domain, application, adapter    (안 → 밖 순서)

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| hex.deps-inward | layer-order | layers=domain,application,adapter |
| hex.domain-pure | confine-type | type=jpa-entity; allowed_layer=adapter |
| hex.domain-no-framework | forbid-import | from=domain; to=org.springframework..,jakarta.persistence.. |
| hex.ports-owned-inside | naming-suffix | scope=application; suffixes=Port,UseCase |
```

**② 컨텍스트가 스타일을 채택** (`ARCHITECTURE.md`)

```markdown
## 컨텍스트: claim
- 분류: core
- 스타일: hexagonal
- 규칙 예외: -hex.ports-owned-inside (ADR-0002)
```

**③ 정규화** — 파서가 컨텍스트 × 레이어 → 패키지 패턴으로 바꾼다(기본 패키지 `com.acme`).

| 레이어 | 패키지 패턴 |
|---|---|
| domain | `com.acme.claim.domain..` |
| application | `com.acme.claim.application..` |
| adapter | `com.acme.claim.adapter..` |

**④ 유효 규칙 집합** — 선언된 4개에서 예외 1개를 뺀 3개 + 파생 규칙(§3.2 주의).

| 규칙 id | 이 컨텍스트에서 강제되는 내용 |
|---|---|
| hex.deps-inward | `com.acme.claim.domain..`은 application·adapter를 참조 못 함, `...application..`은 adapter를 참조 못 함 |
| hex.domain-pure | `@Entity` 타입은 `com.acme.claim.adapter..` 안에서만 선언·참조 |
| hex.domain-no-framework | `com.acme.claim.domain..`은 `org.springframework..`·`jakarta.persistence..` 참조 금지 |
| ~~hex.ports-owned-inside~~ | ADR-0002로 예외 — 강제하지 않음 |

**⑤ 생성** — fitness가 프로파일의 `rule-mappings.md`로 primitive를 번역해 Konsist/ArchUnit 테스트를 만든다. 프로파일은 `hexagonal`이라는 스타일을 모른다 — `layer-order`·`confine-type`·`forbid-import`만 안다. **이것이 폐쇄 어휘가 사는 이유다.**

### 새 커스텀 스타일을 선언할 때

위 ①의 형식을 그대로 쓴다. 파일 위치는 `docs/architecture/styles/<name>.md`이고, 컨텍스트는 `- 스타일: custom/<name>`으로 채택한다.

- [ ] `- 레이어:` 라벨에 레이어 이름을 나열한다. 개수는 자유이고 이름도 자유롭게 지을 수 있지만, **기본 관례를 쓰면 레이어 이름이 그대로 패키지 세그먼트가 된다**(`domain` → `{기본 패키지}.{컨텍스트}.domain..`). 따라서 실제 소스의 패키지 이름과 일치시키거나, 일치시킬 수 없으면 패키지 규약 표로 명시적 매핑을 선언한다. 소스가 `...web...`인데 레이어를 `presentation`으로 지으면 그 레이어를 참조하는 규칙은 매칭 0건이 되어 조용히 통과한다(§2.1의 실패 모드와 같다). 정규화 메커니즘의 정본은 `architecture-template.md`다.
- [ ] 짧고 겹치지 않는 id 접두사를 정한다(§4).
- [ ] 의존 방향을 `layer-order`로 쓴다 — **`layers`는 안→밖 순서**이며 레이어 라벨의 순서와 다를 수 있다.
- [ ] 도메인을 순수하게 유지할 것인지 정한다. 유지한다면 `confine-type`(`<접두사>.domain-pure`)과 프레임워크 차단 `forbid-import`를 넣는다. 넣지 않는다면 그 스타일은 JPA 엔티티 직접 사용을 허용한다는 뜻이며, `layered-simple`로 충분하지 않은지 먼저 검토한다.
- [ ] `layer-order`로 표현되지 않는 예외적 금지를 `forbid-import`로 보완한다(예: 조립 지점만 열어두는 경우).
- [ ] 명명 규칙이 구조적 의미를 가질 때만 `naming-suffix`를 넣는다. 스코프가 레이어 전체면 강한 규칙이 된다(§3.4).
- [ ] 모든 규칙이 §3의 primitive 중 하나인지 확인한다. 아니면 §6 → §7.

---

## 6. 새 규칙이 필요할 때 — 먼저 이것부터

새 primitive를 만들려는 시도의 대부분은 **기존 primitive의 다른 파라미터**다. 순서대로 확인한다.

- [ ] **"A는 B를 쓰면 안 된다"** → `forbid-import`. from/to는 레이어도 패키지 패턴도 목록도 된다. 별도 규칙이 아니다.
- [ ] **"이 애노테이션이 붙은 타입은 여기에만"** → `confine-type`. 셀렉터만 추가하면 되는지 확인한다(primitive 추가보다 훨씬 작은 변경이다).
- [ ] **"이 계층은 저 계층 위에 있다"** → `layer-order`. 레이어 이름과 개수는 완전히 자유다 — 4계층도 6계층도 같은 primitive다.
- [ ] **"이런 타입은 이런 이름이어야 한다"** → `naming-suffix`. 스코프를 패키지 패턴으로 좁혀 쓸 수 있다.
- [ ] **"같은 종류끼리 부르면 안 된다"** → `forbid-sibling-dependency`.
- [ ] **기계로 판정할 수 있는가?** — "적절한 크기", "응집도가 높을 것"처럼 판정 기준이 사람의 해석에 달려 있으면 규칙이 아니다. `knowledge/`나 프로젝트의 `conventions/` 문서에 리뷰 체크리스트로 쓴다.

여기까지에서 답이 나오지 않았을 때만 §7로 간다.

---

## 7. 어휘 확장 절차

새 primitive(또는 새 셀렉터)를 추가하는 유일한 합법 경로. **세 가지는 한 변경에 함께 들어간다.**

1. **이 문서에 정의를 추가한다** — 이름, 강제 내용, 파라미터 표, 선언 예, 위반 예, 주의.
2. **`profiles/kotlin-spring/rule-mappings.md`에 Konsist 매핑을 추가한다.**
3. **`profiles/java-spring/rule-mappings.md`에 ArchUnit 매핑을 추가한다.**

**한 프로파일이 표현하지 못하는 primitive는 어휘에 넣지 않는다.** 반쪽 어휘는 그 언어를 쓰는 프로젝트에서 "선언은 되는데 강제되지 않는 규칙"이 되고, 그것이 폐쇄 원칙이 막으려던 바로 그 상태다. 두 도구 중 하나로 표현이 어렵다면 primitive의 정의를 두 도구 모두 표현 가능한 형태로 다시 설계한다.

부가 조건:

- 확장은 ADR로 남긴다 — 어휘는 플러그인의 공개 인터페이스이므로 변경 이유가 기록되어야 한다.
- 기존 primitive의 파라미터를 추가할 때도 같은 3종 세트를 지킨다. 새 파라미터에는 기존 선언을 깨지 않는 기본값을 준다.
- primitive 이름은 kebab-case, 파라미터 키는 snake_case로 통일한다.

---

## 8. 관련 문서

- `references/governance/architecture-template.md` — 스타일 선언 표의 섹션 구조, 정규화 규칙, 파생 규칙의 정본. **단, 표의 `파라미터` 셀 문법은 이 문서 §2가 정본이다** — 두 문서가 각자 정의하면 파서와 프로파일이 갈라진다.
- `profiles/<profile>/rule-mappings.md` — primitive → Konsist/ArchUnit 번역
- `references/knowledge/styles/` — 프리셋 4종의 선언(이 어휘의 인스턴스)
- `references/governance/adr-template.md` — 규칙 예외·어휘 확장의 근거를 남기는 형식
