# AcmePay 결제 승인 API

결제창에서 인증을 마친 결제를 최종 승인한다. 승인을 요청하지 않으면 결제는 10분 뒤 자동으로 취소된다.

## 흐름

1. 클라이언트가 AcmePay 결제창에서 결제를 인증하면 `paymentKey`를 받는다.
2. 클라이언트가 우리 서버에 `paymentKey`, `orderId`, `amount`를 보낸다.
3. 우리 서버가 AcmePay에 승인을 요청한다.

## 요청

```
POST https://api.acmepay.example/v1/payments/confirm
Authorization: Basic base64("{secretKey}:")
Content-Type: application/json

{ "paymentKey": "pk_3f9a...", "orderId": "1024", "amount": 15000 }
```

## 응답

- 200 OK

  ```json
  { "paymentKey": "pk_3f9a...", "orderId": "1024", "status": "DONE", "totalAmount": 15000, "approvedAt": "2026-09-30T12:34:56+09:00" }
  ```

- 4xx

  ```json
  { "code": "REJECT_CARD_PAYMENT", "message": "한도 초과" }
  ```

  주요 코드: `INVALID_REQUEST`(잘못된 요청), `NOT_FOUND_PAYMENT`(없는 결제), `ALREADY_PROCESSED_PAYMENT`(이미 처리됨), `REJECT_CARD_PAYMENT`(카드사 거절)

- 5xx 또는 응답 시간 초과: 승인 여부를 알 수 없다. `GET /v1/payments/{paymentKey}`로 상태를 조회할 수 있다.

## 제약

- 같은 `paymentKey`로 다시 승인을 요청하면 `ALREADY_PROCESSED_PAYMENT`를 돌려준다.
- 응답은 보통 1초 안팎이고, 길면 30초까지 걸린다.
