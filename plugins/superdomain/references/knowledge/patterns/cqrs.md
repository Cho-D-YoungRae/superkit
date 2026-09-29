---
summary: CQRS 적용 판단 스펙트럼(호출 분리~저장소 분리)과 커맨드/쿼리 분리 규칙 — 기본값은 가장 낮은 단계다
read_when: [apply, review]
---

## 개념

CQRS는 **커맨드(상태를 바꾸는 것)와 쿼리(상태를 읽는 것)를 분리한다**는 한 문장이 전부다. 논쟁은
분리하느냐가 아니라 **어느 수준에서 분리하느냐**이고, 그 수준은 네 단계의 스펙트럼을 이룬다.

| 단계 | 무엇을 분리하는가 | 저장소 | 일관성 | 추가 비용 |
|---|---|---|---|---|
| **L0** | 분리 없음 — 한 메서드가 상태를 바꾸고 화면 데이터를 반환한다 | 하나 | 즉시 | 없음 |
| **L1** | **호출** — 커맨드 메서드와 쿼리 메서드가 갈리고, 커맨드는 식별자 이상을 반환하지 않는다 | 하나 | 즉시 | 거의 없음 |
| **L2** | **모델** — 조회가 애그리거트를 거치지 않고 전용 프로젝션으로 답한다 | 하나 | 즉시 | 조회 전용 타입·질의의 중복 |
| **L3** | **저장소** — 읽기 전용 저장소를 따로 두고 비동기로 동기화한다 | 둘 이상 | 결과적 | 동기화 파이프라인·재구축·지연 |

"CQRS를 도입하자"는 말은 이 표의 어느 칸인지 밝히기 전에는 의미가 없다. 발표 슬라이드의 그림은
거의 언제나 L3지만, **대부분의 컨텍스트에서 맞는 답은 L1**이고, L2는 컨텍스트 전체가 아니라
조회 요구가 쓰기 모델을 망가뜨리기 시작한 **유스케이스 하나** 단위로 올린다.

**스펙트럼의 끝은 목적지가 아니다.** L3에 있다는 것은 성숙의 표시가 아니라 결과적 일관성이라는
비용을 치르는 중이라는 표시다. 아래 단계로 언제든 되돌아올 수 있어야 하고, 되돌아오지 못하게
만드는 것은 대개 화면과 업무 규칙으로 새어 나간 L3의 지연이다.

**CQRS는 [[event-sourcing]]을 요구하지 않는다.** 둘은 같은 자리에서 소개되는 일이 많지만 독립이다.
CQRS 없이 이벤트 소싱을 하는 것은 어렵지만([[event-sourcing]] R5), 이벤트 소싱 없는 CQRS는
L1~L3 어디서든 정상이며 훨씬 흔하다. 하나를 채택하는 근거로 다른 하나를 끌어오지 않는다.

**CQRS는 경계 결정이 아니다.** 컨텍스트를 나누지도 합치지도 않고 코드 배치 관례만 바꾼다. 선언은
컨텍스트의 `- 패턴: cqrs` 한 줄이고 **파서는 그 값을 검증하지 않는다** — 이 문서의 `## 규칙`은
기계가 아니라 `apply`·`review`가 읽는 판정 도구다.

## 적용 기준

### 두 수를 센다

| | 세는 것 |
|---|---|
| **Q** | 이 컨텍스트의 조회 유스케이스 중 **애그리거트 하나를 그대로 돌려주는 것으로 답할 수 없는** 것의 수 — 목록·검색·집계·여러 애그리거트를 합친 화면 |
| **W** | **조회 때문에 쓰기 모델에 들어간 왜곡의 수** — 조회 전용 필드·연관, 화면 정렬을 위해 애그리거트에 추가한 값, 리포지토리의 화면용 조회 메서드 |

두 수 모두 **지금 코드에 있거나 지금 요구서에 있는 것만** 센다. "언젠가 목록 화면이 늘 것이다"는
Q에 세지 않는다 — 이름을 댈 수 있는 화면만 센다.

### 단계별 채택 기준

**L1 — 항상 채택한다.** 조건이 없다. 커맨드 메서드가 화면 데이터를 반환하지 않게 하는 것은 비용이
거의 없고, 위로 올라갈 때의 전제이기도 하다. `- 패턴: cqrs`를 선언하지 않은 컨텍스트도 L1은
지킨다 — 선언은 L2 이상을 뜻한다.

