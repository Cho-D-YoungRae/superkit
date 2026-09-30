package com.acme.commerce.order.domain

data class Order(
    val id: Long,
    val userId: Long,
    val status: OrderStatus,
    val totalAmount: Long,
)
