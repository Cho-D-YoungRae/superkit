# Chapter 5: Formatting — 형식 맞추기

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 5, pp. 75–92
> 한 줄 요약: 형식은 의사소통 수단이므로, 팀이 합의한 단순한 규칙을 일관되게 적용해 소스 파일이 신문 기사처럼 위에서 아래로 읽히게 한다.

## 핵심

- 개념 사이는 빈 줄로 띄우고, 밀접한 줄은 빈 줄이나 쓸모없는 주석 없이 붙인다.
- 관련된 개념은 세로로 가까이 두고, 파일 위쪽에 고수준 개념을, 아래로 갈수록 세부를 둔다(Newspaper Metaphor). 호출하는 함수는 가능하면 위에, 호출되는 함수는 그 가까이 아래에 둔다.
- 지역 변수는 쓰는 곳 가까이, 인스턴스 변수는 클래스 맨 위 한곳에 모은다.
- 줄은 짧게 유지하고(저자 개인 한도 120자), 정렬용 공백을 넣지 않으며, 짧은 스코프도 한 줄로 접지 않는다.
- 개인 취향보다 팀 규칙이 우선이다. 규칙을 IDE 포매터 같은 자동 도구에 넣어 두면 지키기 쉽다.

## The Purpose of Formatting — 형식은 의사소통이다

**어떻게**

- 단순한 형식 규칙을 정하고 모든 코드에 일관되게 적용한다. 팀이라면 규칙 하나에 합의해 모두 따르고, 자동 도구로 적용하면 좋다. 형식을 무시하지도, 종교처럼 떠받들지도 않는다.

**왜**

- 저자는 "Code formatting is about communication" (p. 76)이라고 한다. 전문 개발자의 첫 번째 일은 '일단 돌아가게 하기'가 아니라 의사소통이다.
- 오늘 만든 기능은 다음 릴리스에서 바뀌기 쉽지만, 가독성은 앞으로의 모든 변경에 영향을 준다. 코드가 알아볼 수 없게 바뀐 뒤에도 스타일과 규율은 남아 유지보수성과 확장성을 좌우한다. 또한 엉망인 코드를 본 사람은 프로젝트의 다른 부분도 똑같이 세부에 무심하리라고 판단한다.

## Vertical Formatting — 파일은 작게, 신문 기사처럼

**어떻게**

- 소스 파일을 작게 유지한다. 보통 200줄, 길어도 500줄 정도를 목표로 한다. 엄격한 규칙은 아니지만 저자는 매우 바람직하다고 본다. Java에서 파일 크기는 클래스 크기와 밀접하다([chapter_10_classes.md](chapter_10_classes.md)).
- **The Newspaper Metaphor**: 파일 이름은 단순하면서도 설명적이어서 이름만으로 맞는 모듈인지 판단할 수 있게 한다. 맨 위에는 고수준 개념과 알고리즘을, 아래로 갈수록 세부를, 맨 끝에는 가장 저수준의 함수와 세부 사항을 둔다.

**왜**

- 수치의 근거는 저자가 7개 프로젝트(JUnit, FitNesse, testNG, Time and Money, JDepend, Ant, Tomcat)의 파일 길이를 잰 결과다. JUnit·FitNesse·Time and Money는 500줄 넘는 파일이 없고 대부분 200줄 미만이었으며, 그 크기의 파일로도 FitNesse(약 50,000줄) 같은 큰 시스템을 만들 수 있다고 저자는 본다. 작은 파일이 대개 큰 파일보다 이해하기 쉽다.
- 신문 기사는 제목으로 읽을지 정하고, 첫 문단에서 큰 그림을 얻고, 내려가며 세부를 얻는다. 파일이 기사라면 시스템은 신문이다. 신문은 대부분 짧은 기사로 이루어져 쓸 만하고, 사실·날짜·이름을 뒤섞은 긴 기사 하나뿐이라면 아무도 읽지 않는다.

## Vertical Openness Between Concepts / Vertical Density — 개념은 띄우고, 밀접한 줄은 붙인다

