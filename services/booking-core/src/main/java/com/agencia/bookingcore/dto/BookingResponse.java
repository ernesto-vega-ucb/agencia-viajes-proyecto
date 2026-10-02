package com.agencia.bookingcore.dto;

import com.agencia.bookingcore.domain.enums.BookingStatus;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

public record BookingResponse(
        Long id,
        String userId,
        BookingStatus status,
        String currency,
        BigDecimal totalPrice,
        Instant createdAt,
        List<Item> items
) {
    public record Item(
            Long id,
            Long packageId,
            String packageTitle,
            LocalDate startDate,
            Integer travelers,
            BigDecimal unitPrice,
            BigDecimal subtotal
    ) {
    }
}