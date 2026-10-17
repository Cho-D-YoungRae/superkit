# Chapter 13: Concurrency — 동시성

> 원서: *Clean Code* (Robert C. Martin, 2008), Chapter 13, pp. 177–191 · by Brett L. Schuchert · Appendix A pp. 317–348 포함
> 한 줄 요약: 동시성은 '무엇을'과 '언제'를 떼어 내는 전략이지만 올바르게 짜기 어려우므로, 동시성 코드는 따로 두고 공유 데이터와 임계 영역을 최소로 줄이며 라이브러리를 알고 간헐적 실패를 끝까지 추적한다.

## 핵심

- "Concurrency is a decoupling strategy." (p. 178) 처리량·응답 시간·구조를 개선할 수 있지만 공짜가 아니고 설계를 바꾼다.
- 스레드를 다루는 코드는 업무 로직과 분리해 몇 곳에 모은다. 업무 로직은 스레드를 모르는 POJO로 두고 스레드 밖에서 먼저 동작시킨다.
- 공유 가변 데이터를 최소화한다. 캡슐화로 갱신 지점을 줄이고, 복사본·지역 변수·독립 분할로 공유 자체를 없앤다.
- 직접 짜기 전에 `java.util.concurrent`를 쓴다. 공유 객체의 메서드를 여러 개 이어 부르지 않고, 필요하면 서버 쪽 한 메서드로 묶는다.
- `synchronized`는 최소 임계 영역만 감싸고, 잠긴 구간에서 다른 잠긴 구간을 부르는 일을 피한다. 여러 자원을 함께 잡아야 하면 모든 스레드가 같은 전역 순서로 잡는다(대가는 아래 Breaking Circular Wait). 종료 처리는 일찍 설계한다.
- 스레드 수·설정·플랫폼을 바꿔 가며 테스트하고, 간헐적 실패를 일회성으로 넘기지 않는다.

## Why Concurrency? / Myths and Misconceptions — 왜 동시성인가, 무엇을 오해하나

**어떻게**
- 동시성을 '무엇을 하는가(what)'와 '언제 하는가(when)'를 분리하는 결합 해소(decoupling) 수단으로 본다. 도입 근거는 구조 개선(큰 메인 루프 하나 대신 협력하는 작은 단위들)과 응답 시간·처리량(여러 사이트를 차례로 기다리는 수집기, 줄 서서 기다리는 사용자, 나눠 처리할 수 있는 대용량 데이터)이다.
- 동시성이 항상 성능을 높인다고 가정하지 않는다. 여러 스레드나 프로세서가 나눠 쓸 대기 시간이 많을 때만 빨라질 수 있고, 그런 상황을 만드는 일도 간단하지 않다.
- 동시성을 넣으면서 설계를 그대로 두지 않는다. 동시 알고리즘의 설계는 단일 스레드 설계와 크게 다를 수 있고, what/when 분리는 대개 구조를 크게 바꾼다. Web·EJB 컨테이너를 쓰더라도 컨테이너가 무엇을 해 주는지 정확히 알고, 동시 갱신(concurrent update)과 deadlock은 직접 막을 줄 알아야 한다. 컨테이너가 주는 결합 해소는 완벽과 거리가 멀다.

**왜**
- 단일 스레드에서는 what과 when이 강하게 묶여 스택 추적만으로 상태를 알 정도다. 둘을 떼면 처리량과 구조를 크게 개선할 수 있다. 대신 동시성은 성능과 코드 양 모두에 비용을 더하고, 단순한 문제라도 올바르게 짜기 복잡하며, 버그가 대개 재현되지 않아 진짜 결함인데도 일회성으로 무시되기 쉽다.

## Challenges — 무엇이 어려운가

**어떻게**
- 한 줄짜리 `++`도 원자적이라고 믿지 않는다. 공유 객체의 필드를 읽고-바꾸고-쓰는 코드는 보호한다.

**왜**
- 두 스레드가 같은 인스턴스의 증가 메서드를 한 번씩 부르면 같은 값을 받고 증가 하나가 사라질 수 있다. 한 줄의 Java 코드도 바이트코드 수준의 실행 경로가 매우 많고(경로 수는 아래 Possible Paths of Execution), 대부분은 맞지만 일부가 틀린 결과를 낸다.

```java
// Bad: 두 스레드가 동시에 부르면 같은 주문 번호가 두 번 나올 수 있다
private int lastOrderNo;
public int issue() { return ++lastOrderNo; }
// Good 1: 읽기-증가-쓰기를 한 임계 영역으로 묶는다
public synchronized int issue() { return ++lastOrderNo; }
// Good 2 (Good 1의 대안. 필드 선언도 바꾼다): 원자 연산 클래스를 쓴다 (아래 Nonblocking Solutions)
private final AtomicInteger lastOrderNo = new AtomicInteger();
public int issue() { return lastOrderNo.incrementAndGet(); }
```

## Concurrency Defense Principles — 동시성 방어 원칙

### Single Responsibility Principle — 동시성 코드를 분리한다

**어떻게**
- 동시성 관련 코드를 다른 코드와 분리한다. 스레드 생성·스케줄링·동기화를 업무 로직 안에 박아 넣지 않는다. 스레드를 아는 코드(thread-aware code)는 작고 한 가지에 집중하게 만든다. 그래야 그 코드를 테스트할 때 다른 것을 함께 테스트하지 않는다.

