package {{pkg:domain}};

import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 도메인 단위 테스트 골격 — 스프링 컨텍스트도 DB도 없이 돈다.
 * 아키텍처 테스트와 달리 GENERATED 헤더가 없다: 이 파일은 사람이 고치는 파일이다.
 *
 * <p>메서드 이름은 ASCII로 두고 읽을 문장은 {@code @DisplayName}에 담는다 — 생성 테스트의
 * 이름 규약과 같은 갈래다(rule-mappings.md §0.1).
 */
class {{Context}}Test {

    // 불변식을 domain 문서에서 confirmed로 확정한 뒤 아래 두 줄의 주석을 풀고 그 ID를 그대로 적는다
    // (`INV-<컨텍스트 이름 대문자>-001`). check_invariants가 이 **리터럴**을 대조한다.
    // import org.junit.jupiter.api.Tag;
    // @Tag("INV-...-001")
    @Test
    @DisplayName("DRAFT가 아니면 활성화할 수 없다")
    void cannotActivateUnlessDraft() {
        {{Context}} target = new {{Context}}(new {{Context}}.Id(1), {{Context}}.Status.ACTIVE);

        assertThrows(IllegalStateException.class, target::activate);
    }
}
