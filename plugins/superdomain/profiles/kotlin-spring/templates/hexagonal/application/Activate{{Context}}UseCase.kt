package {{pkg:application}}

import {{pkg:domain}}.{{Context}}Id
import {{pkg:domain}}.{{Context}}NotFound

/**
 * in 포트. application의 **모든 최상위 public 타입**은 이름이 `Port`·`UseCase`로 끝나야
 * 한다(hex.ports-owned-inside). 그래서 구현에는 접두사를 붙여 `Default…UseCase`로 짓고,
 * 커맨드·결과 타입은 중첩 타입으로 둔다(중첩 타입은 검사 대상이 아니다).
 */
interface Activate{{Context}}UseCase {

    fun handle(command: Command)

    data class Command(val id: {{Context}}Id)
}

class DefaultActivate{{Context}}UseCase(
    private val port: {{Context}}Port,
) : Activate{{Context}}UseCase {

    override fun handle(command: Activate{{Context}}UseCase.Command) {
        val target = port.findById(command.id) ?: throw {{Context}}NotFound(command.id)
        target.activate()
        port.save(target)
    }
}