**L2 — W ≥ 1인 그 조회부터, 또는 Q ≥ 3이면 컨텍스트 단위로.** 신호는 왜곡이 먼저 나타난다.
애그리거트에 조회 전용 연관을 추가하라는 요구, 목록 화면 하나 때문에 늘어나는 join fetch 메서드,
"이 필드는 화면 때문에 있는 것"이라는 주석이 W다. **W = 1이면 그 유스케이스 하나만 L2로 올린다** —
컨텍스트 전체를 올리는 것이 아니다. Q ≥ 3이 되어서야 command/query 패키지를 갈라 둘 값이 생긴다.

**L3 — 아래 셋을 전부 충족할 때만.** 하나라도 아니면 L2에 머문다.

1. **측정했다.** 읽기와 쓰기의 부하 비가 실제 지표로 확인되고, L2에서 인덱스·질의 튜닝·캐시를
   이미 시도했고 그것으로 부족하다는 근거가 있다. 부하 추정치는 근거가 아니다.
2. **업무가 지연을 수용했다.** "이 화면은 N초 늦은 데이터를 보여도 된다"를 **화면 단위로** 업무
   담당자가 승인했다. 개발자끼리 "괜찮을 것"이라고 합의한 것은 승인이 아니다.
3. **재구축 소유자가 있다.** 리드 모델이 깨졌을 때 처음부터 다시 만드는 절차와 그 소요 시간이
   문서에 있고, 누가 수행하는지 정해져 있다.

L3를 채택하면 발행 경로의 유실이 곧 데이터 불일치가 되므로 [[outbox]]가 사실상 함께 온다.

### 고르지 않는 조건

- **CRUD에 가까운 컨텍스트다** → L1에서 끝낸다. `generic`으로 분류한 컨텍스트에 command/query
  패키지를 가르는 것은 이름만 늘린다([[domain-classification]]).
- **조회가 느린 원인이 인덱스 부재·N+1이다** → 그것을 고친다. CQRS는 질의 성능 도구가 아니다.
  인덱스를 넣지 않은 채 L3로 올라가면 리드 모델에서도 같은 질의가 느리다.
- **"나중에 확장될 것 같아서"** → 세지 않는다. Q·W는 지금 이름을 댈 수 있는 것만 센다.
- **이벤트 소싱을 도입했으니 세트로** → 반대 방향은 참이지만 이 방향은 아니다. 두 문서의 적용
  기준을 각각 따로 통과해야 한다.
- **마이크로서비스라서 / 팀이 커져서** → 조직 구조는 Q·W를 바꾸지 않는다. 컨텍스트 경계 문제라면
  [[bounded-contexts]]가 먼저다.
- **컨텍스트 경계가 아직 흔들린다** → 경계를 먼저 확정한다. 경계가 움직이면 리드 모델의 소유자가
  누구인지부터 다시 정해야 한다.

### 되돌아오는 기준

한 단계 내려오는 것은 실패가 아니라 정상 운영이다. 아래 중 하나면 내린다.

- L3인데 리드 모델과 쓰기 모델의 스키마가 사실상 같다 → L2. 동기화 파이프라인만 남은 상태다.
- L2인데 쿼리 모델이 애그리거트의 필드를 그대로 복사한 모양이다 → L1. 분리의 값이 0이다.
- 새 커맨드 하나를 추가할 때 손대는 파일이 다섯 개를 넘는다 → 한 단계 내리고 다시 센다.

## 규칙

기계 검증 규칙이 아니라 **리뷰 판정 도구**다 — 이 플러그인의 유일한 기계 강제 규칙
(`derived.context-isolation`)은 컨텍스트 사이의 참조만 보므로 아래를 아무것도 잡지 않는다.
아래 R1~R3은 diff 위에서 그대로 판정할 수
있도록 "어디를 보는가 / 위반 문형 / 위반이 아닌 것"으로 적었다. R1·R2는 `- 패턴: cqrs` 선언
여부와 무관하게 적용한다(L1은 항상 채택하므로). R3은 command/query 패키지가 실재할 때만 적용한다.

