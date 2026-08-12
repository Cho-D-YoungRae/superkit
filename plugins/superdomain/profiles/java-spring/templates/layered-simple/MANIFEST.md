# layered-simple — java-spring 골격 매니페스트

스타일 선언의 정본은 `references/knowledge/styles/layered-simple.md`의 `## 선언`이고, 치환 변수의
정본은 `profiles/README.md`의 「플레이스홀더 규약」이다. 이 파일은 **그 스타일의 골격이 어떤
파일로 이루어지고 어디에 놓이는가**만 정한다.

레이어는 셋이다 — `presentation`, `application`, `data`. 레이어 라벨은 **호출 방향**(위 → 아래)이고
`ls.layer-order`의 `layers`는 **안 → 밖**이라 정확히 역순이다(`data,application,presentation`).
가장 안쪽은 `data`다 — 프리셋 4종 중 도메인 모델이 가장 안쪽이 아닌 유일한 스타일이다.

## 이 골격이 통과해야 하는 규칙

수용 기준은 하나다: **그대로 전개된 골격은 이 스타일의 유효 규칙에 대해 `check_imports` 클린이고
fitness가 생성한 ArchUnit 테스트를 통과한다.**

| 규칙 id | 골격이 만족시키는 방식 |
|---|---|
| `ls.layer-order` | `presentation → application → data` 한 방향뿐이다. `data`는 다른 레이어를 참조하지 않는다. 세 레이어 모두 파일이 1개 이상이다 — **빈 레이어는 위반이 아니라 실패**다(매핑 §0.3-2) |
| `ls.controller-naming` | `presentation`의 최상위 public 타입이 `{{Context}}Controller` 하나뿐이다. 요청 DTO는 **중첩 record**라 검사 대상이 아니다 |
| `ls.service-naming` | `application`의 최상위 public 타입이 `{{Context}}Service` 하나뿐이다. 예외 `NotFound`도 **중첩 클래스**로 들어가 있다 |

명명 규칙 둘은 **검사 대상 0건도 실패**다(매핑 §0.3-1 — `classes()`의 `that()` 매칭 0건은 실패).
그리고 접미사를 갖지 않는 보조 타입을 최상위로 빼는 순간 위반이므로, 골격은 처음부터 DTO와 예외를
중첩 타입으로 둔다 — 이것이 이 스타일에서 사실상 유일하게 깔끔한 답이고(스타일 R2·R3의 1번),
**Java에서는 파일이 갈리는 문제까지 겹치므로 중첩이 더 강한 답이 된다.**

**`*.domain-pure`가 없는 것이 이 스타일의 내용이다.** 그래서 골격의 `@Entity`는 격리 대상이 아니라
모델 그 자체이고, `data` 레이어에 산다. 프레임워크 차단 규칙도 없다.

**강제되는 파일과 교육 목적의 파일.**

| 파일 | 지우면 |
|---|---|
| `data/{{Context}}Repository.java` | `data` 링은 `{{Context}}.java`로 이미 채워져 규칙은 통과한다. 다만 `{{Context}}Service`가 이 타입을 쓰므로 **컴파일이 깨진다** — 이 스타일의 "포트 1"이 그것이다 |
| 나머지 넷 | 전부 레이어를 채우는 데 필요하다. 셋 중 어느 레이어가 비어도 `ls.*` 규칙이 실패한다 |

**규칙이 보지 못하는 것 — Java·Spring 쪽 세 자리.** Kotlin 프로파일이 컴파일러
플러그인(`plugin.jpa`·`plugin.spring`·`plugin.allopen`)으로 막던 자리가 Java에서는 사라지지 않고
**모양만 바뀐다.**

| 항목 | 어디에 있나 | 빠지면 |
|---|---|---|
| `@Entity`의 no-arg 생성자 | `data/{{Context}}.java`의 `protected` 기본 생성자 — Java에는 `plugin.jpa`에 해당하는 것이 없어 **소스가 직접 갖는다** | 두 검사를 다 통과하고 부팅에서 깨진다 |
| 엔티티·getter를 `final`로 잠그지 않기 | `data/{{Context}}.java`(주석) | 지연 로딩 프록시가 서지 못한다. Kotlin이 `plugin.allopen`을 켜야 했던 자리이고, **엔티티가 곧 모델인 이 스타일이 가장 먼저 닿는다** |
| `-parameters` 컴파일 옵션 | `build.gradle.kts.presentation`의 `tasks.withType<JavaCompile>` | `@PathVariable`의 이름을 못 읽어 **첫 요청에서** 깨진다. 부트 플러그인이 이 옵션을 넣어 주는 것은 앱 모듈뿐이다 |

