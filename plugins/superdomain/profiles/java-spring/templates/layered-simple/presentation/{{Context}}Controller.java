package {{pkg:presentation}};

import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import {{pkg:application}}.{{Context}}Service;

/**
 * presentation의 <b>모든 최상위 public 타입</b>이 {@code Controller}로 끝나야 한다
 * (ls.controller-naming). 요청·응답 DTO도 중첩 타입으로 둔다.
 */
@RestController
public class {{Context}}Controller {

    private final {{Context}}Service service;

    public {{Context}}Controller({{Context}}Service service) {
        this.service = service;
    }

    @PutMapping("/{{context}}s/{id}/name")
    public void rename(@PathVariable long id, @RequestBody RenameRequest request) {
        service.rename(id, request.name());
    }

    /** 중첩 record — 최상위가 아니므로 명명 규칙의 대상이 아니다. */
    public record RenameRequest(String name) {
    }
}
