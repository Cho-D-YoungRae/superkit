package {{pkg:data}};

import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 이 스타일은 domain 문서가 <b>선택</b>이다 — 확정한 불변식이 있을 때만
 * {@code @Tag("INV-...")}를 단다(`INV-<컨텍스트 이름 대문자>-001`,
 * {@code import org.junit.jupiter.api.Tag;}). 필드 단위를 넘는 불변식이 둘 이상 쌓이면 그것은
 * layered-domain 승격 신호다.
 */
class {{Context}}Test {

    @Test
    @DisplayName("빈 이름으로는 만들 수 없다")
    void cannotCreateWithBlankName() {
        assertThrows(IllegalArgumentException.class, () -> new {{Context}}(""));
    }
}
