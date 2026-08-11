// 나쁜 예 1/2 — hexagonal, domain. 위반 규칙: hex.domain-no-framework
//   Konsist 실패 첫 줄: Assert 'claim - hex domain-no-framework' was violated (1 time).
//   check_imports  : ClaimPolicy.kt:5: [hex.domain-no-framework] 컨텍스트 'claim': 금지된 대상
//                    'org.springframework..'을(를) import합니다 — org.springframework.stereotype.Component
package com.acme.claim.domain

import org.springframework.stereotype.Component

// @Entity도 아니고 jakarta 타입도 아니라 hex.domain-pure로는 잡히지 않는다.
// R2가 타입 집합을, R3이 import 자체를 막기 때문에 이 파일을 잡는 것은 R3 하나뿐이다.
@Component
class ClaimPolicy {
    fun isReviewable(claim: Claim): Boolean = claim.status() == ClaimStatus.RECEIVED
}

// 고치는 법: 애노테이션을 지우고 빈 등록은 adapter의 설정 클래스가 한다.
// 도메인 서비스는 생성자 주입만 받는 평범한 클래스다.