**어떻게**

- package 선언, import 묶음, 각 메서드처럼 생각 하나가 끝나는 곳마다 빈 줄을 넣는다. 반면 밀접하게 연관된 줄(함께 쓰이는 필드 묶음 등)은 빈 줄이나 쓸모없는 주석으로 끊지 않고 세로로 촘촘하게 붙인다.

**왜**

- 코드는 거의 모두 위에서 아래로 읽히고, 줄 묶음 하나가 완결된 생각 하나다. 빈 줄은 새 개념이 시작된다는 시각 신호여서, 훑어 내려가는 눈이 빈 줄 다음 첫 줄에 멈춘다.
- 빈 줄이 분리라면 촘촘함은 가까운 관계를 뜻한다. 필드 사이의 무의미한 주석은 그 관계를 끊어, 한눈에 들어올 클래스를 눈과 고개를 움직여 가며 읽게 만든다.

```java
// Bad: 이름을 되풀이하는 주석이 필드 묶음을 끊고, 필드와 메서드 사이에 빈 줄이 없다
public class Cart {
    /** 담긴 상품 목록 */
    private final List<CartItem> items = new ArrayList<>();
    /** 담긴 수량 합계 */
    private int totalQuantity;
    public void add(CartItem item) {
        items.add(item);
        totalQuantity += item.quantity();
    }
}

// Good: 필드는 붙이고, 개념(필드 묶음, 메서드) 사이는 띄운다
public class Cart {
    private final List<CartItem> items = new ArrayList<>();
    private int totalQuantity;

    public void add(CartItem item) {
        items.add(item);
        totalQuantity += item.quantity();
    }
}
```

## Vertical Distance — 연관된 개념은 세로로 가깝게

**어떻게**

- 밀접한 개념은 세로로 가까이 둔다 [G10]. 같은 파일에 둘 만큼 밀접한 개념은 서로를 이해하는 데 중요할수록 더 가깝게 둔다. 아주 타당한 이유가 없으면 밀접한 개념을 다른 파일로 나누지 않는다. 상위 클래스의 protected 변수는 쓰는 코드와 다른 파일에 선언되어 상속 사슬을 거슬러 정의를 찾게 만든다. protected 변수를 피할 이유 중 하나다.
- **Variable Declarations**: 지역 변수는 사용하는 곳에 최대한 가깝게 선언한다. 함수를 아주 짧게 만들므로 지역 변수는 각 함수 맨 위에 둔다. 루프 제어 변수는 대개 루프 문 안에서 선언한다. 드물게 긴 함수에서는 블록 맨 위나 루프 바로 앞에 선언하기도 한다.
- **Instance variables**: 클래스 맨 위에 선언한다. 핵심은 누구나 아는 한곳에 모으는 것이다. C++에서는 맨 아래에 두는 scissors rule도 썼지만 Java 관례는 맨 위이며, 저자는 다른 관례를 따를 이유가 없다고 본다. 클래스 중간에 끼운 필드는 읽는 사람이 우연히 마주쳐야 찾을 수 있다.
- **Dependent Functions**: 한 함수가 다른 함수를 호출하면 둘을 세로로 가까이 두고, 가능하면 호출하는 쪽을 위에 둔다. 덧붙여, 잘 알려진 기본값 같은 상수는 저수준 함수에 묻지 말고 그 값을 아는 게 자연스러운 고수준 위치에서 인수로 내려보낸다 [G35].
- **Conceptual Affinity**: 개념적 친화도(conceptual affinity)가 강할수록 세로 거리를 좁힌다. 친화도는 직접 의존(함수 호출, 변수 사용)뿐 아니라, 이름 체계가 같고 같은 일을 조금씩 달리 하는 함수들(예: 오버로드 묶음) 사이에서도 생긴다. 서로 호출하는지는 부차적이며, 호출하지 않아도 모아 둔다.

**왜**

