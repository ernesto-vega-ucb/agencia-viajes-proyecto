package com.agencia.bookingcore.web.controller;

import com.agencia.bookingcore.dto.BookingRequest;
import com.agencia.bookingcore.dto.BookingResponse;
import com.agencia.bookingcore.dto.CancelBookingResponse;
import com.agencia.bookingcore.dto.PaymentRequest;
import com.agencia.bookingcore.service.BookingService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/bookings")
@RequiredArgsConstructor
public class BookingController {

    private final BookingService bookingService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public BookingResponse createBooking(@Valid @RequestBody BookingRequest request,
                                         @AuthenticationPrincipal Jwt jwt) {
        return bookingService.createBooking(request, jwt);
    }

    @GetMapping("/me")
    public List<BookingResponse> listMyBookings(@AuthenticationPrincipal Jwt jwt) {
        return bookingService.listMyBookings(jwt);
    }

    @GetMapping("/{id}")
    public BookingResponse getBooking(@PathVariable Long id,
                                      @AuthenticationPrincipal Jwt jwt) {
        return bookingService.getBooking(id, jwt);
    }

    @PostMapping("/{id}/confirm")
    @PreAuthorize("hasAnyRole('AGENT', 'ADMIN')")
    public BookingResponse confirmBooking(@PathVariable Long id) {
        return bookingService.confirmBooking(id);
    }

    @PostMapping("/{id}/pay")
    public BookingResponse payBooking(@PathVariable Long id,
                                      @Valid @RequestBody PaymentRequest payment,
                                      @AuthenticationPrincipal Jwt jwt) {
        return bookingService.payBooking(id, payment, jwt);
    }

    @PostMapping("/{id}/cancel")
    public CancelBookingResponse cancelBooking(@PathVariable Long id,
                                               @AuthenticationPrincipal Jwt jwt) {
        return bookingService.cancelBooking(id, jwt);
    }
}