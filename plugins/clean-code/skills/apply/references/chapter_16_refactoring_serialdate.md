# Chapter 16: Refactoring SerialDate — SerialDate 리팩터링

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 16, pp. 267–284
> 한 줄 요약: 잘 짜인 남의 코드라도 커버리지로 테스트 빈틈을 찾아 빠진 테스트와 버그 수정부터 하고(Make It Work), 작은 단계마다 전체 테스트를 돌리며 Chapter 17 휴리스틱으로 다듬는(Make It Right) 사례 연구다.

## 핵심

- 리팩터링 전에 커버리지 도구로 테스트 빈틈을 찾고, 빠진 테스트를 먼저 써서 실패하는 테스트로 버그를 드러낸다. 기존 테스트가 다 통과한다고 테스트가 충분한 것은 아니다.
- 순서는 First, Make It Work → Then Make It Right다. 동작을 바로잡은 다음에 구조를 고치고, 구조 변경은 작은 단계로 나눠 단계마다 전체 테스트를 돌린다.
- 다듬기 전에 그 코드를 누가 쓰는지부터 확인한다. 사용처가 없거나 테스트뿐이면 다듬지 말고 그 테스트와 함께 지운다.
- 이 작업은 작성자를 깎아내리는 일이 아니라 전문가다운 리뷰다. 목표는 Boy Scout Rule, 즉 받았을 때보다 조금 더 깨끗하게 체크인하는 것이다.
- 반복된 변환: int 상수 → enum, 구현 세부는 파생 클래스·팩토리로, 기능은 그 데이터가 있는 곳으로, 불필요한 주석·죽은 코드 삭제, 이름 바로잡기, 설명 변수.

## First, Make It Work — 먼저 돌아가게 만든다

**어떻게**

- 기존 테스트가 모두 통과해도 그대로 믿지 않는다(`T1`). 커버리지 도구로 실행되지 않은 문장을 찾는다(`T2`). 원서 사례는 실행 가능한 185문장 중 91개(약 50%)만 실행됐다.
- IDE의 `Find Usages`로 사용처를 찾는다. 테스트를 포함해 사용처가 하나도 없으면 기존 테스트도 그 메서드를 부르지 않는다는 뜻이고, 그만큼 테스트 빈틈이 있다(`T1`, `F4`).
- 기존 테스트와 독립된 테스트 스위트를 직접 쓴다. 마땅히 해야 할 동작인데 실패하는 테스트는 (원서에서는 주석 처리해) 남겨 두고 통과시킬 목표로 삼는다. 원서는 일부를 주석 처리한 상태로도 커버리지를 92%로 올렸고, 구조를 다듬기 전에 이들을 통과시켰다. 지원해야 하는지 불분명한 동작(예: 비표준 약어)만 억지로 구현하지 않고 보류했다.
- 당연해 보이는 동작(예: 이름 파싱에서 대소문자 무시)이 빠졌으면 테스트로 요구한다(`G2`). 쓰기 쉬운 사소한 테스트도 건너뛰지 않는다(`T3`). 단, 저자는 그중 일부가 원래 설계에 없던 동작을 자기 기준으로 요구한 것이라고 인정했다. 원 설계를 넘어 동작을 바꾸는 판단임을 알고 쓴다.
- 경계 조건을 테스트한다(`T5`, `G3`). 원서에서 찾은 버그 하나는 비교 연산자 `>`를 `>=`로 고치면 되는 전형적인 경계 오류였다.
- 버그 수정 이력이 있는 함수와, 처음 쓴 테스트 사례가 일부라도 실패한 함수는 주변 사례를 철저히 늘린다(`T6`). 실패하는 사례들의 패턴(`T7`)과 한 번도 실행되지 않는 줄(`T8`)이 알고리즘 결함을 가리킨다. 실행되지 않는 분기는 그 조건이 늘 거짓이라는 신호일 수 있다.
- 오류를 문자열로 반환하던 곳은 `IllegalArgumentException`을 던지게 바꾼다(이유는 Chapter 7).

**왜**

- 클래스를 완전히 이해하고 리팩터링하려면 커버리지가 훨씬 높아야 한다. 테스트가 덮지 않은 곳은 고친 뒤 깨졌는지 알 길이 없다.
- 실패하는 테스트가 숨은 버그와 잘못된 알고리즘을 드러낸다. 모든 테스트가 통과해야 비로소 '돌아간다'고 말할 수 있고, 그때 '제대로' 만드는 단계로 넘어간다.

## Then Make It Right — 그다음 제대로 만든다

