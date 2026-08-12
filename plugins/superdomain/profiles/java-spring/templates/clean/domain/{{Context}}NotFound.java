package {{pkg:domain}};

/** 도메인 예외. 바깥 원이 잡아 전달 메커니즘의 언어로 옮긴다. */
public class {{Context}}NotFound extends RuntimeException {

    public {{Context}}NotFound({{Context}}.Id id) {
        super("{{context}} 없음: " + id.value());
    }
}
