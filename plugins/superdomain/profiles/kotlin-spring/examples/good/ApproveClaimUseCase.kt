// 좋은 예 2/3 — hexagonal, application. 최상위 public 타입 셋이 모두 Port·UseCase로 끝난다.
package com.acme.claim.application

import com.acme.claim.domain.Claim
import com.acme.claim.domain.ClaimId
import com.acme.claim.domain.ClaimNotFound
import com.acme.claim.domain.UserId

interface LoadClaimPort { fun findById(id: ClaimId): Claim? }

interface SaveClaimPort { fun save(claim: Claim) }

interface ApproveClaimUseCase {
    fun handle(command: Command)

    data class Command(val claimId: ClaimId, val approver: UserId)   // 중첩 — 검사 대상 아님
}

// 구현에 접두사를 붙여 UseCase로 끝나게 한다 — hexagonal.md R4의 1번.
class DefaultApproveClaimUseCase(
    private val load: LoadClaimPort,
    private val save: SaveClaimPort,
) : ApproveClaimUseCase {
    override fun handle(command: ApproveClaimUseCase.Command) {
        val claim = load.findById(command.claimId) ?: throw ClaimNotFound(command.claimId)
        claim.approve(command.approver)
        save.save(claim)
    }
}
