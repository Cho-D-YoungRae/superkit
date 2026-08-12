package {{pkg:usecase}};

import {{pkg:domain}}.{{Context}};

/** 입력 경계 — 바깥(adapter·framework)이 인터랙터를 부를 때 쓰는 유일한 표면이다. */
public interface {{Context}}InputBoundary {

    void activate(Command command);

    /** 커맨드는 중첩 record로 둔다 — 경계의 일부이지 독립 개념이 아니다. */
    record Command({{Context}}.Id id) {
    }
}
