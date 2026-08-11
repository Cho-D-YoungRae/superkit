---
summary: 트랜잭션적 이벤트 발행(outbox) 패턴 — 적용 시점, 릴레이 방식 비교, at-least-once와 멱등 소비
read_when: [apply, review, scaffold]
---

## 개념

DB와 메시지 브로커는 서로 다른 저장소이므로 **하나의 원자적 작업으로 둘 다 쓸 수 없다.** 이것이
이중 쓰기(dual write) 문제이고, 순서를 어떻게 잡아도 실패 창이 남는다.

| 순서 | 중간에 죽으면 | 결과 |
|---|---|---|
| 커밋 → 발행 | 커밋 후 발행 전 | **유실** — 상태는 바뀌었는데 아무도 모른다 |
| 발행 → 커밋 | 발행 후 커밋 전(롤백) | **유령 이벤트** — 일어나지 않은 일이 알려졌다 |
| 2PC | — | 브로커·DB 양쪽 지원과 운영 비용이 필요하고, 조정자 장애 시 잠금이 남는다 |

outbox는 이 문제를 **저장소를 하나로 만들어** 푼다. 상태 변경과 같은 트랜잭션 안에서 같은 DB의
`outbox` 테이블에 발행할 메시지를 한 행으로 쓴다. 커밋되면 상태와 메시지가 함께 존재하고,
롤백되면 함께 사라진다. 별도의 **릴레이**가 그 테이블을 읽어 브로커로 내보내고 발행 표시를 남긴다.

```
[커맨드] ──트랜잭션 1개──> (도메인 테이블 UPDATE + outbox INSERT) ──커밋
                                          │
                              [릴레이] ────┴──> 브로커 ──> 소비자
```

**outbox가 주는 것은 "발행된다"이지 "한 번만 발행된다"가 아니다.** 릴레이가 브로커에 보낸 뒤
발행 표시를 남기기 전에 죽으면 같은 메시지를 다시 보낸다. 즉 전달 보장은 **at-least-once**이며,
중복은 예외 상황이 아니라 정상 동작이다. 정확히 한 번처럼 보이게 만드는 책임은 전적으로 **소비자의
멱등성**에 있다(R3). 이 사실을 받아들이지 못하는 소비자가 있으면 outbox를 넣어도 문제는 남는다.

## 적용 기준

### 세 필요 조건

셋 다 참일 때 채택한다. 하나라도 거짓이면 아래 대안 표로 간다.

1. **이벤트가 프로세스·컨텍스트 경계를 넘어 나간다.** 같은 트랜잭션 안에서 끝나는 인프로세스
   핸들러만 있으면 이중 쓰기 자체가 없다.
2. **유실이 업무적으로 허용되지 않는다.** 가르는 질문: 이 이벤트가 하나 사라지면 무슨 일이
   일어나는가? "정산이 틀어진다 / 재고가 맞지 않는다 / 고객에게 갈 통지가 안 간다"면 참이고,
   "대시보드 숫자가 조금 어긋난다"면 거짓이다.
3. **수신자가 재처리를 감당한다.** 중복 수신이 소비자 쪽에서 안전하거나, 안전하게 만들 수 있다.
   3번이 거짓인 채로 outbox를 넣으면 유실을 중복으로 바꾸기만 한다.

### 대안 표 — 그 요구를 더 싸게 만족하는가

| 상황 | 더 싼 수단 | outbox가 추가로 주는 것 |
|---|---|---|
| 같은 프로세스 안에서만 소비 | 커밋 후 인프로세스 이벤트 리스너 | 없음(리스너 실패 시 유실은 남지만, 소비자가 같은 DB면 트랜잭션으로 합칠 수 있다) |
| 유실이 허용되는 알림·통계·로그 | 발행 실패 재시도 + 실패 큐 + 모니터링 | 없음 — 운영 부품만 는다 |
| 브로커가 아니라 같은 DB의 다른 테이블에 쓴다 | 같은 트랜잭션에 포함 | 없음 |
| 이벤트 계약을 테이블 스키마로 대신할 수 있다 | 도메인 테이블에 CDC를 직접 건다 | **있다** — CDC를 도메인 테이블에 걸면 내부 스키마가 곧 외부 계약이 되어, 컬럼 하나를 바꾸는 리팩터링이 소비자를 깬다. outbox 행은 의도적으로 설계한 계약이다 |
| 브로커와 DB 양쪽이 분산 트랜잭션을 지원한다 | 2PC | 있다 — 조정자 운영·잠금·성능 비용을 지지 않는다 |

### 릴레이 방식 — 폴링과 CDC