**왜**
- 동시성 설계는 그 자체로 변경의 이유가 될 만큼 복잡하다. 개발·변경·튜닝 주기가 따로 있고, 어려움의 종류가 일반 코드와 다르며 흔히 더 어렵다. 잘못 짠 동시성 코드가 실패하는 방식은 이미 충분히 많은데, 주변 애플리케이션 코드까지 섞이면 감당하기 더 어렵다.

```java
// Bad: 주문 처리 로직과 스레드 정책이 한 메서드에 섞여 있다
public void fulfillAll(List<Order> orders) {
    orders.forEach(o -> new Thread(() -> courier.dispatch(packer.pack(o))).start());
}
// Good: 업무 로직은 스레드를 모르는 POJO, 스레드 정책은 스케줄러 한 곳
public class OrderFulfiller {                      // 스레드 없이 단위 테스트한다
    public void fulfill(Order order) { courier.dispatch(packer.pack(order)); }
}
public interface FulfillmentScheduler { void schedule(Runnable task); }  // 요청당 스레드, 풀 등으로 교체
public void fulfillAll(List<Order> orders) {
    orders.forEach(o -> scheduler.schedule(() -> fulfiller.fulfill(o)));
}
```

### Corollaries: Limit the Scope of Data · Use Copies of Data · Threads Should Be as Independent as Possible — 공유를 줄인다

**어떻게**
- **Limit the Scope of Data**: 공유 객체를 보호하는 임계 영역(critical section)의 수를 제한한다. 공유될 수 있는 데이터는 철저히 캡슐화하고 접근 경로를 크게 줄인다.
- **Use Copies of Data**: 공유를 피하는 좋은 방법은 처음부터 공유하지 않는 것이다. 상황에 따라 객체를 복사해 읽기 전용으로 다루거나, 스레드마다 복사본에 결과를 모은 뒤 한 스레드에서 병합한다. 객체 생성 비용이 걱정되면 실제로 문제인지 실험해 본다.
- **Threads Should Be as Independent as Possible**: 요청 하나를 스레드 하나가 처리하고, 필요한 데이터는 공유되지 않는 출처에서 받아 지역 변수에 둔다. 데이터를 독립적인 부분집합으로 나눠 서로 다른 스레드(가능하면 다른 프로세서)가 처리하게 한다.

**왜**
- 공유 데이터를 갱신하는 곳이 많을수록 한 곳의 보호를 빠뜨려 그 데이터를 고치는 모든 코드를 깨뜨리기 쉽고, 같은 보호 작업이 반복되며(DRY 위반), 실패 출처를 찾기 더 어렵다. 복사본 덕분에 동기화를 없앨 수 있다면, 내재 락(intrinsic lock)을 피해 아끼는 비용이 추가 생성·GC 비용을 메울 가능성이 크다. 공유가 없으면 스레드는 세상에 자기 하나뿐인 것처럼 동작해 동기화가 필요 없다. 서블릿도 지역 변수만 쓰면 동기화 문제가 없다. 다만 대부분의 애플리케이션은 결국 DB 커넥션 같은 공유 자원을 만난다.

```java
// Bad: 인스턴스 하나를 모든 요청 스레드가 쓰는데, 요청별 상태를 필드에 둔다
private Cart cart;
public Receipt handle(Request request) {
    cart = cartRepository.load(request.memberId());   // 다른 스레드가 덮어쓸 수 있다
    return cashier.checkout(cart);
}
// Good: 요청별 상태는 지역 변수에 둔다
public Receipt handle(Request request) {
    Cart cart = cartRepository.load(request.memberId());
    return cashier.checkout(cart);
}
```

## Know Your Library — 라이브러리를 안다

**어떻게**
- 스레드 코드를 쓸 때는 thread-safe 컬렉션을 쓰고, 서로 관련 없는 작업 실행에는 Executor framework를, 가능하면 nonblocking 방식을 쓴다. 일부 라이브러리 클래스는 thread-safe하지 않다는 것을 안다(아래 보강 절).
- (Java 5 기준) 스레드 코드의 맵은 `ConcurrentHashMap`부터 고려한다. 원서는 거의 모든 상황에서 `HashMap`보다 성능이 좋다고 본다. 동시 읽기·쓰기를 허용하며, 원래 thread-safe하지 않은 흔한 복합 연산을 메서드로 제공한다. `ReentrantLock`(한 메서드에서 얻고 다른 메서드에서 놓는 락), `Semaphore`(개수가 있는 락), `CountDownLatch`(정해진 수의 이벤트를 기다렸다가 대기 스레드를 한꺼번에 풀어, 모두 거의 동시에 출발할 공정한 기회를 줌)를 알아 두고, `java.util.concurrent` 패키지와 그 하위 `atomic`, `locks` 패키지를 익힌다.

**왜**
- 이 패키지의 컬렉션은 멀티스레드 상황에서 안전하면서 성능도 좋다. 손으로 짠 스레드 풀 대신 Executor framework를 쓰면 코드가 더 깔끔하고 짧아진다.

## Know Your Execution Models — 실행 모델을 안다

**어떻게**
- 다음 용어로 문제를 진단한다.

