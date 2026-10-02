package com.agencia.bookingcore.service;

import com.agencia.bookingcore.domain.entity.Booking;
import com.agencia.bookingcore.domain.entity.BookingItem;
import com.agencia.bookingcore.domain.entity.TourPackage;
import com.agencia.bookingcore.domain.repository.TourPackageRepository;
import com.agencia.bookingcore.dto.BookingResponse;
import com.agencia.bookingcore.error.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.LocalDate;

@Component
@RequiredArgsConstructor
public class PricingService {

    private final TourPackageRepository packageRepository;

    public BookingItem buildItem(TourPackage tourPackage, LocalDate startDate, int travelers) {
        validateTravelers(tourPackage, travelers);
        validateStartDate(tourPackage, startDate);

        var unitPrice = tourPackage.getBasePrice();
        var subtotal = unitPrice.multiply(java.math.BigDecimal.valueOf(travelers));

        return BookingItem.builder()
                .tourPackage(tourPackage)
                .packageTitle(tourPackage.getTitle())
                .startDate(startDate)
                .travelers(travelers)
                .unitPrice(unitPrice)
                .subtotal(subtotal)
                .build();
    }

    public void validateTravelers(TourPackage tourPackage, int travelers) {
        if (travelers > tourPackage.getMaxTravelers()) {
            throw new BusinessException(
                    "El paquete " + tourPackage.getCode() + " admite máximo "
                            + tourPackage.getMaxTravelers() + " viajeros");
        }
    }

    public void validateStartDate(TourPackage tourPackage, LocalDate startDate) {
        if (!tourPackage.getStartDates().contains(startDate)) {
            throw new BusinessException(
                    "La fecha " + startDate + " no está disponible para el paquete "
                            + tourPackage.getCode());
        }
    }

    public int refundPercentage(Booking booking) {
        if (booking.getItems().isEmpty()) {
            return 0;
        }
        Long firstPackageId = booking.getItems().get(0).getTourPackage().getId();
        return packageRepository.findById(firstPackageId)
                .map(TourPackage::getCancelRefundPercent)
                .orElse(0);
    }
}