| | 폴링(애플리케이션이 주기적으로 조회) | CDC(트랜잭션 로그 tailing) |
|---|---|---|
| 지연 | 폴링 주기(보통 0.5~5초) | 수십 ms |
| 운영 비용 | 낮음 — 앱 코드와 스케줄러뿐 | 높음 — 커넥터·복제 슬롯·별도 파이프라인 운영 |
| 순서 | 단일 릴레이 + id 순 정렬로 애그리거트 단위 보장 | 로그 순서 그대로 |
| DB 부하 | 주기 질의. 미발행 행 인덱스가 없으면 풀스캔이 된다 | 낮음 — 로그만 읽는다 |
| 필요 권한 | 일반 테이블 접근 | 논리 복제·복제 슬롯 권한(관리형 DB에서 막히는 일이 있다) |
| 대표 실패 모드 | 릴레이 다중 실행 시 중복 발행 — 행 잠금(`FOR UPDATE SKIP LOCKED`)이나 단일 리더가 필요하다 | 소비 지연으로 복제 슬롯이 로그를 붙잡아 **DB 디스크가 찬다** |

**기본은 폴링이다.** 아래 중 하나가 참일 때만 CDC로 올린다.

- 폴링 주기를 낮춰도 지연 요구를 맞추지 못한다(요구가 초 단위 이하로 문서화되어 있다)
- outbox 폴링 질의가 DB 부하로 **관측**되었다
- 이미 같은 DB에 CDC 파이프라인을 운영 중이고 커넥터 운영 역량이 있다

폴링에서 CDC로 옮기는 것은 릴레이 교체이고 소비자 계약은 그대로다 — 나중에 바꿀 수 있으므로 지금
CDC를 고를 이유로 "언젠가 지연이 문제가 될 것"을 쓰지 않는다.

### 고르지 않는 조건

- **이벤트가 컨텍스트 안에서만 돈다** → 인프로세스 처리. outbox 테이블·릴레이·모니터링이 전부
  순비용이다.
- **유실이 허용된다** → 재시도와 실패 큐로 충분하다. 필요 조건 2번이 이 패턴의 관문이다.
- **소비자가 중복을 감당하지 못한다** → outbox보다 소비자 멱등화가 먼저다. 순서가 바뀌면 문제를
  옮기기만 한다.
- **"이벤트를 쓰니까 outbox도"** → [[domain-events]]를 발행하는 것과 프로세스 경계를 넘겨보내는
  것은 다른 문제다.
- **[[event-sourcing]]을 하니까 자동으로** → 이벤트 스토어가 있어도 브로커로 내보내는 순간 같은
  이중 쓰기 문제가 생긴다. 다만 이벤트 스토어 자체가 outbox 역할을 겸할 수 있으므로 테이블을
  하나 더 만들기 전에 그것부터 검토한다.

## 규칙

**리뷰 판정 도구**다(기계 규칙 id는 스타일이 소유한다 —
`references/governance/rule-vocabulary.md` §1). 아래는 diff 위에서 판정할 수 있도록 적었다.

### R1. outbox 삽입은 상태 변경과 같은 트랜잭션 안에 있다

**어디를 보는가**: outbox 저장을 호출하는 메서드와 그 트랜잭션 경계.

**위반 문형**

- (a) outbox 저장이 상태 변경과 **다른** 트랜잭션에 있다 — `Propagation.REQUIRES_NEW`, 별도
  `TransactionTemplate`, 커밋 이후 콜백(`AFTER_COMMIT`)에서의 삽입.
- (b) outbox 저장이 다른 데이터소스·다른 DB를 향한다. 같은 트랜잭션에 참여할 수 없으므로 패턴이
  성립하지 않는다.
- (c) 상태 변경 경로 중 일부만 outbox에 쓴다 — 같은 도메인 이벤트가 어떤 경로에서는 outbox로,
  어떤 경로에서는 브로커로 직접 나간다.

**위반이 아닌 것**: 애그리거트가 모은 도메인 이벤트를 커밋 직전에 한 번에 outbox로 옮기는 것
(같은 트랜잭션 안이면 시점은 자유다).

**보고**: `type=violation`, `severity=blocker`. 이 규칙이 깨지면 outbox가 있는 채로 이중 쓰기다.

### R2. 릴레이는 도메인 로직을 갖지 않는다

**어디를 보는가**: 릴레이(폴러·커넥터 어댑터) 코드.

**위반 문형**: 릴레이가 도메인 리포지토리를 조회해 페이로드를 채운다, 발행 여부를 업무 조건으로
판단한다(`if (claim.status == APPROVED)`), 페이로드를 재계산·변환하며 현재 상태를 읽는다.