**어떻게**

- 파일을 위에서 아래로 훑으며 하나씩 고친다. 변경할 때마다 그 클래스의 테스트만이 아니라 라이브러리 전체 단위 테스트를 돌린다.
- 이름 바꾸기·메서드 옮기기는 IDE 리팩터링 도구로 해서 호출처까지 함께 안전하게 바꾼다.
- 정교한 리팩터링 사슬을 시작하기 전에 호출처와 테스트부터 확인한다. 저자는 옮기고, 이름 바꾸고, 끝내 메서드를 없애는 사슬을 마친 뒤에야 사용처가 테스트뿐임을 알고 테스트도 지웠다. 다음 함수는 사용처부터 확인해 바로 지웠다. 테스트가 없는 메서드를 만나면 다듬는 중에도 그 자리에서 테스트를 쓴다.
- 끝까지 간 뒤 클래스 전체를 한 번 더 훑어 흐름을 다듬는다. 낡은 머리 주석 정리(`C2`), 남은 enum을 별도 파일로 분리, 정적 유틸리티를 유틸리티 클래스로 이동(`G6`), 추상 메서드를 맨 위로(`G24`), 남은 중복 추출(`G5`), 매직 넘버를 이름 있는 상수로(`G25`).
- 코드가 줄면 커버리지 비율이 떨어질 수 있다(원서: 84.9%). 덜 테스트해서가 아니라 클래스가 작아져 남은 미실행 줄의 비중이 커진 것이다. 비율보다 무엇이 안 덮였는지를 본다. 원서는 남은 줄이 테스트할 가치가 없을 만큼 사소하다고 판단했다.

**왜**

- 작은 단계마다 전체 테스트를 돌려야 모든 변경이 시스템 전체에서 여전히 동작한다고 확신할 수 있다.
- Boy Scout Rule대로 받았을 때보다 조금 더 깨끗하게 체크인해 두면, 다음 사람이 이 코드를 더 쉽게 다루고 아마 조금 더 정리할 수 있게 된다.

## 변환 패턴

