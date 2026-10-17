# Chapter 12: Emergence — 창발성

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 12, pp. 171–176 · by Jeff Langr
> 한 줄 요약: Kent Beck의 Simple Design 네 규칙(테스트 통과, 중복 제거, 의도 표현, 클래스·메서드 최소화)을 중요도 순으로 지키면 좋은 설계가 드러나기 쉬워진다.

## 핵심

- 네 규칙은 중요도 순이다(테스트 > 중복 제거 > 표현력 > 클래스·메서드 수 최소화). 클래스·메서드 수를 줄이려고 앞의 세 규칙을 희생하지 않는다.
- 테스트할 수 있게 만들려는 압력이 설계를 SRP(Single Responsibility Principle)를 지키는 작은 단일 목적 클래스와, DIP(Dependency Inversion Principle)·의존성 주입으로 결합도(coupling)를 낮춘 구조 쪽으로 민다.
- 테스트가 있으니 몇 줄 쓸 때마다 멈추고 설계를 돌아보며 두려움 없이 리팩터링한다. 규칙 2~4는 이 단계에서 적용한다.
- 몇 줄짜리 중복도 없앤다. 똑같은 줄만이 아니라 비슷한 줄과 구현의 중복도 중복이다.
- 돌아가게 만든 뒤 바로 다음 문제로 넘어가지 말고 다음 독자(아마 나 자신)를 위해 다듬는다. 다만 작게 만들려다 클래스·메서드를 지나치게 늘리지 않는다.

## Getting Clean via Emergent Design — 창발적 설계로 깨끗해지기

**어떻게**

- Kent Beck이 말하는 "단순한" 설계는 다음 규칙을 따른다(중요도 순).
  1. Runs all the tests — 모든 테스트를 실행하고 통과한다
  2. Contains no duplication — 중복이 없다
  3. Expresses the intent of the programmer — 프로그래머의 의도를 표현한다
  4. Minimizes the number of classes and methods — 클래스와 메서드 수를 최소로 줄인다

**왜**

- 많은 개발자가 이 네 규칙이 잘 설계된 소프트웨어를 만드는 데 크게 도움이 된다고 느낀다. 작업하면서 규칙을 따르면 코드의 구조와 설계가 잘 보이고 SRP나 DIP 같은 원칙도 적용하기 쉬워져, 좋은 설계가 창발(emergence)하기 쉽다. 단순한 규칙이 경험을 대신하지는 못한다. 그래도 익히는 데 몇 년씩 걸리는 원칙과 패턴을 따르도록 이끌어 준다.

## Simple Design Rule 1: Runs All the Tests — 모든 테스트를 실행하라

**어떻게**

- 시스템을 철저히 테스트하고 모든 테스트가 늘 통과하게 유지한다(이런 시스템이 testable하다).
- 테스트를 쓰기 어렵게 만드는 강한 결합(tight coupling)은 DIP, 의존성 주입, 인터페이스, 추상화로 줄인다.

**왜**

- 설계가 아무리 그럴듯해도 의도대로 동작하는지 간단히 확인할 방법이 없으면 그 가치는 의심스럽다. 테스트할 수 없는 시스템은 검증할 수 없고, 검증할 수 없는 시스템은 배포하지 말아야 한다고 볼 수 있다(저자도 단정하지는 않는다).
- SRP를 지키는 클래스가 테스트하기 쉽고, 결합도가 높으면 테스트를 쓰기 어렵다. 그래서 테스트를 많이 쓸수록 작은 단일 목적 클래스와 결합도를 낮추는 원칙·도구 쪽으로 밀려간다. 테스트를 갖추고 계속 돌리라는 단순한 규칙이 객체 지향의 주요 목표인 낮은 결합도와 높은 응집도(cohesion)로 이어진다. "Writing tests leads to better designs." (p. 172)

## Simple Design Rules 2–4: Refactoring — 리팩터링

**어떻게**

- 테스트를 갖췄으면 코드를 점진적으로 리팩터링한다. 몇 줄 추가할 때마다 멈추고 새 설계를 돌아본다. 나빠졌다면 정리하고, 테스트를 돌려 아무것도 깨지지 않았음을 확인한다.
- 이 단계에서 좋은 설계 지식을 무엇이든 적용한다. 응집도 높이기, 결합도 낮추기, 관심사 분리, 시스템 관심사의 모듈화, 함수와 클래스를 작게 만들기, 더 나은 이름 고르기 등이다. Simple Design의 나머지 세 규칙(중복 제거, 표현력, 클래스·메서드 최소화)도 여기서 적용한다.

**왜**

- 테스트가 있으면 코드를 정리하다 망가뜨릴지 모른다는 두려움이 사라진다.

## No Duplication — 중복을 없애라

**어떻게**

