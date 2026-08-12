package {{pkg:framework}}

import jakarta.persistence.Entity
import jakarta.persistence.Id
import org.springframework.stereotype.Repository
import {{pkg:domain}}.{{Context}}
import {{pkg:domain}}.{{Context}}Id
import {{pkg:usecase}}.{{Context}}Gateway

/** 게이트웨이 구현 — 영속 기술은 가장 바깥 원에서 끝난다. 매핑도 여기의 책임이다. */
@Repository
class {{Context}}GatewayAdapter : {{Context}}Gateway {

    override fun findById(id: {{Context}}Id): {{Context}}? = TODO("영속 조회 후 도메인 모델로 매핑")

    override fun save(aggregate: {{Context}}) = TODO("도메인 모델을 엔티티로 매핑 후 저장")
}

/** `@Entity` 타입은 framework 밖에서 선언될 수도, 참조될 수도 없다(cl.domain-pure — 양방향). */
@Entity
class {{Context}}JpaEntity(@Id val id: Long, var status: String)
