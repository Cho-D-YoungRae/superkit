# 아키텍처 테스트 구성

컨벤션 「아키텍처 규칙은 테스트로 강제한다」를 따를 때 쓰는 구성 방법과 예시다. 규칙과 도구 분담은 `conventions.md`의 그 항목이 기준이고, 이 문서는 테스트를 만들거나 고칠 때 읽는다. superdomain은 테스트 코드를 생성하지 않는다.

- 예시는 Spring Modulith 2.x, Konsist, ArchUnit 기준이다. API는 프로젝트가 쓰는 버전의 문서로 확인한다.
- 패키지 이름(`com.acme`, `infrastructure`, `domain` 등)은 예시다. 대상 프로젝트의 관례로 바꾼다.
- Spring Modulith 레퍼런스: [Fundamentals](https://docs.spring.io/spring-modulith/reference/fundamentals.html) · [Verification](https://docs.spring.io/spring-modulith/reference/verification.html) · [Events](https://docs.spring.io/spring-modulith/reference/events.html)

## 도메인 사이: Spring Modulith

### 모듈 감지

Modulith의 기본 감지는 애플리케이션 루트 패키지의 직속 하위 패키지를 모듈 하나로 본다. 한 도메인의 코드가 모두 그 도메인 패키지 안에 있다는 전제다.

도메인 × 역할로 나눈 구조(영속은 `infrastructure.db.{도메인}`, 외부 클라이언트는 `client.{외부}`처럼 역할 패키지 아래에 도메인을 둔다)에서는 이 전제가 맞지 않는다. `infrastructure`·`client`가 모듈이 되고 도메인 사이 참조가 모두 그 모듈을 거치므로 위반이 수백 건 나온다. 이때는 감지 전략을 직접 구현한다.

- 모듈은 도메인 최상위 패키지로 정하고, 역할 패키지는 모듈에서 뺀다.
- 다른 도메인이 써도 되는 패키지(공개 인터페이스)는 `detectNamedInterfaces`에서 관례 패키지 이름으로 정한다. 운영 코드에 `@ApplicationModule`·`@NamedInterface` 같은 애노테이션을 붙이지 않는다.
- 전략 클래스와 등록(`spring.modulith.detection-strategy`)은 테스트 소스·테스트 리소스에 둔다. 검증용 구성이라 운영 코드에 둘 이유가 없다.
- 등록은 테스트 리소스의 `config/application.properties`에 둔다. 테스트 리소스 루트에 `application.properties`를 두면 같은 이름의 운영 설정을 가린다.
- 모듈에서 뺀 역할 패키지는 어느 모듈에도 속하지 않는다. 그 안의 도메인 사이 의존(예: `infrastructure.db.order`가 payment를 참조)은 이 검사가 보지 않으므로 리뷰가 본다.

```kotlin
// src/test/kotlin/com/acme/architecture/DomainModuleDetectionStrategy.kt
class DomainModuleDetectionStrategy : ApplicationModuleDetectionStrategy {

    // 도메인 최상위 패키지만 모듈로 본다. 역할 패키지는 모듈이 아니다.
    override fun getModuleBasePackages(rootPackage: JavaPackage): Stream<JavaPackage> =
        rootPackage.directSubPackages.stream()
            .filter { it.localName !in ROLE_PACKAGES }

    // 다른 도메인이 써도 되는 패키지를 관례로 정한다.
    override fun detectNamedInterfaces(basePackage: JavaPackage, information: ApplicationModuleInformation): NamedInterfaces =
        NamedInterfaces.builder(basePackage)
            .matching("domain", "application")
            .build()

    companion object {
        private val ROLE_PACKAGES = setOf("infrastructure", "client", "config", "support")
    }
}
```

```properties
# src/test/resources/config/application.properties
spring.modulith.detection-strategy=com.acme.architecture.DomainModuleDetectionStrategy
```

### 허용 관계 검사

DOMAIN.md 관계 표를 허용 관계로 옮겨 적고, Modulith가 코드에서 만든 모듈 그래프와 대조한다.

- 모듈 그래프는 `ApplicationModules.of("<루트 패키지>")`로 만든다. 실행 앱(api·batch·worker)이 여럿이면 특정 앱의 애플리케이션 클래스 대신 루트 패키지를 넘긴다. 검사할 도메인의 코드가 모두 테스트 클래스패스에 있어야 한다.
- 검사는 둘이다. 코드의 도메인 사이 의존이 허용 관계 안에 있는지, 코드에서 찾은 도메인마다 선언이 있는지. 의존 대상이 없는 도메인도 빈 집합으로 선언한다.
- 기반 도메인(`모든 도메인이 참조`)은 모든 도메인의 허용 대상에 넣는다.
- `verify()`는 순환과 공개하지 않은 패키지 접근을 잡는다. 허용 관계 검사와 함께 돌린다.

```kotlin
class DomainDependencyTest {

    private val modules = ApplicationModules.of("com.acme")

    // DOMAIN.md 관계 표를 옮긴다. 관계 표를 바꾸면 여기도 같은 변경에서 고친다.
    private val allowed: Map<String, Set<String>> = mapOf(
        "product" to emptySet(),
        "order" to setOf("product"),
        "payment" to setOf("order"),
        "delivery" to setOf("order"),
    )

    @Test
    fun `코드의 도메인마다 허용 관계가 선언되어 있다`() {
        val declared = modules.map { it.identifier.toString() }.toSet()
        assertThat(declared - allowed.keys).isEmpty()
    }

    @Test
    fun `도메인 사이 의존은 허용 관계 안에 있다`() {
        val violations = modules.flatMap { module ->
            val source = module.identifier.toString()
            module.getDirectDependencies(modules).uniqueModules()
                .map { it.identifier.toString() }
                .filter { it !in allowed[source].orEmpty() }
                .map { "$source -> $it" }
                .toList()
        }
        assertThat(violations).isEmpty()
    }

    @Test
    fun `순환과 공개하지 않은 패키지 접근이 없다`() {
        modules.verify()
    }
}
```

Java로는 이렇게 쓴다.

```java
// src/test/java/com/acme/architecture/DomainModuleDetectionStrategy.java
public class DomainModuleDetectionStrategy implements ApplicationModuleDetectionStrategy {

    private static final Set<String> ROLE_PACKAGES = Set.of("infrastructure", "client", "config", "support");

    @Override
    public Stream<JavaPackage> getModuleBasePackages(JavaPackage rootPackage) {
        return rootPackage.getDirectSubPackages().stream()
            .filter(it -> !ROLE_PACKAGES.contains(it.getLocalName()));
    }

    @Override
    public NamedInterfaces detectNamedInterfaces(JavaPackage basePackage, ApplicationModuleInformation information) {
        return NamedInterfaces.builder(basePackage).matching("domain", "application").build();
    }
}

class DomainDependencyTest {

    ApplicationModules modules = ApplicationModules.of("com.acme");

    Map<String, Set<String>> allowed = Map.of(
        "product", Set.of(),
        "order", Set.of("product"),
        "payment", Set.of("order"),
        "delivery", Set.of("order"));

    @Test
    void 도메인_사이_의존은_허용_관계_안에_있다() {
        var violations = modules.stream()
            .flatMap(module -> {
                var source = module.getIdentifier().toString();
                return module.getDirectDependencies(modules).uniqueModules()
                    .map(target -> target.getIdentifier().toString())
                    .filter(target -> !allowed.getOrDefault(source, Set.of()).contains(target))
                    .map(target -> source + " -> " + target);
            })
            .toList();
        assertThat(violations).isEmpty();
    }

    // 선언 누락 검사와 verify()는 Kotlin 예시와 같다.
}
```

### 모듈 슬라이스 테스트

`@ApplicationModuleTest`는 컴포넌트 스캔을 모듈 패키지로 좁힌다. 도메인 × 역할 구조에서는 역할 패키지에 있는 빈(외부 클라이언트, JPA 리포지토리 등)이 빠져 컨텍스트가 뜨지 않을 수 있다. 이 구조에서는 구조 검사(`ApplicationModules`)만 쓰고, 통합 테스트는 기존 방식대로 둔다.

### 이벤트 저장소

Modulith의 이벤트 저장소(event publication registry)는 이벤트를 발행한 애플리케이션 컨텍스트 안의 트랜잭션 리스너에 대해서만 발행 기록을 남긴다. 다른 프로세스(워커·배치)의 리스너는 이 저장소로 받지 못한다. 프로세스를 넘겨야 하면 externalization으로 메시지 브로커에 내보낸다(「도메인 사이 의존은 한 방향으로만 둔다」의 이벤트·아웃박스 참고).

## 도메인 안·소스 수준: Konsist·ArchUnit

Modulith가 도메인 사이를 맡으므로, 여기에는 도메인 안의 계층·JPA 위치·외부 연동 경계와 소스 수준 규칙만 둔다. 도메인 사이 import 규칙을 Konsist·ArchUnit에 다시 두지 않는다. Konsist의 import 규칙은 다른 도메인의 `domain` 패키지 참조를 어디서든 허용하는 식이 되기 쉬워, 역방향 의존을 놓친다.

Kotlin(Konsist): 소스 수준에서 domain 패키지가 JPA를 import하지 않는지 본다.

```kotlin
class LayerKonsistTest {

    @Test
    fun `domain은 JPA를 모른다`() {
        Konsist.scopeFromProduction()
            .files
            .withPackage("..domain..")
            .assertFalse { it.hasImport { import -> import.hasNameStartingWith("jakarta.persistence") } }
    }
}
```

Java(ArchUnit): 계층 방향과 JPA 위치를 바이트코드 수준에서 본다. infrastructure는 계층 밖에 두므로 `consideringOnlyDependenciesInLayers()`를 쓴다.

```java
@AnalyzeClasses(packages = "com.acme", importOptions = ImportOption.DoNotIncludeTests.class)
class LayerArchitectureTest {

    @ArchTest
    static final ArchRule layers = layeredArchitecture()
        .consideringOnlyDependenciesInLayers()
        .layer("Presentation").definedBy("..presentation..")
        .layer("Application").definedBy("..application..")
        .layer("Domain").definedBy("..domain..")
        .whereLayer("Presentation").mayNotBeAccessedByAnyLayer()
        .whereLayer("Application").mayOnlyBeAccessedByLayers("Presentation")
        .whereLayer("Domain").mayOnlyBeAccessedByLayers("Application", "Presentation");

    @ArchTest
    static final ArchRule domainDoesNotUseJpa = noClasses()
        .that().resideInAPackage("..domain..")
        .should().dependOnClassesThat().resideInAPackage("jakarta.persistence..");
}
```

- 「JPA는 인프라에 둔다」의 예외(분류가 generic인 도메인, 어드민·워커·배치)는 규칙에서 그 패키지를 빼고, 뺀 이유를 테스트에 주석으로 남긴다.
- 기존 위반이 많아 바로 켤 수 없으면 ArchUnit은 `FreezingArchRule`로 지금 위반을 고정하고 새 위반만 막는다. Konsist에는 위반을 고정하는 기능이 없으므로 검사 범위를 정리된 패키지로 좁혀 시작하거나, 기존 위반 선언에 `@Suppress("konsist.<테스트 이름>")`를 붙이고 줄여 간다.
