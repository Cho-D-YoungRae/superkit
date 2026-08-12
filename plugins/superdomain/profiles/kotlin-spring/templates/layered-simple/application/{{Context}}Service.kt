package {{pkg:application}}

import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import {{pkg:data}}.{{Context}}Repository

/**
 * application의 **모든 최상위 public 타입**이 `Service`로 끝나야 한다(ls.service-naming).
 * 예외·DTO를 최상위로 빼는 순간 위반이므로 **중첩 타입으로 둔다** — 이 스타일에서 사실상
 * 유일하게 깔끔한 답이다(layered-simple.md R2·R3의 1번).
 */
@Service
class {{Context}}Service(private val repository: {{Context}}Repository) {

    class {{Context}}NotFound(id: Long) : RuntimeException("{{context}} 없음: $id")

    @Transactional
    fun rename(id: Long, name: String) {
        val target = repository.findById(id).orElseThrow { {{Context}}NotFound(id) }
        target.name = name          // 엔티티를 그대로 다룬다 — 이 스타일에서는 정상이다
    }
}
