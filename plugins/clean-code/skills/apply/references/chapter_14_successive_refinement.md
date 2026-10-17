# Chapter 14: Successive Refinement — 점진적인 개선

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 14, pp. 193–250
> 한 줄 요약: 명령행 인수 파서 사례로, 깨끗한 코드는 동작하는 초안을 테스트가 통과하는 작은 단계로 다듬어 얻으며, 같은 종류의 기능이 한 클래스 곳곳에 흩어져 엉망이 커지기 시작하면 기능 추가를 멈추고 구조부터 고쳐야 함을 보여 준다.

## 핵심

- 깨끗한 코드는 한 번에 나오지 않는다. 지저분한 초안을 먼저 쓰고 여러 번 다듬는다(successive refinement).
- "It is not enough for code to work." (p. 250) 동작한 뒤 구조를 정리하는 데까지가 작업이다. 엉망은 오래 둘수록 모듈 사이에 숨은 의존이 얽혀 끊기 어려워지므로, 시간이 없다는 이유로 미루지 말고 만든 직후(같은 날, 몇 분 뒤)에 치운다.
- 같은 종류의 기능을 더할 때마다 한 클래스 안의 필드·분기·getter·오류 처리에 수정이 흩어지고 그 클래스가 함께 커진다면 엉망이 자라는 중이다. 같은 종류가 더 들어올 예정이면 기능 추가를 멈추고 리팩터링한다.
- 개선을 명분으로 구조를 한꺼번에 갈아엎지 않는다. 언제든 돌릴 수 있는 테스트를 매 단계 통과시키며 아주 작게 바꾼다.
- 타입별 분기(type-case)는 다형성으로 옮기고, 오류 처리 코드는 자기 모듈로 분리한다. 좋은 설계의 상당 부분은 종류가 다른 코드에 알맞은 자리를 만드는 분할(partitioning)이다.

## How Did I Do This? — 처음부터 깨끗하게 쓰지 않는다

- **어떻게**: 첫 시도에 깨끗하고 우아한 코드를 기대하지 않는다. 작문처럼 초고 → 재고 → 여러 번의 수정으로 최종본을 만든다. 동작하게 만든 시점을 완료로 보지 않는다.
- **왜**: 저자는 프로그래밍을 과학보다 기술(craft)에 가깝다고 본다. 깨끗한 코드는 일단 지저분하게 쓴 뒤 정리해서 얻는다. '동작하는' 상태 그대로 두고 다음 작업으로 넘어가는 것을 대부분의 숙련자는 직업적 자살로 여긴다.

## Args: The Rough Draft — 엉망은 조금씩 쌓인다

- **어떻게**: 작고 깨끗해 보이는 코드도 같은 종류가 늘 때 어디가 불어날지 살핀다. 다음 신호가 보이면 초안이 무너지는 중이라고 본다. 인스턴스 변수가 불어난다. 기본값 자리나 '여기 오면 안 됨' 표시에 쓰는 의미 없는 문자열(원서의 `TILT`), 잡다한 컬렉션, catch가 여럿 달린 try가 늘어난다. 새 타입 하나가 같은 클래스 안의 맵 필드·parse/set/is 함수·getter·오류 코드·메시지 switch에 흩어져 들어간다.
- **왜**: boolean만 다루던 초기 버전은 작고 이해하기 쉬웠지만, 거기에도 이후 엉망의 씨앗은 이미 보였다. 타입 두 개(String, integer)를 더한 것만으로 유지보수할 만하던 코드가 버그와 흠집투성이가 될 것이 뻔한 코드가 되었다. 이름과 구조를 신경 써도 문제를 방치하면 이렇게 통제를 벗어난다. 이 초안을 보고 드는 거부감은 내가 초안 상태로 남긴 코드를 볼 때 다른 사람이 느낄 감정과 같다.

## So I Stopped — 더 나빠지기 전에 멈춘다