- 몇 줄짜리 중복도 없앤다. 똑같아 보이는 줄은 당연히 중복이다. 비슷한 줄은 더 비슷하게 다듬을 수 있는 경우가 많고, 그렇게 맞춘 뒤 공통 부분을 뽑으면 리팩터링하기 쉽다.
- 구현의 중복도 찾는다. 같은 사실을 두 곳에서 따로 관리하지 말고 한쪽을 다른 쪽의 정의에서 파생한다. 예: 품절 플래그를 따로 두지 말고 `isOutOfStock()`을 `availableQuantity() == 0`으로 정의한다.
- 아주 작은 공통부분을 뽑다 보면 SRP 위반이 보인다. 그러면 뽑은 메서드를 다른 클래스로 옮길 수 있다. 노출 범위가 넓어지면 팀의 다른 사람이 그것을 더 추상화해 다른 맥락에서 재사용할 수 있다.
- TEMPLATE METHOD 패턴은 더 높은 수준의 중복을 없애는 흔한 기법이다. 여러 단계로 된 알고리즘이 일부 단계만 다르면, 고정된 순서는 부모 클래스에 두고 달라지는 단계만 자식 클래스가 채운다. 그러면 자식은 알고리즘의 "빈칸", 즉 중복되지 않는 정보만 제공한다.

**왜**

- 중복은 잘 설계된 시스템의 가장 큰 적이다. 추가 작업, 추가 위험, 불필요한 복잡도를 뜻한다.
- 이런 작은 규모의 재사용(reuse in the small)이 시스템 복잡도를 크게 줄일 수 있다. 작은 재사용을 할 줄 알아야 큰 재사용도 이룬다.

```java
// Bad: 두 메서드가 같은 두 줄로 끝난다
public void receive(Sku sku, int quantity) {
    stock.increase(sku, quantity);
    repository.save(stock);
    events.publish(new StockChanged(sku, stock.quantityOf(sku)));
}
public void reserve(Sku sku, int quantity) {
    stock.decrease(sku, quantity);
    repository.save(stock);
    events.publish(new StockChanged(sku, stock.quantityOf(sku)));
}

// Good: 공통 꼬리를 한곳으로 뽑는다(SRP 위반이 보이면 다른 클래스로 옮길 후보)
public void receive(Sku sku, int quantity) { stock.increase(sku, quantity); commitChange(sku); }
public void reserve(Sku sku, int quantity) { stock.decrease(sku, quantity); commitChange(sku); }
private void commitChange(Sku sku) {
    repository.save(stock);
    events.publish(new StockChanged(sku, stock.quantityOf(sku)));
}
```

```java
// Bad: 지역 할증 한 단계만 빼고 기본 요금 → 할증 → 반올림 절차가 같다
public Money domesticFee(Parcel parcel) {
    Money fee = baseFeeByWeight(parcel);
    fee = fee.plus(remoteAreaSurcharge(parcel));
    return roundToTen(fee);
}
public Money overseasFee(Parcel parcel) {
    Money fee = baseFeeByWeight(parcel);
    fee = fee.plus(customsHandlingFee(parcel));
    return roundToTen(fee);
}

// Good: TEMPLATE METHOD. 순서와 공통 단계(private)는 부모에, 할증 계산은 각 자식으로 옮긴다
public abstract class ShippingFeePolicy {
    public Money feeFor(Parcel parcel) {
        Money fee = baseFeeByWeight(parcel);
        fee = fee.plus(regionalSurcharge(parcel));
        return roundToTen(fee);
    }
    protected abstract Money regionalSurcharge(Parcel parcel);
}
public class DomesticShippingFee extends ShippingFeePolicy { @Override protected Money regionalSurcharge(Parcel p) { return remoteAreaSurcharge(p); } }
public class OverseasShippingFee extends ShippingFeePolicy { @Override protected Money regionalSurcharge(Parcel p) { return customsHandlingFee(p); } }
```

## Expressive — 표현하라

**어떻게**

- 좋은 이름을 고른다. 클래스나 함수 이름을 듣고 실제 책임을 확인했을 때 놀라는 일이 없어야 한다. 예: `OrderHelper.run()`보다 `CancelOrderCommand.execute()`.
- 함수와 클래스를 작게 유지한다. 작은 클래스와 함수는 대개 이름 짓기도, 작성하기도, 이해하기도 쉽다.
- 표준 명명법을 쓴다. 디자인 패턴은 대부분 의사소통과 표현력에 관한 것이다. 패턴을 구현한 클래스 이름에 COMMAND, VISITOR 같은 표준 패턴 이름을 넣으면 설계를 짧게 전달할 수 있다.
- 단위 테스트를 표현력 있게 쓴다. 테스트의 주된 목적 중 하나는 예제를 통한 문서(documentation by example) 역할이다. 테스트를 읽으면 클래스가 무엇을 하는지 빨리 알 수 있어야 한다.
- 가장 중요한 것은 표현하려고 노력하는 것이다. 함수와 클래스마다 시간을 조금 들여 더 나은 이름을 고르고, 큰 함수를 작은 함수로 나누고, 만든 것을 돌본다. "Care is a precious resource." (p. 176)

