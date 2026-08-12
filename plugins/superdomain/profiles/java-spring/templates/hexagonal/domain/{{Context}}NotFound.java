package {{pkg:domain}};

/**
 * 예외는 domain에 둔다 — application에는 명명 규칙이 있어서(hex.ports-owned-inside) 거기서는
 * 최상위 타입으로 살 수 없다. 바깥 레이어가 잡아 HTTP 상태로 옮기므로 중첩이 아니라 최상위다.
 */
public class {{Context}}NotFound extends RuntimeException {

    public {{Context}}NotFound({{Context}}.Id id) {
        super("{{context}} 없음: " + id.value());
    }
}
