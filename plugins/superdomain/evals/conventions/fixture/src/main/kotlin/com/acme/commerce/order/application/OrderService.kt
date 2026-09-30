package com.acme.commerce.order.application

import com.acme.commerce.order.domain.Order
import com.acme.commerce.support.error.CoreException
import com.acme.commerce.support.error.ErrorType
import org.springframework.stereotype.Service

@Service
class OrderService(
    private val orderRepository: OrderRepository,
) {
    fun find(orderId: Long): Order =
        orderRepository.find(orderId) ?: throw CoreException(ErrorType.ORDER_NOT_FOUND)
}
