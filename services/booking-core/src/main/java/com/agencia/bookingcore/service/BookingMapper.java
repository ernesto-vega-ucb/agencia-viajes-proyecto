package com.agencia.bookingcore.service;

import com.agencia.bookingcore.domain.entity.Booking;
import com.agencia.bookingcore.domain.entity.TourPackage;
import com.agencia.bookingcore.dto.BookingResponse;
import com.agencia.bookingcore.dto.TourPackageResponse;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class BookingMapper {

    public BookingResponse toResponse(Booking booking) {
        return new BookingResponse(
                booking.getId(),
                booking.getUser().getUserSub(),
                booking.getStatus(),
                booking.getCurrency(),
                booking.getTotalPrice(),
                booking.getCreatedAt(),
                booking.getItems().stream()
                        .map(item -> new BookingResponse.Item(
                                item.getId(),
                                item.getTourPackage().getId(),
                                item.getPackageTitle(),
                                item.getStartDate(),
                                item.getTravelers(),
                                item.getUnitPrice(),
                                item.getSubtotal()))
                        .toList());
    }

    public TourPackageResponse toResponse(TourPackage tourPackage) {
        return new TourPackageResponse(
                tourPackage.getId(),
                tourPackage.getCode(),
                tourPackage.getTitle(),
                tourPackage.getDestination(),
                tourPackage.getCountry(),
                tourPackage.getDescription(),
                tourPackage.getCategory(),
                tourPackage.getDurationDays(),
                tourPackage.getBasePrice(),
                tourPackage.getCurrency(),
                tourPackage.getMaxTravelers(),
                tourPackage.getCancelDaysBefore(),
                tourPackage.getCancelRefundPercent(),
                tourPackage.getRating(),
                tourPackage.getActive(),
                tourPackage.getImages() == null ? List.of() : List.copyOf(tourPackage.getImages()),
                tourPackage.getStartDates() == null ? List.of() : List.copyOf(tourPackage.getStartDates()),
                tourPackage.getSource() == null ? "MANUAL" : tourPackage.getSource());
    }
}