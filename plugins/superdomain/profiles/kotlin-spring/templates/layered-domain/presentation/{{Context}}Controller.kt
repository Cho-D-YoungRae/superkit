package {{pkg:presentation}}

import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RestController
import {{pkg:application}}.{{Context}}Service
import {{pkg:domain}}.{{Context}}Id

/**
 * JPA 엔티티를 그대로 응답으로 내보내는 코드는 ld.domain-pure 위반이다 —
 * 이 스타일에서 가장 자주 잡히는 위반이므로 응답 타입은 도메인 타입에서 만든다.
 */
@RestController
class {{Context}}Controller(private val service: {{Context}}Service) {

    @PostMapping("/{{context}}s/{id}/activate")
    fun activate(@PathVariable id: Long) = service.activate({{Context}}Id(id))
}
