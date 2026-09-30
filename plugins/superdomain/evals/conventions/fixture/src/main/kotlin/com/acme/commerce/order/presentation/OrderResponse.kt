package com.acme.commerce.order.presentation

import com.acme.commerce.order.domain.Order
import com.acme.commerce.order.domain.OrderStatus

data class OrderResponse(
    val id: Long,
    val status: OrderStatus,
    val totalAmount: Long,
) {
    companion object {
        fun from(order: Order) = OrderResponse(id = order.id, status = order.status, totalAmount = order.totalAmount)
    }
}
