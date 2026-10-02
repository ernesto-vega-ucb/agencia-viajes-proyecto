package com.agencia.bookingcore.error;

public class BusinessException extends RuntimeException {

    public BusinessException(String message) {
        super(message);
    }
}