- **상수 상속·int 코드 → enum** (`J2`, `J3`, `G5`) — 상수 클래스를 상속해 이름을 줄여 쓰거나 종류를 int로 넘길 때 — enum으로 바꾸고 정수 코드와의 변환, 문자열 파싱을 enum에 둔다. 클래스와 사용자 코드를 두루 고쳐야 하지만 유효성 검사 함수와 흩어진 오류 검사가 사라진다. 정수가 아니라 기호로 넘기므로 이름이나 타입이 마음에 안 들어도 IDE로 안전하게 바꿀 수 있다.
- **기반 클래스가 파생 클래스를 생성 → ABSTRACT FACTORY** (`G7`, `N1`) — 추상 클래스 안에서 특정 구현체를 직접 만들 때, 또는 추상 클래스의 사용자가 구현 정보(지원 범위 등)가 필요한데 파생 클래스 인스턴스를 받지 못할 때 — 팩토리를 따로 두고 인스턴스 생성과 구현에 관한 질문(지원 범위의 최솟값·최댓값 등)을 함께 맡긴다. 기반 클래스가 파생 클래스를 아는 것은 대개 나쁘다. 팩토리를 두면 구현 정보를 기반 클래스에 넣지 않고 제공할 수 있고, 기본 팩토리는 필요할 때 다른 팩토리로 바꿔 끼울 수 있다. 생성 메서드는 `createInstance` 같은 막연한 이름 대신 만드는 대상이 드러나게(예: `makeReservation`) 짓는다.
- **구현 세부는 아래로, 구현과 무관한 것은 위로** (`G6`, `G10`, `G11`) — 상수·표·함수가 특정 구현의 사정에 속하고(`G6`) 검색해 보니 실제로 그 구현에서만 쓰일 때, 또는 추상 메서드의 구현이 파생 클래스 세부에 전혀 의존하지 않을 때 — 앞의 것은 파생 클래스로 내리고 뒤의 것은 기반 클래스로 올린다. 추상 클래스가 구현을 예고하지 않아야 구현을 숨길 수 있다. 어느 구현에도 특정되지 않아 판단이 갈리는 표는 지금 쓰는 곳 가까이 둔다(`G10`). 기반 클래스에 남기면 다른 표처럼 private으로 숨기고 접근 함수를 둬야 일관되는데(`G11`), 그런 함수는 아무도 필요로 하지 않았다. 나중에 다시 옮기기 쉬운지도 본다.
- **논리적 의존을 물리적으로** (`G22`, `G6`) — 위로 올리려는 알고리즘이 구현의 가정(예: 0번째 날이 무슨 요일인지)에 몰래 기대고 있을 때 — 그 가정을 추상 메서드로 드러내고 파생 클래스가 구현하게 한다. 알고리즘의 일반적인 부분은 위에, 구현에 의존하는 작은 부분만 아래에 남는다.
- **파일 머리·주석 정리** (`C1`, `C2`, `C3`, `G1`, `J1`) — 변경 이력, 긴 import 목록, 시그니처를 되풀이할 뿐인 Javadoc, 코드 변경으로 틀려진 주석, 소스에 섞인 HTML — 변경 이력은 소스 관리 도구에 맡기고 지운다. 저작권·라이선스는 법적 이유로 남긴다. 긴 import 목록은 `java.util.*` 같은 와일드카드로 줄였다(`J1`, 현대 관행은 원서 밖 보충). 중복 주석은 거짓이 쌓이는 곳이므로 지운다. 한 파일에 언어가 여럿 섞이면 다루기 어렵다. 원서는 Javadoc에 HTML 태그를 흩뿌리는 대신 주석 전체를 `<pre>`로 감싸 소스의 서식이 문서에도 남게 하는 방법을 제안한다.
- **죽은 코드·잡동사니 제거** (`G8`, `G9`, `G12`, `F4`) — 아무도 쓰지 않는 필드·표·접근자, 컴파일러가 만들어 줄 빈 기본 생성자, 쌍둥이 함수에서만 호출되는 함수, 같은 데이터를 함수로도 제공하는 public 표 — 지우거나 하나로 합친다. 같은 데이터를 함수가 이미 제공하니 표는 공개할 이유가 없으므로 private으로 숨긴다(`G8`). 루프 안에서 같은 일을 하는 if가 반복되면 `||`로 합친다(`G5`).
- **기능을 데이터가 있는 곳으로** (`G14`, `G17`, `G13`) — 함수가 남의 데이터만 만지거나(Feature Envy), 자기 클래스 타입을 인수로 받는 인스턴스 메서드일 때 — 앞의 것은 그 데이터를 가진 enum·클래스로 옮기고(`G14`), 엉뚱한 곳에 있는 데이터 표도 그 개념의 enum으로 옮긴다(`G17`). 뒤의 것은 인수를 없애고 this의 데이터를 쓰는 진짜 인스턴스 메서드로 바꾼다(`G14`). 옮긴 뒤 enum이 커지고 그 개념이 원래 클래스에 의존하지 않으면 별도 파일로 뺀다(`G13`).
- **선택자 인수·switch → 메서드 분리·다형성** (`G15`, `G23`) — 함수가 플래그 인수로 동작을 고르거나(한 함수가 플래그를 넘겨 쌍둥이 함수를 부르는 경우 포함) 종류별 switch가 있을 때 — 플래그 인수는 대개 나쁘고, 출력 형식만 고르는 플래그라면 특히 그렇다. 형식마다 메서드를 나누고(예: `displayName()`·`abbreviation()`), switch의 각 case는 enum 상수별 메서드로 옮긴다.
- **정적 → 인스턴스, 그리고 이름 다시 보기** (`G18`, `G5`, `G20`, `N4`) — static 함수가 그 클래스의 인스턴스 변수를 다룰 때 — 인스턴스 메서드로 바꾸고, 같은 일을 하는 인스턴스 메서드가 따로 있으면 없앤다(`G5`). 바꾸고 나면 `cart.addItems(2);`가 cart 자체를 바꾸는 것으로 읽히는 새 모호함이 생기므로 이름도 함께 바꾼다(`G20`, `N4`). 새 객체를 돌려주면 `add` 대신 `plus`처럼 짓는다. 결과를 대입하는 `updated = cart.plusItems(2)`는 자연스럽게, 반환값을 버리는 `cart.plusItems(2);`는 어색하게 읽히는 이름이 좋다.
- **알고리즘 이해 → 설명 변수, 형제 함수와 같은 형태** (`G21`, `G19`, `G16`, `G11`) — 한눈에 읽히지 않는 계산이 있거나, 비슷한 일을 하는 형제 함수끼리 모양이 다를 때 — 무엇을 하는지 먼저 이해한 뒤 단순하게 고치고 중간값에 이름을 붙인다. 형제 함수는 같은 형태로 맞춘다. 동작을 바로잡느라 먼저 고친 알고리즘도 다듬기 단계에서 형제 함수들의 패턴과 설명 변수에 맞춰 다시 쓴다.
- **이름을 맞는 추상화 수준·표준 용어로** (`N1`, `N2`, `N3`) — 이름이 구현 방식을 암시하거나 뜻이 부정확할 때 — 추상 클래스 이름에서 구현을 빼고, 수학의 open/closed interval처럼 널리 아는 용어를 쓴다. 다른 라이브러리와 이름이 겹치면 타협한다.
- **논란이 있는 저자의 선택: `final` 제거** (`G12`) — 인수·지역 변수의 `final`을 잡동사니로 보고 지웠다. 통념과 반대임을 스스로 밝히며, 가끔 쓰는 `final` 상수는 쓸모 있다고 인정하고 단위 테스트가 그런 오류를 이미 잡아서 그렇게 느끼는지도 모른다고 했다.
- **논란이 있는 저자의 선택: `serialVersionUID` 삭제** (`G4`) — 일단 지웠다. 선언하지 않으면 모듈을 바꿀 때마다 컴파일러가 다른 값을 만들어, 이전 버전으로 직렬화한 객체를 읽으면 `InvalidClassException`이 난다. 저자는 수동 관리에서 갱신을 잊어 조용히 이상하게 동작하는 것보다 원인이 분명한 이 실패가 낫다고 보았다. 공개 프레임워크라면 사소한 변경이 옛 직렬화 데이터를 깨지 않게 수동 관리해야 한다는 리뷰어 반론에도 일리가 있다고 인정했고, 버전을 넘는 역직렬화를 기대하지 말라고 정리했다.