| 용어 | 뜻 |
|---|---|
| Bound Resources | 크기나 개수가 고정된 자원. DB 커넥션, 고정 크기 읽기/쓰기 버퍼 |
| Mutual Exclusion | 공유 데이터·자원에 한 번에 한 스레드만 접근 |
| Starvation | 일부 스레드가 지나치게 오래 또는 영원히 진행하지 못함(빠른 작업만 계속 먼저 통과시킬 때 등) |
| Deadlock | 둘 이상의 스레드가 서로 상대가 쥔 자원을 기다리며 아무도 끝내지 못함 |
| Livelock | 스레드들이 같은 박자로 움직이며 서로 길을 막아, 일을 하려 해도 오래 또는 영원히 진전하지 못함 |

- 기본 모델 세 가지와 그 해법을 익히고, 새 동시성 문제를 만나면 먼저 셋 중 무엇의 변형인지(작업을 큐로 주고받는가, 주로 읽히는 공유 자원인가, 한정된 자원 여럿을 함께 잡는가) 식별해 그 모델의 알려진 해법부터 검토한다. **Producer-Consumer**: 생산자가 큐에 넣고 소비자가 꺼낸다. 큐가 bound resource라 생산자는 빈자리를, 소비자는 일감을 기다리며 서로 신호를 보낸다. **Readers-Writers**: 주로 읽히고 가끔 갱신되는 자원. 처리량을 우선하면 writer가 굶고 정보가 낡으며, writer를 우선하면 처리량이 떨어진다. **Dining Philosophers**: 한정된 자원을 두고 경쟁하는 엔터프라이즈 애플리케이션의 축소판으로, 설계를 잘못하면 deadlock, livelock, 처리량·효율 저하가 온다.

**왜**
- 실무의 동시성 문제는 대부분 이 세 문제의 변형이다. 해법을 직접 구현해 보면 실제 문제를 풀 준비가 된다.

## Beware Dependencies Between Synchronized Methods — 동기화된 메서드 사이의 의존성을 조심한다

**어떻게**
- 공유 객체에서 메서드를 둘 이상 쓰는 것을 피한다. 꼭 써야 하면 세 방법 중 하나로 바로잡는다. **Client-Based Locking**: 클라이언트가 첫 메서드 호출 전에 서버를 잠그고, 마지막 메서드 호출까지 락 범위에 넣는다. **Server-Based Locking**: 서버 안에 잠금, 필요한 메서드 호출, 잠금 해제를 차례로 하는 메서드 하나를 만들고, 클라이언트는 그 메서드만 부르게 한다. **Adapted Server**: 원래 서버를 고칠 수 없을 때 잠금을 맡는 중간 객체를 둔다. server-based locking의 한 형태다.

**왜**
- `synchronized`는 메서드 하나만 보호한다. 클라이언트가 공유 객체의 synchronized 메서드 여러 개를 이어 부르면 그 사이에 다른 스레드가 끼어들 수 있다. 예시와 득실은 아래 보강 절의 Dependencies Between Methods를 본다.

## Keep Synchronized Sections Small — 동기화 영역을 작게 유지한다

**어떻게**
- `synchronized`를 코드 곳곳에 뿌리지 않는다. 임계 영역은 반드시 보호하되, 임계 영역이 최대한 적게 생기도록 설계한다. 다만 임계 영역 수를 줄이려고 영역을 크게 잡지 않는다. 동기화 범위는 최소 임계 영역으로 한정한다.
- 잠가야 하는 구간은 찾아서 잠그고, 잠글 필요가 없는 구간은 잠그지 않는다. 잠긴 구간 안에서 다른 잠긴 구간을 부르는 일을 피한다. 그러려면 무엇이 공유되고 무엇이 공유되지 않는지 정확히 알아야 한다. 여러 락을 꼭 함께 잡아야 하면 아래 보강 절의 Breaking Circular Wait처럼 모든 스레드가 같은 전역 순서로 잡는다.

**왜**
- 임계 영역(critical section)은 프로그램이 올바르게 동작하려면 동시에 실행되지 않게 막아야 하는 코드 구간이다. '최소'를 정하는 기준은 공유 필드를 건드리는 줄이 아니라 정확성이다. 읽은 값으로 계산해 다시 쓰는 흐름이라면 그 흐름 전체가 임계 영역이다. 같은 락이 지키는 코드는 한 번에 한 스레드만 지나간다. 락은 지연과 오버헤드를 만들고, 최소 임계 영역보다 넓게 동기화하면 경합(contention)이 늘어 성능이 떨어진다.

```java
// Bad: 주문 하나에만 의존하는 느린 세금 계산까지 락 안에 있다
public synchronized void record(Order order) {
    Money gross = taxCalculator.grossOf(order);   // 공유 상태를 읽지 않는 느린 계산
    dailyTotal = dailyTotal.plus(gross);
    recordedCount++;
}
// Good: 공유 상태를 읽고 쓰는 부분만 잠근다 (taxCalculator는 상태가 없고, 합산은 순서와 무관해 결과가 같다)
public void record(Order order) {
    Money gross = taxCalculator.grossOf(order);
    synchronized (this) { dailyTotal = dailyTotal.plus(gross); recordedCount++; }
}
```

## Writing Correct Shut-Down Code Is Hard — 올바른 종료 코드는 짜기 어렵다

