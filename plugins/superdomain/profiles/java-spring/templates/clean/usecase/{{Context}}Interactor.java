package {{pkg:usecase}};

import {{pkg:domain}}.{{Context}};
import {{pkg:domain}}.{{Context}}NotFound;

/**
 * 인터랙터. <b>애노테이션이 하나도 붙지 않는다</b> — 생성자 주입만 받는 평범한 클래스이고,
 * 빈 등록과 트랜잭션 경계는 framework가 진다(cl.domain-no-framework의 from에 usecase가 있다).
 */
public class {{Context}}Interactor implements {{Context}}InputBoundary {

    private final {{Context}}Gateway gateway;

    public {{Context}}Interactor({{Context}}Gateway gateway) {
        this.gateway = gateway;
    }

    @Override
    public void activate(Command command) {
        {{Context}} target = gateway.findById(command.id())
                .orElseThrow(() -> new {{Context}}NotFound(command.id()));
        target.activate();
        gateway.save(target);
    }
}
