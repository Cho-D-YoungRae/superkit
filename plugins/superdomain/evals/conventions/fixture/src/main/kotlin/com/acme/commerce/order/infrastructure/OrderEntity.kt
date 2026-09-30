package com.acme.commerce.order.infrastructure

import com.acme.commerce.order.domain.Order
import com.acme.commerce.order.domain.OrderStatus
import jakarta.persistence.Entity
import jakarta.persistence.EnumType
import jakarta.persistence.Enumerated
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table

@Entity
@Table(name = "orders")
class OrderEntity(
    userId: Long,
    status: OrderStatus,
    totalAmount: Long,
) {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null
        protected set

    var userId: Long = userId
        protected set

    @Enumerated(EnumType.STRING)
    var status: OrderStatus = status
        protected set

    var totalAmount: Long = totalAmount
        protected set

    fun toOrder(): Order = Order(id = id!!, userId = userId, status = status, totalAmount = totalAmount)
}
