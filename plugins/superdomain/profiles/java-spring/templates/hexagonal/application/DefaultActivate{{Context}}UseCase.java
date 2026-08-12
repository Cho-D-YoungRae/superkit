package {{pkg:application}};

import {{pkg:domain}}.{{Context}};
import {{pkg:domain}}.{{Context}}NotFound;

/**
 * in 포트의 구현. Java는 파일당 public 최상위 타입이 하나이므로 인터페이스와 같은 파일에 둘 수
 * 없고, 그래서 이름이 규칙에 걸리지 않도록 접두사를 붙였다(hex.ports-owned-inside).
 * {@code {{Context}}Service}로 지으면 바로 위반이다.
 */
public class DefaultActivate{{Context}}UseCase implements Activate{{Context}}UseCase {

    private final {{Context}}Port port;

    public DefaultActivate{{Context}}UseCase({{Context}}Port port) {
        this.port = port;
    }

    @Override
    public void handle(Command command) {
        {{Context}} target = port.findById(command.id())
                .orElseThrow(() -> new {{Context}}NotFound(command.id()));
        target.activate();
        port.save(target);
    }
}
