# Chapter 4: Comments — 주석

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 4, pp. 53–74
> 한 줄 요약: 주석은 코드로 의도를 표현하지 못한 부분을 메우는 차선책이므로, 먼저 코드로 말하게 하고 꼭 필요한 주석만 정확하게 남긴다.

## 핵심

- 주석을 쓰고 싶어지면 먼저 이름·함수·설명 변수로 같은 말을 할 수 있는지 시도한다. 코드로 말할 수 있으면 주석을 쓰지 않는다.
- 지저분한 코드를 주석으로 해명하지 말고 코드를 정리한다.
- 주석은 코드와 따로 낡아 간다. 부정확한 주석은 주석이 없는 것보다 해롭고, 정확한 정보는 코드에만 있다.
- 남길 만한 주석: 법적 고지, 정보 제공, 의도 설명, 바꿀 수 없는 코드의 의미 해설, 결과 경고, TODO, 중요성 강조, 공개 API의 Javadoc.
- 지울 주석: 웅얼거림(대충 단 주석), 코드 되풀이와 잡음, 부정확한 설명, 규칙 때문에 단 Javadoc, 변경 이력·바이라인, 주석 처리한 코드, HTML, 먼 곳의 정보, 과도한 배경 설명. 배너와 닫는 괄호 주석도 대개 지운다.
- 주석을 쓰기로 했다면 시간을 들여 정확하게, 바로 옆 코드에 대해, 코드와의 연결이 보이게 쓴다.
- 누가·언제·무엇을 바꿨는지와 옛 코드는 소스 관리 시스템에 맡긴다. 단, 코딩 표준이 요구하는 법적 저작권·저자 고지는 남긴다.

## Comments Do Not Make Up for Bad Code — 주석으로 나쁜 코드를 메우지 않는다

**어떻게**

- 모듈이 헷갈리고 엉망이라는 걸 알면서 "주석을 달아 두자"는 생각이 들면, 그 시간에 코드를 정리한다.
- 주석이 필요해 보이는 순간마다 코드로 표현할 방법이 없는지 먼저 따져 본다. 코드로 표현했다면 잘한 것이고, 주석을 썼다면 표현에 실패한 것으로 여긴다.
- 주석이 꼭 필요할 때는 쓰되, 개수를 줄이는 데 힘을 쓴다.

**왜**

- 저자는 주석을 기껏해야 필요악으로 본다. 언어가 충분히 표현력 있거나 우리가 그것을 능숙하게 다룬다면 주석은 거의 필요 없다. Kernighan과 Plaugher의 말을 빌린 장 첫머리 인용 "Don't comment bad code—rewrite it." (p. 53)이 이 태도를 요약한다.
- 코드는 옮겨지고 쪼개지고 다시 합쳐지지만 주석은 따라가지 못한다. 그래서 주석은 오래될수록, 설명하는 코드에서 멀어질수록 틀리기 쉽다(예: 상수와 그 예시 주석 사이에 나중에 필드가 끼어든다).
- 주석을 꼼꼼히 관리하는 규율도 옳지만, 저자는 그 에너지를 주석이 필요 없을 만큼 코드를 명료하게 만드는 데 쓰자고 한다.
- 틀린 주석은 호출자에게 잘못된 기대를 심고 이미 버린 규칙을 따르게 하므로 주석이 없는 것보다 해롭다.
- 주석을 덧붙여도 복잡한 코드는 그대로 복잡하다. 독자에게는 주석이 적더라도 명료한 코드가 낫다.

## Explain Yourself in Code — 코드로 의도를 설명한다

**어떻게**

- 쓰려던 주석과 같은 말을 하는 이름의 함수를 만든다. 대부분은 몇 초만 생각하면 된다.
- 플래그 검사나 여러 조건이 얽힌 식은 의도를 드러내는 메서드로 감싼다.

**왜**

- 코드가 설명에 서툰 경우가 있다고 해서 코드로 설명하기를 포기하지 않는다. 대부분의 의도는 함수 이름으로 옮길 수 있다.