- **어떻게**: 같은 유형의 기능이 더 들어올 예정이고 지금 구조로는 악화될 것이 보이면 기능 추가를 멈추고 리팩터링부터 한다. 새 기능이 매번 건드리는 지점(이 사례에서는 스키마 해석, 값 변환, 타입별 getter 세 곳)을 찾아 그 공통점을 하나의 개념으로 묶는다. 비슷한 메서드를 가진 여러 타입은 클래스가 필요하다는 신호다.
- **왜**: 밀어붙이면 동작은 시킬 수 있어도 고치기에 너무 큰 엉망이 남는다. 구조를 살릴 수 있는 때는 엉망이 그만큼 커지기 전이다.

## On Incrementalism — 시스템이 늘 동작하는 작은 단계로 바꾼다

- **어떻게**: 개선이라는 이름으로 구조를 대규모로 바꾸지 않는다. TDD의 원칙대로 시스템을 늘 동작하는 상태로 두고, 모든 변경이 이전과 같은 동작을 유지하게 한다.
  - 언제든 돌릴 수 있는 자동화 테스트 묶음을 먼저 갖추고, 단위 테스트와 인수 테스트(acceptance test)가 있으면 둘 다 돌린다. 원서는 단위 테스트만 돌리다 인수 테스트에만 있던 검증에 걸렸고, 이후 단위 테스트가 인수 테스트 전체를 호출하게 했다.
  - 단계 중에 테스트가 깨질 수는 있다. 깨지면 다른 변경을 하기 전에 그것부터 통과시킨다. 고치는 도중의 정리 단계에서는 실패 양상이 이전과 같은지 본다. 같으면 새 오류를 넣지 않았다는 근거가 된다.
  - 새 추상 메서드를 들일 때는 먼저 빈 구현이나 임시 반환값으로 컴파일을 유지하고, 구현을 하나씩 채우며 테스트를 돌린다.
  - 다음 단계를 위해 무언가를 넣었다가 다시 빼는 일은 흔하다. 루빅스 큐브처럼 작은 단계 하나가 다음 단계를 가능하게 한다. 변경으로 쓸모없어진 함수·필드는 바로 지우고, 하는 일이 거의 없어진 작은 함수(한 줄짜리 판별·위임 함수)는 인라인한다.
- **왜**: 대규모 '개선' 뒤에는 프로그램을 이전과 똑같이 동작하게 만들기가 매우 어렵고, 끝내 회복하지 못하는 프로그램도 있다. 원서는 예외·오류 코드 분리만 약 30개의 작은 단계로 나눠 단계마다 테스트를 통과시켰다.

## Conclusion — 동작하는 코드로 만족하지 않는다

- **어떻게**: 동작을 확인한 뒤 구조와 설계를 정리하는 데까지 한다. 구조를 고칠 시간이 없다는 이유로 미루지 않는다. 방금(몇 분 전, 오늘 오전) 만든 엉망은 지금 치우고, 코드를 늘 가능한 한 깨끗하고 단순하게 유지한다.
- **왜**: 동작하는 코드도 속은 심하게 망가져 있는 경우가 많다. 나쁜 일정·요구사항·팀 관계는 다시 고칠 수 있지만, 나쁜 코드는 썩어 가며 팀의 속도를 계속 떨어뜨린다. 코드가 썩을수록 모듈끼리 서로 파고들어 숨은 의존이 얽히고, 이를 찾아 끊는 일은 길고 비싸다. 반대로 만든 직후의 엉망은 치우기 쉽다.

## 변환 패턴

### 옛 구조 옆에 새 구조를 세우고 하나씩 옮긴다