**어떻게**
- 종료를 일찍 고민하고 일찍 동작하게 만든다. 예상보다 오래 걸린다고 보고 기존 알고리즘을 검토한다. 종료 신호가 닿지 않을 수 있는 대기 지점을 미리 찾아 둔다. deadlock에 빠질 수 있는 자식 스레드를 기다리는 부모, 먼저 끝난 생산자의 메시지를 기다리며 막힌 소비자가 그런 곳이다.

**왜**
- 영원히 도는 시스템과 달리 한동안 일하다 깔끔하게 끝나야 하는 시스템은 우아한 종료(graceful shutdown)를 올바르게 짜기 어렵다. 흔한 실패는 오지 않을 신호를 기다리는 deadlock이다. 위 두 경우 모두 부모가 영원히 끝나지 못해 시스템이 종료되지 않으며, 막힌 소비자는 종료 신호조차 받지 못한다. 이런 상황은 드물지 않다. 깔끔한 종료, 반복의 마지막 회차 같은 경계 상황에서 동시성 결함이 특히 잘 생긴다.

## Testing Threaded Code — 스레드 코드를 테스트한다

**어떻게**
- 문제를 드러낼 가능성이 있는 테스트를 쓰고, 프로그램 설정·시스템 설정·부하를 바꿔 가며 자주 돌린다. 한 번이라도 실패하면 원인을 끝까지 찾는다. 다음 실행에서 통과했다고 무시하지 않는다.
- **Treat Spurious Failures as Candidate Threading Issues**: 설명되지 않는 실패를 우주 방사선(cosmic ray)·하드웨어 결함 같은 일회성으로 치부하지 않는다. "assume that one-offs do not exist." (p. 187)
- **Get Your Nonthreaded Code Working First**: 스레드가 호출할 로직을 스레드를 모르는 POJO로 만들어 스레드 밖에서 먼저 검증한다. 시스템에서 POJO로 옮길 수 있는 부분은 많을수록 좋다. 스레드 버그와 비스레드 버그를 동시에 쫓지 않는다.
- **Make Your Threaded Code Pluggable**: 스레드 하나·여럿·실행 중 변경, 실제 객체·test double, 빠르게·느리게·들쭉날쭉 도는 test double, 반복 횟수 설정 등 여러 구성으로 돌릴 수 있게 한다. **Make Your Threaded Code Tunable**: 적절한 스레드 수는 대개 시행착오로 찾는다. 초기부터 구성별 성능을 재고, 스레드 수를 쉽게 바꿀 수 있게 한다. 실행 중 변경이나 처리량·사용률 기반 자동 조정도 고려한다.
- **Run with More Threads Than Processors**: 작업 전환이 잦을수록 빠진 임계 영역이나 deadlock을 만날 확률이 높다. **Run on Different Platforms**: OS마다 스레딩 정책이 달라 같은 코드도 다르게 실행된다(저자들의 결함 있는 예제는 OS X보다 XP에서 덜 실패했다). 배포 대상 플랫폼 모두에서 일찍, 자주 돌린다.

**왜**
- 정확성 증명은 비현실적이고 테스트도 정확성을 보장하지 않지만 좋은 테스트는 위험을 줄인다. 일회성으로 무시할수록 결함이 있을지 모르는 방식 위에 코드가 더 쌓인다.

### Instrument Your Code to Try and Force Failures — 계측해서 실패를 끌어낸다

**어떻게**
- `wait()`, `sleep()`, `yield()`, 우선순위 변경 같은 호출을 넣어 실행 순서를 흔든다. 깨진 코드는 될 수 있는 한 일찍, 자주 실패하는 편이 낫다. POJO와 스레드 제어 클래스를 나눠 두면 계측 위치를 찾기 쉽다. 방법은 둘이다.
  - **Hand-coded**: 의심 구간에 직접 넣는다. 특히 까다로운 코드에는 쓸 만하지만, 위치와 호출 종류를 손으로 골라야 하고, 운영에 남으면 느려지며, 결함을 찾을지 운에 맡기는 산탄총식 접근이다.
  - **Automated**: AOP 프레임워크, CGLIB, ASM으로 계측하거나, 아래 코드처럼 운영용·테스트용 구현을 바꿔 끼우는 지점 메서드를 둔다. 다소 단순하지만 정교한 도구(IBM ConTest 등)가 없을 때 쓸 만하다. 이 흔들기(jiggling)로 테스트를 천 번쯤 돌리면 일부 결함을 찾을 수도 있고, 통과하면 적어도 할 만큼은 한 것이다.

**왜**
- 취약 구간을 지나는 수천 개 경로 중 실패하는 경로는 극소수라서 스레드 버그는 드물고 재현이 어렵다. 순서를 흔들면 그 경로를 밟을 확률이 오른다. 흔들어서 깨졌다면 계측 탓이 아니라 원래 깨진 코드가 드러난 것이다(엄밀히는 JVM이 선점형 스레딩을 보장하지 않아 예외가 있을 수 있다).

```java
public interface Jitter { void point(); }
Jitter noJitter = () -> { };                       // 운영용: 아무것도 하지 않는다
Jitter randomJitter = () -> {                      // 테스트용: 무작위로 양보·대기·통과
    int choice = ThreadLocalRandom.current().nextInt(3);
    if (choice == 0) Thread.yield();
    else if (choice == 1) LockSupport.parkNanos(1_000_000);
};
public Coupon issueOrNull() {                      // 동기화가 빠졌을 수 있는 구간
    if (remaining <= 0) return null;
    jitter.point();                                // 주입된 Jitter. 확인과 차감 사이를 흔든다
    remaining--;
    return new Coupon(nextSerial++);
}
```