```java
// Bad
// VIP 회원이 기준 금액 이상 주문하면 배송비를 받지 않는다
if (order.member().grade() == Grade.VIP && order.total() >= FREE_SHIPPING_MIN_TOTAL) {
    shipping.waiveFee();
}

// Good
if (order.qualifiesForFreeShipping()) {
    shipping.waiveFee();
}

// Order 안
boolean qualifiesForFreeShipping() {
    return member.grade() == Grade.VIP && total() >= FREE_SHIPPING_MIN_TOTAL;
}
```

## Good Comments — 좋은 주석

아래 유형은 비용을 치를 만한 주석이다. 그래도 주석 없이 해결할 길을 먼저 찾고, 그런 길이 없을 때 쓴다.

| 유형 | 언제 쓰나 | 주의 |
|---|---|---|
| Legal Comments | 회사 코딩 표준이 요구하는 저작권·저자 고지를 파일 첫머리에 둔다. | 계약서나 법률 전문을 넣지 않는다. 가능하면 표준 라이선스나 외부 문서를 가리킨다. |
| Informative Comments | 추상 메서드의 반환값, 정규식이 맞추려는 날짜 형식처럼 기본 정보를 준다. | 함수 이름으로 전할 수 있으면 이름을 바꿔 주석을 없앤다. 형식 변환 코드는 전용 클래스로 옮기면 주석이 필요 없어질 수 있다. |
| Explanation of Intent | 구현 정보를 넘어 결정의 의도를 밝힌다(예: 왜 다른 타입보다 항상 크다고 판정하는지, 왜 스레드를 대량으로 띄우는지). | 구현 설명이 아니라 결정의 이유를 쓴다. 목표는 독자의 동의가 아니라, 작성자가 무엇을 하려 했는지 알리는 것이다. |
| Clarification | 모호한 인수나 반환값의 뜻을 읽기 쉽게 풀어 준다. 표준 라이브러리나 고칠 수 없는 코드일 때 쓸모 있다. | 일반적으로는 인수·반환값 자체를 명확하게 만드는 편이 낫다. 해설 주석은 틀릴 위험이 크고 검증하기 어렵다. 더 나은 방법이 없는지 확인하고, 정확한지 한 번 더 확인한다. |
| Warning of Consequences | 실행이 매우 오래 걸리는 테스트, 스레드 안전하지 않은 객체처럼 다른 개발자가 알아야 할 결과를 경고한다. | 저자도 더 나은 해법이 있을 수 있다고 인정하지만, 경고 주석 자체는 타당하다고 본다. "효율"을 앞세워 정적 초기화로 공유하려는 사람을 막아 주기 때문이다. 테스트를 끌 때 원서는 오늘날이라면 JUnit 4의 `@Ignore("이유")`를 쓴다고 한다. |
| TODO Comments | 지금은 할 수 없지만 해야 할 일을 남긴다: 임시 구현인 이유와 앞으로의 모습, 폐기 기능 삭제, 다른 사람에게 검토·이름 제안 요청, 예정된 일에 달린 변경. | 나쁜 코드를 남겨 두는 핑계가 되지 않는다. 코드가 TODO로 뒤덮이지 않게 주기적으로 훑어 없앨 수 있는 것은 없앤다. |
| Amplification | 대수롭지 않아 보이지만 사실 중요한 코드를 강조한다. | 빠뜨리면 버그가 나는 이유를 함께 적는다. |
| Javadocs in Public APIs | 공개 API를 만든다면 좋은 Javadoc을 반드시 쓴다. API 사용자는 문서에 크게 기댄다. 표준 Java 라이브러리의 Javadoc 없이 Java 프로그램을 짜기 어려운 것이 그 예다. | Javadoc도 다른 주석처럼 틀리거나, 먼 곳의 정보를 담거나, 부정직할 수 있다. 이 장의 나머지 조언을 그대로 적용한다. |

```java
// Bad: 이름으로 전할 수 있는 정보를 주석에 둔다 (Informative)
// 결제 대기 상태인 주문 목록을 반환한다
protected abstract List<Order> orders();

// Good
protected abstract List<Order> ordersAwaitingPayment();
```

