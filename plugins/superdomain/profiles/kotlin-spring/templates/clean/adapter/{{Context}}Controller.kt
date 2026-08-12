package {{pkg:adapter}}

import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RestController
import {{pkg:domain}}.{{Context}}Id
import {{pkg:usecase}}.{{Context}}InputBoundary

/**
 * 전달 메커니즘 쪽 번역만 한다. `@RestController`는 위반이 아니다 —
 * cl.domain-no-framework의 from에 adapter가 없다. 단 **framework를 import할 수는 없다**.
 */
@RestController
class {{Context}}Controller(private val inputBoundary: {{Context}}InputBoundary) {

    @PostMapping("/{{context}}s/{id}/activate")
    fun activate(@PathVariable id: Long) =
        inputBoundary.activate({{Context}}InputBoundary.Command({{Context}}Id(id)))
}