- **언제**: 타입마다 따로 둔 저장소(맵·필드)와 parse/set/get 함수 묶음을 하나의 추상으로 합치고 싶을 때.
- **어떻게**: ① 새 추상의 뼈대만 추가한다(아무것도 깨지지 않는다). ② 가장 적게 깨지는 변경 하나(한 타입의 맵 값을 새 추상으로 바꾸기)부터 한다. ③ 새 저장소를 추가해 옛 저장소와 함께 채운다. ④ 사용처를 하나씩 새 저장소로 옮긴다. ⑤ 아무도 쓰지 않는 옛 저장소를 지운다.
- **왜**: 옛 저장소를 바로 지우면 시스템이 깨진다. 새 구조를 옆에 두면 옮기는 동안에도 단계마다 테스트를 통과시킬 수 있다.
- **주의**: 값을 객체로 감싸면 null 방어의 대상도 바뀐다. 원서에서는 기존 null 대체 함수가 무의미해져 NPE가 났고, null 검사 대상을 값에서 맵이 돌려준 감싼 객체로 옮겨 고쳤다.

### Type-case → Polymorphism — 타입 분기를 다형성으로 (`G23` Prefer Polymorphism to If/Else or Switch/Case)

- **언제**: `instanceof`나 타입 코드로 분기하는 if-else 체인이 있고, 타입이 늘 때마다 체인이 길어질 때.
- **어떻게**: ① 타입과 무관한 조건(대상을 못 찾음 등)을 먼저 체인 밖으로 뺀다. ② 타입별 함수의 시그니처를 맞춘다. 한 구현은 쓰지 않는 인수라도 다른 구현이 쓴다면 받게 해서 공통 추상 메서드로 올린다. ③ 동작을 일단 공통 상위 타입에 모은 뒤, 추상 메서드를 만들어 하위 구현으로 하나씩 내린다. 내릴 때마다 테스트한다. ④ 모든 분기가 같은 호출이 되면 체인을 호출 하나로 바꾼다. ⑤ 상태가 남지 않은 추상 클래스는 interface로 바꾼다.
- **남는 것**: 구현 객체를 만드는 지점의 분기 하나는 남는다(Chapter 17 G23의 ONE SWITCH 규칙과 같은 모양). 원서 완성본도 값을 꺼내는 쪽에는 타입 검사가 남아 있다. 구조는 새 타입을 더할 때 변경이 적고 격리되는지로 확인한다. 테스트, 새 구현 클래스 하나, 생성 분기 한 줄, 오류 코드·메시지와 getter 정도로 끝나고 기존 구현 클래스는 그대로 두면 된다. 원서는 새 타입(double)을 테스트부터 써서 추가해 보며 구조를 검증했다.

```java
// Bad: 결제 수단이 늘 때마다 이 체인과 타입별 메서드가 함께 늘어난다
void pay(String methodId, Order order) {
    PaymentMethod method = methods.get(methodId);
    if (method instanceof CardPayment) chargeCard((CardPayment) method, order);
    else if (method instanceof PointPayment) deductPoints((PointPayment) method, order);
    else if (method instanceof BankTransfer) requestTransfer((BankTransfer) method, order);
    else throw new UnknownPaymentMethodException(methodId);
}
// Good: 못 찾는 경우만 먼저 걸러 내고, 나머지는 각 구현이 자기 방식으로 처리한다
interface PaymentMethod { void pay(Order order); }
void pay(String methodId, Order order) {
    PaymentMethod method = methods.get(methodId);
    if (method == null) throw new UnknownPaymentMethodException(methodId);
    method.pay(order);
}
```

### Too Many Arguments (F1) — 함께 다니는 인수 둘을 객체 하나로

- **언제**: 메서드를 다른 클래스로 내리려는데 인스턴스 변수 두 개(배열과 현재 위치)를 같이 넘겨야 할 때.
- **어떻게**: 둘을 하나의 객체로 묶어 넘긴다. 원서는 배열을 리스트로 바꾸고 반복자(iterator) 하나만 넘겼다. 이것도 열 단계로 나눠 단계마다 테스트를 통과시켰다.
- **왜**: 인스턴스 변수에 기대던 메서드를 다른 클래스로 옮기면 그 변수들이 모두 인수가 된다. 인수는 적을수록 좋고, 저자는 둘을 넘기는 쪽을 지저분하다(dirty)고 했다.

