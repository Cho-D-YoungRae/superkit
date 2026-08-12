package {{pkg:domain}};

/**
 * {{Context}} 애그리거트 루트 — 스텁. 프레임워크를 모르는 순수 Java다(hex.domain-no-framework).
 * 불변식은 {@code docs/architecture/domain/{{context}}.md}에서 confirmed로 확정한 뒤 여기에서
 * 강제한다.
 *
 * <p><b>식별자와 상태를 중첩 타입으로 둔 이유.</b> Java는 파일 하나에 public 최상위 타입을
 * 하나만 허용한다. Kotlin 골격이 한 파일에 담던 넷(애그리거트·식별자 VO·상태 enum·예외)을 그대로
 * 옮기면 파일이 넷으로 갈리므로, 애그리거트에 종속된 둘은 안으로 넣고 바깥 레이어가 잡아야 하는
 * 예외만 최상위로 뺐다({@code {{Context}}NotFound}).
 */
public final class {{Context}} {

    private final Id id;
    private Status status;

    public {{Context}}(Id id, Status status) {
        this.id = id;
        this.status = status;
    }

    public void activate() {
        if (status != Status.DRAFT) {
            throw new IllegalStateException("DRAFT 상태에서만 활성화할 수 있다");
        }
        status = Status.ACTIVE;
    }

    public Id id() {
        return id;
    }

    public Status status() {
        return status;
    }

    /** 식별자 VO. record는 equals·hashCode를 값으로 준다 — 식별자에 필요한 것이 그것이다. */
    public record Id(long value) {
    }

    public enum Status {
        DRAFT, ACTIVE
    }
}
