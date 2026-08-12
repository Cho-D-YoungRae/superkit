package {{basePackage}}.{{app}}

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

/**
 * 실행 진입점. 이 클래스가 있는 패키지가 컴포넌트 스캔의 뿌리이므로, 앱이 조립할 컨텍스트의
 * 코드는 이 패키지 아래가 아니라 **각자의 모듈**에 있고 스캔 대상만 여기서 넓힌다
 * (`@SpringBootApplication(scanBasePackages = [...])`).
 *
 * 이 파일에는 업무 로직도, 컨텍스트 타입에 대한 import도 없는 것이 정상이다 — 조립이 전부다.
 */
@SpringBootApplication
class {{App}}Application

fun main(args: Array<String>) {
    runApplication<{{App}}Application>(*args)
}
