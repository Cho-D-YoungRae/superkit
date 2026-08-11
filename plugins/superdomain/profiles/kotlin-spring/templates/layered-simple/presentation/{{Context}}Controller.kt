package {{pkg:presentation}}

import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PutMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController
import {{pkg:application}}.{{Context}}Service

/**
 * presentation의 **모든 최상위 public 타입**이 `Controller`로 끝나야 한다(ls.controller-naming).
 * 요청·응답 DTO도 중첩 타입으로 둔다.
 */
@RestController
class {{Context}}Controller(private val service: {{Context}}Service) {

    data class RenameRequest(val name: String)

    @PutMapping("/{{context}}s/{id}/name")
    fun rename(@PathVariable id: Long, @RequestBody request: RenameRequest) =
        service.rename(id, request.name)
}
