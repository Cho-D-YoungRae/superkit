package com.acme.commerce.order.presentation

import com.acme.commerce.order.application.OrderService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/orders")
class OrderController(
    private val orderService: OrderService,
) {
    @GetMapping("/{orderId}")
    fun find(@PathVariable orderId: Long): OrderResponse = OrderResponse.from(orderService.find(orderId))
}
