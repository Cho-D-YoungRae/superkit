package {{pkg:usecase}}

import {{pkg:domain}}.{{Context}}Id
import {{pkg:domain}}.{{Context}}NotFound

/** 입력 경계 — 바깥(adapter·framework)이 인터랙터를 부를 때 쓰는 유일한 표면이다. */
interface {{Context}}InputBoundary {

    fun activate(command: Command)

    data class Command(val id: {{Context}}Id)
}

/**
 * 인터랙터. **애노테이션이 하나도 붙지 않는다** — 생성자 주입만 받는 평범한 클래스이고,
 * 빈 등록과 트랜잭션 경계는 framework가 진다(cl.domain-no-framework).
 */
class {{Context}}Interactor(private val gateway: {{Context}}Gateway) : {{Context}}InputBoundary {

    override fun activate(command: {{Context}}InputBoundary.Command) {
        val target = gateway.findById(command.id) ?: throw {{Context}}NotFound(command.id)
        target.activate()
        gateway.save(target)
    }
}