**왜 위반인가**: 릴레이가 도는 시점의 상태는 커밋 시점의 상태와 다르다. 발행되는 이벤트가 "그때
일어난 일"이 아니게 되면 소비자는 순서가 뒤바뀐 사실을 받는다.

**요구**: 페이로드는 **삽입 시점에 완성**된다. 릴레이가 하는 일은 읽기·전송·표시뿐이다.

**보고**: `type=violation`, `severity=warn`. 도메인 조회가 페이로드에 반영되면 `blocker`.

### R3. 모든 메시지에 이벤트 id가 있고, 소비자가 멱등하다

**어디를 보는가**: outbox 행 스키마·페이로드 헤더, 그리고 소비자의 처리 진입점.

**위반 문형**

- (a) outbox 행에 유니크한 이벤트 id가 없다(PK 자동 증가만 있고 메시지에 실리지 않는다).
- (b) 소비자가 중복 수신을 처리하지 않는다 — 처리 이력 테이블·유니크 제약·업서트·자연 멱등 연산
  중 어느 것도 없이 `insert`·`+=` 같은 누적 연산을 한다.
- (c) 소비자가 "브로커가 한 번만 준다"는 전제로 작성되었다(주석·설계 문서에 그렇게 적혀 있다).
- (d) 순서 의존이 있는데 파티션 키가 애그리거트 id가 아니다. 전역 순서는 보장되지 않으며, 보장할
  수 있는 것은 같은 애그리거트 내부의 순서뿐이다.

**보고**: `type=violation`, `severity=warn`. (b)로 금액·수량이 이중 반영되면 `blocker`.

### R4. outbox는 어댑터에 격리된다

**어디를 보는가**: outbox 테이블 엔티티·DTO를 import하는 파일의 레이어.

**위반 문형**: domain·application이 `OutboxMessage`·`OutboxRepository` 타입을 참조한다,
애플리케이션 서비스가 직렬화 형식(JSON 문자열)을 직접 만든다, 포트 이름이 발행 수단을 드러낸다
(`OutboxPublishPort` — 안쪽이 알아야 할 것은 "이벤트를 발행한다"뿐이다).

**기계와 리뷰의 분담**: `@Entity`로 선언된 outbox 엔티티가 어댑터 밖으로 새는 것은
`*.domain-pure`(`confine-type`)가 잡는다([[persistence]]). 이 규칙이 보는 것은 그것이 잡지 못하는
쪽이다 — **이름과 시그니처로 새는 누수**.

**보고**: `type=violation`, `severity=warn`.

### R5. 정체와 재발행이 운영 가능하다

**어디를 보는가**: 릴레이 운영 코드와 운영 문서.

**요구 항목** — 없으면 `type=missing`, `severity=info`(2번은 `warn`).

1. 미발행 행의 **최고 경과 시간** 지표가 있고 임계값 경보가 걸려 있다. 행 개수만으로는 정체를
   구분하지 못한다.
2. 발행 완료 행의 삭제·보관 정책이 있다. 없으면 outbox 테이블은 단조 증가하고, 폴링 질의가
   느려지는 형태로 어느 날 갑자기 장애가 된다.
3. 특정 구간을 다시 발행하는 절차와 그 소유자가 정해져 있다(R3가 참이어야 안전하다).

### R6. 리뷰 체크리스트 (기계가 보지 않는 것)

- [ ] 필요 조건 2번("이 이벤트가 사라지면 무슨 일이 일어나는가")의 답이 근거 절이나 ADR에 있는가?
- [ ] outbox 페이로드가 **계약**으로 설계되었는가, 아니면 도메인 엔티티를 그대로 직렬화한 것인가?
      후자면 내부 리팩터링이 소비자를 깬다([[context-mapping]]의 관계 표 `계약` 칸과 같은 대상이다)
- [ ] 페이로드에 담긴 것이 이벤트 전체인가, 식별자뿐인가? 식별자만 보내고 소비자가 되조회하는
      방식은 되조회 시점의 상태를 받으므로 순서 보장이 무의미해진다 — 의도한 선택인지 확인한다
- [ ] 릴레이가 다중 인스턴스로 뜨는가? 잠금이나 리더 선출이 있는가?
- [ ] 폴링 질의가 쓰는 인덱스가 실제로 있는가(미발행 상태 + 생성 순)?
- [ ] 소비자 쪽 멱등 처리 이력의 보존 기간이 재발행 가능 구간보다 긴가?

## 사례

