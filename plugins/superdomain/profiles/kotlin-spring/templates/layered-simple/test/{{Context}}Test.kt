package {{pkg:data}}

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows

/**
 * 이 스타일은 domain 문서가 **선택**이다 — 확정한 불변식이 있을 때만 `@Tag("INV-...")`를 단다
 * (`INV-<컨텍스트 이름 대문자>-001`, `import org.junit.jupiter.api.Tag`).
 * 필드 단위를 넘는 불변식이 둘 이상 쌓이면 그것은 layered-domain 승격 신호다.
 */
class {{Context}}Test {

    @Test
    fun `빈 이름으로는 만들 수 없다`() {
        assertThrows<IllegalArgumentException> { {{Context}}(name = "") }
    }
}
