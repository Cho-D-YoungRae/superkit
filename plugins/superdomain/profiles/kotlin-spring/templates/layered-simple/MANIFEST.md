# layered-simple — kotlin-spring 골격 매니페스트

스타일 선언의 정본은 `references/knowledge/styles/layered-simple.md`의 `## 선언`이고, 치환 변수의
정본은 `profiles/README.md`의 「플레이스홀더 규약」이다. 이 파일은 **그 스타일의 골격이 어떤
파일로 이루어지고 어디에 놓이는가**만 정한다.

레이어는 셋이다 — `presentation`, `application`, `data`. 레이어 라벨은 **호출 방향**(위 → 아래)이고
`ls.layer-order`의 `layers`는 **안 → 밖**이라 정확히 역순이다(`data,application,presentation`).
가장 안쪽은 `data`다 — 프리셋 4종 중 도메인 모델이 가장 안쪽이 아닌 유일한 스타일이다.

## 이 골격이 통과해야 하는 규칙

수용 기준은 하나다: **그대로 전개된 골격은 이 스타일의 유효 규칙에 대해 `check_imports` 클린이고
fitness가 생성한 Konsist 테스트를 통과한다.**

| 규칙 id | 골격이 만족시키는 방식 |
|---|---|
| `ls.layer-order` | `presentation → application → data` 한 방향뿐이다. `data`는 아무것도 import하지 않는다. 세 레이어 모두 파일이 1개 이상이다(빈 레이어는 예외로 죽는다 — 매핑 §0.3-1) |
| `ls.controller-naming` | `presentation`의 최상위 public 타입이 `{{Context}}Controller` 하나뿐이다. 요청 DTO는 **중첩 타입**이라 검사 대상이 아니다 |
| `ls.service-naming` | `application`의 최상위 public 타입이 `{{Context}}Service` 하나뿐이다. 예외 `{{Context}}NotFound`도 **중첩 타입**으로 들어가 있다 |

명명 규칙 둘은 `strict = true`라 **검사 대상 0건도 실패**다. 그리고 접미사를 갖지 않는 보조 타입을
최상위로 빼는 순간 위반이므로, 골격은 처음부터 DTO와 예외를 중첩 타입으로 둔다 — 이것이 이
스타일에서 사실상 유일하게 깔끔한 답이다(스타일 R2·R3의 1번).

**`*.domain-pure`가 없는 것이 이 스타일의 내용이다.** 그래서 골격의 `@Entity`는 격리 대상이 아니라
모델 그 자체이고, `data` 레이어에 산다. 프레임워크 차단 규칙도 없다.

**규칙이 보지 못하는 것 — 컴파일러 플러그인.** `check_imports`도 Konsist도 **구조**만 본다.
`@Entity`의 no-arg 생성자와 `@Transactional`의 CGLIB 프록시(Kotlin 클래스는 기본이 final)는
어느 쪽에도 걸리지 않으므로, 빠지면 골격이 **두 검사를 다 통과하고 부팅에서 깨진다.** 그래서
`kotlin("plugin.jpa")`가 `build.gradle.kts.data`에,
`kotlin("plugin.spring")`이 `build.gradle.kts.application`에 근거 주석과 함께 들어 있다.

## 파일 목록

| 템플릿 파일 | 레이어 | 전개 뒤 |
|---|---|---|
| `settings.gradle.kts.fragment` | — | 루트 `settings.gradle.kts`에 **추가**(덮어쓰기 아님) |
| `build.gradle.kts.data` | data | 그 레이어 모듈의 `build.gradle.kts` |
| `build.gradle.kts.application` | application | 〃 |
| `build.gradle.kts.presentation` | presentation | 〃 |
| `data/{{Context}}.kt` | data | JPA 엔티티 = 모델. 다른 스타일의 애그리거트 스텁 자리 |
| `data/{{Context}}Repository.kt` | data | 스프링 데이터 리포지터리 = 이 스타일의 포트 1 |
| `application/{{Context}}Service.kt` | application | 서비스 = 유스케이스 1 (예외는 중첩) |
| `presentation/{{Context}}Controller.kt` | presentation | 컨트롤러 = 어댑터 1 (DTO는 중첩) |