**왜**

- 작성자는 문제를 깊이 알고 있어 자기 코드를 쉽게 이해하지만, 다음 독자(아마 나 자신)는 그만큼 알지 못한다.
- 비용의 대부분은 장기 유지보수에서 나오고 시스템이 복잡할수록 이해하기 어렵고 오해하기 쉽다. 의도가 명확할수록 이해 시간, 변경할 때 생기는 결함, 유지보수 비용이 준다.

## Minimal Classes and Methods — 클래스와 메서드 수를 최소로

**어떻게**

- 중복 제거, 표현력, SRP 같은 기본 개념도 지나치게 적용할 수 있다. 작게 만들려다 아주 작은 클래스와 메서드를 너무 많이 만들지 않는다. 함수와 클래스 개수도 적게 유지한다. 다만 이 규칙은 네 규칙 중 우선순위가 가장 낮으므로, 개수를 줄이려고 테스트, 중복 제거, 표현력을 희생하지 않는다.
- 무의미한 독단(dogmatism)을 거부하고 실용적으로 판단한다. 예: 모든 클래스마다 인터페이스를 만들라는 코딩 표준, 필드와 동작을 항상 데이터 클래스와 동작 클래스로 나누라는 고집.

**왜**

- 클래스와 메서드 수가 많은 것은 때로 이런 독단의 결과다. 목표는 함수와 클래스를 작게 유지하면서 시스템 전체도 작게 유지하는 것이다. 결합도를 낮추려고 인터페이스를 쓰는 것(규칙 1)과, 표준이라서 모든 클래스에 인터페이스를 붙이는 것은 다르다.

```java
// Bad: 결합도를 낮추거나 테스트 대역을 끼울 필요가 없는데도 '모든 클래스에 인터페이스'라는 표준 때문에 만든다
public interface MemberNameFormatter { String format(Member member); }
public class MemberNameFormatterImpl implements MemberNameFormatter { /* format 구현 */ }

// Good: 인터페이스가 필요한 이유(결합도 감소, 테스트)가 없으면 같은 구현을 클래스 하나에 둔다
public class MemberNameFormatter { /* format 구현 */ }
```

## 체크리스트

- [ ] 모든 테스트가 통과하는가? 테스트하기 어렵다면 그 원인(강한 결합, 여러 책임)을 설계에서 고쳤는가?
- [ ] 몇 줄 쓸 때마다 설계가 나빠지지 않았는지 돌아보고, 정리한 뒤 테스트를 다시 돌렸는가?
- [ ] 똑같거나 비슷한 줄, 같은 사실을 두 곳에서 관리하는 구현 중복이 남아 있지 않은가? 일부 단계만 다른 알고리즘의 중복은 TEMPLATE METHOD 같은 기법으로 없애 달라지는 빈칸만 따로 채우게 했는가?
- [ ] 이름만 듣고 책임을 짐작할 수 있는가(돌아가게 만든 뒤 다시 다듬었는가)? 패턴을 썼다면 표준 패턴 이름이 드러나는가?
- [ ] 테스트 이름과 본문만 읽고 대상 클래스가 무엇을 하는지 알 수 있는가?
- [ ] 규칙이라서 만든 인터페이스나 데이터/동작 분리 클래스가 개수만 늘리고 있지 않은가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)): `G5` Duplication, `G16` Obscured Intent, `G30` Functions Should Do One Thing, `N3` Use Standard Nomenclature Where Possible, `T1` Insufficient Tests
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — 테스트가 변경을 가능하게 하고, 테스트도 표현력 있게 쓴다
- [chapter_10_classes.md](chapter_10_classes.md) — SRP, 응집도, 작은 클래스
- [chapter_11_systems.md](chapter_11_systems.md) — 의존성 주입과 관심사 분리
- [chapter_03_functions.md](chapter_03_functions.md) — 작은 함수, 중복 제거
- [chapter_02_meaningful_names.md](chapter_02_meaningful_names.md) — 의도를 드러내는 이름

## 원서 밖 보충

- 중복을 너무 일찍 추상화하면 잘못된 추상화가 굳을 수 있어, 같은 패턴이 세 번째 나올 때 추상화하는 rule of three 같은 경험칙도 널리 쓰인다. 원서는 몇 줄짜리 중복도 없애라고 하므로 이 경험칙은 원서와 다른 관점이다. 둘이 충돌하면 어느 쪽을 따를지 팀 관례로 정한다.
- TEMPLATE METHOD의 빈칸은 상속 대신 Strategy 객체로 주입하기도 하며, Java 8 이후에는 함수형 인터페이스와 람다로 이를 가볍게 쓸 수 있다. 상속을 쓴다면 템플릿 메서드에 `final`을 붙여 자식이 순서를 바꾸지 못하게 하기도 한다.
- Mockito 같은 목 라이브러리는 구체 클래스도 목으로 만들 수 있어, 테스트만을 위해 모든 클래스에 인터페이스를 둘 필요는 줄었다.