### 저수준 예외는 구현 안에 묻고, 맥락은 경계에서 붙인다

- **언제**: 숫자 변환 실패 같은 저수준 예외가 그 구현을 쓰는 바깥 클래스까지 올라와, 바깥 클래스가 구현마다 다른 예외를 잡아 오류 코드를 정하거나 오류 상태 필드(오류 코드, 문제 값)를 직접 들고 있을 때.
- **어떻게**: 변환을 맡은 구현 안에서 저수준 예외를 잡아 도메인 예외(오류 코드 + 문제 값)로 바꾼다. 구현을 호출하는 쪽은 그 예외를 잡아 자기만 아는 맥락(어느 항목인지)을 덧붙여 다시 던진다.
- **왜**: 변환 예외라는 개념이 그 타입의 구현 안으로 숨는다. 바깥 클래스는 구현 종류가 늘어도 catch를 더하지 않고, 오류 정보는 바깥 클래스의 필드가 아니라 예외에 담긴다.

```java
// Bad: 폼이 필드 구현의 변환 예외를 알고 오류 코드까지 정한다. 필드 종류가 늘면 catch도 는다
void fill(String fieldName, String raw) {
    try { fields.get(fieldName).fill(raw); }     // 수량 필드는 parseInt 예외를 그대로 올린다
    catch (NumberFormatException e) { throw new OrderFormException(INVALID_QUANTITY, raw, fieldName); }
}
// Good: 수량 필드가 변환 실패를 도메인 예외로 바꾸고, 호출하는 폼은 필드 이름만 덧붙인다
class QuantityField implements FormField {
    private int quantity;
    public void fill(String raw) {
        try { quantity = Integer.parseInt(raw); }
        catch (NumberFormatException e) { throw new OrderFormException(INVALID_QUANTITY, raw); }
    }
}
void fill(String fieldName, String raw) {
    try { fields.get(fieldName).fill(raw); }
    catch (OrderFormException e) { e.setFieldName(fieldName); throw e; }
}
```

### 오류 처리와 타입별 구현을 각자의 모듈로 옮긴다 (Single Responsibility Principle, SRP)

- **언제**: 핵심 클래스(원서에서는 인수 파서 본체)에 오류 코드 enum과 오류 메시지 switch가 섞여 있고, 남의 예외(라이브러리의 파싱 예외 등)까지 그대로 던질 때.
- **어떻게**: 던지는 예외를 자기 예외 클래스 하나로 합쳐 별도 모듈로 옮긴다. 오류 코드, 맥락 필드, 메시지 생성 같은 오류 지원 코드를 그쪽에 모으고, 타입별 구현도 각자 파일로 옮긴다. 핵심 클래스는 인수 처리에만 집중한다.
- **왜**: 오류 메시지 포맷을 핵심 클래스에 두는 것은 SRP 위반이다. 관심사마다 자리를 나눠 주면 코드를 이해하고 유지보수하기 쉬워진다. 원서에서 핵심 클래스 쪽 변경은 대부분 삭제였다. 코드가 제자리로 옮겨 갔을 뿐이다.
- **단서**: 메시지 포맷을 예외 클래스에 둔 것도 저자 스스로 타협(compromise)이라 한다. 제공 메시지가 맞지 않는 사용자는 직접 써야 하지만, 준비된 메시지의 편의도 작지 않다.

## 체크리스트