### R1. 커맨드 핸들러는 조회 결과를 반환하지 않는다

**커맨드 핸들러 판별** — 위에서부터 **먼저 걸리는 것이 답이다.** 순서를 지켜야 같은 코드에 대해
같은 판정이 나온다.

1. 타입 이름이 `Command`·`CommandHandler`·`CommandService`로 끝나거나 패키지 경로에 `.command.`
   세그먼트가 있다 → **커맨드 핸들러.**
2. R2의 쿼리 핸들러 판별(이름·패키지)에 걸린다 → **커맨드 핸들러가 아니다.** R2로 넘어간다.
3. 이름으로 갈리지 않으면 본문을 본다. 애그리거트의 상태 변경 메서드, 리포지토리·포트의 `save`·
   `delete`·`persist`·`merge`, 또는 도메인 이벤트 발행 중 하나를 호출하면 → **커맨드 핸들러.**
   하나도 없으면 쿼리 핸들러로 보고 R2를 적용한다.

`@Transactional`의 유무는 판별 근거가 아니다 — `readOnly`가 빠진 조회 메서드는 커맨드 핸들러가
아니라 R2 (d) 위반이다.

**위반 문형** — 아래 중 하나라도 해당하면 보고한다.

- (a) **반환 타입**이 `Unit`·`void`, 식별자 값 타입(`ClaimId`·`Long`·`UUID`), 또는 그 식별자
  하나만 담은 결과 타입 중 어느 것도 아니다. 반환 타입 이름이 `...View`·`...Detail`·`...Summary`·
  `...ListResponse`거나 `List<...>`·`Page<...>`면 그 자체로 위반이다.
- (b) 상태 변경 호출(`save`·도메인 동사) **뒤에** 조회 호출이 나오고, 그 결과가 반환값이나 응답
  DTO를 채운다.
- (c) 커맨드 핸들러가 부르는 리포지토리·포트 메서드가 화면용 조회다 — 이름이 `findAll*`·`search*`·
  `...ListView`·`...Summary`로 시작·끝나거나, join fetch·프로젝션 질의다.

**위반이 아닌 것** — 아래는 정상이며 보고하지 않는다.

- `findById`·`getById`로 변경 대상 애그리거트를 불러오는 것
- `existsBy...`·`countBy...`로 중복·한도 같은 불변식을 판정하는 것
- 참조 무결성 확인을 위해 다른 애그리거트를 하나 불러오는 것
- 생성된 식별자 하나를 반환하는 것(`createClaim(): ClaimId`)

**애매할 때 가르는 한 문장**: 이 조회의 결과가 **상태 변경 판단에 쓰이는가**, 아니면 **호출자에게
돌려줄 화면 데이터를 만드는 데 쓰이는가**? 후자면 위반이다.

**보고**: `type=violation`, `severity=warn`. (a)~(c) 중 어느 문형인지와 해당 라인을 `observation`에
적는다. **`severity=info`로 내리는 경우는 하나뿐이다** — 판별 3번(이름이 아니라 본문)으로 커맨드
핸들러가 되었고 걸린 문형이 (c)뿐일 때. 그 조회가 화면용인지 불변식 판정용인지가 판단에 달려
있기 때문이다. (a)·(b)는 상태 변경 호출과 같은 메서드에 있다는 사실이 판별의 불확실성을 이미
해소하므로 판별 경로와 무관하게 `warn`을 유지한다.

### R2. 쿼리 핸들러는 상태를 바꾸지 않는다

**쿼리 핸들러 판별** — 타입 이름이 `Query`·`QueryService`·`Reader`·`Finder`로 끝나거나, 패키지
경로에 `.query.` 세그먼트가 있거나, 메서드에 `@Transactional(readOnly = true)`가 붙어 있다.

**위반 문형**

- (a) 본문에 `save`·`delete`·`persist`·`merge`·`flush`·`update` 호출이 있다.
- (b) 애그리거트의 상태 변경 메서드(도메인 동사 — `approve`·`cancel`·`markAsRead`)를 호출한다.
- (c) 도메인 이벤트를 발행한다(`registerEvent`·`publishEvent`).
- (d) 조회 메서드에 `@Transactional`이 붙어 있는데 `readOnly = true`가 없다. **지연 로딩을 위한
  것이라도 위반이다** — 답은 쓰기 트랜잭션을 여는 것이 아니라 프로젝션으로 바꾸는 것이다.
  `@Transactional`이 아예 없는 조회 메서드는 (d)의 대상이 아니다.

