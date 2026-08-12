// 좋은 예 3/4 — hexagonal, adapter. @Entity 참조와 매핑이 이 레이어에서 끝난다.
// 실제 프로젝트에서는 이 클래스가 application의 out 포트(`…Port`)를 구현한다 — 발췌라서 뺐다.
package com.acme.claim.adapter;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import com.acme.claim.domain.Claim;

public class ClaimPersistenceAdapter {

    private final Map<Long, ClaimJpaEntity> rows = new HashMap<>();

    public Optional<Claim> findById(Claim.Id id) {
        return Optional.ofNullable(rows.get(id.value()))
                .map(row -> new Claim(new Claim.Id(row.getId()),
                        Claim.Status.valueOf(row.getStatus())));
    }

    public void save(Claim claim) {
        rows.put(claim.id().value(),
                new ClaimJpaEntity(claim.id().value(), claim.status().name()));
    }
}