## 보강: Appendix A — Concurrency II

### Client/Server Example · Increasing Throughput — 병목을 알고, 스레드 관리는 한곳에 두고, 공유 부분만 동기화한다

**어떻게**
- 처리량 요구는 시간 제한이 있는 테스트로 표현할 수 있다(예: 요청 묶음이 10초 안에 끝나면 통과). 테스트가 실패해 스레드를 넣기 전에 시간이 어디에 쓰이는지 본다. I/O bound(소켓, DB 연결, 스와핑 대기)라면 기다리는 동안 다른 일을 해 효율이 오른다. processor bound(수치 계산, 정규식, GC)라면 하드웨어를 늘리면 처리량이 나아질 수 있지만 스레드만 더해서는 빨라지지 않는다.
- 요청마다 스레드를 무제한으로 만드는 방식은 순진하다. 상한이 없어 JVM 한계에 닿거나 접속이 몰리면 시스템이 멈출 수 있다(단순한 시스템이라면 충분할 수도 있다). 연결 관리, 요청 처리, 스레딩 정책, 종료 정책을 한 함수에 두지 말고 책임마다 클래스로 나눈다. 스레드 관리 코드는 몇 곳에서 통제하고 스레드 관리 외에는 아무것도 하지 않게 한다.
- 작업을 아무 순서로나 가져와 독립적으로 처리할 수 있으면 스레드로 처리량을 높인다. 여러 스레드가 공유하는 부분(다음 작업을 꺼내는 반복자 등)만 `synchronized`로 감싸고, 느린 I/O와 파싱은 각 스레드가 자기 객체로 동기화 밖에서 한다. 동기화는 최대한 적게 하는 편이 늘 낫다.

**왜**
- 책임을 나누면 스레딩 전략을 바꿀 때 영향받는 코드가 적고, 나머지 책임은 스레드 걱정 없이 테스트할 수 있으며, 동시성 문제가 생기면 볼 곳이 하나다. 앞의 `FulfillmentScheduler`를 Executor framework 기반 풀로 바꾸는 일도 구현 클래스 하나를 끼우면 끝난다. 처리량 계산 예: 페이지 읽기 I/O 1초(CPU 0%), 파싱 0.5초(CPU 100%)라면 단일 스레드는 페이지당 1.5초다. 세 스레드로 파싱을 I/O 대기와 겹치면 이상적으로 초당 2페이지, 3배 처리량이 된다.

### Possible Paths of Execution — 한 줄 코드에도 실행 경로는 많다

**어떻게**
- 원자적 연산(atomic operation), 즉 중간에 끼어들 수 없는 연산을 구분한다. Java 메모리 모델에서 32비트 값 대입은 원자적이고, 64비트 값 대입은 JVM 명세상 32비트 대입 두 번이라 원자성이 보장되지 않는다(특정 프로세서에서는 원자적일 수 있다). 전위·후위 `++`는 원자적이지 않다. 원자적이라고 여기는 것은 흔한 오해다. 바이트코드를 깊이 알 필요는 없다. 공유 객체·값이 어디 있는지, 어떤 코드가 동시 읽기/갱신 문제를 일으키는지, 그것을 어떻게 막는지 안다.

**왜**
- 분기·루프 없는 N개 명령을 T개 스레드가 실행하면 경로는 (N·T)! / (N!)^T가지다. `++` 한 줄은 바이트코드 8개라 두 스레드면 12,870가지이고, 메서드를 `synchronized`로 만들면 2가지로 준다. 한 스레드가 필드 값을 읽은 직후 선점되고 다른 스레드가 증가를 끝낸 뒤, 첫 스레드가 옛 값으로 계산해 덮어쓰면 증가 하나가 사라진다. 상수 대입은 피연산자가 모두 메서드 지역 정보라 섞여 실행돼도 결과가 하나다.

### Knowing Your Library: Executor Framework · Nonblocking Solutions · Nonthread-Safe Classes — 스레드 관리·원자적 갱신·thread-safe하지 않은 클래스

**어떻게**
- **Executor Framework**: 스레드를 직접 만들거나 손으로 짠 풀을 쓰고 있다면 Executor framework를 검토한다. 풀링, 자동 크기 조정, 스레드 재생성을 해 주고 `Runnable`과 결과를 돌려주는 `Callable`을 받는다. `Future`는 독립 작업을 여러 개 실행해 놓고 모두 끝나기를 기다릴 때 편하다(`get()`은 완료까지 블록된다).
- **Nonblocking Solutions**: 값 하나를 thread-safe하게 갱신하려고 `synchronized`를 쓰기보다 `AtomicBoolean`, `AtomicInteger`, `AtomicReference` 같은 클래스를 쓴다.
- **Nonthread-Safe Classes**: `SimpleDateFormat`, DB 커넥션, `java.util`의 컨테이너, 서블릿은 본질적으로 thread-safe하지 않다. 개별 메서드가 thread-safe한 컬렉션이라도 메서드를 둘 이상 부르는 연산(확인 후 넣기 등)은 thread-safe하지 않다. client-based locking, ADAPTER로 감싼 server-based locking, `putIfAbsent()` 같은 복합 연산을 가진 thread-safe 컬렉션 중 하나로 고친다. `Iterator` 인터페이스도 본래 thread-safe하지 않다. 처음부터 여러 스레드가 함께 쓰도록 설계되지 않았다.

