// 좋은 예 4/4 — hexagonal, adapter. @Entity는 여기서만 선언되고 여기 밖에서 참조되지 않는다.
// Java는 이 타입을 어댑터와 같은 파일에 둘 수 없다 — public 최상위 타입은 파일당 하나다.
package com.acme.claim.adapter;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class ClaimJpaEntity {

    @Id
    private Long id;
    private String status;

    /** Hibernate가 요구하는 no-arg 생성자 — Java에는 `plugin.jpa`가 없어 손으로 쓴다. */
    protected ClaimJpaEntity() {
    }

    public ClaimJpaEntity(Long id, String status) {
        this.id = id;
        this.status = status;
    }

    public Long getId() {
        return id;
    }

    public String getStatus() {
        return status;
    }
}
