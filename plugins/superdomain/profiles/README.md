# 언어 프로파일 계약

프로파일은 **규칙 어휘를 특정 언어·도구로 번역하는 어댑터**다. 번역 단위는 스타일이 아니라
primitive다 — 프로파일은 `hexagonal`이라는 스타일을 모르고, `layer-order`·`forbid-import`·
`confine-type`·`naming-suffix`·`forbid-sibling-dependency` 다섯 개와 파생 규칙 3종만 안다. 그래서
프리셋이든 아무도 예상하지 않은 커스텀 스타일이든, 어휘의 조합이기만 하면 fitness가 테스트를 만든다.

어휘의 의미 정본은 `references/governance/rule-vocabulary.md`다. 프로파일은 그 의미를 바꾸지 않고
코드로 옮기기만 한다. 두 문서가 어긋나면 어휘가 이긴다.

## 현황

| 프로파일 | 도구 | 상태 |
|---|---|---|
| `kotlin-spring` | Konsist 0.17.3 (`com.lemonappdev:konsist`) | `rule-mappings.md` 있음 |
| `java-spring` | ArchUnit 1.4.1 (`com.tngtech.archunit:archunit`) | 빈 디렉터리 — 아래 구현 상태 |

이 계약의 소비자는 모두 도착했다: 매핑을 읽어 테스트를 만드는 `fitness` 스킬, 템플릿이 소비하는
`EffectiveRule`·`DerivedRule`을 내는 `scripts/resolve_rules.py`, 그리고 `profiles/` 디렉터리를
동적으로 읽는 `parse_architecture.py`.

> **구현 상태 — `java-spring`은 Phase 6이다.** `profiles/java-spring/`에는 아직
> `rule-mappings.md`가 없다. Java 프로젝트를 선언할 수는 있지만 fitness는 매핑 부재를 그대로
> 알리고 중단한다(생성하지 않는다). 어휘 확장 절차(`rule-vocabulary.md` §7)가 요구하는 "두
> 프로파일 매핑 동시 추가"도 그때까지 완주할 수 없다.

## 디렉터리 구조

```
profiles/<이름>/
├── rule-mappings.md      # 필수 — primitive → 도구 코드 번역
├── templates/<style>/    # 선택 — scaffold가 쓰는 골격
└── examples/             # 선택 — 좋은 예 1, 나쁜 예 1
```

디렉터리 이름이 곧 프로파일 이름이고, `ARCHITECTURE.md`의 `- 프로파일:` 값이 그것을 가리킨다.
파서는 `profiles/` 아래 디렉터리 목록을 읽어 정규 값 집합을 만든다 — 상수 목록이 아니므로
디렉터리를 만드는 것만으로 새 프로파일 이름이 허용된다.

## ① `rule-mappings.md` — 필수

이 파일이 없는 디렉터리는 프로파일이 아니다. fitness의 유일한 번역 사전이며, 여기에 없는
primitive를 만나면 fitness는 **임의로 번역하지 않고 오류로 보고한다**. 다음을 모두 담는다.

1. **생성 파일 헤더**(고정 문자열)와 **파일 배치 규약** — 어떤 이름의 파일이 어디에 생기는가.
2. **primitive 5종 각각**에 대해: 입력(어느 필드를 읽는가) → 코드 템플릿(그대로 컴파일되는 완전한
   형태) → 주의·커버리지 한계.
3. **파생 규칙 3종**(`derived.context-isolation`·`derived.app-confinement`·
   `derived.shared-module-direction`) 각각의 템플릿.
4. **검증 표기** — 사용한 도구 API가 공식 문서·소스로 확인된 것인지, 확인하지 못했는지.
   확인하지 못한 API에는 반드시 `(미검증 — 첫 실행 시 확인)`을 남긴다. 미검증을 검증된 것처럼
   쓰는 것은 이 저장소가 가장 경계하는 실패다 — 생성은 되는데 강제되지 않는 규칙을 만든다.
5. **커버리지 한계** — 그 도구가 원리적으로 보지 못하는 것. 침묵은 금지다.

### 플레이스홀더 규약

템플릿의 치환 지점은 `{{...}}`로 쓴다. 세 가지 형태뿐이다.

| 형태 | 뜻 |
|---|---|
| `{{name}}` | 스칼라 1개를 그 자리에 치환 |
| `{{items:<필드>}}` | 문자열 목록을 `"a", "b"` 꼴로 전개(따옴표 포함, 쉼표 구분) |
| `{{#<필드>}} … {{/<필드>}}` | 목록 항목마다 블록을 1회씩 반복. 블록 안에서 `{{.}}`는 현재 항목, `{{i}}`는 0-기준 순번 |

이름은 `resolve_rules.py`의 산출 스키마에서 온다. 프로파일이 이름을 새로 지어내지 않는다.

