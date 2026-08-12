# clean — kotlin-spring 골격 매니페스트

스타일 선언의 정본은 `references/knowledge/styles/clean.md`의 `## 선언`이고, 치환 변수의 정본은
`profiles/README.md`의 「플레이스홀더 규약」이다. 이 파일은 **그 스타일의 골격이 어떤 파일로
이루어지고 어디에 놓이는가**만 정한다.

레이어는 넷이다 — `domain`, `usecase`, `adapter`, `framework`(안 → 밖).

## 이 골격이 통과해야 하는 규칙

수용 기준은 하나다: **그대로 전개된 골격은 이 스타일의 유효 규칙에 대해 `check_imports` 클린이고
fitness가 생성한 Konsist 테스트를 통과한다.**

| 규칙 id | 골격이 만족시키는 방식 |
|---|---|
| `cl.deps-inward` | 모듈 의존이 `framework → adapter → usecase → domain` 방향뿐이다. **adapter는 framework를 의존하지 않는다** — 그래서 게이트웨이 구현이 framework에 있다. 네 레이어 모두 파일이 1개 이상이다(빈 레이어는 예외로 죽는다 — 매핑 §0.3-1) |
| `cl.domain-pure` | `@Entity`는 `framework`의 `{{Context}}JpaEntity` 하나뿐이고, 그 타입을 import하는 파일이 framework 밖에 없다(격리는 양방향) |
| `cl.domain-no-framework` | `domain`과 `usecase`의 파일에 `org.springframework..`·`jakarta.persistence..` import가 없다. `build.gradle.kts.usecase`도 그 의존을 갖지 않는다 |

`from`에 `usecase`가 들어가는 것이 clean과 hexagonal의 유일한 선언 차이이고, 이 골격에서 그것이
드러나는 자리는 두 곳이다 — 애노테이션 없는 `{{Context}}Interactor`와, 그 대가로 생긴
`Transactional{{Context}}Interactor` 데코레이터.

**규칙이 보지 못하는 것 — 컴파일러 플러그인.** `check_imports`도 Konsist도 **구조**만 본다.
`@Entity`의 no-arg 생성자와 `@Transactional`의 CGLIB 프록시(Kotlin 클래스는 기본이 final)는
어느 쪽에도 걸리지 않으므로, 빠지면 골격이 **두 검사를 다 통과하고 부팅에서 깨진다.** 그래서
`kotlin("plugin.jpa")`·`kotlin("plugin.spring")`이 `build.gradle.kts.framework`에 근거 주석과 함께 들어 있다.

## 파일 목록

| 템플릿 파일 | 레이어 | 전개 뒤 |
|---|---|---|
| `settings.gradle.kts.fragment` | — | 루트 `settings.gradle.kts`에 **추가**(덮어쓰기 아님) |
| `build.gradle.kts.domain` | domain | 그 레이어 모듈의 `build.gradle.kts` |
| `build.gradle.kts.usecase` | usecase | 〃 |
| `build.gradle.kts.adapter` | adapter | 〃 |
| `build.gradle.kts.framework` | framework | 〃 |
| `domain/{{Context}}.kt` | domain | 애그리거트 루트 + 식별자 VO + 상태 enum + 예외 |
| `usecase/{{Context}}Gateway.kt` | usecase | 게이트웨이(out 경계) 인터페이스 1 |
| `usecase/{{Context}}Interactor.kt` | usecase | 입력 경계 + 인터랙터 = 유스케이스 1 |
| `adapter/{{Context}}Controller.kt` | adapter | 컨트롤러 1 |
| `framework/{{Context}}GatewayAdapter.kt` | framework | 게이트웨이 구현 1 + JPA 엔티티 |
| `framework/Transactional{{Context}}Interactor.kt` | framework | 트랜잭션 데코레이터 |

**소스 파일이 hexagonal보다 둘 많은 이유**는 둘이 서로 다르다.

- `adapter/{{Context}}Controller.kt`는 **0건 규율이 강제한다.** 원이 하나 더 있고 `adapter` 링이
  비면 `cl.deps-inward`가 예외로 죽으므로, 이 파일 없이는 골격이 수용 기준을 통과하지 못한다.
- `framework/Transactional{{Context}}Interactor.kt`는 **강제되지 않는다.** `framework` 링은
  `{{Context}}GatewayAdapter.kt`만으로 이미 채워지고, 이 파일을 지워도 check_imports는 여전히
  exit 0이다(실측). 그런데도 골격에 두는 이유는 위 「통과해야 하는 규칙」 끝에 적은 것 —
  clean과 hexagonal의 유일한 선언 차이가 **눈에 보이는 코드가 되는 자리가 여기뿐**이기 때문이다.
  이 파일을 지우면 골격은 통과하지만, 트랜잭션 경계를 어디에 두라는 것인지가 사라져 사람이
  인터랙터에 `@Transactional`을 붙이는 것으로 되돌아간다.

`test/{{Context}}Test.kt`는 레이어가 아니라 **소스셋**이다 — domain 레이어를 소유한 모듈의
`src/test/kotlin`에 놓인다. 아키텍처 테스트는 이 골격이 만들지 않는다(fitness의 생성물이고 배치
규약은 `rule-mappings.md` §0.1).

## 레이아웃 3형 배치

소스 파일의 `package` 줄은 세 형태 모두 `{{pkg:<레이어>}}`가 정하므로 **파일 내용은 바뀌지
않는다.** 바뀌는 것은 경로와 빌드 조각의 개수뿐이다.