**그리고 규칙이 보지 못하는 빌드 쪽 한 자리 — `api` vs `implementation`.**
`{{Context}}Repository`가 `JpaRepository`를 상속하는 순간 스프링 데이터 타입이 `data` 모듈의
**공개 API**가 된다. `build.gradle.kts.data`가 그 좌표를 `implementation`으로 감추면
`{{Context}}Service`가 `cannot access JpaRepository`로 깨진다 ✅ 실측 — 그래서 그 조각만
`java-library` + `api`다. 영속 기술이 안쪽 레이어의 계약에 그대로 드러나는 것이 이 스타일의
성질이고, 그 성질이 빌드 그래프에도 나타난 것이다.

## 파일 목록

| 템플릿 파일 | 레이어 | 전개 뒤 |
|---|---|---|
| `settings.gradle.kts.fragment` | — | 루트 `settings.gradle.kts`에 **추가**(덮어쓰기 아님) |
| `build.gradle.kts.data` | data | 그 레이어 모듈의 `build.gradle.kts` (`java-library` + `api`) |
| `build.gradle.kts.application` | application | 〃 |
| `build.gradle.kts.presentation` | presentation | 〃 (`-parameters` 설정 포함) |
| `data/{{Context}}.java` | data | JPA 엔티티 = 모델. 다른 스타일의 애그리거트 스텁 자리 |
| `data/{{Context}}Repository.java` | data | 스프링 데이터 리포지터리 = 이 스타일의 포트 1 |
| `application/{{Context}}Service.java` | application | 서비스 = 유스케이스 1 (예외는 **중첩**) |
| `presentation/{{Context}}Controller.java` | presentation | 컨트롤러 = 어댑터 1 (DTO는 **중첩 record**) |
| `test/{{Context}}Test.java` | data(테스트) | 단위 테스트 골격 |

**Kotlin 골격과 파일 수가 같은 유일한 스타일이다.** 다른 셋은 Java의 "파일당 public 최상위 타입
하나" 때문에 파일이 늘지만, 이 스타일은 애초에 파일마다 타입이 하나씩이고 예외·DTO가 중첩이라
갈릴 것이 없다 — 명명 규칙이 이미 그렇게 만들어 두었다.

`test/{{Context}}Test.java`는 레이어가 아니라 **소스셋**이다 — `data` 레이어를 소유한 모듈의
`src/test/java`에 놓인다(이 스타일의 모델이 거기 있다). 아키텍처 테스트는 이 골격이 만들지
않는다(fitness의 생성물이고 배치 규약은 `rule-mappings.md` §0.1).

## 레이아웃 3형 배치

소스 파일의 `package` 줄은 세 형태 모두 `{{pkg:<레이어>}}`가 정하므로 **파일 내용은 바뀌지
않는다.** 바뀌는 것은 경로와 빌드 조각의 개수뿐이다.

### multi-module — 레이어별 모듈

```
{{context}}/<레이어>/src/main/java/<{{pkg:<레이어>}}의 . → />/<파일>
{{context}}/data/src/test/java/<{{pkg:data}}의 . → />/{{Context}}Test.java
```

`build.gradle.kts.<레이어>` 셋을 각 모듈에 두고 settings 조각을 그대로 쓴다. 다만 이 스타일에서
multi-module을 고를 이유는 드물다 — 모듈 구성은 스타일과 직교하지만, 여기까지 쪼개는 비용을
정당화하는 관측이 있어야 한다(`module-composition.md` 선택 절차 4).

### single-module — 단일 모듈 + 레이어 패키지

**이 스타일의 기본값에 가장 가까운 형태다.** 모듈은 `{{context}}` 하나이고 세 레이어는 그 안의
패키지다.

- settings 조각은 `include(":{{context}}")` **한 줄**로 줄인다 — 모듈 이름이 곧 디렉터리라
  `projectDir` 재지정 줄은 함께 사라진다.
- `build.gradle.kts.<레이어>` 셋을 **하나로 합친다.** 단순히 이어 붙이면 `plugins` 블록이
  여럿이 되어 Gradle이 구성 단계에서 거부한다. 병합은 결정적으로 한다.