```java
// Bad: 종류를 int로 받아 switch로 가르고, 잘못된 값은 default에서야 걸린다
public static final int FULL_REFUND = 1, HALF_REFUND = 2, NO_REFUND = 3;
public long refundAmount(long paid, int policy) {
    switch (policy) {
        case FULL_REFUND: return paid;
        case HALF_REFUND: return paid / 2;
        case NO_REFUND:   return 0;
        default: throw new IllegalArgumentException("Invalid policy " + policy);
    }
}
// Good: 기호로 넘기니 검사는 경계(fromCode) 한 곳에만 남고, 각 case는 상수별 메서드가 된다
public enum RefundPolicy {
    FULL(1) { public long refundAmount(long paid) { return paid; } },
    HALF(2) { public long refundAmount(long paid) { return paid / 2; } },
    NONE(3) { public long refundAmount(long paid) { return 0; } };
    private final int code;
    RefundPolicy(int code) { this.code = code; }
    public abstract long refundAmount(long paid);
    public static RefundPolicy fromCode(int code) {
        for (RefundPolicy p : values()) if (p.code == code) return p;
        throw new IllegalArgumentException("Invalid policy " + code);
    }
}
```

```java
// Bad: 인스턴스 데이터를 다루는 static, 뜻이 묻힌 식
public static Cart addItems(Cart cart, int qty) {
    return new Cart(cart.unitPrice, cart.qty + qty,
        (cart.qty + qty) * cart.unitPrice >= 50_000 ? 0 : 3_000);
}
// 이름은 두고 인스턴스 메서드로만 바꾸면 cart.addItems(2);가 cart를 바꾸는 것처럼 읽힌다
// Good: 인스턴스 메서드, 설명 변수, 새 객체를 돌려준다는 이름
public Cart plusItems(int qty) {
    int resultQty = this.qty + qty;
    long subtotal = resultQty * unitPrice;
    boolean freeShipping = subtotal >= FREE_SHIPPING_THRESHOLD; // 50_000
    long shippingFee = freeShipping ? 0 : STANDARD_SHIPPING_FEE; // 3_000
    return new Cart(unitPrice, resultQty, shippingFee);
}
// 호출: Cart updated = cart.plusItems(2);  // cart 자체는 그대로다
```

## 체크리스트

- [ ] 리팩터링 전에 커버리지 도구로 실행되지 않는 코드를 확인했는가?
- [ ] 빠진 테스트를 먼저 쓰고, 실패하는 테스트가 드러낸 버그를 구조 변경 전에 고쳤는가?
- [ ] 경계 조건과 버그가 있던 함수 주변에 테스트 사례를 충분히 추가했는가?
- [ ] 실패하는 사례들의 공통점이나 한 번도 실행되지 않는 분기를 근거로 알고리즘 결함을 점검했는가?
- [ ] 변경을 작은 단계로 나누고 단계마다 전체 테스트를 돌렸는가?
- [ ] 다듬기 전에 호출처를 확인했는가? 테스트만 부르는 코드도 그 테스트와 함께 지웠는가?
- [ ] 종류를 int 상수로 넘기거나 상수 클래스를 상속하는 곳이 남아 있지 않은가?
- [ ] 기반 클래스가 파생 클래스나 구현 세부를 알고 있지 않은가?
- [ ] 메서드가 자기 데이터보다 남의 데이터를 주로 다루지 않는가?
- [ ] 새 객체를 돌려주는 메서드 이름이 원본을 바꾸는 것처럼 읽히지 않는가?
- [ ] 이번 변경으로 지운 죽은 코드·낡은 주석·중복이나 바로잡은 이름이 하나 이상 있는가?

