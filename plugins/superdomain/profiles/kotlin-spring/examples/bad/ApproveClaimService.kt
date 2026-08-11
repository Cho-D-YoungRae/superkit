// 나쁜 예 2/2 — hexagonal, application. 한 파일이 규칙 셋을 동시에 위반한다.
//   hex.ports-owned-inside : Assert 'claim - hex ports-owned-inside' was violated (1 time).
//   hex.domain-pure(참조)  : Assert 'claim - hex domain-pure (참조)' was violated (1 time).
//   hex.deps-inward        : 'claim - hex deps-inward' test has failed.
//                            'hex.deps-inward:application' layer does not depends on
//                            'hex.deps-inward:adapter' layer failed.
package com.acme.claim.application

// 안쪽(application)이 바깥(adapter)을 import한다 — hex.deps-inward.
// 그 타입이 @Entity라 격리의 두 번째 절반에도 걸린다 — hex.domain-pure(참조).
import com.acme.claim.adapter.persistence.ClaimJpaEntity

// 최상위 public 타입 이름이 Port·UseCase로 끝나지 않는다 — hex.ports-owned-inside.
// 흔한 경로는 이것 하나다: in 포트는 ApproveClaimUseCase인데 구현만 ...Service로 지었다.
class ApproveClaimService(private val load: LoadClaimPort) {
    fun rowOf(id: Long): ClaimJpaEntity = ClaimJpaEntity(id, "RECEIVED")
}

// 고치는 법: 이름을 DefaultApproveClaimUseCase로 바꾸고(hexagonal.md R4의 1번),
// 엔티티는 어댑터 안에 두고 포트 시그니처에는 도메인 타입만 오가게 한다.
