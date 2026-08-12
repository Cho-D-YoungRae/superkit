// 좋은 예 1/4 — hexagonal, domain. 프레임워크 참조가 없고 예외도 여기 산다.
// Java는 파일 하나에 public 최상위 타입이 하나뿐이라, Kotlin 예제가 한 파일에 담던 다섯 타입을
// **애그리거트의 중첩 타입**으로 접었다. 중첩은 최상위 타입 규칙(hex.ports-owned-inside)의
// 대상이 아니므로 이름도 자유롭다.
package com.acme.claim.domain;

public final class Claim {

    private final Id id;
    private Status status;

    public Claim(Id id, Status status) {
        this.id = id;
        this.status = status;
    }

    public void approve() {
        if (status != Status.REVIEWING) {
            throw new IllegalStateException("심사 중인 청구만 승인할 수 있다");
        }
        status = Status.APPROVED;
    }

    public Id id() {
        return id;
    }

    public Status status() {
        return status;
    }

    public record Id(long value) {
    }

    public enum Status {
        RECEIVED, REVIEWING, APPROVED, REJECTED
    }

    /** 예외를 domain에 두면 application의 명명 규칙에 걸리지 않는다. */
    public static class NotFound extends RuntimeException {
        public NotFound(Id id) {
            super("청구 없음: " + id.value());
        }
    }
}
