package com.agencia.bookingcore.service;

import com.agencia.bookingcore.domain.entity.AppUser;
import com.agencia.bookingcore.domain.entity.Booking;
import com.agencia.bookingcore.domain.entity.BookingItem;
import com.agencia.bookingcore.domain.entity.TourPackage;
import com.agencia.bookingcore.domain.enums.BookingStatus;
import com.agencia.bookingcore.domain.repository.AppUserRepository;
import com.agencia.bookingcore.domain.repository.BookingRepository;
import com.agencia.bookingcore.domain.repository.TourPackageRepository;
import com.agencia.bookingcore.dto.BookingRequest;
import com.agencia.bookingcore.dto.BookingResponse;
import com.agencia.bookingcore.dto.CancelBookingResponse;
import com.agencia.bookingcore.dto.PaymentRequest;
import com.agencia.bookingcore.error.BusinessException;
import com.agencia.bookingcore.error.ForbiddenException;
import com.agencia.bookingcore.error.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BookingService {

    private final BookingRepository bookingRepository;
    private final TourPackageRepository packageRepository;
    private final AppUserRepository userRepository;
    private final PricingService pricingService;
    private final BookingMapper mapper;

    @Transactional
    public BookingResponse createBooking(BookingRequest request, Jwt jwt) {
        AppUser user = resolveUser(jwt);
        Booking booking = Booking.builder()
                .user(user)
                .status(BookingStatus.PENDING)
                .currency("EUR")
                .totalPrice(BigDecimal.ZERO)
                .items(new java.util.ArrayList<>())
                .build();

        BigDecimal total = BigDecimal.ZERO;
        for (BookingRequest.BookingItemRequest item : request.items()) {
            TourPackage tourPackage = packageRepository.findByIdAndActiveTrue(item.packageId())
                    .orElseThrow(() -> new ResourceNotFoundException(
                            "Paquete no encontrado: " + item.packageId()));

            BookingItem bookingItem = pricingService.buildItem(
                    tourPackage, item.startDate(), item.travelers());
            booking.addItem(bookingItem);
            total = total.add(bookingItem.getSubtotal());
        }
        booking.setTotalPrice(total);

        Booking saved = bookingRepository.save(booking);
        return mapper.toResponse(saved);
    }

    @Transactional(readOnly = true)
    public BookingResponse getBooking(Long id, Jwt jwt) {
        Booking booking = findOwnedBooking(id, jwt);
        return mapper.toResponse(booking);
    }

    @Transactional(readOnly = true)
    public List<BookingResponse> listMyBookings(Jwt jwt) {
        return userRepository.findByUserSub(jwt.getSubject())
                .map(user -> bookingRepository.findByUser_IdOrderByCreatedAtDesc(user.getId()).stream()
                        .map(mapper::toResponse)
                        .toList())
                .orElse(List.of());
    }

    @Transactional
    public BookingResponse confirmBooking(Long id) {
        Booking booking = bookingRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Reserva no encontrada: " + id));
        if (!booking.getStatus().equals(BookingStatus.PENDING)) {
            throw new BusinessException("Solo las reservas PENDING pueden confirmarse");
        }
        booking.setStatus(BookingStatus.CONFIRMED);
        return mapper.toResponse(bookingRepository.save(booking));
    }

    @Transactional
    public BookingResponse payBooking(Long id, PaymentRequest payment, Jwt jwt) {
        Booking booking = findOwnedBooking(id, jwt);
        if (!booking.getStatus().equals(BookingStatus.CONFIRMED)) {
            throw new BusinessException("La reserva debe estar CONFIRMED antes de pagar");
        }
        if (payment.amount().compareTo(booking.getTotalPrice()) != 0) {
            throw new BusinessException(
                    "El importe (" + payment.amount() + ") no coincide con el total ("
                            + booking.getTotalPrice() + ")");
        }
        booking.setStatus(BookingStatus.PAID);
        return mapper.toResponse(bookingRepository.save(booking));
    }

    @Transactional
    public CancelBookingResponse cancelBooking(Long id, Jwt jwt) {
        Booking booking = findOwnedBooking(id, jwt);
        if (List.of(BookingStatus.PAID, BookingStatus.CANCELLED).contains(booking.getStatus())) {
            throw new BusinessException("La reserva no se puede cancelar en estado " + booking.getStatus());
        }
        int refundPercent = pricingService.refundPercentage(booking);
        BigDecimal refund = booking.getTotalPrice()
                .multiply(BigDecimal.valueOf(refundPercent))
                .divide(BigDecimal.valueOf(100));

        booking.setStatus(BookingStatus.CANCELLED);
        bookingRepository.save(booking);

        return new CancelBookingResponse(
                booking.getId(),
                booking.getStatus().name(),
                booking.getTotalPrice(),
                refund,
                "Reembolso estimado del " + refundPercent + "%");
    }

    private Booking findOwnedBooking(Long id, Jwt jwt) {
        Booking booking = bookingRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Reserva no encontrada: " + id));
        if (!booking.getUser().getUserSub().equals(jwt.getSubject())) {
            throw new ForbiddenException("No tienes acceso a esta reserva");
        }
        return booking;
    }

    private AppUser resolveUser(Jwt jwt) {
        return findOrCreate(jwt.getSubject(), jwt);
    }

    private AppUser findOrCreate(String subject, Jwt jwt) {
        return userRepository.findByUserSub(subject).orElseGet(() -> {
            AppUser user = AppUser.builder()
                    .userSub(subject)
                    .email(jwt.getClaimAsString("email"))
                    .displayName(jwt.getClaimAsString("preferred_username"))
                    .build();
            return userRepository.save(user);
        });
    }
}