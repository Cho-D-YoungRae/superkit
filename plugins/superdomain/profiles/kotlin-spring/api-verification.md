# kotlin-spring — Konsist API 검증 대장

`rule-mappings.md`가 쓰는 Konsist API의 검증 대장이다 — 행 갱신 규율(`✅`·`✅ 실측`·
`⚠️ (미검증 — 첫 실행 시 확인)`)은 `rule-mappings.md` §0과 같다. **새 API를 템플릿에 쓰기 전에
여기에 행을 먼저 추가한다.** 아래에서 `§n`은 `rule-mappings.md`의 절 번호다.

2026-08-11 확인. 소스는 `lemonappdev/konsist` 태그 `v0.17.3`, 문서는 `konsist-documentation` main.
**`✅ 실측`은 gradle+Konsist 실행으로 확인한 행이다**(샘플 4종 · Konsist 0.17.3 · Gradle 9.7.0).

| API | 상태 | 근거 |
|---|---|---|
| `Konsist.scopeFromProject()` / `scopeFromProduction()` / `scopeFromModule()` | ✅ | `api/container/KoScope.kt`, `writing-tests/koscope.md` |
| `KoScope.assertArchitecture(additionalMessage, testName) { }` | ✅ | `api/architecture/KoArchitectureAssertion.kt` |
| `Layer(name, rootPackage)`와 rootPackage 검증 규칙 | ✅ | `api/architecture/Layer.kt` |
| `dependsOn(vararg, strict)`·`dependsOnNothing()`·`doesNotDependOn(...)`·`include()`와 각 `Collection<Layer>` 버전 | ✅ | `api/architecture/LayerDependencies.kt` |
| `strict = false`인 `dependsOn`은 아무 실패도 만들지 않음 | ✅ | `core/verify/KoArchitectureAssert.kt` `getFailedDependsOnLayers` |
| 빈 레이어 → `KoPreconditionFailedException` | ✅ | `core/architecture/LayerDependenciesCore.kt` `checkLayersWithoutFiles` |
| 레이어 의존 판정이 import 기반 | ✅ | `core/verify/KoArchitectureAssert.kt` `Layer.isDependentOn` |
| `assertTrue`/`assertFalse(strict, additionalMessage, testName) { }`와 빈 목록 처리 | ✅ | `api/verify/KoDeclarationAndProviderAssert.kt` |
| `classes`/`interfaces`/`objects`/`classesAndInterfacesAndObjects(includeNested, includeLocal)` — 기본 `true` | ✅ | `api/container/KoScope.kt` |
| `withPackage`/`withoutPackage`(vararg·Collection) | ✅ | `api/ext/list/KoHasPackageProviderListExt.kt`, `…/KoResideInPackageProviderListExt.kt` |
| `KoFileDeclaration`이 `KoHasPackageProvider`·`KoImportProvider` 구현 | ✅ | `api/declaration/KoFileDeclaration.kt` |
| `resideInPackage(name)`/`resideOutsidePackage(name)` (**단수형**) | ✅ | `api/provider/KoResideInPackageProvider.kt` |
| `hasImportWithName(name, vararg)`·`(Collection)` — 정확 일치, 빈 컬렉션이면 `hasImports()` | ✅ | `core/provider/KoImportProviderCore.kt` |
| `hasImport(predicate)`·`imports`·`KoImportDeclaration.name`·`isWildcard` | ✅ | `api/provider/KoImportProvider.kt`, `api/declaration/KoImportDeclaration.kt`(`KoIsWildcardProvider`) |
| `hasNameEndingWith`·`withNameEndingWith` | ✅ | `api/provider/KoNameProvider.kt`, `api/ext/list/KoNameProviderListExt.kt` |
| `withAnnotationNamed(name, vararg)`·**`(names: Collection<String>)`** — 단순명·FQN 모두 매칭 | ✅ | `api/ext/list/KoAnnotationProviderListExt.kt` L36·L47, `core/provider/KoAnnotationProviderCore.kt`(`representsType`) |
| `withPublicOrDefaultModifier()` | ✅ | `api/ext/list/modifierprovider/KoVisibilityModifierProviderListExt.kt` |
| `fullyQualifiedName` | ✅ | `api/provider/KoFullyQualifiedNameProvider.kt` |
| `KoClassDeclaration`이 `KoConstructorProvider` 구현 | ✅ | `api/declaration/KoClassDeclaration.kt` |
| 단수 `klass.constructors`·`constructor.parameters`·`klass.properties()`·`type.sourceType` | ✅ 실측 | 프리셋 4종이 `forbid-sibling-dependency`를 쓰지 않아 생성물에는 인스턴스가 없었다 — §5 템플릿을 프로브로 직접 실행해 확인. `sourceType`은 널 표시 `?`를 포함한다(§5) |
| 같은 레이어에 `include()`와 다른 의존 선언을 함께 호출 — **순서 제약** | ✅ 실측 | `include()`가 먼저면 `KoInvalidAssertArchitectureConfigurationException`("already defined with a strict=null value")으로 어서션이 실행 전에 죽는다(스타일 3종 재현). 의존 선언 뒤로 옮기면 정상 판정하고 §0.3-1의 빈 레이어 검사도 그대로 걸린다 |

## 관련 문서

- `profiles/kotlin-spring/rule-mappings.md` — 이 대장을 소비하는 번역 사전
- `profiles/README.md` — 프로파일 계약(이 파일이 계약 ①의 두 번째 구성물이다)