**왜**
- `synchronized`는 경쟁이 없어도 항상 락을 잡는다(DB의 비관적 락과 비슷). Atomic 클래스가 쓰는 CAS(Compare and Swap)는 마지막으로 본 값이 그대로일 때만 바꾸고 아니면 재시도한다(낙관적 락과 비슷). 이 감지는 중간~높은 경합에서도 락 획득보다 거의 항상 싸서, 성능이 거의 항상 앞서고(때로는 조금 빠른 정도) 더 느린 경우는 사실상 없다.

```java
// Bad: 메서드 하나하나는 thread-safe해도 확인과 넣기 사이에 다른 스레드가 끼어든다
Map<MemberId, Cart> carts = Collections.synchronizedMap(new HashMap<>());
if (!carts.containsKey(memberId)) carts.put(memberId, new Cart(memberId));
// Good: 복합 연산을 한 번에 하는 thread-safe 컬렉션의 메서드를 쓴다
ConcurrentMap<MemberId, Cart> carts = new ConcurrentHashMap<>();
carts.putIfAbsent(memberId, new Cart(memberId));
```

### Dependencies Between Methods Can Break Concurrent Code — 메서드 사이의 의존성이 동시성 코드를 깬다

**어떻게**
- 공유 객체에 확인 메서드와 행동 메서드(`hasNext()` → `next()`)를 이어 부르는 클라이언트를 만들지 않는다. 이미 그런 코드라면 실패를 용인하거나, 클라이언트를 고치거나, 서버를 고친다.
  - **Tolerate the Failure**: 때로는 실패해도 해가 없게 만들 수 있다(예외를 잡고 정리). 저자는 엉성하다고 본다. 자정마다 재부팅해 메모리 누수를 치우는 격이다.
  - **Client-Based Locking**: 모든 클라이언트가 확인과 행동을 같은 락으로 감싼다. 잠금이 클라이언트마다 반복되어 DRY를 어기지만, thread-safe하지 않은 서드파티 도구를 쓸 때는 필요할 수 있다. 모든 프로그래머가 잠그기를 기억해야 해서 위험하다(저자는 수백 곳 중 한 곳의 누락으로 단말이 하루 한 번꼴로 멈추는 버그를 몇 주에 걸쳐 찾았다).
  - **Server-Based Locking**: 서버 API를 멀티스레드를 의식하게 바꾼다. 확인과 행동을 한 synchronized 메서드로 합치고 클라이언트는 null을 검사한다. 일반적으로 이쪽을 선호한다. 서버 코드를 소유하지 않았다면 ADAPTER로 API를 바꾸며 잠금을 더하고, 확장 인터페이스를 가진 thread-safe 컬렉션이 있으면 그편이 더 낫다.

**왜**
- 스레드 1이 `hasNext()`로 true를 받고 선점된 사이 스레드 2가 마지막 원소를 가져가면 스레드 1의 `next()`가 끝을 넘어간다. 마지막 반복에서만 드러나 운영 후 한참 뒤에 나타나고 추적이 어렵다. Server-based locking은 반복 코드를 줄이고, 단일 스레드 배포에서는 thread-safe하지 않은 서버로 바꿔 오버헤드를 없앨 수 있고, 한 사람의 잠금 누락으로 깨질 위험을 줄이며, 정책을 한곳에 두고, 공유 변수를 클라이언트에서 감춰 볼 곳을 줄인다.

```java
// Bad: 두 메서드 각각은 synchronized지만 클라이언트가 둘을 이어 부른다
while (shipments.hasNext()) {
    courier.dispatch(shipments.next());   // 그 사이 다른 스레드가 마지막 건을 가져갔을 수 있다
}
// Good: 확인과 꺼내기를 서버의 한 메서드로 합친다 (API가 바뀐다)
public synchronized Shipment takeOrNull() {        // PendingShipments 안
    return pending.isEmpty() ? null : pending.removeFirst();
}
for (Shipment s = shipments.takeOrNull(); s != null; s = shipments.takeOrNull()) {
    courier.dispatch(s);
}
```

### Deadlock — 네 가지 조건과 깨는 방법

**어떻게**
- deadlock은 다음 네 조건이 모두 성립할 때만 가능하다. 하나만 깨도 불가능하다.

| 조건 | 뜻 |
|---|---|
| Mutual exclusion | 여러 스레드가 쓰는 자원이 동시 사용 불가이고 개수가 한정됨(DB 커넥션, 쓰기용 파일, 레코드 락, 세마포어) |
| Lock & wait | 자원을 하나 잡으면 필요한 자원을 모두 잡고 일을 마칠 때까지 놓지 않음 |
| No preemption | 다른 스레드의 자원을 빼앗을 수 없음. 쥔 쪽이 놓아야만 얻음 |
| Circular wait | T1은 R1을 쥐고 R2를, T2는 R2를 쥐고 R1을 기다림(deadly embrace) |

