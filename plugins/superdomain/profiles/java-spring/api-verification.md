# java-spring — ArchUnit API 검증 대장

`rule-mappings.md`가 쓰는 ArchUnit API의 검증 대장이다 — 행 갱신 규율(`✅`·`✅ 실측`·
`⚠️ (미검증 — 첫 실행 시 확인)`)은 `rule-mappings.md` §0과 같다. **새 API를 템플릿에 쓰기 전에
여기에 행을 먼저 추가한다.** 아래에서 `§n`은 `rule-mappings.md`의 절 번호다.

2026-08-12 확인. 소스는 `com.tngtech.archunit:archunit:1.4.1`의 sources jar(경로는 그 안 기준),
문서는 archunit.org 사용자 가이드.
**`✅ 실측`은 gradle 실행으로 확인한 행이다** — ArchUnit 1.4.1 · JUnit 5.12.2 · Gradle 9.7.0 · Java 17
프로브에서 클린 트리·위반 트리·건너뛴 의존 트리 셋을 같은 규칙으로 대조했다(green/red 양방향).

| API | 상태 | 근거 |
|---|---|---|
| `new ClassFileImporter().importPackages(...)` — **클래스패스**에서 컴파일된 클래스를 읽는다(소스 트리가 아니다) | ✅ 실측 | `core/importer/ClassFileImporter.java`. 아키텍처 테스트 모듈이 프로덕션 모듈을 의존해야 스코프가 찬다(§0.1) |
| `ImportOption.Predefined.DO_NOT_INCLUDE_TESTS` | ✅ 실측 | `core/importer/ImportOption.java` — 위치 경로 정규식 3종(`.*/target/test-classes/.*`·`.*/build/classes/([^/]+/)?test/.*`·`.*/out/test/.*`). 실측: 이 옵션이 없으면 스코프가 14→22로 늘고 **생성 테스트 자신**(`…architecture.ClaimArchitectureTest$1` 포함)이 검사 대상이 된다 |
| `ImportOption.Predefined.DO_NOT_INCLUDE_JARS` — **쓰지 않는다** | ✅ 실측 | 같은 파일. 프로젝트 의존이 jar로 실릴 수 있어(실측: `getSource()`가 `jar:file:…/sample.jar!/…`) 이 옵션을 켜면 검사 대상이 통째로 빈다 |
| `JavaClass.Predicates.resideInAPackage(String)`의 패턴 의미 | ✅ 실측 | `core/domain/JavaClass.java`, `core/domain/PackageMatcher.java`. `com.a.b..`는 그 패키지 **자신과 하위 전체**(2건 매칭), `com.a.b`는 정확히 그 패키지(하위 0건), **타입 FQN을 넣으면 0건**이다 |
| `HasName.Predicates.name(String)` — FQN 정확 일치 | ✅ 실측 | `core/domain/properties/HasName.java`. 어휘 §2의 `..` 없는 항목이 "타입"일 때 이것으로 잡는다(§0.2) |
| `DescribedPredicate` `and`·`or`·`not`·`as`·`forSubtype` | ✅ 실측 | `base/DescribedPredicate.java`. `forSubtype()`이 없으면 `annotatedWith(...)`(= `DescribedPredicate<CanBeAnnotated>`)를 `DescribedPredicate<JavaClass>` 자리에 넣을 수 없다(실측 — 컴파일 오류) |
| `ArchRuleDefinition.classes()`·`noClasses()`와 `.that(DescribedPredicate)` | ✅ 실측 | `lang/syntax/ArchRuleDefinition.java` |
| `ClassesShould.dependOnClassesThat(DescribedPredicate)` — **바이트코드 의존 전부** | ✅ 실측 | `lang/syntax/ClassesShould.java`. 실측 검출 목록: 필드 타입·생성자 파라미터·메서드 반환 타입·**메서드 본문의 생성자/메서드 호출**·**애노테이션**(`is annotated with <jakarta.persistence.Entity>`). 자기 자신에 대한 의존은 위반으로 세지 않는다(실측 — 자기 타입 필드·메서드를 가진 클래스가 검출 3건에 들지 않았다) |
| `should().haveSimpleNameEndingWith(...)`·`orShould()` | ✅ 실측 | `lang/syntax/ClassesShould.java`·`ClassesShouldConjunction.java` |
| `that().areTopLevelClasses()`·`arePublic()` | ✅ 실측 | `lang/syntax/GivenClassesThat.java`. 실측: 두 필터를 빼면 중첩 공개 타입(`ClaimUseCase$Nested`)이 검사 대상이 되고, package-private 최상위 타입은 `arePublic()`이 걸러 낸다 |
| `should().resideInAnyPackage(...)` | ✅ 실측 | `lang/syntax/ClassesShould.java` (§3 위반 A) |
| `CanBeAnnotated.Predicates.annotatedWith(DescribedPredicate<? super JavaAnnotation<?>>)` + `HasType.Predicates.rawType(...)` + `JavaClass.Predicates.simpleName(...)` | ✅ 실측 | `core/domain/properties/CanBeAnnotated.java`·`HasType.java`·`JavaClass.java`. 애노테이션 타입이 클래스패스에 없어도 이름으로 매칭된다 — `Class` 오버로드를 쓰지 않는 이유(테스트 모듈에 JPA 컴파일 의존이 생긴다) |
| `ArchRule.allowEmptyShould(boolean)`와 **기본 실패** | ✅ 실측 | `lang/ArchRule.java`. 기본값에서 `that()` 매칭 0건이면 `Rule '…' failed to check any classes.`로 **실패한다**(`classes()`·`noClasses()`·스코프 자체가 0건인 경우 모두 실측). 그 메시지가 안내하는 전역 스위치 `archRule.failOnEmptyShould=false`는 이 프로파일이 쓰지 않는다(§0.3) |
| `Architectures.layeredArchitecture().consideringOnlyDependenciesInLayers()` | ✅ 실측 | `library/Architectures.java`. `considering…`을 부르지 않는 구형 진입점은 쓰지 않는다 |
| `.layer(name).definedBy(String...)` / `.definedBy(DescribedPredicate<? super JavaClass>)` | ✅ 실측 | 같은 파일 L553·L563. 술어 오버로드가 §7 강등의 자리다 |
| `whereLayer(x).mayNotAccessAnyLayer()`·`mayOnlyAccessLayers(...)` | ✅ 실측 | 같은 파일 L621 부근. 실측: 건너뛴 의존(adapter → domain)이 비-strict에서 통과하고 strict 번역에서만 실패한다 |
| `withOptionalLayers(boolean)` — 기본값에서 **빈 레이어는 실패** | ✅ 실측 | 같은 파일 L154–L162(javadoc: "layers … must not be empty"). `allowEmptyShould(b)`는 이 메서드와 같다(L357–L362). 실측: 빈 레이어 하나로 규칙이 실패하고 `withOptionalLayers(true)`면 통과한다 |
| `LayeredArchitecture.because(String)`의 반환형이 `ArchRule` — **순서 제약** | ✅ 실측 | 같은 파일 L352. `because()` 뒤에는 `withOptionalLayers`·`as`를 부를 수 없다(실측 — 컴파일 오류). 템플릿에서 `because(...)`가 마지막인 이유 |
| `ArchRule.because(String)`·`check(JavaClasses)`와 실패 메시지 형식 | ✅ 실측 | `lang/ArchRule.java`. `because`는 자동 생성 설명을 유지한 채 `, because …`를 덧붙인다(실측 — 규칙 id가 메시지에 남는다) |
| `JavaClass.getPackageName()`·`getSourceCodeLocation().getSourceFileName()` | ✅ 실측 | `core/domain/JavaClass.java` L159, `core/domain/SourceCodeLocation.java` L58–L70(`resolveSourceFileName`: 바이트코드의 SourceFile 속성 → 없으면 최외곽 클래스 이름 + `.java`). 널이 아니다. §7의 경로 사상이 이 둘로만 만들어진다 |
| `JavaClass.getSource().getUri()` — **파일 경로 유도에 쓸 수 없다** | ✅ 실측 | `core/domain/Source.java`. 실측값이 `jar:file:…/build/libs/sample.jar!/…/Claim.class`였다 — 소스 파일 경로가 아니고 jar 안일 수도 있다. §7이 URI 대신 (패키지 + SourceFile 이름) 꼬리 일치를 쓰는 이유 |
| `FreezingArchRule` + `ViolationStore` — **채택하지 않는다** | ✅ | `library/freeze/ViolationStore.java` L68·L74: `save(ArchRule, List<String> violations)`·`getViolations(ArchRule)`로 **위반 설명 줄(String)** 을 규칙 단위로 저장하고, 동치 판정은 `ViolationLineMatcher.matches(String, String)`(줄 대 줄)이다. 코어 계약의 `(rule, path)` 키와 사상되지 않는다 — 근거는 `rule-mappings.md` §8 |
| `archunit_ignore_patterns.txt` — **쓰지 않는다** | ✅ | `lang/EvaluationResult.java` L62. 위반 메시지 정규식으로 무시하는 장부라 baseline과 이중 장부가 된다(§8) |
| JUnit 5 `@Test`·`@DisplayName` | ✅ 실측 | 생성 파일이 쓰는 유일한 테스트 프레임워크 API. 메서드 이름의 안전 변환으로 잃은 원본 규칙 id를 `@DisplayName`이 보존한다(§0.1) |

## 관련 문서

- `profiles/java-spring/rule-mappings.md` — 이 대장을 소비하는 번역 사전
- `profiles/README.md` — 프로파일 계약(이 파일이 계약 ①의 두 번째 구성물이다)
