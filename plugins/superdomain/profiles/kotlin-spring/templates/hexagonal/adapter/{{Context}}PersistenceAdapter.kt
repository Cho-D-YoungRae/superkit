package {{pkg:adapter}}

import jakarta.persistence.Entity
import jakarta.persistence.Id
import {{pkg:application}}.{{Context}}Port
import {{pkg:domain}}.{{Context}}
import {{pkg:domain}}.{{Context}}Id

/** out 어댑터 — 도메인 모델 ↔ 영속 엔티티 매핑이 이 레이어의 책임이다. */
class {{Context}}PersistenceAdapter : {{Context}}Port {

    override fun findById(id: {{Context}}Id): {{Context}}? = TODO("영속 조회 후 도메인 모델로 매핑")

    override fun save(aggregate: {{Context}}) = TODO("도메인 모델을 엔티티로 매핑 후 저장")
}

/** `@Entity` 타입은 adapter 밖에서 선언될 수도, 참조될 수도 없다(hex.domain-pure — 양방향). */
@Entity
class {{Context}}JpaEntity(@Id val id: Long, var status: String)