## 관련

- Chapter 17 휴리스틱(이 장에서 적용된 것): `C1` Inappropriate Information, `C2` Obsolete Comment, `C3` Redundant Comment, `F4` Dead Function, `J1` Avoid Long Import Lists by Using Wildcards, `J2` Don't Inherit Constants, `J3` Constants versus Enums
  - `G1` Multiple Languages in One Source File, `G2` Obvious Behavior Is Unimplemented, `G3` Incorrect Behavior at the Boundaries, `G4` Overridden Safeties, `G5` Duplication, `G6` Code at Wrong Level of Abstraction, `G7` Base Classes Depending on Their Derivatives, `G8` Too Much Information, `G9` Dead Code, `G10` Vertical Separation, `G11` Inconsistency, `G12` Clutter, `G13` Artificial Coupling
  - `G14` Feature Envy, `G15` Selector Arguments, `G16` Obscured Intent, `G17` Misplaced Responsibility, `G18` Inappropriate Static, `G19` Use Explanatory Variables, `G20` Function Names Should Say What They Do, `G21` Understand the Algorithm, `G22` Make Logical Dependencies Physical, `G23` Prefer Polymorphism to If/Else or Switch/Case, `G24` Follow Standard Conventions, `G25` Replace Magic Numbers with Named Constants
  - `N1` Choose Descriptive Names, `N2` Choose Names at the Appropriate Level of Abstraction, `N3` Use Standard Nomenclature Where Possible, `N4` Unambiguous Names, `T1` Insufficient Tests, `T2` Use a Coverage Tool!, `T3` Don't Skip Trivial Tests, `T5` Test Boundary Conditions, `T6` Exhaustively Test Near Bugs, `T7` Patterns of Failure Are Revealing, `T8` Test Coverage Patterns Can Be Revealing
- [chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md) — 위 휴리스틱 각각의 설명
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — 테스트가 변경을 가능하게 하는 이유, 테스트를 개념 하나씩 나누면 빠진 경계 사례가 드러난다(Single Concept per Test)
- [chapter_01_clean_code.md](chapter_01_clean_code.md) — The Boy Scout Rule
- [chapter_14_successive_refinement.md](chapter_14_successive_refinement.md) — 작은 단계로 점진적으로 개선한 또 다른 사례 연구
- [chapter_04_comments.md](chapter_04_comments.md) — 중복·낡은 주석, 변경 이력 주석, 주석 속 HTML
- [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) — 서술적이고 모호하지 않은 이름 짓기
- [chapter_03_functions.md](chapter_03_functions.md) — 플래그 인수, switch 문을 다형성 뒤로 숨기기
- [chapter_07_error_handling.md](chapter_07_error_handling.md) — 오류 코드·문자열 대신 예외를 던지는 이유

## 원서 밖 보충

- 원서는 Java 5/6 기준이다. Java 8의 `java.time.LocalDate`가 시간 없는 날짜를 표준으로 제공하므로 이런 날짜 클래스를 직접 만들 일은 드물다. `LocalDate`도 불변 객체에 `plusDays`·`plusMonths` 같은 이름을 쓴다.
- `J1`의 와일드카드 import는 Google Java Style Guide 등 여러 현대 스타일 가이드가 금지한다. 팀의 규칙을 따른다.
- `final` 제거와 `serialVersionUID` 삭제는 저자 개인의 선택이다. 팀 규칙이 `final`을 요구하거나 버전 간 직렬화 호환이 필요하면 유지한다.
- 원서 방식을 그대로 옮길 때 주의한다. 보류할 테스트는 주석 처리 대신 JUnit 5의 `@Disabled("지원 여부 미정")`처럼 사유를 남긴다. 공개 API는 저장소 안에 호출처가 없어도 외부 사용자가 있을 수 있으므로 `@Deprecated` 단계를 거쳐 지운다.
