package {{pkg:domain}};

/** 도메인 예외. presentation이 잡아 HTTP 상태로 옮긴다. */
public class {{Context}}NotFound extends RuntimeException {

    public {{Context}}NotFound({{Context}}.Id id) {
        super("{{context}} 없음: " + id.value());
    }
}
