package com.acme.commerce.support.error

class CoreException(
    val errorType: ErrorType,
    val detail: Any? = null,
) : RuntimeException(errorType.message)
