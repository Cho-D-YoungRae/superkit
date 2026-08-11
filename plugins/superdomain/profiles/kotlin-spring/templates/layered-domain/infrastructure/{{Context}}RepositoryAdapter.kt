package {{pkg:infrastructure}}

import jakarta.persistence.Entity
import jakarta.persistence.Id
import org.springframework.stereotype.Repository
import {{pkg:domain}}.{{Context}}
import {{pkg:domain}}.{{Context}}Id
import {{pkg:domain}}.{{Context}}Repository

/** 리포지터리 구현 — 도메인 모델 ↔ 영속 엔티티 매핑이 이 레이어의 책임이다. */
@Repository
class {{Context}}RepositoryAdapter : {{Context}}Repository {

    override fun findById(id: {{Context}}Id): {{Context}}? = TODO("영속 조회 후 도메인 모델로 매핑")

    override fun save(aggregate: {{Context}}) = TODO("도메인 모델을 엔티티로 매핑 후 저장")
}

/** `@Entity`는 infrastructure 밖에서 선언될 수도, 참조될 수도 없다(ld.domain-pure — 양방향). */
@Entity
class {{Context}}JpaEntity(@Id val id: Long, var status: String)
