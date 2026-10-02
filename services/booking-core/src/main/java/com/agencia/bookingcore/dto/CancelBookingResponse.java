package com.agencia.bookingcore.dto;

import java.math.BigDecimal;

public record CancelBookingResponse(
        Long id,
        String status,
        BigDecimal totalPrice,
        BigDecimal refundAmount,
        String message
) {
}