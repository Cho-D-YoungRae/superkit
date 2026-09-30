package com.acme.commerce.support.error

import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.RestControllerAdvice

@RestControllerAdvice
class ApiControllerAdvice {
    @ExceptionHandler(CoreException::class)
    fun handle(e: CoreException): ResponseEntity<ErrorResponse> =
        ResponseEntity.status(e.errorType.status).body(ErrorResponse(e.errorType.code, e.errorType.message))
}

data class ErrorResponse(val code: String, val message: String)
