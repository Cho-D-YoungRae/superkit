package {{basePackage}}.{{app}};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 실행 진입점. 이 파일에는 업무 로직도, 컨텍스트 타입에 대한 import도 없는 것이 정상이다 —
 * 조립이 전부다.
 *
 * <p><b>{@code scanBasePackages}가 비어 있지 않은 이유.</b> 기본값은 이 클래스의 패키지
 * ({@code {{basePackage}}.{{app}}})를 컴포넌트 스캔의 뿌리로 삼는데, 컨텍스트 코드는 그 아래가
 * 아니라 각자의 모듈({@code {{basePackage}}.<컨텍스트>.<레이어>})에 산다. 그대로 두면 빈이 하나도
 * 잡히지 않고 <b>구조 검사는 전부 통과한 채 부팅에서 깨진다.</b> 스캔을 기본 패키지까지 넓혀도
 * 선언에 없는 컨텍스트가 끌려오지는 않는다 — 이 앱의 클래스패스에는 {@code 포함 컨텍스트} 모듈만
 * 있기 때문이다(그 목록은 {@code build.gradle.kts}가, 그 강제는 derived.app-confinement가 진다).
 */
@SpringBootApplication(scanBasePackages = "{{basePackage}}")
public class {{App}}Application {

    public static void main(String[] args) {
        SpringApplication.run({{App}}Application.class, args);
    }
}