- 함수 사이를 오르내리고 상속 사슬을 거슬러 정의를 찾다 보면, 시스템을 이해하는 데 쓸 시간과 정신력을 조각의 위치를 찾고 기억하는 데 쓰게 된다.
- 잘 설계된 클래스에서는 인스턴스 변수를 대부분의(또는 모든) 메서드가 쓰므로 맨 위에 두어도 거리가 늘지 않는다. 호출되는 함수가 곧 아래에 나온다는 규칙을 꾸준히 지키면 독자는 그 순서를 믿고 읽는다.

```java
// Bad: 도우미가 호출자보다 위에 있고, 기본값 2가 저수준 함수에 묻혀 있다
public class ReservationService {
    private int resolveGuestCount(BookingRequest request) {
        return request.guestCount() > 0 ? request.guestCount() : 2;
    }
    public Reservation reserve(BookingRequest request) {
        return new Reservation(request.roomId(), resolveGuestCount(request));
    }
}

// Good: 호출자가 위, 호출되는 함수가 가까이 아래. 기본값은 위에서 내려보낸다
public class ReservationService {
    private static final int DEFAULT_GUEST_COUNT = 2;

    public Reservation reserve(BookingRequest request) {
        int guests = resolveGuestCount(request, DEFAULT_GUEST_COUNT);
        return new Reservation(request.roomId(), guests);
    }

    private int resolveGuestCount(BookingRequest request, int defaultCount) {
        return request.guestCount() > 0 ? request.guestCount() : defaultCount;
    }
}
```

## Vertical Ordering — 고수준에서 저수준으로 내려가게

**어떻게**

- 일반적으로 함수 호출 의존성이 아래를 향하게 한다. 호출되는 함수를 호출하는 함수 아래에 둔다. 가장 중요한 개념을 세부를 최소한으로 줄여 먼저 보여 주고, 저수준 세부는 마지막에 둔다.

**왜**

- 고수준에서 저수준으로 흐르므로 처음 몇 함수만 훑어도 세부에 빠지지 않고 요지를 얻는다. 함수를 사용 전에 정의(또는 선언)하게 하는 Pascal, C, C++과는 정반대 순서다(원서 각주).

## Horizontal Formatting — 줄은 짧게

**어떻게**

- 줄을 짧게 유지하려고 노력한다. 저자는 100자, 나아가 120자까지는 반대하지 않지만 그 이상은 아마 부주의라고 본다. 저자 개인의 한도는 120자다. 글꼴을 아주 작게 줄여 화면에 200자를 넣는 식으로 긴 줄을 만들지 않는다.

**왜**

- 수치의 근거는 앞의 7개 프로젝트에서 잰 줄 길이 분포다. 줄은 대부분 짧았고(20~60자가 합쳐 약 40%, 10자 미만도 30% 정도) 80자를 넘으면 급격히 줄었다. 프로그래머는 분명히 짧은 줄을 선호한다.
- 80자라는 옛 Hollerith 한도는 다소 임의적이다. 저자는 예전에 오른쪽 스크롤이 없어야 한다는 규칙을 따랐지만, 요즘 모니터는 너무 넓어 그 기준만으로는 부족하다고 본다.

## Horizontal Openness and Density / Horizontal Alignment — 공백으로 관계를 보여 주되, 정렬하지 않는다

**어떻게**

- 할당 연산자 양옆에 공백을 둬 좌변과 우변을 분명히 가른다.
- 함수 이름과 여는 괄호 사이에는 공백을 두지 않는다. 쉼표 뒤에는 공백을 둬 인수가 서로 별개임을 드러낸다.
- 공백으로 연산자 우선순위를 강조할 수 있다. 우선순위가 높은 곱셈의 피연산자끼리는 붙이고, 낮은 덧셈·뺄셈 항 사이는 띄운다. 단, 대부분의 재포맷 도구는 우선순위를 모른 채 모든 연산자에 같은 간격을 적용하므로 이 간격은 재포맷하면 사라지기 쉽다.
- **Horizontal Alignment**: 선언의 변수 이름이나 할당문의 우변을 세로로 맞추려고 공백을 넣지 않는다. 정렬하고 싶을 만큼 목록이 길다면 문제는 정렬이 아니라 목록의 길이다. 길게 늘어선 필드 선언은 클래스를 쪼갤 신호로 본다.

