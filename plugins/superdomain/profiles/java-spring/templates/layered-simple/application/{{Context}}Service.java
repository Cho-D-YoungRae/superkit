package {{pkg:application}};

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import {{pkg:data}}.{{Context}};
import {{pkg:data}}.{{Context}}Repository;

/**
 * application의 <b>모든 최상위 public 타입</b>이 {@code Service}로 끝나야 한다
 * (ls.service-naming). 예외·DTO를 최상위로 빼는 순간 위반이므로 <b>중첩 타입으로 둔다</b> —
 * 이 스타일에서 사실상 유일하게 깔끔한 답이다(layered-simple.md R2·R3의 1번).
 * Java에서는 파일이 갈리는 문제까지 겹치므로 중첩이 더 강한 답이 된다.
 */
@Service
public class {{Context}}Service {

    private final {{Context}}Repository repository;

    public {{Context}}Service({{Context}}Repository repository) {
        this.repository = repository;
    }

    @Transactional
    public void rename(long id, String name) {
        {{Context}} target = repository.findById(id).orElseThrow(() -> new NotFound(id));
        target.setName(name);      // 엔티티를 그대로 다룬다 — 이 스타일에서는 정상이다
    }

    /** 중첩 타입 — 최상위가 아니므로 명명 규칙의 대상이 아니다. */
    public static class NotFound extends RuntimeException {

        public NotFound(long id) {
            super("{{context}} 없음: " + id);
        }
    }
}
