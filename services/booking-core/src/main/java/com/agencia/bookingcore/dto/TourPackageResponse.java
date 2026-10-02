package com.agencia.bookingcore.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record TourPackageResponse(
        Long id,
        String code,
        String title,
        String destination,
        String country,
        String description,
        String category,
        Integer durationDays,
        BigDecimal basePrice,
        String currency,
        Integer maxTravelers,
        Integer cancelDaysBefore,
        Integer cancelRefundPercent,
        BigDecimal rating,
        Boolean active,
        List<String> images,
        List<LocalDate> startDates,
        String source
) {
}