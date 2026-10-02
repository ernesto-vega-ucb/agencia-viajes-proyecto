package com.agencia.bookingcore.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.time.LocalDate;
import java.util.List;

public record BookingRequest(
        @NotNull @Valid @NotEmpty List<BookingItemRequest> items
) {
    public record BookingItemRequest(
            @NotNull Long packageId,
            @NotNull LocalDate startDate,
            @NotNull @Positive Integer travelers
    ) {
    }
}