```java
// Good: 주석이 코드가 못 하는 말을 한다 (차례로 Warning of Consequences, Amplification, TODO)
public PaymentRequest create(Order order) throws NoSuchAlgorithmException {
    // MessageDigest는 스레드 안전하지 않으므로 요청마다 새로 만든다.
    // 성능을 이유로 static 필드에 두고 공유하지 말 것.
    MessageDigest digest = MessageDigest.getInstance("SHA-256");

    // 대문자 변환이 중요하다: 결제사는 소문자 통화 코드를 받으면 요청을 거절한다.
    String currency = order.currencyCode().toUpperCase(Locale.ROOT);

    // TODO 결제사 v2 API로 옮기면 이 해시 생성 코드를 지운다.
    byte[] idDigest = digest.digest(order.id().getBytes(StandardCharsets.UTF_8));
    return new PaymentRequest(order.id(), currency, idDigest);
}

// Good (Clarification): 바꿀 수 없는 표준 API의 반환값 규칙만 풀어 주고, 계산은 설명 변수에 맡긴다
int found = Collections.binarySearch(sortedSkus, sku);
if (found < 0) {
    int insertionPoint = -(found + 1); // binarySearch는 못 찾으면 -(삽입 위치) - 1을 돌려준다
    sortedSkus.add(insertionPoint, sku);
}
```

## Bad Comments — 나쁜 주석

대부분의 주석이 여기에 속한다. 이런 주석은 허술한 코드나 미흡한 결정을 감싸 줄 뿐, 읽는 사람에게 전하는 것이 없다.

| 유형 | 증상 | 대신 할 것 / 이유 |
|---|---|---|
| Mumbling | 해야 할 것 같아서, 혹은 절차가 요구해서 대충 단 주석. 작성자만 뜻을 안다(예: 빈 catch 블록에 "설정 파일이 없으면 기본값을 쓴다"만 적어, 기본값을 누가 언제 로드하는지, 아직 쓰지 않은 코드에 대한 메모인지 알 수 없다). | 쓰기로 했다면 최선의 주석이 되도록 시간을 들인다. 빈 catch에 주석을 달 때는 무시해도 되는 이유와 그 뒤의 상태를 구체적으로 쓴다. 뜻을 알려고 다른 모듈을 뒤져야 하는 주석은 전달에 실패한 것이다. |
| Redundant Comments | 코드 내용을 다시 말하는 헤더 주석. 코드보다 읽는 데 오래 걸린다. 필드마다 이름을 되풀이한 Javadoc도 같다. | 지운다. 근거나 의도를 더하지 않으면서 코드보다 덜 정확해, 독자가 코드를 제대로 읽지 않고 넘어가게 만든다. |
| Misleading Comments | 선의로 썼지만 정확하지 않은 설명. | 실제 동작과 맞추거나 지운다. 미묘한 오정보가 호출자에게 잘못된 기대를 심어 긴 디버깅으로 이끈다(아래 예). |
| Mandated Comments | 모든 함수에 Javadoc, 모든 변수에 주석을 요구하는 규칙. | 그런 규칙을 두지 않는다. 결과물은 코드를 가리는 잡음이자 거짓과 오해의 씨앗이다. |
| Journal Comments | 모듈을 고칠 때마다 파일 첫머리에 쌓는 변경 기록. | 완전히 지운다. 소스 관리 시스템이 없던 시절에나 이유가 있던 관행이다. |
| Noise Comments | "기본 생성자", "일자를 반환한다"처럼 뻔한 말을 되풀이하거나, 짜증을 쏟아낸 주석. | 지운다. 잡음 주석은 결국 눈이 건너뛰게 되고, 주변 코드가 바뀌면 거짓이 된다. 반면 예외를 일부러 무시하는 이유를 밝힌 주석은 적절하므로 남긴다. 짜증이 난다면 구조를 개선하라는 신호다(아래 예). |
| Scary Noise | 필드마다 이름만 되풀이하는 Javadoc. 복사·붙여넣기 실수가 섞이기 쉽다. | 지운다. 작성자조차 주의를 기울이지 않은 주석에서 독자가 얻을 것은 없다. |
| Don't Use a Comment When You Can Use a Function or a Variable | 복잡한 식 위에 그 의미를 풀어 쓴 주석. | 설명 변수나 함수로 나눠 주석을 없앤다(아래 예). |
| Position Markers | `// Actions /////////` 같은 배너. | 대개 지운다. 특히 끝의 슬래시 행렬은 잡음이다. 함수를 배너 아래 모으는 게 의미 있는 드문 경우에만 아껴 쓴다. 남용하면 배경 잡음이 되어 무시된다. |
| Closing Brace Comments | `} // while`, `} // try` 같은 닫는 괄호 주석. | 길고 깊게 중첩된 함수라면 의미가 있을 수 있지만, 작은 함수에서는 잡음이다. 달고 싶어지면 함수를 줄인다. |
| Attributions and Bylines | `/* 김OO 추가 */` 같은 작성자 표기. | 소스 관리 시스템에 맡긴다. 누구에게 물어볼지 알리려는 의도라도, 이런 표기는 수년간 남아 점점 부정확해진다. |
| Commented-Out Code | 주석으로 막아 둔 옛 코드. | 그냥 지운다. 남들은 중요해서 남긴 줄 알고 감히 지우지 못해 계속 쌓인다. 소스 관리 시스템이 기억하므로 잃지 않는다. |
| HTML Comments | 주석 안의 HTML 태그·엔티티. | 쓰지 않는다. 주석을 가장 읽기 쉬워야 할 편집기에서 읽기 어려워진다. 웹 페이지용 꾸밈은 Javadoc 같은 추출 도구의 몫이다. |
| Nonlocal Information | 주변 코드가 아니라 시스템의 먼 곳(예: 이 함수가 통제하지 않는 기본 포트 값)을 설명. | 주석은 바로 옆 코드만 설명한다. 먼 곳의 코드가 바뀔 때 이 주석도 고쳐진다는 보장이 없다. |
| Too Much Information | 흥미로운 역사나 상관없는 세부(예: 표준 문서 본문을 통째로 옮김). | 독자에게 필요한 것만 남긴다(예: 표준 문서 번호). |
| Inobvious Connection | 주석과 코드의 관계가 불분명해 주석에 또 설명이 필요한 경우(예: 배열 크기 계산식의 숫자들이 주석의 어느 말에 대응하는지 알 수 없음). | 주석과 코드를 함께 보면 무엇을 가리키는지 바로 알 수 있게 쓴다. 주석의 목적은 스스로 설명하지 못하는 코드를 설명하는 것이다. |
| Function Headers | 짧은 함수 위의 설명 헤더. | 짧은 함수에는 설명이 별로 필요 없다. 한 가지 일만 하는 작은 함수라면 잘 고른 이름이 대개 헤더 주석보다 낫다. |
| Javadocs in Nonpublic Code | 외부에 공개하지 않는 클래스·함수의 Javadoc. | 쓰지 않는다. 내부 코드의 Javadoc 페이지는 대체로 쓸모없고, 격식만 더해 산만하게 만든다. |

