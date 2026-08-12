package {{pkg:data}}

import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.Id

/**
 * 엔티티가 곧 모델이다 — 매핑 레이어가 없다. 이것이 빠뜨린 것이 아니라 이 스타일의 정의적
 * 특징이며, 프리셋 4종 중 `*.domain-pure`가 없는 유일한 스타일인 이유다(layered-simple.md R4).
 * data 레이어에는 명명 규칙이 없다.
 */
@Entity
class {{Context}}(
    @Id @GeneratedValue val id: Long = 0,
    var name: String,
    var status: String = "DRAFT",
) {
    init {
        require(name.isNotBlank()) { "이름은 비어 있을 수 없다" }
    }
}
