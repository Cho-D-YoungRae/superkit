# layered-domain — java-spring 골격 매니페스트

스타일 선언의 정본은 `references/knowledge/styles/layered-domain.md`의 `## 선언`이고, 치환 변수의
정본은 `profiles/README.md`의 「플레이스홀더 규약」이다. 이 파일은 **그 스타일의 골격이 어떤
파일로 이루어지고 어디에 놓이는가**만 정한다.

레이어는 넷이다 — `domain`, `application`, `presentation`, `infrastructure`(domain이 가장 안쪽).
`ld.layer-order`에는 앞의 셋만 들어간다. **빠진 `infrastructure`가 규칙 밖이라는 뜻은 아니다** —
`ld.infra-isolated`와 `ld.domain-pure`가 그 레이어를 따로 다룬다. ArchUnit 쪽에서 그 빠짐이
성립하는 이유는 `consideringOnlyDependenciesInLayers()`다(매핑 §1) — 등록되지 않은 레이어와의
의존은 `ld.layer-order`의 판정에서 아예 빠진다.

## 이 골격이 통과해야 하는 규칙

수용 기준은 하나다: **그대로 전개된 골격은 이 스타일의 유효 규칙에 대해 `check_imports` 클린이고
fitness가 생성한 ArchUnit 테스트를 통과한다.**

| 규칙 id | 골격이 만족시키는 방식 |
|---|---|
| `ld.layer-order` | `presentation → application → domain` 한 방향뿐이다. 세 레이어 모두 파일이 1개 이상이다 — **빈 레이어는 위반이 아니라 실패**다(매핑 §0.3-2) |
| `ld.domain-pure` | `@Entity`는 `infrastructure`의 `{{Context}}JpaEntity` 하나뿐이고, 그 타입을 참조하는 코드가 infrastructure 밖에 없다. 컨트롤러가 응답으로 도메인 타입만 다루는 것도 이 규칙 때문이다 |
| `ld.domain-no-framework` | `domain`의 세 파일에 `org.springframework..`·`jakarta.persistence..` 참조가 없다. 리포지터리 **인터페이스**가 domain에 있어도 스프링 데이터를 상속하지 않는 이유다 |
| `ld.infra-isolated` | `domain`·`application` 어느 파일도 infrastructure를 참조하지 않는다. `build.gradle.kts.application`에 infrastructure 의존이 없는 것이 그 강제를 컴파일까지 끌어온다 |

`infrastructure`에 파일이 하나도 없으면 그 레이어의 패턴이 비고, `ld.domain-pure`와
`ld.infra-isolated`가 조용히 사라진다(`resolve_rules`의 공허 레이어 경고). 그래서 골격은 네
레이어를 모두 채운다.

**강제되는 파일과 교육 목적의 파일.**

| 파일 | 지우면 |
|---|---|
| `domain/{{Context}}Repository.java` | 규칙은 통과한다. 다만 이 인터페이스가 **이 스타일의 정체성**이다 — 나가는 쪽만 뒤집는 배치를 `ld.infra-isolated`가 강제하는데, 인터페이스가 없으면 강제할 대상이 없어진다. `{{Context}}Service`·`{{Context}}RepositoryAdapter`가 함께 깨진다 |
| `infrastructure/{{Context}}JpaEntity.java` | `infrastructure` 레이어는 어댑터 하나로 채워져 `ld.infra-isolated`는 살아 있지만, **`ld.domain-pure`가 진공 통과로 바뀐다** — 격리 대상 0건은 "JPA를 쓰지 않는 프로젝트"와 구분되지 않는다(매핑 §3 커버리지 한계 ③) |
| `domain/{{Context}}NotFound.java` | 규칙은 통과하고 컴파일은 `{{Context}}Service`를 함께 고쳐야 산다 |

**규칙이 보지 못하는 것 — Java·Spring 쪽 두 자리.** Kotlin 프로파일이 컴파일러
플러그인(`plugin.jpa`·`plugin.spring`)으로 막던 자리가 Java에서는 사라지지 않고 **모양만 바뀐다.**

| 항목 | 어디에 있나 | 빠지면 |
|---|---|---|
| `@Entity`의 no-arg 생성자 | `infrastructure/{{Context}}JpaEntity.java`의 `protected` 기본 생성자 — Java에는 `plugin.jpa`에 해당하는 것이 없어 **소스가 직접 갖는다** | 두 검사를 다 통과하고 부팅에서 깨진다 |
| `-parameters` 컴파일 옵션 | `build.gradle.kts.presentation`의 `tasks.withType<JavaCompile>` | `@PathVariable`의 이름을 못 읽어 **첫 요청에서** 깨진다. 부트 플러그인이 이 옵션을 넣어 주는 것은 앱 모듈뿐이다 |