**위반이 아닌 것**: 읽기 캐시 조회, 조회 결과를 DTO로 매핑하는 것, 페이징 계산.

**흔한 함정 — "조회하면서 읽음 처리"**: `markAsRead`는 커맨드다. 조회 API가 그것을 함께 원하면
쿼리 핸들러에 밀어 넣지 말고 커맨드를 따로 두거나, 조회 이후 별도 커맨드로 처리한다. 이 한 줄이
쿼리 경로를 트랜잭션·락·이벤트에 묶는 시작점이다.

**보고**: `type=violation`, `severity=warn`. (d)만 해당하면 `severity=info`.

### R3. command·query 패키지는 서로를 import하지 않는다

**어디를 보는가**: 경로에 `.command.` 또는 `.query.` 세그먼트가 있는 파일의 import 문.

**위반 문형**: `.query.` 패키지의 파일이 `.command.`를 import하거나, 그 반대. 한 방향만 있어도
위반이다.

**공유가 필요하면** 공유 대상을 domain으로 내린다 — 식별자·값 객체·열거형은 domain에 있어야 할
것이 잘못 놓인 경우가 대부분이다. 커맨드 쪽이 쿼리 DTO를 쓰고 싶어진 것이라면 그것은 공유 문제가
아니라 R1 위반 신호다.

**기계에 넘길 자리는 없다.** 이 플러그인의 선언은 컨텍스트 경계만 표현하고, command·query처럼
**컨텍스트 안**의 구획을 강제하는 규칙 문법이 없다. 팀이 이 금지를 세우기로 했다면
`docs/superdomain/conventions/`의 리뷰 체크리스트로 적고 근거를 ADR에 남긴다 — 여기서는 끝까지 리뷰 항목이다.

**보고**: `type=violation`, `severity=warn`.

### R4. 선언과 코드가 같은 단계를 가리킨다

`- 패턴: cqrs` 선언은 단계를 담지 못한다(라벨 값은 문서 key 목록이고 파서가 검증하지 않는다 —
`references/governance/domain-template.md` §3). 그러므로 채택 단계는 `DOMAIN.md`의 `### 근거`
절이나 ADR에 한 줄로 남긴다: `cqrs: L2 (조회 프로젝션 분리, 저장소는 하나)`.

- 선언은 있는데 단계 기록이 없다 → `type=missing`, `severity=info`.
- 기록은 L2인데 코드에 리드 모델 동기화 파이프라인이 있다(또는 그 반대) → `type=drift`,
  `severity=warn`.
- 선언이 없는데 command/query 패키지가 갈려 있다 → `type=drift`, `severity=info`. 선언을
  추가하거나 패키지를 합친다.

### R5. 리뷰 체크리스트 (기계가 보지 않는 것)

- [ ] L2인데 쿼리 모델이 애그리거트 필드를 그대로 복사한 모양인가? → 분리의 값이 0이다. L1로 내린다
- [ ] command/query는 갈렸는데 양쪽이 같은 리포지토리 인터페이스를 쓰는가? → L1을 L2로 착각한 상태
- [ ] 커맨드 하나를 추가할 때 손대는 파일이 다섯 개를 넘는가? → 분리 비용이 값을 넘었다
- [ ] L3인데 리드 모델 재구축 절차와 소유자가 문서에 있는가? 없으면 L3를 유지할 수 없다
- [ ] L3의 지연이 업무 규칙에 새어 들어갔는가? (조회 결과로 커맨드의 가부를 판단하는 화면) →
      그 판단은 쓰기 모델에서 해야 한다
- [ ] CQRS 채택 근거가 Q·W 수치로 적혀 있는가? 없으면 다음 세션에 다시 추측된다

## 사례

### 올바른 예 — L1/L2 (Kotlin)

