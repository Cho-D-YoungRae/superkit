package {{pkg:framework}};

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

/**
 * {@code @Entity} 타입은 framework 밖에서 선언될 수도, 참조될 수도 없다(cl.domain-pure — 양방향).
 */
@Entity
public class {{Context}}JpaEntity {

    @Id
    private Long id;

    private String status;

    /**
     * Hibernate가 요구하는 no-arg 생성자. Kotlin 프로파일은 {@code kotlin("plugin.jpa")}가
     * 만들어 주지만 Java에는 그 플러그인이 없어 <b>손으로 쓴다</b>. 빠뜨리면 {@code check_imports}도
     * ArchUnit도 통과한 채 부팅에서 깨진다 — 구조 검사가 보지 못하는 자리다.
     */
    protected {{Context}}JpaEntity() {
    }

    public {{Context}}JpaEntity(Long id, String status) {
        this.id = id;
        this.status = status;
    }

    public Long getId() {
        return id;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
