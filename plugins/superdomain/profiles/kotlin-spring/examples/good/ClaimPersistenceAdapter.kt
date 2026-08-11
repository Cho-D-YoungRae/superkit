// 좋은 예 3/3 — hexagonal, adapter. @Entity가 여기서만 선언되고 매핑도 여기서 끝난다.
package com.acme.claim.adapter.persistence

import jakarta.persistence.Entity
import jakarta.persistence.Id
import com.acme.claim.application.LoadClaimPort
import com.acme.claim.application.SaveClaimPort
import com.acme.claim.domain.Claim
import com.acme.claim.domain.ClaimId
import com.acme.claim.domain.ClaimStatus

@Entity
class ClaimJpaEntity(@Id val id: Long, var status: String)

class ClaimPersistenceAdapter : LoadClaimPort, SaveClaimPort {
    private val rows = mutableMapOf<Long, ClaimJpaEntity>()

    override fun findById(id: ClaimId): Claim? =
        rows[id.value]?.let { Claim(ClaimId(it.id), ClaimStatus.valueOf(it.status)) }

    override fun save(claim: Claim) {
        rows[claim.id.value] = ClaimJpaEntity(claim.id.value, claim.status().name)
    }
}
