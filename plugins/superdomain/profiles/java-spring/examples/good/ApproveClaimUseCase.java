// 좋은 예 2/4 — hexagonal, application. 최상위 public 타입이 UseCase로 끝나고 커맨드는 중첩이다.
// 나가는 쪽 포트는 같은 패키지의 `ClaimPort`처럼 **Port**로 끝나면 되고(같은 규칙의 다른 접미사),
// 구현 클래스는 Java에서 별도 파일이라 `DefaultApproveClaimUseCase`처럼 접두사를 붙인다.
package com.acme.claim.application;

import com.acme.claim.domain.Claim;

public interface ApproveClaimUseCase {

    void handle(Command command);

    /** 중첩 record — 최상위가 아니므로 hex.ports-owned-inside의 대상이 아니다. */
    record Command(Claim.Id claimId, String approver) {
    }
}