Kotlin의 `plugin.spring`에 해당하는 것은 필요 없다 — Java 클래스는 기본이 final이 아니라 CGLIB이
`{{Context}}Service`를 그대로 감싼다. 다만 `@Transactional` 메서드를 `final`로 잠그면 그 메서드만
조용히 프록시되지 않는데, 그것도 구조 검사가 보지 못한다.

## 파일 목록

| 템플릿 파일 | 레이어 | 전개 뒤 |
|---|---|---|
| `settings.gradle.kts.fragment` | — | 루트 `settings.gradle.kts`에 **추가**(덮어쓰기 아님) |
| `build.gradle.kts.domain` | domain | 그 레이어 모듈의 `build.gradle.kts` |
| `build.gradle.kts.application` | application | 〃 |
| `build.gradle.kts.presentation` | presentation | 〃 (`-parameters` 설정 포함) |
| `build.gradle.kts.infrastructure` | infrastructure | 〃 |
| `domain/{{Context}}.java` | domain | 애그리거트 루트 + 식별자 VO(중첩 record) + 상태 enum(중첩) |
| `domain/{{Context}}NotFound.java` | domain | 도메인 예외 |
| `domain/{{Context}}Repository.java` | domain | 리포지터리 인터페이스 = 이 스타일의 포트 1 |
| `application/{{Context}}Service.java` | application | 애플리케이션 서비스 = 유스케이스 1 |
| `presentation/{{Context}}Controller.java` | presentation | 컨트롤러 = 들어오는 쪽 어댑터 1 |
| `infrastructure/{{Context}}RepositoryAdapter.java` | infrastructure | 리포지터리 구현 1 |
| `infrastructure/{{Context}}JpaEntity.java` | infrastructure | JPA 엔티티(격리 대상) |
| `test/{{Context}}Test.java` | domain(테스트) | 도메인 단위 테스트 골격(`@Tag` 예시 주석 포함) |

**Kotlin 골격보다 파일이 둘 많은 이유는 규칙이 아니라 언어다.** Java는 파일 하나에 public 최상위
타입을 하나만 허용하므로, 애그리거트 파일에서 예외가, 리포지터리 구현 파일에서 엔티티가 떨어져
나왔다. 애그리거트에 종속된 식별자 VO와 상태 enum은 **중첩 타입**으로 남겨 갈라짐을 둘에서 멈췄다.

`test/`는 레이어가 아니라 **소스셋**을 뜻한다 — domain 레이어를 소유한 모듈의 `src/test/java`에
놓인다. 아키텍처 테스트는 이 골격이 만들지 않는다(fitness의 생성물이고 배치 규약은
`rule-mappings.md` §0.1).

## 레이아웃 3형 배치

소스 파일의 `package` 줄은 세 형태 모두 `{{pkg:<레이어>}}`가 정하므로 **파일 내용은 바뀌지
않는다.** 바뀌는 것은 경로와 빌드 조각의 개수뿐이다.

### multi-module — 레이어별 모듈

```
{{context}}/<레이어>/src/main/java/<{{pkg:<레이어>}}의 . → />/<파일>
{{context}}/domain/src/test/java/<{{pkg:domain}}의 . → />/{{Context}}Test.java
```

`build.gradle.kts.<레이어>` 넷을 각 모듈에 두고 settings 조각을 그대로 쓴다.

### single-module — 단일 모듈 + 레이어 패키지

모듈은 `{{context}}` 하나이고 네 레이어는 그 안의 패키지다.

- settings 조각은 `include(":{{context}}")` **한 줄**로 줄인다.
- `build.gradle.kts.<레이어>` 넷을 **하나로 합친다.** 단순히 이어 붙이면 `plugins` 블록이
  여럿이 되어 Gradle이 구성 단계에서 거부한다. 병합은 결정적으로 한다.

| 조각의 요소 | 병합 규칙 |
|---|---|
| 주석 | **버리지 않는다 — 위치와 무관하게 전부 보존한다.** 조각 머리의 주석은 레이어 순서대로 파일 맨 위에 모으고, 블록 안(`plugins`·`dependencies`)과 블록 뒤의 근거 주석은 그 항목을 따라 옮긴다 |
| `plugins { … }` | 블록은 **하나만.** 안의 항목은 합집합이고 같은 플러그인은 한 번만 적는다 |
| `dependencies { … }` | 블록 **하나로** 합친다. 같은 좌표가 둘 이상이면 **넓은 configuration 하나만** 남긴다(`api` > `implementation` > `runtimeOnly`, `testImplementation` > `testRuntimeOnly`) |
| `project(":{{context}}:…")` | **지운다** — 모듈이 하나뿐이라 자기 자신을 가리키게 된다 |
| `tasks.test { useJUnitPlatform() }` | 파일 전체에 **한 번**만 |
| `tasks.withType<JavaCompile> { … "-parameters" }` | 파일 전체에 **한 번**만. 합친 모듈에는 컨트롤러가 함께 들어오므로 이 블록은 **반드시 남는다** |