### 올바른 예 — 같은 트랜잭션, 완성된 페이로드 (Kotlin)

```kotlin
// com.acme.claim.application — 안쪽은 "발행한다"만 안다 (R4)
interface PublishClaimEventPort { fun publish(events: List<ClaimEvent>) }

@Service
class ApproveClaimCommandHandler(
    private val loadClaim: LoadClaimPort,
    private val saveClaim: SaveClaimPort,
    private val publishEvent: PublishClaimEventPort,
) {
    @Transactional                                        // 하나의 트랜잭션 (R1)
    fun handle(command: ApproveClaim): ClaimId {
        val claim = loadClaim.findById(command.claimId) ?: throw ClaimNotFound(command.claimId)
        claim.approve(command.approver)
        saveClaim.save(claim)
        publishEvent.publish(claim.pullEvents())          // 같은 트랜잭션 안에서 outbox INSERT
        return claim.id
    }
}

// com.acme.claim.adapter.out.messaging — outbox는 여기서 끝난다
@Repository
class OutboxPublishAdapter(private val outbox: OutboxJpaRepository) : PublishClaimEventPort {
    override fun publish(events: List<ClaimEvent>) = events.forEach { event ->
        outbox.save(
            OutboxMessage(
                eventId = event.eventId,                  // 유니크 이벤트 id (R3 a)
                partitionKey = event.claimId.value,        // 애그리거트 단위 순서 (R3 d)
                type = event.typeName,
                payload = objectMapper.writeValueAsString(event.toContract()),  // 계약 (R6)
            ),
        )
    }
}

// 릴레이 — 읽고, 보내고, 표시한다. 그것뿐이다 (R2)
@Scheduled(fixedDelay = 1_000)
fun relay() {
    outbox.findUnpublished(limit = 100).forEach { message ->   // FOR UPDATE SKIP LOCKED
        broker.send(message.partitionKey, message.payload)
        outbox.markPublished(message.id)
    }
}
```

`broker.send` 성공 후 `markPublished` 전에 죽으면 같은 메시지가 다시 나간다 — 정상이며, 그래서
소비자가 `eventId`로 멱등해야 한다.

### 안티패턴 1 — 커밋 후 발행

```kotlin
@Transactional
fun handle(command: ApproveClaim): ClaimId { /* ... */ saveClaim.save(claim); return claim.id }

@TransactionalEventListener(phase = AFTER_COMMIT)
fun onApproved(event: ClaimApproved) {
    broker.send(event.claimId.value, objectMapper.writeValueAsString(event))  // R1 (a) 위반
}
```

가장 흔한 모양이고, 대부분의 시간 동안 잘 동작한다는 것이 문제다. 커밋과 `send` 사이에 프로세스가
죽거나 브로커가 잠깐 응답하지 않으면 이벤트는 조용히 사라지고 남는 흔적이 없다. 이 코드가 정당한
경우는 필요 조건 2번이 거짓일 때뿐이며, 그때는 outbox 자체가 필요 없다.

### 안티패턴 2 — 릴레이가 상태를 다시 읽는다

```kotlin
@Scheduled(fixedDelay = 1_000)
fun relay() {
    outbox.findUnpublished(limit = 100).forEach { message ->
        val claim = claimRepository.findById(message.aggregateId)   // R2·R4 위반
        if (claim.status != APPROVED) return@forEach                // 업무 판단이 릴레이에 있다
        broker.send(message.partitionKey, claim.toPayload())        // 현재 상태를 발행한다
    }
}
```

발행되는 것이 "승인되었다"가 아니라 "지금 승인 상태다"가 되었다. 승인 뒤 취소가 이어지면 취소
이벤트만 나가거나 아무것도 나가지 않으며, 소비자는 두 사실 중 하나를 영영 받지 못한다. 릴레이는
outbox 행을 해석하지 않는다.

## 관련 문서

- [[domain-events]] — outbox가 실어 나르는 것. 발행 위치·시점·명명은 그 문서가 정본이다
- [[cqrs]] — L3의 리드 모델 동기화 경로에서 유실을 막는 수단
- [[event-sourcing]] — 이벤트 스토어가 outbox를 겸할 수 있는 경우와 그렇지 않은 경우
- [[context-mapping]] — 발행 이벤트의 페이로드는 관계 표의 `계약`이다
- [[persistence]] — outbox 엔티티를 어댑터에 가두는 것은 `*.domain-pure`가 기계로 잡는다
- [[aggregates]] — 파티션 키의 단위이자 순서 보장의 단위
- [[hexagonal]] — 발행 포트를 안쪽이 소유하고 outbox를 어댑터에 두는 배치
