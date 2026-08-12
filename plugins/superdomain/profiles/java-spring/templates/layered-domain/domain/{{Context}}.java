package {{pkg:domain}};

/**
 * {{Context}} 애그리거트 루트 — 스텁. 순수 Java이고 영속 엔티티와는 다른 타입이다.
 * 불변식은 {@code docs/architecture/domain/{{context}}.md}에서 confirmed로 확정한 뒤 여기에서
 * 강제한다.
 *
 * <p>Java는 파일 하나에 public 최상위 타입을 하나만 허용한다. 애그리거트에 종속된 식별자 VO와
 * 상태 enum은 <b>중첩 타입</b>으로 두고, 바깥 레이어가 잡아야 하는 예외만 최상위로 뺐다.
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