**왜**

- 수평 공백은 강하게 연관된 것은 묶고 약하게 연관된 것은 떼어 놓는다. 함수와 인수는 밀접하므로 붙여야 한 덩어리로 보인다.
- 정렬은 엉뚱한 것을 강조해 진짜 의도에서 눈을 돌린다. 선언 목록에서는 타입을 건너뛰고 이름만, 할당 목록에서는 할당 연산자를 건너뛰고 우변만 훑게 된다. 게다가 자동 포매터가 대개 이런 정렬을 없앤다.

```java
// Bad: 간격이 관계를 드러내지 못하고, 덧셈이 먼저인 것처럼 보인다
long subtotal=sumPrices (items,priceTable);
long payable = subtotal+shippingFee * boxCount - discount;
// Good
long subtotal = sumPrices(items, priceTable);
long payable = subtotal + shippingFee*boxCount - discount;
```

## Indentation — 스코프 계층을 들여쓰기로 보여 준다

**어떻게**

- 소스 파일은 개요(outline)와 비슷한 스코프 계층이다. 파일 수준 문장(대부분의 클래스 선언)은 들여쓰지 않고, 클래스 안 메서드는 한 단계, 메서드 구현은 다시 한 단계, 블록은 감싸는 블록보다 한 단계 더 들여쓴다.
- **Breaking Indentation**: 짧은 if 문, 짧은 while 루프, 짧은 함수라도 스코프를 한 줄로 접지 않고 펼쳐서 들여쓴다.
- **Dummy Scopes**: 본문이 빈 while·for 문은 되도록 피한다. 피할 수 없다면 빈 본문을 while·for 줄 끝에 붙이지 말고 자기 줄에 드러낸다. 원서 본문은 빈 본문을 들여쓰고 중괄호로 감싸라고 하고, 원서 예시는 중괄호 없이 `;`만 다음 줄에 들여써 둔다.

**왜**

- 프로그래머는 줄의 왼쪽 위치로 스코프를 판단하고, 지금 상관없는 if·while 본문을 건너뛰며, 새 메서드·변수·클래스를 왼쪽에서 찾는다. 들여쓰기가 없으면 사람이 읽기가 사실상 불가능하다.
- 저자는 짧은 스코프를 한 줄로 접었다가 거의 항상 되돌아가 들여쓰기를 되살렸다. while 문 줄 끝에 조용히 붙은 세미콜론에는 셀 수 없이 속았다.

```java
// Bad: 메서드를 한 줄로 접었고, 빈 루프 본문 `;`이 while 줄 끝에 숨어 있다
public void releaseExpiredHolds() {while (holdQueue.releaseNextExpired() != null);}

// Good: 스코프를 펼쳐 들여쓰고, 빈 본문을 자기 줄의 중괄호로 드러낸다
public void releaseExpiredHolds() {
    while (holdQueue.releaseNextExpired() != null) {
    }
}
```

## Team Rules — 팀 규칙이 개인 취향에 앞선다

**어떻게**

- 팀은 형식 스타일 하나에 합의하고 모든 팀원이 그 스타일을 쓴다.
- 중괄호 위치, 들여쓰기 크기, 클래스·변수·메서드 명명 방식 등을 정해 IDE 코드 포매터에 넣고 계속 지킨다. 저자의 FitNesse 팀(2002)은 이 합의에 약 10분을 썼고, 저자는 자기 선호가 아닌 팀 규칙을 따랐다.
- **Uncle Bob's Formatting Rules**: 저자는 자기 규칙을 문서 대신 예시 코드(Listing 5-6)로 보여 주며, 코드가 최고의 코딩 표준 문서라고 본다. 그 코드에서는 필드가 맨 위에 빈 줄 없이 모여 있고, 메서드 사이마다 빈 줄이 있고, private 도우미가 호출하는 함수 아래에 오며, getter끼리 모여 있다.

