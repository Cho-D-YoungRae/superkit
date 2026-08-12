package {{pkg:framework}};

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import {{pkg:usecase}}.{{Context}}InputBoundary;
import {{pkg:usecase}}.{{Context}}Interactor;

/**
 * clean을 고르는 실제 비용이자 유일한 실질적 이득이 이 클래스다.
 * 인터랙터에는 {@code @Transactional}을 붙일 수 없으므로(cl.domain-no-framework) 입력 경계를
 * 구현한 데코레이터를 framework에 두고 트랜잭션을 여기서 연다. 인터랙터 코드에는 흔적이 없다.
 *
 * <p>Kotlin에서는 이 클래스를 위해 {@code plugin.spring}이 필요했다(클래스가 기본 final).
 * Java에는 필요 없지만, {@code activate}를 {@code final}로 잠그면 그 메서드만 프록시되지 않는다 —
 * 구조 검사가 보지 못하는 자리이므로 잠그지 않는다.
 */
@Service
public class Transactional{{Context}}Interactor implements {{Context}}InputBoundary {

    private final {{Context}}Interactor delegate;

    public Transactional{{Context}}Interactor({{Context}}Interactor delegate) {
        this.delegate = delegate;
    }

    @Override
    @Transactional
    public void activate(Command command) {
        delegate.activate(command);
    }
}
