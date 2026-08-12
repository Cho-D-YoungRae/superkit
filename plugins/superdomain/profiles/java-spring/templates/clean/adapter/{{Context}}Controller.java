package {{pkg:adapter}};

import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

import {{pkg:domain}}.{{Context}};
import {{pkg:usecase}}.{{Context}}InputBoundary;

/**
 * 전달 메커니즘 쪽 번역만 한다. {@code @RestController}는 위반이 아니다 —
 * cl.domain-no-framework의 from에 adapter가 없다. 단 <b>framework를 참조할 수는 없다</b>
 * (cl.deps-inward — 이 링은 안쪽만 본다).
 */
@RestController
public class {{Context}}Controller {

    private final {{Context}}InputBoundary inputBoundary;

    public {{Context}}Controller({{Context}}InputBoundary inputBoundary) {
        this.inputBoundary = inputBoundary;
    }

    @PostMapping("/{{context}}s/{id}/activate")
    public void activate(@PathVariable long id) {
        inputBoundary.activate(new {{Context}}InputBoundary.Command(new {{Context}}.Id(id)));
    }
}
