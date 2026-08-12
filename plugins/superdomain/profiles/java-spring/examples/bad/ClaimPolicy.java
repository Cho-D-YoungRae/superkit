// 나쁜 예 1/2 — hexagonal, domain. 위반 규칙: hex.domain-no-framework
//   ArchUnit 실패 메시지 첫 줄(실측 — 아래 줄바꿈은 읽기 위해 넣은 것이고 원문은 한 줄이다):
//     java.lang.AssertionError: Architecture Violation [Priority: MEDIUM] - Rule 'no classes that
//     com.acme.claim.domain.. should depend on classes that org.springframework..,
//     jakarta.persistence.., because 규칙 hex.domain-no-framework — 컨텍스트 claim'
//     was violated (1 times):
//   그다음 줄이 지목하는 곳: Class <com.acme.claim.domain.ClaimPolicy> is annotated with
//     <org.springframework.stereotype.Component> in (ClaimPolicy.java:0)
//   check_imports : ClaimPolicy.java:4: [hex.domain-no-framework] 컨텍스트 'claim': 금지된
//     대상 'org.springframework..'을(를) import합니다 — org.springframework.stereotype.Component
package com.acme.claim.domain;

import org.springframework.stereotype.Component;

// @Entity도 아니고 jakarta 타입도 아니라 hex.domain-pure로는 잡히지 않는다.
// R2가 타입 집합을, R3이 참조 자체를 막기 때문에 이 파일을 잡는 것은 R3 하나뿐이다.
@Component
public class ClaimPolicy {

    public boolean isReviewable(Claim claim) {
        return claim.status() == Claim.Status.RECEIVED;
    }
}

// 고치는 법: 애노테이션을 지우고 빈 등록은 adapter의 설정 클래스가 한다.
// 도메인 서비스는 생성자 주입만 받는 평범한 클래스다.
