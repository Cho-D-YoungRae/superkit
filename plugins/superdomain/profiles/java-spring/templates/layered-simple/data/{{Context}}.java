package {{pkg:data}};

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;

/**
 * 엔티티가 곧 모델이다 — 매핑 레이어가 없다. 이것이 빠뜨린 것이 아니라 이 스타일의 정의적
 * 특징이며, 프리셋 4종 중 {@code *.domain-pure}가 없는 유일한 스타일인 이유다
 * (layered-simple.md R4). data 레이어에는 명명 규칙이 없다.
 */
@Entity
public class {{Context}} {

    @Id
    @GeneratedValue
    private Long id;

    private String name;

    private String status = "DRAFT";

    /**
     * Hibernate가 요구하는 no-arg 생성자. Kotlin 프로파일은 {@code kotlin("plugin.jpa")}가
     * 만들어 주지만 Java에는 그 플러그인이 없어 <b>손으로 쓴다</b>. 빠뜨리면 {@code check_imports}도
     * ArchUnit도 통과한 채 부팅에서 깨진다 — 구조 검사가 보지 못하는 자리다.
     */
    protected {{Context}}() {
    }

    public {{Context}}(String name) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("이름은 비어 있을 수 없다");
        }
        this.name = name;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getStatus() {
        return status;
    }
}
