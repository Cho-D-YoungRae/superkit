# hexagonal — java-spring 골격 매니페스트

스타일 선언의 정본은 `references/knowledge/styles/hexagonal.md`의 `## 선언`이고, 치환 변수의
정본은 `profiles/README.md`의 「플레이스홀더 규약」이다. 이 파일은 **그 스타일의 골격이 어떤
파일로 이루어지고 어디에 놓이는가**만 정한다.

레이어는 셋이다 — `domain`, `application`, `adapter`(안 → 밖).

## 이 골격이 통과해야 하는 규칙

수용 기준은 하나다: **그대로 전개된 골격은 이 스타일의 유효 규칙에 대해 `check_imports` 클린이고
fitness가 생성한 ArchUnit 테스트를 통과한다.** 골격의 모양은 대부분 그 기준에서 나온 것이다.

| 규칙 id | 골격이 만족시키는 방식 |
|---|---|
| `hex.deps-inward` | 모듈 의존이 `adapter → application → domain` 한 방향뿐이다. 세 레이어 모두 파일이 1개 이상이다 — **빈 레이어는 위반이 아니라 실패**다(`layeredArchitecture`의 기본값 `withOptionalLayers(false)` — 매핑 §0.3-2) |
| `hex.domain-pure` | `@Entity`는 `adapter`의 `{{Context}}JpaEntity` 하나뿐이고, 그 타입을 참조하는 코드가 adapter 밖에 없다(격리는 양방향) |
| `hex.domain-no-framework` | `domain`의 두 파일에 `org.springframework..`·`jakarta.persistence..` 참조가 없다. `build.gradle.kts.domain`도 그 의존을 갖지 않아 컴파일이 먼저 막는다 |
| `hex.ports-owned-inside` | `application`의 최상위 public 타입이 `{{Context}}Port`·`Activate{{Context}}UseCase`·`DefaultActivate{{Context}}UseCase` 셋뿐 — 전부 `Port`·`UseCase`로 끝난다. 커맨드는 중첩 record, 예외는 `domain`에 있다 |

**0건은 통과가 아니라 실패다.** ArchUnit은 `that()` 매칭이 0건인 규칙을 실패시키고
(`Rule '…' failed to check any classes.` — 매핑 §0.3-1), `layeredArchitecture`는 레이어 하나만
비어도 실패한다. 레이어마다 파일을 최소 하나씩 두는 것이 골격의 요구 사항인 이유다.
Konsist의 `strict` 파라미터에 해당하는 것은 java-spring에 없다 — 기본값이 이미 그 편이다.

**강제되는 파일과 교육 목적의 파일.** 아래 셋은 지워도 `check_imports`가 exit 0이다(실측).

| 파일 | 지우면 |
|---|---|
| `domain/{{Context}}NotFound.java` | 규칙은 통과한다. 다만 `DefaultActivate{{Context}}UseCase`가 이 타입을 쓰므로 **컴파일이 깨진다** — 지우려면 유스케이스도 함께 고친다 |
| `application/{{Context}}Port.java` 또는 두 UseCase 파일 중 하나 | `application` 링은 나머지로 채워져 규칙은 통과한다. 셋이 함께 있는 이유는 "포트 1 + 유스케이스 1"이라는 최소 구성(`profiles/README.md` ②)이 Java에서 파일 셋으로 나뉘기 때문이다 |
| `adapter/{{Context}}JpaEntity.java` | 규칙은 통과하지만 **`hex.domain-pure`가 진공 통과로 바뀐다** — 격리 대상이 0건이면 두 어서션 모두 아무것도 검사하지 않고, 그 상태는 "JPA를 쓰지 않는 프로젝트"와 구분되지 않는다(매핑 §3 커버리지 한계 ③) |

**규칙이 보지 못하는 것 — Java·Spring 쪽 두 자리.** `check_imports`도 ArchUnit도 **구조**만 본다.
Kotlin 프로파일이 컴파일러 플러그인(`plugin.jpa`·`plugin.spring`)으로 막던 자리가 Java에서는
사라지지 않고 **모양만 바뀐다.**

