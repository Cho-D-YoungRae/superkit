# commerce 도메인

온라인으로 상품을 주문하고 결제하는 쇼핑몰이다.

## order — 주문
- 역할: 고객의 구매 요청을 받아 결제 완료와 취소까지의 상태를 관리한다
- 기능: 주문 조회, 주문 취소
- 분류: core
- 코드: `com.acme.commerce.order`
- 규칙: 결제된 주문만 취소할 수 있다
- 하지 않는 것: 결제 승인 (→ payment), 포인트 적립·사용 (→ point)

## payment — 결제
- 역할: 주문의 결제 승인과 그 결과를 관리한다
- 기능: 결제 승인
- 분류: supporting
- 코드: `com.acme.commerce.payment`
- 외부: AcmePay(PG) — 결제 승인 API (docs/pg-api.md)

## point — 포인트
- 역할: 사용자별 포인트 잔액과 적립·사용 내역을 관리한다
- 기능: 포인트 적립, 포인트 사용, 잔액 조회
- 분류: supporting
- 코드: `com.acme.commerce.point`
- 규칙: 잔액보다 많이 쓸 수 없다

## 관계
| 도메인 | 의존 대상 | 방식 | 설명 |
|---|---|---|---|
| payment | order | 동기 호출 | 결제가 승인되면 주문을 결제 완료로 바꾼다 |
| payment | point | 동기 호출 | 결제가 완료되면 포인트를 적립한다 |