### multi-module — 레이어별 모듈

```
{{context}}/<레이어>/src/main/kotlin/<{{pkg:<레이어>}}의 . → />/<파일>
{{context}}/domain/src/test/kotlin/<{{pkg:domain}}의 . → />/{{Context}}Test.kt
```

`build.gradle.kts.<레이어>` 넷을 각 모듈에 두고 settings 조각을 그대로 쓴다.

### single-module — 단일 모듈 + 레이어 패키지

모듈은 `{{context}}` 하나이고 네 레이어는 그 안의 패키지다.

- settings 조각은 `include(":{{context}}")` **한 줄**로 줄인다.
- `build.gradle.kts.<레이어>` 넷을 **하나로 합친다.** 단순히 이어 붙이면 `plugins` 블록이
  여럿이 되어 Gradle이 구성 단계에서 거부한다. 병합은 결정적으로 한다.

| 조각의 요소 | 병합 규칙 |
|---|---|
| 주석 | **버리지 않는다 — 위치와 무관하게 전부 보존한다.** 조각 머리의 주석은 레이어 순서대로 파일 맨 위에 모으고, 블록 안(`plugins`·`dependencies`)과 블록 뒤의 근거 주석은 그 항목을 따라 옮긴다. "이 의존을 여기 더하면 어느 규칙이 잡는다"·"이 플러그인이 빠지면 부팅에서 깨진다"는 근거가 사라지면 나중에 아무나 더하고 아무나 지운다 |
| `plugins { … }` | 블록은 **하나만.** 안의 항목은 합집합이고 같은 플러그인은 한 번만 적는다 |
| `dependencies { … }` | 블록 **하나로** 합친다. 같은 좌표가 둘 이상이면 **넓은 configuration 하나만** 남긴다(`implementation` > `runtimeOnly`, `testImplementation` > `testRuntimeOnly`) |
| `project(":{{context}}:…")` | **지운다** — 모듈이 하나뿐이라 자기 자신을 가리키게 된다 |
| `tasks.test { useJUnitPlatform() }` | 파일 전체에 **한 번**만 |

합치면 `usecase`에 스프링이 클래스패스로 들어온다. `cl.domain-no-framework`는 import를 보므로
규칙은 그대로 살아 있지만, 컴파일러가 막아 주던 몫은 사라진다 — single-module에서 clean을 고를
때 알고 고르는 대가다.

### app-embedded — 규약 패턴 위치에 레이어 패키지만

모듈을 만들지 않는다. settings 조각과 빌드 조각을 **쓰지 않고**, 소스 파일만 각 레이어의 패키지
위치에 놓는다.

- 위치는 `### 패키지 규약` 표가 정한다. `{{pkg:<레이어>}}`가 그 표의 전개 결과다.
- 패턴에 `{앱}`이 있으면 **앱마다 사본이 있는 레이어**라 각 앱 모듈에 하나씩 두고, 없으면 앱들이
  함께 의존하는 **비실행 모듈**에 하나만 둔다(`module-composition.md`).
- 그 비실행 모듈의 경로는 선언 어디에도 없다 — 관측으로 찾고, 찾지 못하면 사용자에게 묻는다.
- 같은 프로젝트의 app-embedded 컨텍스트들은 **같은 스타일이어야 한다.** 그중 하나라도 clean이면
  규약 표에 네 레이어의 행이 모두 있어야 한다.

## ARCHITECTURE.md 등록

```markdown
| 모듈 | 경로 | 레이어 |
|---|---|---|
| {{context}}-domain | {{context}}/domain | domain |
| {{context}}-usecase | {{context}}/usecase | usecase |
| {{context}}-adapter | {{context}}/adapter | adapter |
| {{context}}-framework | {{context}}/framework | framework |
```

single-module이어도 **행은 레이어마다 하나씩**이고 `모듈`·`경로`만 같은 값이 반복된다.
행 하나로 줄이면서 레이어를 `all`로 적으면 네 레이어의 패턴이 모두 사라져 `cl.*` 세 규칙이 전부
아무것도 검사하지 않는다(`resolve_rules`가 공허 레이어로 경고한다).

**앱 실행 모듈.** 이 컨텍스트를 `포함 컨텍스트`로 선언한 앱의 모듈은 이 골격이 만들지 않는다 —
`templates/_shared/`의 `build.gradle.kts.app`과 `{{App}}Application.kt`가 만들고, 배치는
`### 애플리케이션` 표의 `모듈 경로`다(`profiles/README.md` ②「앱 실행 모듈」). 그 앱이 이
컨텍스트에서 의존하는 모듈은 **가장 바깥 레이어인 `:{{context}}:framework` 하나**이며(안쪽은 전이
의존으로 따라온다), 그 값이 `{{#app.contextModules}}`에 들어가는 항목이다.

## 치환

변수의 뜻과 목록은 `profiles/README.md`의 「플레이스홀더 규약」이 정본이다. 이 골격이 쓰는 것은
`{{context}}`, `{{Context}}`, `{{pkg:<레이어>}}`, 그리고 조각 파일 이름의 `<레이어>`다. 파일
이름과 디렉터리 이름에도 같은 치환을 적용한다.

## 수용 기준 확인

```
python3 <플러그인>/scripts/check_imports.py ARCHITECTURE.md      # exit 0, [0건 경고] 없음
/superarchitect:fitness                                          # 생성 → 대상 프로젝트 빌드로 실행
```
