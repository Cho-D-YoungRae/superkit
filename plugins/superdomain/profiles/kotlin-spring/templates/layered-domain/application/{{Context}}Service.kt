package {{pkg:application}}

import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import {{pkg:domain}}.{{Context}}Id
import {{pkg:domain}}.{{Context}}NotFound
import {{pkg:domain}}.{{Context}}Repository

/**
 * 애플리케이션 서비스 = 유스케이스. 들어오는 쪽은 뒤집지 않으므로 컨트롤러가 이것을 직접 부른다
 * (in 포트도 포트 명명 규칙도 없다 — 그것이 hexagonal과의 차이다).
 */
@Service
class {{Context}}Service(private val repository: {{Context}}Repository) {

    @Transactional
    fun activate(id: {{Context}}Id) {
        val target = repository.findById(id) ?: throw {{Context}}NotFound(id)
        target.activate()
        repository.save(target)
    }
}
