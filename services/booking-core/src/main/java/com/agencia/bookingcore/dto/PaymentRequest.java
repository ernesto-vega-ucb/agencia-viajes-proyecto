package com.agencia.bookingcore.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public record PaymentRequest(
        @NotNull @Size(min = 3, max = 16) String method,
        @NotNull @PositiveOrZero BigDecimal amount
) {
}