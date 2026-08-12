// 좋은 예 2/4 — hexagonal, application. 최상위 public 타입이 UseCase로 끝나고 커맨드는 중첩이다.
// 나가는 쪽 포트는 **Port**로 끝나면 된다(같은 규칙의 다른 접미사) — 이 발췌에는 없고, 자리는
// 이 패키지다(`ClaimPersistenceAdapter`가 실제 프로젝트에서 구현할 out 포트가 그것이다).
// 구현 클래스는 Java에서 별도 파일이라 `DefaultApproveClaimUseCase`처럼 접두사를 붙인다.
package com.acme.claim.application;

import com.acme.claim.domain.Claim;

public interface ApproveClaimUseCase {

    void handle(Command command);

    /** 중첩 record — 최상위가 아니므로 hex.ports-owned-inside의 대상이 아니다. */
    record Command(Claim.Id claimId, String approver) {
    }
}
