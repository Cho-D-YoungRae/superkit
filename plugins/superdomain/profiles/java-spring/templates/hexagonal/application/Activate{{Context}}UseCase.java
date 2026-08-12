package {{pkg:application}};

import {{pkg:domain}}.{{Context}};

/**
 * in 포트. application의 <b>모든 최상위 public 타입</b>은 이름이 {@code Port}·{@code UseCase}로
 * 끝나야 한다(hex.ports-owned-inside). 커맨드·결과 타입은 <b>중첩</b>으로 두면 검사 대상이 아니고,
 * 구현 클래스는 Java에서 별도 파일이어야 하므로 접두사를 붙여
 * {@code DefaultActivate{{Context}}UseCase}로 짓는다.
 */
public interface Activate{{Context}}UseCase {

    void handle(Command command);

    /** 중첩 타입 — 최상위가 아니므로 명명 규칙의 대상이 아니다. */
    record Command({{Context}}.Id id) {
    }
}