- [ ] 동작한다는 이유나 시간이 없다는 이유로, 방금 만든 엉망이나 초안 상태의 코드를 두고 넘어가려 하지 않는가?
- [ ] 같은 종류의 기능을 하나 더할 때 수정이 한 클래스 곳곳에 흩어지지 않고 새 클래스 하나와 몇 줄로 격리되는가?
- [ ] 지금 변경이 테스트를 통과하는 작은 단계 하나인가?
- [ ] 단위 테스트와 인수 테스트(acceptance test)를 모두 돌렸고, 깨진 테스트를 고친 뒤에야 다음 변경으로 넘어가는가?
- [ ] 옛 구조와 쓸모없어진 함수·필드를, 사용처를 모두 새 구조로 옮긴 뒤 지웠는가?
- [ ] 타입별 동작을 고르는 `instanceof`·타입 코드 분기가 객체 생성 지점 밖에서 반복되지 않는가?
- [ ] 저수준 예외가 그것을 일으킨 구현 밖으로 새어 나가거나, 오류 상태가 필드로 떠다니지 않는가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)), 원서가 이 장에서 직접 붙인 것: `N5` Use Long Names for Long Scopes(짧은 범위의 군더더기 긴 변수명을 줄임), `G23` Prefer Polymorphism to If/Else or Switch/Case(type-case 제거), `F1` Too Many Arguments(인수 둘 대신 하나)
- Chapter 17 휴리스틱(변환 과정에서 드러나는 것): `G5` Duplication(같은 조회 호출 반복 제거), `F4` Dead Function·`G9` Dead Code(쓸모없어진 함수 삭제), `G17` Misplaced Responsibility(오류 메시지 포맷의 자리)
- [chapter_03_functions.md](chapter_03_functions.md) — 인수 개수(F1)와, 타입별 switch를 객체 생성 지점 한 곳에 묻는 규칙
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md)·[chapter_12_emergence.md](chapter_12_emergence.md) — 리팩터링을 안전하게 만드는 테스트와 TDD, 테스트가 받쳐 주는 리팩터링으로 설계 다듬기
- [chapter_10_classes.md](chapter_10_classes.md) — SRP, 변경을 고립시키는 클래스 분리
- [chapter_07_error_handling.md](chapter_07_error_handling.md) — 반환 코드 대신 예외, 예외에 맥락 담기
- [chapter_06_objects_and_data_structures.md](chapter_06_objects_and_data_structures.md) — 다형성과 switch 중 무엇을 고를지(새 타입 추가 vs 새 함수 추가)
- [chapter_16_refactoring_serialdate.md](chapter_16_refactoring_serialdate.md) — 같은 방식의 두 번째 사례(먼저 동작하게, 그다음 제대로)

## 원서 밖 보충

- 원서의 '새 구조를 옆에 세우고 옮긴 뒤 옛 것을 지우기'는 이후 Parallel Change(expand/contract)라는 이름으로 널리 불린다. 테스트가 통과한 단계마다 커밋해 두면 꼬였을 때 바로 되돌릴 수 있고, IDE의 자동 리팩터링(추출·이동·인라인·시그니처 변경)을 쓰면 작은 단계를 더 안전하게 밟는다.
- 원서는 값을 꺼낼 때 중간 단계에서는 Object 반환과 캐스팅에, 완성본에서는 instanceof 검사와 캐스팅에 기댄다. 제네릭 인터페이스(예: `FormField<T>`의 `T value()`)로 반환 타입을 드러내면, 구체 타입으로 쥔 참조에서는 캐스트가 필요 없다. 다만 서로 다른 T의 구현을 한 맵(`Map<String, FormField<?>>`)에 담으면 꺼낸 값은 와일드카드 타입이라 캐스트가 한 곳에 남는다. unchecked 캐스트 없이 꺼내려면 `Class<T>`를 쥔 타입 키로 `type.cast(...)`를 하거나 타입별 조회 경로를 둔다.
- Java 17의 sealed 인터페이스와 Java 21의 switch 패턴 매칭은 컴파일러가 타입 분기의 누락을 잡아 준다. 타입 집합이 닫혀 있고 함수가 더 자주 늘어나는 곳이라면 다형성 대신 이 방식도 선택지다.
