package {{pkg:framework}}

import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import {{pkg:usecase}}.{{Context}}InputBoundary
import {{pkg:usecase}}.{{Context}}Interactor

/**
 * clean을 고르는 실제 비용이자 유일한 실질적 이득이 이 클래스다.
 * 인터랙터에는 `@Transactional`을 붙일 수 없으므로(cl.domain-no-framework) 입력 경계를 구현한
 * 데코레이터를 framework에 두고 트랜잭션을 여기서 연다. 인터랙터 코드에는 흔적이 남지 않는다.
 */
@Service
class Transactional{{Context}}Interactor(private val delegate: {{Context}}Interactor) : {{Context}}InputBoundary {

    @Transactional
    override fun activate(command: {{Context}}InputBoundary.Command) = delegate.activate(command)
}