- **Breaking Mutual Exclusion**: 동시 사용 가능한 자원(`AtomicInteger` 등)을 쓰거나, 자원 수를 경쟁 스레드 수 이상으로 늘리거나, 잡기 전에 모든 자원이 비었는지 확인한다. 하지만 대부분의 자원은 수가 한정되고 동시 사용이 안 되며, 두 번째 자원이 첫 자원의 처리 결과로 정해지는 일도 흔하다.
- **Breaking Lock & Wait**: 기다리지 않는다. 잡기 전에 확인하고 하나라도 바쁘면 다 놓고 다시 시작한다. Starvation(낮은 CPU 사용률)이나 Livelock(높지만 쓸모없는 CPU 사용률)이 생길 수 있지만, 없는 것보다 낫고 다른 방법이 다 안 될 때도 거의 항상 구현할 수 있다.
- **Breaking Preemption**: 자원이 바쁘면 주인에게 놓아 달라고 요청하고, 주인이 다른 자원을 기다리는 중이면 모두 놓고 다시 시작하게 한다. 기다릴 수 있어 재시작이 줄지만 요청 관리가 까다롭다.
- **Breaking Circular Wait**: 가장 흔한 방법이다. 모든 스레드가 자원의 전역 순서에 합의하고 그 순서대로 잡는다. 대개 간단한 규약이면 된다. 대가: 획득 순서와 사용 순서가 달라 필요 이상 오래 잠글 수 있고, 두 번째 자원의 ID가 첫 자원에서 나오면 순서를 정할 수 없다.

**왜**
- 크기가 정해진 두 자원 풀을 두 연산이 반대 순서로 잡으면, 사용자가 풀 크기보다 많을 때 각자 하나씩 쥔 채 서로를 기다리며 영원히 멈춘다. 현장에서 터져 고치는 데 몇 주가 걸리고, 디버그 출력을 넣으면 타이밍이 바뀌어 문제가 사라진 듯 보이다 몇 달 뒤 다시 난다. 어느 전략에나 대가가 있다(TANSTAAFL). 스레드 관련 부분을 격리해 두면 튜닝과 실험으로 맞는 전략을 찾을 수 있다.

```java
// Bad: 인수 순서대로 잠가서, A→B 이동과 B→A 이동이 동시에 오면 서로 상대가 쥔 락을 기다린다
public void moveStock(Warehouse from, Warehouse to, Sku sku, int qty) {
    synchronized (from) { synchronized (to) { transfer(from, to, sku, qty); } }
}
// Good: 두 락을 꼭 함께 잡아야 하므로 모든 스레드가 같은 전역 순서(창고 ID 순)로 잠근다 → circular wait 불가
public void moveStock(Warehouse from, Warehouse to, Sku sku, int qty) {
    Warehouse first = from.id() < to.id() ? from : to;
    Warehouse second = (first == from) ? to : from;
    synchronized (first) { synchronized (second) { transfer(from, to, sku, qty); } }
}
```

### Testing Multithreaded Code · Tool Support for Testing Thread-Based Code — 깨졌음을 증명하는 테스트와 도구

**어떻게**
- 경쟁 조건을 증명하는 테스트는 시작 값을 기억하고, 두 스레드가 같은 객체의 메서드를 한 번씩 부르게 하고, 결과가 시작 값 + 2인지 비교하는 일을 어긋날 때까지 반복한다. 어긋남을 찾으면 통과, 못 찾으면 실패다.
- 반복 횟수에만 기대지 않는다. **Monte Carlo Testing**: 테스트를 조정 가능하게 만들고 테스트 서버에서 조정 값을 무작위로 바꿔 가며 계속 돌린다. 한 번이라도 실패하면 코드가 깨진 것이다. 일찍 작성해 CI에서 돌리고 실패 조건을 꼼꼼히 기록한다. 배포 대상 플랫폼마다 반복해서 계속 돌리고(오래 통과할수록 코드가 맞을 가능성도, 테스트가 문제를 드러내기에 부족할 가능성도 커진다), 가능하면 운영에 가까운 부하를 바꿔 가며 돌린다.
- IBM ConTest 같은 도구로 테스트와 운영 코드를 계측해, 여러 사용자·가변 부하를 흉내 내는 테스트를 돌린다. 계측에는 일찍 투자하고, 운영 전에 스레드 코드를 최대한 오래 돌려 본다.

**왜**
- 단순한 경쟁 조건도 매우 드물게 드러난다. 저자의 실험에서는 100만 번 반복을 10회 돌려 한 번 드러났고, 기계·OS·JVM이 바뀌면 반복 횟수를 다시 맞춰야 할 가능성이 크다. Monte Carlo testing, 모든 대상 플랫폼, 다양한 부하를 다 동원해도 스레드 문제를 찾을 가능성은 그리 높지 않다. 10억 번에 한 번꼴로 나는 문제가 가장 위험하다. 계측 도구는 thread-safe하지 않은 코드가 더 잘 실패하게 만든다. 저자들은 ConTest 계측 후 실패 빈도가 약 1천만 번에 한 번에서 약 30번에 한 번으로 늘었다.

## 체크리스트