| 이름 | 출처 |
|---|---|
| `{{project}}` | `EffectiveRule.project` / `DerivedRule.project` |
| `{{basePackage}}` | 프로젝트 섹션의 `- 기본 패키지:` |
| `{{context}}` | `EffectiveRule.context` |
| `{{Context}}` | `context`의 PascalCase (파일명·클래스명용) |
| `{{ruleId}}` | `EffectiveRule.rule_id` |
| `{{ruleIdSafe}}` | `ruleId`에서 대상 언어의 식별자에 쓸 수 없는 문자를 공백으로 바꾼 형태 (Kotlin 백틱 함수 이름은 `.`을 담을 수 없다 — `hex.domain-pure` → `hex domain-pure`) |
| `{{primitive}}` | `EffectiveRule.primitive` |
| `{{layerName}}` | §2.1(나) 파라미터가 담은 레이어 이름 1개 — `params[키]`의 항목 |
| `{{LayerName}}` | `layerName`의 PascalCase (도구가 오류 메시지에 쓰는 표시 이름) |
| `{{pattern}}` | 패키지 패턴 1개 — `layer_patterns[layerName]`의 항목 또는 `resolved[키]`의 항목 |
| `{{subject}}` | `DerivedRule.subject` (컨텍스트명 \| 앱명 \| 공용 모듈명) |
| `{{kind}}` | `DerivedRule.kind` |
| `{{modulePath}}` | `detail["module_path"]`(app-confinement) 또는 `detail["path"]`(shared-module-direction) |
| `{{role}}` | `detail["role"]` |

primitive마다 있는 스칼라 파라미터는 키 이름을 그대로 쓴다 — `{{suffix}}`, `{{type}}`. 어휘 §2에
따라 `params`의 **모든 값은 목록**이므로, 목록이 아닌 키(`type`·`layer`·`suffix`·`scope`·`strict`)의
스칼라 플레이스홀더는 그 목록의 유일한 항목을 뜻한다.
`{{items:...}}`·`{{#...}}`의 `<필드>`도 같은 출처를 쓴다: `resolved.from`, `resolved.to`,
`params.suffixes`, `layer_patterns.<레이어>`, `detail.forbidden`, `detail.reverse_from`,
`detail.domain_restricted_contexts` 등. `detail.app_patterns` 같은 **맵 필드는 목록
플레이스홀더의 대상이 아니다** — 매핑 문서가 이름 있는 파생 목록으로 풀어 쓴다(kotlin-spring
`rule-mappings.md` §6.2가 그 예). 위 표는 프로파일이 **공유하는 어휘**이고, 각 프로파일은
필요한 것만 쓴다. 파생 목록(예: `confine-type`의 허용 범위)을 쓰는 템플릿은 그 목록이 어떻게
만들어지는지를 자기 "입력" 줄에서 정의한다.

**규칙 어휘의 파라미터 이름과 도구 API 이름이 우연히 같아도 뜻은 같지 않을 수 있다.** 어휘의
`layer-order`에는 `strict` 파라미터가 있고 Konsist에도 `strict`가 있지만 두 뜻은 다르다 —
매핑 문서는 그런 충돌을 이름이 아니라 의미로 풀고, 푼 근거를 적는다.

## ② `templates/<style>/` — 선택

scaffold가 골격을 만들 때 쓰는 파일 묶음이다. 스타일 이름(`layered-simple`, `layered-domain`,
`hexagonal`, `clean`)마다 하나씩 두고, single-module용 패키지 경계 변형과 app-embedded용 레이어
패키지 변형을 함께 제공한다. 치환 변수는 `{{context}}`·`{{basePackage}}` 등 위 규약을 따른다.
커스텀 스타일은 템플릿 없이 스타일 선언(레이어 + 규칙)에서 골격을 유도한다.

> **구현 상태 — `templates/`는 Phase 4다.** 어느 프로파일에도 아직 없다. scaffold 스킬 자체가
> 없으므로 이 규약은 지금 소비자가 없다. kotlin-spring 4종이 최초 구현이다.

## ③ `examples/` — 선택

그 프로파일의 규칙이 실제로 무엇을 잡는지 보여주는 최소 코드 두 개. **좋은 예 1개, 나쁜 예 1개**로
충분하다 — 예제는 판정 근거가 아니라 읽는 사람의 이해용이므로 늘리지 않는다.

- `examples/good-<primitive>.kt` — 규칙을 만족하는 최소 코드.
- `examples/bad-<primitive>.kt` — 위반하는 최소 코드. 첫 줄 주석에 **어떤 규칙 id의 위반인지와
  도구가 내는 실패 메시지의 첫 줄**을 적는다.

## ④ 제3 프로파일을 추가하려면

프로파일 추가는 "계약 구현"이다. 순서대로 한다.

1. `profiles/<이름>/` 디렉터리를 만든다. 이름은 `<언어>-<프레임워크>` 꼴을 쓴다. 파서가
   디렉터리를 읽어 정규 값으로 인정하므로 코드 수정은 필요 없다.
2. `rule-mappings.md`를 위 ①대로 쓴다. **어휘 5종 전부**를 커버해야 한다. 하나라도 그 도구로
   표현할 수 없으면 프로파일을 추가하는 대신 그 사실을 보고한다 — 반쪽 프로파일은 "선언은 되는데
   강제되지 않는 규칙"을 만들고, 그것이 폐쇄 어휘가 막으려던 상태다(`rule-vocabulary.md` §1).
3. 도구 API를 공식 문서 또는 릴리스 소스로 확인하고, 확인하지 못한 것은 미검증으로 표기한다.
4. (선택) `templates/`·`examples/`를 채운다.
5. init이 그 스택의 프로젝트를 거버넌스 대상으로 제안하기 시작하는지 확인한다 — 제안 기준은
   "백엔드라서"가 아니라 **프로파일이 있어서**다(스펙 부록 A-6).

## 관련 문서

- `references/governance/rule-vocabulary.md` — 어휘 정본(§2 파라미터 문법, §3 primitive 5종, §7 확장 절차)
- `references/governance/architecture-template.md` — 정규화(§6)와 파생 규칙(§5.1 규칙 5)의 정본
- `scripts/resolve_rules.py` — 템플릿이 소비하는 `EffectiveRule`·`DerivedRule`의 산출처