**왜**

- 절 제목 Team Rules는 '팀 규칙'과 '팀이 결정권을 쥔다'를 겹친 말장난이다. 저마다 좋아하는 형식이 있어도 팀에서 일한다면 "then the team rules" (p. 90).
- 좋은 소프트웨어 시스템은 잘 읽히는 문서의 집합이다. 독자는 한 파일에서 본 형식 표현이 다른 파일에서도 같은 뜻이라고 믿을 수 있어야 한다. 개인 스타일이 뒤섞이면 소스 코드에 복잡성만 더해지고, 의견이 엇갈리는 여러 사람이 쓴 코드처럼 보인다.

## 체크리스트

- [ ] 파일 위쪽만 읽어도 무엇을 하는 클래스인지 알 수 있고, 세부 구현은 아래쪽에 있는가?
- [ ] 파일이 대략 200줄 안팎이고 500줄을 크게 넘지 않는가? 필드 목록이 정렬하고 싶어질 만큼 길지 않은가(길다면 클래스를 나눴는가)?
- [ ] 개념 사이에 빈 줄이 있고, 밀접한 줄은 빈 줄·무의미한 주석 없이 붙어 있는가?
- [ ] 호출하는 함수가 위에, 호출되는 함수가 그 가까이 아래에 있는가? 비슷한 일을 하는 함수끼리 모여 있는가?
- [ ] 지역 변수는 첫 사용 위치 가까이, 인스턴스 변수는 클래스 맨 위 한곳에 있는가? 잘 알려진 기본값이 저수준 함수에 묻혀 있지 않은가?
- [ ] 줄이 지나치게 길지 않은가(저자 한도 120자, 팀 규칙이 있으면 그것을 따른다)?
- [ ] 정렬용 공백, 한 줄로 접은 스코프, 줄 끝에 숨은 빈 루프 본문(`;`)이 없는가?
- [ ] 프로젝트(팀)의 형식 규칙과 포매터 설정을 따랐는가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)): `G10` Vertical Separation, `G11` Inconsistency, `G24` Follow Standard Conventions, `G35` Keep Configurable Data at High Levels, `C3` Redundant Comment
- [chapter_03_functions.md](chapter_03_functions.md) — The Stepdown Rule: 위에서 아래로 추상화 수준이 한 단계씩 내려가게(원서는 Chapter 3의 코드가 Vertical Ordering의 더 좋은 예일 수 있다고 한다)
- [chapter_04_comments.md](chapter_04_comments.md) — 쓸모없는 주석이 세로 밀도를 깨뜨린다
- [chapter_10_classes.md](chapter_10_classes.md) — 클래스 크기, 길게 늘어선 필드 목록은 분리 신호

## 원서 밖 보충

- 원서 밖 내용: 오늘날에는 google-java-format, Spotless, Checkstyle, `.editorconfig` 같은 도구로 팀 형식 규칙을 저장소에 두고 빌드·CI에서 강제하는 방식이 흔하다. 원서의 'IDE 포매터에 규칙을 넣는다'를 팀 전체로 넓힌 형태다.
- 원서 밖 내용: 예컨대 Google Java Style Guide는 if·else·for·do·while 본문이 한 문장이거나 비어 있어도 중괄호를 요구하고(빈 블록은 `{}`로 써도 된다) 줄 길이를 100자로 둔다. 줄 길이 한도는 가이드마다 80·100·120자 등으로 다르다. 원서 Listing 5-6은 한 줄 본문에 중괄호를 생략하고, Dummy Scopes 예시도 `;`만 다음 줄에 둔다. 프로젝트에 정해진 규칙이 있으면 그것을 따른다.
- 원서 밖 내용: google-java-format 같은 포매터와 Checkstyle 공백 검사는 이항 연산자 양옆에 똑같이 공백을 두게 하므로, 우선순위를 드러내는 간격(`a*b + c`)은 유지되지 않는다. 이런 도구가 설정된 프로젝트에서는 그 결과를 따른다.
