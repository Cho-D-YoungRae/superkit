// 나쁜 예 2/2 — hexagonal, application. 한 파일이 규칙 셋을 동시에 위반한다.
// 아래 세 메시지는 모두 **실측 채록**이다(줄바꿈은 읽기 위해 넣었고 원문은 각각 한 줄이다).
// 채록의 줄 번호(`ApproveClaimService.java:13`)는 **이 주석을 뺀 실행 트리** 기준이라 이 파일의
// 줄 번호와 맞지 않는다 — 돌린 트리에는 설명 주석이 없었다.
//   hex.ports-owned-inside :
//     java.lang.AssertionError: Architecture Violation [Priority: MEDIUM] - Rule 'classes that
//     com.acme.claim.application.. and are top level classes and are public should have simple
//     name ending with 'Port' or should have simple name ending with 'UseCase',
//     because 규칙 hex.ports-owned-inside — 컨텍스트 claim' was violated (1 times):
//   hex.deps-inward (첫 줄이 짧은 것은 규칙 설명 자체가 여러 줄이기 때문이다) :
//     java.lang.AssertionError: Architecture Violation [Priority: MEDIUM] - Rule 'Layered
//     architecture considering only dependencies in layers, consisting of
//   hex.domain-pure(참조) :
//     java.lang.AssertionError: Architecture Violation [Priority: MEDIUM] - Rule 'no classes that
//     com.acme.claim.adapter.., com.acme.claim.application.., com.acme.claim.domain.. and not
//     com.acme.claim.adapter.. should depend on classes that annotated with raw type simple name
//     'Entity' and com.acme.claim.adapter.., com.acme.claim.application.., com.acme.claim.domain..,
//     because 규칙 hex.domain-pure — 격리 범위 밖에서 @Entity 타입 참조' was violated (2 times):
//
// 뒤의 둘이 "2 times"인 것은 **ArchUnit이 import가 아니라 바이트코드 의존을 세기 때문**이다 —
// 지목되는 두 줄이 그 차이를 보여준다(import 기반 검사는 한 건으로 본다):
//     Method <...ApproveClaimService.rowOf(long)> calls constructor
//       <com.acme.claim.adapter.ClaimJpaEntity.<init>(java.lang.Long, java.lang.String)>
//       in (ApproveClaimService.java:13)
//     Method <...ApproveClaimService.rowOf(long)> has return type
//       <com.acme.claim.adapter.ClaimJpaEntity> in (ApproveClaimService.java:0)
package com.acme.claim.application;

// 안쪽(application)이 바깥(adapter)을 참조한다 — hex.deps-inward.
// 그 타입이 @Entity라 격리의 두 번째 절반에도 걸린다 — hex.domain-pure(참조).
import com.acme.claim.adapter.ClaimJpaEntity;

// 최상위 public 타입 이름이 Port·UseCase로 끝나지 않는다 — hex.ports-owned-inside.
// 흔한 경로는 이것 하나다: in 포트는 ApproveClaimUseCase인데 구현만 …Service로 지었다.
public class ApproveClaimService {

    public ClaimJpaEntity rowOf(long id) {
        return new ClaimJpaEntity(id, "RECEIVED");
    }
}

// 고치는 법: 이름을 DefaultApproveClaimUseCase로 바꾸고(hexagonal.md R4의 1번),
// 엔티티는 어댑터 안에 두고 포트 시그니처에는 도메인 타입만 오가게 한다.