| 조각의 요소 | 병합 규칙 |
|---|---|
| 주석 | **버리지 않는다 — 위치와 무관하게 전부 보존한다.** 조각 머리의 주석은 레이어 순서대로 파일 맨 위에 모으고, 블록 안(`plugins`·`dependencies`)과 블록 뒤의 근거 주석은 그 항목을 따라 옮긴다 |
| `plugins { … }` | 블록은 **하나만.** 안의 항목은 합집합이고 같은 플러그인은 한 번만 적는다. `java`와 `java-library`가 함께 오면 **`java-library` 하나만** 남긴다(그쪽이 `java`를 포함한다) |
| `dependencies { … }` | 블록 **하나로** 합친다. 같은 좌표가 둘 이상이면 **넓은 configuration 하나만** 남긴다(`api` > `implementation` > `runtimeOnly`, `testImplementation` > `testRuntimeOnly`). 모듈이 하나뿐이면 `api`와 `implementation`의 차이가 사라지지만, 되쪼갤 때 근거를 잃지 않도록 `api` 줄의 주석은 그대로 옮긴다 |
| `project(":{{context}}-…")` | **지운다** — 모듈이 하나뿐이라 자기 자신을 가리키게 된다 |
| `tasks.test { useJUnitPlatform() }` | 파일 전체에 **한 번**만 |
| `tasks.withType<JavaCompile> { … "-parameters" }` | 파일 전체에 **한 번**만. 합친 모듈에는 컨트롤러가 함께 들어오므로 이 블록은 **반드시 남는다** |

### app-embedded — 규약 패턴 위치에 레이어 패키지만

모듈을 만들지 않는다. settings 조각과 빌드 조각을 **쓰지 않고**, 소스 파일만 각 레이어의 패키지
위치에 놓는다.

- 위치는 `### 패키지 규약` 표가 정한다. `{{pkg:<레이어>}}`가 그 표의 전개 결과다.
- 패턴에 `{앱}`이 있으면 **앱마다 사본이 있는 레이어**라 각 앱 모듈에 하나씩 두고, 없으면 앱들이
  함께 의존하는 **비실행 모듈**에 하나만 둔다(`module-composition.md`).
- 빌드 조각을 쓰지 않으므로 **`-parameters`가 어디에도 없다.** 컨트롤러가 들어가는 모듈의 기존
  빌드 스크립트에 그 설정이 있는지 확인하고, 없으면 그 한 블록만 옮긴다.
- `test/`는 data 패턴을 소유한 모듈의 `src/test/java`에 둔다.

## ARCHITECTURE.md 등록

```markdown
| 모듈 | 경로 | 레이어 |
|---|---|---|
| {{context}}-data | {{context}}/data | data |
| {{context}}-application | {{context}}/application | application |
| {{context}}-presentation | {{context}}/presentation | presentation |
```

single-module이어도 **행은 레이어마다 하나씩**이고 `모듈`·`경로`만 같은 값이 반복된다
(`{{context}}` / `{{context}}` / 레이어명). 행 하나로 줄이면서 레이어를 `all`로 적으면 세
레이어의 패턴이 모두 사라져 `ls.*` 세 규칙이 전부 아무것도 검사하지 않는다
(`resolve_rules`가 공허 레이어로 경고한다).

**앱 실행 모듈.** 이 컨텍스트를 `포함 컨텍스트`로 선언한 앱의 모듈은 이 골격이 만들지 않는다 —
`templates/_shared/`의 `build.gradle.kts.app`과 `{{App}}Application.java`가 만들고, 배치는
`### 애플리케이션` 표의 `모듈 경로`다(`profiles/README.md` ②「앱 실행 모듈」). 그 앱이 이
컨텍스트에서 의존하는 모듈은 **가장 바깥 레이어인 `:{{context}}-presentation` 하나**이며(안쪽은
전이 의존으로 따라온다), 그 값이 `{{#app.contextModules}}`에 들어가는 항목이다.

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

**확인한 레이아웃 — multi-module**(Phase 6 T2: `check_imports` exit 0 · ArchUnit 통과 — 당시
모듈 경로는 colon형. 접두형 개편은 이름-only라 검사 축 실측은 유효하고, 접두형 배선은 kotlin
e2e가 같은 조각 구조로 검증했다). 이 스타일에서 특히 중요하다 — 위 `api` vs `implementation`은 **multi-module에서만 드러나는 실패**라
single-module 확인만으로는 수용 기준이 충족돼 보인다.