```java
// Bad: 코드를 되풀이하는 데다 미묘하게 틀렸다 (Redundant + Misleading)
// 재고가 있으면 회원 몫으로 확보한다.
public void reserve(Sku sku, Member member) {
    if (inventory.available(sku) > 0) {
        inventory.hold(sku, member);
    } else {
        waitlist.add(sku, member);
    }
}
// 실제 동작: 재고가 없으면 회원을 대기열에 넣는다. 주석만 믿은 호출자는 재고가 없으면
// 아무 일도 일어나지 않는다고 여기고, 회원에게 간 대기 알림의 원인을 찾아 헤맨다.

// Good: 주석을 지우고, 이름이 실제 동작을 말하게 한다
public void holdOrWaitlist(Sku sku, Member member) {
    if (inventory.available(sku) > 0) {
        inventory.hold(sku, member);
    } else {
        waitlist.add(sku, member);
    }
}
```

```java
// Bad: 깊은 중첩에 지쳐 짜증을 주석으로 쏟아낸다 (Noise)
for (Order order : orders) {
    if (order.isPaid()) {
        if (!order.isShipped()) {
            if (warehouse.hasStock(order.sku())) {
                // 끝없는 if... 누가 좀 살려 줘
                warehouse.ship(order);
            }
        }
    }
}

// Good: 짜증의 원인인 중첩 조건을 함수로 추출한다
for (Order order : orders) {
    if (isReadyToShip(order)) {
        warehouse.ship(order);
    }
}

private boolean isReadyToShip(Order order) {
    return order.isPaid() && !order.isShipped() && warehouse.hasStock(order.sku());
}
```