- [ ] 스레드 생성·스케줄링 코드가 업무 로직과 분리되어 한두 곳에 모여 있는가? 업무 로직을 스레드 없이 테스트할 수 있는가?
- [ ] 공유 가변 데이터를 복사본·지역 변수·독립 분할로 없앨 수 있는 만큼 없앴는가? 남은 공유 데이터에 접근하는 경로가 소수의 메서드로 제한되어 있는가?
- [ ] `++`, 확인 후 넣기(`containsKey` → `put`), `hasNext()` → `next()` 같은 공유 객체의 복합 연산이 모두 한 락이나 원자 연산으로 보호되는가?
- [ ] 직접 만든 스레드·락 대신 thread-safe 컬렉션, Executor framework, Atomic 클래스를 썼는가? `SimpleDateFormat`, `java.util` 컬렉션, DB 커넥션, `Iterator`처럼 thread-safe하지 않은 객체는 스레드마다 따로 두거나 보호하는가?
- [ ] `synchronized` 범위가 정확성에 필요한 최소 임계 영역과 일치하고, I/O와 오래 걸리는 계산이 그 밖에 있는가?
- [ ] 잠긴 구간(synchronized 메서드·블록) 안에서 다른 잠긴 구간을 부르는 일을 피했는가? 피할 수 없다면 모든 코드가 같은 전역 순서로 락·자원을 잡는가?
- [ ] 종료 경로를 설계했고, 종료 신호가 막힌 스레드(deadlock에 빠진 자식, 메시지를 기다리는 소비자)에도 닿는가?
- [ ] 스레드 수·test double·반복 횟수·플랫폼을 바꿔 가며 테스트를 돌릴 수 있는가? 간헐적 실패를 모두 원인까지 추적했는가?

## 관련

- Chapter 17 휴리스틱([chapter_17_smells_and_heuristics.md](chapter_17_smells_and_heuristics.md)): `G26` Be Precise(동시 갱신 가능성이 있으면 잠금 장치를 둔다), `G5` Duplication(client-based locking은 클라이언트마다 잠금을 반복한다), `G3` Incorrect Behavior at the Boundaries(종료나 반복의 끝 같은 경계에서 동시성 결함이 잘 숨는다)
- [chapter_10_classes.md](chapter_10_classes.md) — SRP와 책임 단위의 클래스 분리
- [chapter_11_systems.md](chapter_11_systems.md) — 관심사 분리, 자동 계측에도 쓰는 AOP
- [chapter_09_unit_tests.md](chapter_09_unit_tests.md) — Three Laws of TDD로 얻는 테스트 가능성이 스레드 코드를 여러 구성으로 돌리는 pluggability의 바탕
- [chapter_08_boundaries.md](chapter_08_boundaries.md) — thread-safe하지 않은 서드파티 API를 감싸는 경계

## 원서 밖 보충

- 원서는 원자성(atomicity)을 주로 다루고 가시성(visibility)은 거의 다루지 않는다. 다른 스레드가 쓴 값을 보려면 `volatile`, 락, 동시성 유틸리티로 happens-before 관계를 만들어야 한다. 종료 플래그 같은 단순 신호도 최소한 `volatile`로 둔다(`volatile` `long`/`double`은 읽기·쓰기가 원자적이다).
- 원서의 `Object.sleep()`, `Object.yield()`, `Object.priority()`는 실제 API가 아니다. `Thread.sleep()`, `Thread.yield()`, `Thread.setPriority()`이고 `wait()`만 `Object` 메서드다. `yield()`와 우선순위는 힌트라서 플랫폼에 따라 효과가 거의 없을 수 있다. ConTest의 원서 링크는 지금 유효하지 않을 수 있고, JVM에서는 OpenJDK jcstress, JetBrains Lincheck 같은 동시성 테스트 도구가 쓰인다.
- Java 8 이후: 복합 갱신은 `ConcurrentHashMap.computeIfAbsent`/`merge`, 비동기 조합은 `CompletableFuture`를 쓴다. 경합이 아주 심하면 CAS 재시도 비용이 커질 수 있어, 그런 카운터는 `LongAdder`를 쓴다. `SimpleDateFormat` 대신 불변인 `java.time.format.DateTimeFormatter`를 쓴다.
- Java 5부터 있었지만 원서가 다루지 않은 것: Producer-Consumer는 `wait()`/`notify()`를 직접 짜기보다 `BlockingQueue`로 만든다(`ArrayBlockingQueue`가 크기가 고정된 bound resource다). `ConcurrentHashMap`은 처음부터 null 키·값을 받지 않는다. 덧붙여 원서의 `HashMap` 대비 성능 주장은 Java 5 시절 이야기다. 한 스레드만 쓰는 맵은 지금도 `HashMap`이 대체로 더 빠르고 충분하다.
- 종료는 `ExecutorService.shutdown()` → `awaitTermination(타임아웃)` → 필요하면 `shutdownNow()`(인터럽트) 순서가 일반적이다. 블로킹 호출이 인터럽트나 타임아웃에 반응해야 종료 신호가 닿는다. Java 19부터 `ExecutorService`는 `AutoCloseable`이다.
- Java 21 가상 스레드(virtual threads)는 I/O 대기가 많은 요청당 스레드 모델의 비용을 크게 낮춰, 원서가 지적한 스레드 수 상한 문제의 성격을 바꿨다. 가상 스레드는 풀링하지 않고 작업마다 만들며(`Executors.newVirtualThreadPerTaskExecutor()`), 동시 접근 수 제한은 `Semaphore`로 한다. 공유 데이터·락·deadlock 원칙은 그대로다. Java 21~23에서는 `synchronized` 안에서 블로킹하면 캐리어 스레드에 고정(pinning)되는 문제가 있었고 Java 24(JEP 491)에서 대부분 해소되었다.