| 항목 | 어디에 있나 | 빠지면 |
|---|---|---|
| `@Entity`의 no-arg 생성자 | `adapter/{{Context}}JpaEntity.java`의 `protected` 기본 생성자 — Java에는 `plugin.jpa`에 해당하는 것이 없어 **소스가 직접 갖는다** | 두 검사를 다 통과하고 부팅에서 깨진다 |
| `-parameters` 컴파일 옵션 | `build.gradle.kts.adapter`의 `tasks.withType<JavaCompile>` | `@PathVariable`·`@RequestParam`의 이름을 못 읽어 **첫 요청에서** 깨진다. 부트 플러그인이 이 옵션을 넣어 주는 것은 앱 모듈뿐이다 |

Kotlin의 `plugin.spring`(클래스 final 해제)에 해당하는 것은 필요 없다 — Java 클래스는 기본이
final이 아니라 CGLIB이 그대로 상속한다. 다만 프록시 대상에 **final 메서드**를 두면 그 메서드만
조용히 프록시되지 않는데, 그것도 구조 검사가 보지 못한다.

## 파일 목록

| 템플릿 파일 | 레이어 | 전개 뒤 |
|---|---|---|
| `settings.gradle.kts.fragment` | — | 루트 `settings.gradle.kts`에 **추가**(덮어쓰기 아님) |
| `build.gradle.kts.domain` | domain | 그 레이어 모듈의 `build.gradle.kts` |
| `build.gradle.kts.application` | application | 〃 |
| `build.gradle.kts.adapter` | adapter | 〃 (`-parameters` 설정 포함) |
| `domain/{{Context}}.java` | domain | 애그리거트 루트 + 식별자 VO(중첩 record) + 상태 enum(중첩) |
| `domain/{{Context}}NotFound.java` | domain | 도메인 예외 |
| `application/{{Context}}Port.java` | application | out 포트 1 |
| `application/Activate{{Context}}UseCase.java` | application | in 포트 + 커맨드(중첩 record) |
| `application/DefaultActivate{{Context}}UseCase.java` | application | in 포트 구현 = 유스케이스 1 |
| `adapter/{{Context}}PersistenceAdapter.java` | adapter | out 어댑터 1 |
| `adapter/{{Context}}JpaEntity.java` | adapter | JPA 엔티티(격리 대상) |
| `test/{{Context}}Test.java` | domain(테스트) | 도메인 단위 테스트 골격(`@Tag` 예시 주석 포함) |

**Kotlin 골격보다 파일이 넷 많은 이유는 규칙이 아니라 언어다.** Java는 파일 하나에 public 최상위
타입을 하나만 허용하므로, Kotlin이 한 파일에 담던 묶음이 갈린다 — 애그리거트 파일에서 예외가,
유스케이스 파일에서 구현이, 어댑터 파일에서 엔티티가 떨어져 나왔다. 애그리거트에 종속된 식별자
VO와 상태 enum은 **중첩 타입**으로 남겨 갈라짐을 넷에서 멈췄다(`{{Context}}.Id`·
`{{Context}}.Status`). 중첩이라 `hex.ports-owned-inside` 같은 최상위 타입 규칙의 대상도 아니다.

`test/`는 레이어가 아니라 **소스셋**을 뜻한다 — domain 레이어를 소유한 모듈의 `src/test/java`에
놓인다. 아키텍처 테스트(`{{Context}}ArchitectureTest.java`)는 이 골격이 만들지 않는다. 그것은
fitness의 생성물이고 배치 규약은 `rule-mappings.md` §0.1이 갖는다.

## 레이아웃 3형 배치

소스 파일의 `package` 줄은 세 형태 모두 `{{pkg:<레이어>}}`가 정하므로 **파일 내용은 바뀌지
않는다.** 바뀌는 것은 파일이 놓이는 경로와 빌드 조각의 개수뿐이다.

### multi-module — 레이어별 모듈

