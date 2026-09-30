package com.acme.commerce.order.application

import com.acme.commerce.order.domain.Order
import com.acme.commerce.order.infrastructure.OrderJpaRepository
import org.springframework.data.repository.findByIdOrNull
import org.springframework.stereotype.Repository

@Repository
class OrderRepository(
    private val orderJpaRepository: OrderJpaRepository,
) {
    fun find(orderId: Long): Order? = orderJpaRepository.findByIdOrNull(orderId)?.toOrder()
}
