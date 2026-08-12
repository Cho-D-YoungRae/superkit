package {{pkg:adapter}};

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

/**
 * {@code @Entity} 타입은 adapter 밖에서 선언될 수도, 참조될 수도 없다(hex.domain-pure — 양방향).
 * 도메인 모델과 <b>다른 타입</b>인 것이 이 스타일의 값이다.
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
     * 클래스와 필드를 final로 잠그지 않는 것도 같은 이유다(프록시·리플렉션 접근).
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