`test/{{Context}}Test.kt`는 레이어가 아니라 **소스셋**이다 — `data` 레이어를 소유한 모듈의
`src/test/kotlin`에 놓인다(이 스타일의 모델이 거기 있다). 아키텍처 테스트는 이 골격이 만들지
않는다(fitness의 생성물이고 배치 규약은 `rule-mappings.md` §0.1).

## 레이아웃 3형 배치

소스 파일의 `package` 줄은 세 형태 모두 `{{pkg:<레이어>}}`가 정하므로 **파일 내용은 바뀌지
않는다.** 바뀌는 것은 경로와 빌드 조각의 개수뿐이다.

### multi-module — 레이어별 모듈

```
{{context}}/<레이어>/src/main/kotlin/<{{pkg:<레이어>}}의 . → />/<파일>
{{context}}/data/src/test/kotlin/<{{pkg:data}}의 . → />/{{Context}}Test.kt
```

`build.gradle.kts.<레이어>` 셋을 각 모듈에 두고 settings 조각을 그대로 쓴다. 다만 이 스타일에서
multi-module을 고를 이유는 드물다 — 모듈 구성은 스타일과 직교하지만, 여기까지 쪼개는 비용을
정당화하는 관측이 있어야 한다(`module-composition.md` 선택 절차 4).

### single-module — 단일 모듈 + 레이어 패키지

**이 스타일의 기본값에 가장 가까운 형태다.** 모듈은 `{{context}}` 하나이고 세 레이어는 그 안의
패키지다.

- settings 조각은 `include(":{{context}}")` **한 줄**로 줄인다.
- `build.gradle.kts.<레이어>` 셋을 **하나로 합친다.** 단순히 이어 붙이면 `plugins` 블록이
  여럿이 되어 Gradle이 구성 단계에서 거부한다. 병합은 결정적으로 한다.

| 조각의 요소 | 병합 규칙 |
|---|---|
| 헤더 주석 | **버리지 않는다.** 레이어 순서대로 파일 맨 위에 모은다 — "이 의존을 여기 더하면 어느 규칙이 잡는다"는 근거가 사라지면 나중에 아무나 더한다 |
| `plugins { … }` | 블록은 **하나만.** 안의 항목은 합집합이고 같은 플러그인은 한 번만 적는다 |
| `dependencies { … }` | 블록 **하나로** 합친다. 같은 좌표가 둘 이상이면 **넓은 configuration 하나만** 남긴다(`implementation` > `runtimeOnly`, `testImplementation` > `testRuntimeOnly`) |
| `project(":{{context}}:…")` | **지운다** — 모듈이 하나뿐이라 자기 자신을 가리키게 된다 |
| `tasks.test { useJUnitPlatform() }` | 파일 전체에 **한 번**만 |

### app-embedded — 규약 패턴 위치에 레이어 패키지만

모듈을 만들지 않는다. settings 조각과 빌드 조각을 **쓰지 않고**, 소스 파일만 각 레이어의 패키지
위치에 놓는다.

- 위치는 `### 패키지 규약` 표가 정한다. `{{pkg:<레이어>}}`가 그 표의 전개 결과다.
- 패턴에 `{앱}`이 있으면 **앱마다 사본이 있는 레이어**라 각 앱 모듈에 하나씩 두고, 없으면 앱들이
  함께 의존하는 **비실행 모듈**에 하나만 둔다(`module-composition.md`).
- `test/`는 data 패턴을 소유한 모듈의 `src/test/kotlin`에 둔다.

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
`templates/_shared/`의 `build.gradle.kts.app`과 `{{App}}Application.kt`가 만들고, 배치는
`### 애플리케이션` 표의 `모듈 경로`다(`profiles/README.md` ②「앱 실행 모듈」). 그 앱이 이
컨텍스트에서 의존하는 모듈은 **가장 바깥 레이어인 `:{{context}}:presentation` 하나**이며(안쪽은 전이
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