```java
// Bad: 식의 의미를 주석으로 풀어 쓴다
// 주문한 상품이 회원 등급에서 살 수 있는 카테고리에 속하는가?
if (member.getGrade().getPurchasableCategories().contains(line.getProduct().getCategory()))

// Good: 설명 변수로 같은 말을 한다
Set<Category> purchasableCategories = member.getGrade().getPurchasableCategories();
Category orderedCategory = line.getProduct().getCategory();
if (purchasableCategories.contains(orderedCategory))
```

## Example — 리팩터링 예시의 교훈

- 원서 예제에서는 한때 "문서화가 잘 됐다"고 여겼을 주석투성이 모듈을 정리하자 주석이 두 개만 남았다: 독자를 알고리즘으로 안내하는 개요, 그리고 어떤 이름이나 구조로도 드러내지 못한 설계 근거(반복 한계를 제곱근으로 둔 이유). 저자는 그 최적화가 남들이 이해하는 수고만큼 가치 있는지 스스로 의문을 제기한다.

## 체크리스트

- [ ] 주석을 쓰기 전에 함수 이름이나 설명 변수로 바꿔 보았는가?
- [ ] 지저분한 코드를 주석으로 해명하는 대신 코드를 정리했는가?
- [ ] 주석이 지금 코드의 동작과 일치하는가?
- [ ] 코드를 고친 곳 근처의 주석도 갱신하거나 지웠는가?
- [ ] 주석이 다른 곳에서 정한 값(기본값·설정)이 아니라 바로 옆 코드를 설명하는가?
- [ ] 남은 주석마다 코드가 말하지 못하는 정보(의도·경고·근거)를 더하는가?
- [ ] 주석 처리한 코드, 변경 이력, 바이라인(법적 고지 제외), 습관적인 배너·닫는 괄호 주석, HTML을 지웠는가?
- [ ] TODO마다 지금 할 수 없는 이유가 있는가?
- [ ] 공개 API에는 정확한 Javadoc이 있는가?
- [ ] Javadoc을 공개 API에만 두었는가?
- [ ] 주석과 코드를 같이 보면 무엇을 가리키는지 바로 보이는가?
- [ ] 고칠 수 없는 API에 단 해설 주석이 정확한지 다시 검증했는가?

## 관련

- Chapter 17 휴리스틱: `C1` Inappropriate Information, `C2` Obsolete Comment, `C3` Redundant Comment, `C4` Poorly Written Comment, `C5` Commented-Out Code, `G12` Clutter, `G19` Use Explanatory Variables, `G20` Function Names Should Say What They Do
- [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) — 주석 대신 의도를 드러내는 이름
- [chapter_03_functions.md](chapter_03_functions.md) — 작은 함수, 함수 추출, 서술적인 이름이 헤더 주석을 대신한다
- [chapter_05_formatting.md](chapter_05_formatting.md) — 쓸모없는 주석이 밀접한 코드 사이를 벌려 놓는다(Vertical Density)
- [chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md) — `C1`~`C5`와 `G12` Clutter의 판정 기준과 이유

## 원서 밖 보충

- (원서 밖) JUnit 5에서는 `@Ignore` 대신 `@Disabled("이유")`로 테스트를 끈다.
- (원서 밖) 원서의 스레드 안전 경고 예시는 `SimpleDateFormat`을 다루며, 저자도 더 나은 해법의 여지를 인정한다. 그 한 예로 Java 8 이후에는 불변·스레드 안전한 `DateTimeFormatter`로 바꾸면 경고 자체가 필요 없다. 경고 주석을 쓰기 전에 안전한 대체 API가 있는지 본다.
- (원서 밖) JDK 23(JEP 467)부터 `///`로 시작하는 Markdown 문서 주석을 쓸 수 있어, Javadoc에 HTML을 직접 넣을 일이 줄었다.
- (원서 밖) 작성자·변경 이력은 `git blame`·`git log`로 확인하고, TODO에는 이슈 번호를 붙여(`// TODO(ORDER-123): ...`) 추적하는 팀이 많다. SonarQube 같은 정적 분석 도구는 주석 처리한 코드를 경고로 잡는다.
- (원서 밖) 코딩 에이전트가 코드를 고칠 때는 바뀐 코드 근처의 주석도 같이 고치거나 지운다. 남겨 둔 옛 주석이 바로 이 장이 경고하는 "거짓말하는 주석"이 된다.