합치면 `ld.infra-isolated`를 컴파일이 대신 막아 주던 몫이 사라진다. 규칙은 참조를 보므로
그대로 살아 있지만, 위반이 빌드 실패가 아니라 fitness 실패로 늦게 온다.

### app-embedded — 규약 패턴 위치에 레이어 패키지만

모듈을 만들지 않는다. settings 조각과 빌드 조각을 **쓰지 않고**, 소스 파일만 각 레이어의 패키지
위치에 놓는다.

- 위치는 `### 패키지 규약` 표가 정한다. `{{pkg:<레이어>}}`가 그 표의 전개 결과다.
- 패턴에 `{앱}`이 있으면 **앱마다 사본이 있는 레이어**라 각 앱 모듈에 하나씩 두고
  (`{{pkg:<레이어>}}`가 앱 수만큼 전개된다), 없으면 앱들이 함께 의존하는 **비실행 모듈**에 하나만
  둔다(`module-composition.md`). 이 스타일에서 `{앱}`이 붙는 레이어는 보통 `presentation`이다.
- 그 비실행 모듈의 경로는 선언 어디에도 없다 — 관측으로 찾고, 찾지 못하면 사용자에게 묻는다.
- 빌드 조각을 쓰지 않으므로 **`-parameters`가 어디에도 없다.** 컨트롤러가 들어가는 모듈의 기존
  빌드 스크립트에 그 설정이 있는지 확인하고, 없으면 그 한 블록만 옮긴다.
- `test/`는 domain 패턴을 소유한 모듈의 `src/test/java`에 둔다.

## ARCHITECTURE.md 등록

```markdown
| 모듈 | 경로 | 레이어 |
|---|---|---|
| {{context}}-domain | {{context}}/domain | domain |
| {{context}}-application | {{context}}/application | application |
| {{context}}-presentation | {{context}}/presentation | presentation |
| {{context}}-infrastructure | {{context}}/infrastructure | infrastructure |
```

single-module이어도 **행은 레이어마다 하나씩**이고 `모듈`·`경로`만 같은 값이 반복된다.
행 하나로 줄이면서 레이어를 `all`로 적으면 네 레이어의 패턴이 모두 사라져 `ld.*` 네 규칙이 전부
아무것도 검사하지 않는다(`resolve_rules`가 공허 레이어로 경고한다).

**앱 실행 모듈.** 이 컨텍스트를 `포함 컨텍스트`로 선언한 앱의 모듈은 이 골격이 만들지 않는다 —
`templates/_shared/`의 `build.gradle.kts.app`과 `{{App}}Application.java`가 만들고, 배치는
`### 애플리케이션` 표의 `모듈 경로`다(`profiles/README.md` ②「앱 실행 모듈」). 그 앱이 이
컨텍스트에서 의존하는 모듈은 **가장 바깥 레이어인 `:{{context}}:presentation` 하나**이며(안쪽은
전이 의존으로 따라온다), 그 값이 `{{#app.contextModules}}`에 들어가는 항목이다. infrastructure는
presentation의 `runtimeOnly`로 함께 실린다.

**아키텍처 테스트 모듈.** `_shared/build.gradle.kts.archtest`가 만드는 그 모듈은
**검사 대상 모듈을 의존해야 한다** — ArchUnit이 클래스패스를 읽기 때문이며, 의존이 없으면 스코프가
비어 전 규칙이 0건으로 실패한다(매핑 §0.1). kotlin-spring의 같은 조각이 "의존 0"을 규율로 삼는
것과 정반대이므로, 그쪽을 복사해 오지 않는다.

## 치환

변수의 뜻과 목록은 `profiles/README.md`의 「플레이스홀더 규약」이 정본이다. 이 골격이 쓰는 것은
`{{context}}`, `{{Context}}`, `{{pkg:<레이어>}}`, 그리고 조각 파일 이름의 `<레이어>`다. 파일
이름과 디렉터리 이름에도 같은 치환을 적용한다. `_shared/`의 두 파일은 `{{basePackage}}`·`{{app}}`·
`{{App}}`·`{{#app.contextModules}}`를 더 쓴다.

## 수용 기준 확인

```
python3 <플러그인>/scripts/check_imports.py ARCHITECTURE.md      # exit 0, [0건 경고] 없음
/superarchitect:fitness                                          # 생성 → 대상 프로젝트 빌드로 실행
```

**확인한 레이아웃 — multi-module**(Phase 6 T2: `check_imports` exit 0 · ArchUnit 통과). 모듈
경계를 넘는 컴파일 가시성처럼 **multi-module에서만 드러나는 실패**가 있으므로, 어느 레이아웃으로
밟았는지를 함께 남긴다.