```kotlin
// com.acme.claim.application.command — 커맨드는 식별자만 돌려준다
@Service
class ApproveClaimCommandHandler(
    private val loadClaim: LoadClaimPort,
    private val saveClaim: SaveClaimPort,
) {
    @Transactional
    fun handle(command: ApproveClaim): ClaimId {          // R1 (a): 반환은 식별자뿐
        val claim = loadClaim.findById(command.claimId)   // 변경 대상 적재 — 위반 아님
            ?: throw ClaimNotFound(command.claimId)
        require(!claim.isDuplicateOf(command))            // 불변식 판정 — 위반 아님
        claim.approve(command.approver)
        saveClaim.save(claim)
        return claim.id
    }
}

// com.acme.claim.application.query — 조회는 애그리거트를 거치지 않는다 (L2)
@Service
class ClaimQueryService(private val claimQueryDao: ClaimQueryDao) {
    @Transactional(readOnly = true)                        // R2 (d)
    fun search(condition: ClaimSearchCondition): Page<ClaimListView> =
        claimQueryDao.search(condition)                    // 전용 프로젝션, 쓰기 모델 무관
}
```

호출자(컨트롤러)는 커맨드로 승인한 뒤 화면이 필요하면 쿼리를 **한 번 더** 부른다. 왕복 한 번이
느는 대신 두 경로가 서로를 오염시키지 않는다.

### 안티패턴 1 — 커맨드 핸들러 안의 조회 로직

```kotlin
@Service
class ApproveClaimCommandHandler(
    private val loadClaim: LoadClaimPort,
    private val saveClaim: SaveClaimPort,
    private val claimQueryDao: ClaimQueryDao,             // 커맨드가 조회 DAO를 들고 있다
) {
    @Transactional
    fun handle(command: ApproveClaim): Page<ClaimListView> {   // R1 (a) 위반: 목록 반환
        val claim = loadClaim.findById(command.claimId) ?: throw ClaimNotFound(command.claimId)
        claim.approve(command.approver)
        saveClaim.save(claim)
        return claimQueryDao.search(                      // R1 (b)(c) 위반: 저장 뒤 화면 조회
            ClaimSearchCondition(assignee = command.approver),
        )
    }
}
```

세 문형이 한 메서드에 다 있다. 증상은 곧 나타난다 — 목록 화면의 정렬 요구가 커맨드의 트랜잭션
안으로 들어오고, 커맨드 테스트가 조회 픽스처를 요구하며, 커맨드를 배치·메시지 소비자에서 부르려
할 때 필요 없는 조회가 함께 실행된다. 고치는 방법은 반환 타입을 `ClaimId`로 되돌리고 목록 조회를
호출자로 올리는 것뿐이다.

### 안티패턴 2 — 쿼리가 상태를 바꾸고, 패키지가 교차한다

```kotlin
// com.acme.claim.application.query.ClaimDetailQueryService
import com.acme.claim.application.command.MarkClaimReadCommand   // R3 위반: query → command

@Service
class ClaimDetailQueryService(private val loadClaim: LoadClaimPort) {
    @Transactional                                        // R2 (d) 위반: readOnly 아님
    fun detail(id: ClaimId): ClaimDetailView {
        val claim = loadClaim.findById(id) ?: throw ClaimNotFound(id)
        claim.markAsRead()                                // R2 (b) 위반: 조회가 상태를 바꾼다
        return ClaimDetailView.from(claim)
    }
}
```

패키지는 갈렸는데 경계가 없다. 이 상태의 L2는 디렉터리 두 개일 뿐이며, 조회 경로가 쓰기 락을
잡기 시작하므로 L1보다 오히려 나쁘다.

## 관련 문서

- [[event-sourcing]] — 함께 소개되지만 독립이다. 각각의 적용 기준을 따로 통과해야 한다
- [[outbox]] — L3의 동기화 경로에서 이벤트 유실을 막는 수단
- [[domain-events]] — 커맨드가 발행하는 것, 그리고 L3 리드 모델을 갱신하는 입력
- [[aggregates]] — 쓰기 모델의 단위. L2가 걷어내는 왜곡은 대부분 애그리거트에 쌓인다
- [[repositories-domain-services]] — 쓰기용 리포지토리와 조회 전용 DAO의 책임 경계
- [[persistence]] — 조회 프로젝션이 영속 엔티티를 어디까지 노출해도 되는가
- [[domain-classification]] — generic 컨텍스트에 L2 이상을 올리지 않는 이유
