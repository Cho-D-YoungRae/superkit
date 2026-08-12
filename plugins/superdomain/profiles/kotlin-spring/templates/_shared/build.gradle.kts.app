// {{app}} — 실행 단위(앱 모듈). 스타일과 무관하므로 프리셋 4종이 이 조각 하나를 공유한다.
// 이 모듈이 하는 일은 **조립뿐**이다: '### 애플리케이션' 표가 이 앱의 `포함 컨텍스트`로 선언한
// 컨텍스트의 가장 바깥 레이어를 의존하고, 스프링 부트가 그것들을 엮는다. 업무 로직을 여기 두면
// 조립 지점과 로직이 한 모듈에 섞이고, 컨텍스트·공용 코드가 이 모듈을 참조하는 순간
// derived.app-confinement 위반이 된다(의존은 앱 쪽으로만 들어온다).
// 플러그인·라이브러리 버전은 대상 프로젝트의 규약(루트 plugins 블록·버전 카탈로그·BOM)을 따른다.
plugins {
    kotlin("jvm")
    // 메인 클래스의 `@SpringBootApplication`이 곧 `@Configuration`이고, 스프링은 그것을 CGLIB로
    // 감싼다. Kotlin 클래스는 기본이 final이라 열어 주지 않으면 **부팅에서** 깨진다.
    kotlin("plugin.spring")
    // 실행 가능한 산출물(bootJar·bootRun)을 만드는 것이 이 모듈을 앱으로 만든다.
    id("org.springframework.boot")
    id("io.spring.dependency-management")
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter")

    // '### 애플리케이션' 표의 `포함 컨텍스트` 열이 이 목록을 정한다. 각 항목은 그 컨텍스트
    // **스타일의 가장 바깥 레이어** 모듈이고(안쪽은 전이 의존으로 따라온다), 어느 레이어인지는
    // 그 스타일의 MANIFEST가 적는다. 표에 없는 컨텍스트를 여기 더하면 derived.app-confinement
    // 위반이다 — 의존을 먼저 더하지 말고 표를 먼저 고친다.
    {{#app.contextModules}}
    implementation(project("{{.}}"))
    {{/app.contextModules}}
}
