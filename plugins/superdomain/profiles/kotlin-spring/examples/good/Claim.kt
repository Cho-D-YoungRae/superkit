// 좋은 예 1/3 — hexagonal, domain. 프레임워크 import가 없고 예외도 여기 산다.
package com.acme.claim.domain

class Claim(val id: ClaimId, private var status: ClaimStatus) {
    fun approve(approver: UserId) {
        require(status == ClaimStatus.REVIEWING) { "심사 중인 청구만 승인할 수 있다" }
        status = ClaimStatus.APPROVED
    }

    fun status(): ClaimStatus = status
}

@JvmInline
value class ClaimId(val value: Long)

@JvmInline
value class UserId(val value: String)

enum class ClaimStatus { RECEIVED, REVIEWING, APPROVED, REJECTED }

// hex.ports-owned-inside는 application의 이름만 검사한다. 예외를 domain에 두면 걸리지 않는다.
class ClaimNotFound(id: ClaimId) : RuntimeException("청구 없음: ${id.value}")