```
{{context}}/domain/src/main/java/<{{pkg:domain}}의 . → />/{{Context}}.java
{{context}}/domain/src/main/java/<{{pkg:domain}}의 . → />/{{Context}}NotFound.java
{{context}}/domain/src/test/java/<{{pkg:domain}}의 . → />/{{Context}}Test.java
{{context}}/application/src/main/java/<{{pkg:application}}의 . → />/{{Context}}Port.java
{{context}}/application/src/main/java/<{{pkg:application}}의 . → />/Activate{{Context}}UseCase.java
{{context}}/application/src/main/java/<{{pkg:application}}의 . → />/DefaultActivate{{Context}}UseCase.java
{{context}}/adapter/src/main/java/<{{pkg:adapter}}의 . → />/{{Context}}PersistenceAdapter.java
{{context}}/adapter/src/main/java/<{{pkg:adapter}}의 . → />/{{Context}}JpaEntity.java
```

`build.gradle.kts.<레이어>` 셋을 각 모듈에 두고 settings 조각을 그대로 쓴다.

### single-module — 단일 모듈 + 레이어 패키지

모듈은 `{{context}}` 하나이고 세 레이어는 그 안의 패키지다. 경로에서 `{{context}}/<레이어>/`가
`{{context}}/`로 줄어드는 것 말고는 같다.

- settings 조각은 `include(":{{context}}")` **한 줄**로 줄인다 — 모듈 이름이 곧 디렉터리라
  `projectDir` 재지정 줄은 함께 사라진다.
- `build.gradle.kts.<레이어>` 셋을 **하나로 합친다.** 단순히 이어 붙이면 `plugins` 블록이
  여럿이 되어 Gradle이 구성 단계에서 거부한다. 병합은 결정적으로 한다.

| 조각의 요소 | 병합 규칙 |
|---|---|
| 주석 | **버리지 않는다 — 위치와 무관하게 전부 보존한다.** 조각 머리의 주석은 레이어 순서대로 파일 맨 위에 모으고, 블록 안(`plugins`·`dependencies`)과 블록 뒤의 근거 주석은 그 항목을 따라 옮긴다. "이 의존을 여기 더하면 어느 규칙이 잡는다"·"이 옵션이 빠지면 첫 요청에서 깨진다"는 근거가 사라지면 나중에 아무나 더하고 아무나 지운다 |
| `plugins { … }` | 블록은 **하나만.** 안의 항목은 합집합이고 같은 플러그인은 한 번만 적는다 |
| `dependencies { … }` | 블록 **하나로** 합친다. 같은 좌표가 둘 이상이면 **넓은 configuration 하나만** 남긴다(`implementation` > `runtimeOnly`, `testImplementation` > `testRuntimeOnly`) |
| `project(":{{context}}-…")` | **지운다** — 모듈이 하나뿐이라 자기 자신을 가리키게 된다 |
| `tasks.test { useJUnitPlatform() }` | 파일 전체에 **한 번**만 |
| `tasks.withType<JavaCompile> { … "-parameters" }` | 파일 전체에 **한 번**만. 합친 모듈에는 컨트롤러가 함께 들어오므로 이 블록은 **반드시 남는다** |

합치면 `domain`에 스프링·JPA가 클래스패스로 들어온다. `hex.domain-no-framework`는 참조를 보므로
규칙은 그대로 살아 있지만, 컴파일러가 막아 주던 몫은 사라진다.

### app-embedded — 규약 패턴 위치에 레이어 패키지만

모듈을 만들지 않는다. settings 조각과 빌드 조각을 **쓰지 않고**, 소스 파일만 각 레이어의 패키지
위치에 놓는다.

- 위치는 `### 패키지 규약` 표가 정한다. `{{pkg:<레이어>}}`가 그 표의 전개 결과이므로 템플릿을
  고칠 일은 없다.
- 어떤 모듈에 두는가: 패턴에 `{앱}`이 있으면 **앱마다 사본이 있는 레이어**라 각 앱 모듈에 하나씩
  두고(`{{pkg:<레이어>}}`가 앱 수만큼 전개된다), 없으면 앱들이 함께 의존하는 **비실행 모듈**에
  하나만 둔다(`module-composition.md`). hexagonal에서 `{앱}`이 붙는 레이어는 보통 `adapter`다.
