package com.agencia.bookingcore.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record TourPackageSyncRequest(
        @NotBlank @Size(max = 64) String code,
        @NotBlank @Size(max = 256) String title,
        @NotBlank @Size(max = 128) String destination,
        @NotBlank @Size(max = 128) String country,
        @NotBlank String description,
        @NotBlank @Size(max = 64) String category,
        @NotNull @Positive Integer durationDays,
        @NotNull @Positive BigDecimal basePrice,
        @Size(max = 8) String currency,
        @NotNull @DecimalMin("0.0") @DecimalMax("5.0") BigDecimal rating,
        @Size(max = 32) String source,
        Integer maxTravelers,
        Integer cancelDaysBefore,
        Integer cancelRefundPercent,
        List<String> images,
        List<LocalDate> startDates
) {
}