- 그 비실행 모듈의 경로는 선언 어디에도 없다 — 관측으로 찾고, 찾지 못하면 사용자에게 묻는다.
- 빌드 조각을 쓰지 않으므로 **`-parameters`가 어디에도 없다.** 컨트롤러가 들어가는 모듈의 기존
  빌드 스크립트에 그 설정이 있는지 확인하고, 없으면 그 한 블록만 옮긴다(부트 플러그인이 적용된
  모듈이면 이미 들어 있다).
- `test/`는 domain 패턴을 소유한 모듈의 `src/test/java`에 둔다.

## ARCHITECTURE.md 등록

골격을 만든 뒤 컨텍스트 섹션의 모듈 표가 이 모양이 되어야 한다(app-embedded는 모듈 표 금지).

```markdown
| 모듈 | 경로 | 레이어 |
|---|---|---|
| {{context}}-domain | {{context}}/domain | domain |
| {{context}}-application | {{context}}/application | application |
| {{context}}-adapter | {{context}}/adapter | adapter |
```

single-module이어도 **행은 레이어마다 하나씩**이고 `모듈`·`경로`만 같은 값이 반복된다.
행 하나로 줄이면서 레이어를 `all`로 적으면 세 레이어의 패턴이 모두 사라져
`hex.*` 네 규칙이 전부 아무것도 검사하지 않는다(`resolve_rules`가 공허 레이어로 경고한다).

**앱 실행 모듈.** 이 컨텍스트를 `포함 컨텍스트`로 선언한 앱의 모듈은 이 골격이 만들지 않는다 —
`templates/_shared/`의 `build.gradle.kts.app`과 `{{App}}Application.java`가 만들고, 배치는
`### 애플리케이션` 표의 `모듈 경로`다(`profiles/README.md` ②「앱 실행 모듈」). 그 앱이 이
컨텍스트에서 의존하는 모듈은 **가장 바깥 레이어인 `:{{context}}-adapter` 하나**이며(안쪽은 전이
의존으로 따라온다), 그 값이 `{{#app.contextModules}}`에 들어가는 항목이다.

**아키텍처 테스트 모듈.** `_shared/build.gradle.kts.archtest`가 만드는 그 모듈은
**검사 대상 모듈을 의존해야 한다** — ArchUnit이 클래스패스를 읽기 때문이며, 의존이 없으면 스코프가
비어 전 규칙이 0건으로 실패한다(매핑 §0.1). kotlin-spring의 같은 조각이 "의존 0"을 규율로 삼는
것과 정반대이므로, 그쪽을 복사해 오지 않는다.

## 치환

변수의 뜻과 목록은 `profiles/README.md`의 「플레이스홀더 규약」이 정본이다. 이 골격이 쓰는 것은
넷이다 — `{{context}}`, `{{Context}}`, `{{pkg:<레이어>}}`, 그리고 조각 파일 이름의 `<레이어>`.
파일 이름과 디렉터리 이름에도 같은 치환을 적용한다(`{{Context}}Port.java` → `ClaimPort.java`).
`_shared/`의 두 파일은 `{{basePackage}}`·`{{app}}`·`{{App}}`·`{{#app.contextModules}}`를 더 쓴다.

`{{basePackage}}`는 이 골격의 소스 템플릿에 직접 나타나지 않는다 — `{{pkg:<레이어>}}`가 이미
정규화를 거친 값이기 때문이다. 패키지를 손으로 조립하지 않는다.

## 수용 기준 확인

전개한 프로젝트 루트에서 두 가지를 돌린다. 둘 다 통과해야 골격이 완성이다.

```
python3 <플러그인>/scripts/check_imports.py ARCHITECTURE.md      # exit 0, [0건 경고] 없음
/superarchitect:fitness                                          # 생성 → 대상 프로젝트 빌드로 실행
```

**확인한 레이아웃 — multi-module**(Phase 6 T2: `check_imports` exit 0 · ArchUnit 통과 ·
`:app:api:bootJar` 성공). 어느 레이아웃으로 밟았는지를 남기는 이유는, 모듈 경계를 넘는 컴파일
가시성처럼 **multi-module에서만 드러나는 실패**가 있어 single-module 확인만으로는 수용 기준이
충족돼 보일 수 있기 때문이다.
