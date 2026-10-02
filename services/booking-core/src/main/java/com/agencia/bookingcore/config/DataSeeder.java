package com.agencia.bookingcore.config;

import com.agencia.bookingcore.domain.entity.TourPackage;
import com.agencia.bookingcore.domain.repository.TourPackageRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Component
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    private final TourPackageRepository packageRepository;

    @Override
    public void run(String... args) {
        if (packageRepository.count() > 0) {
            return;
        }

        packageRepository.saveAll(List.of(
                TourPackage.builder()
                        .code("PVP-CUN-001")
                        .title("Todo incluido en la Riviera Maya")
                        .destination("Cancún")
                        .country("México")
                        .description("7 días todo incluido en hotel 5 estrellas frente al Caribe, con tours a Tulum y snorkel.")
                        .category("playa")
                        .durationDays(7)
                        .basePrice(new BigDecimal("1250.00"))
                        .currency("EUR")
                        .maxTravelers(4)
                        .cancelDaysBefore(14)
                        .cancelRefundPercent(100)
                        .rating(new BigDecimal("4.8"))
                        .active(true)
                        .images(List.of("https://picsum.photos/seed/cancun/600/400"))
                        .startDates(List.of(LocalDate.now().plusWeeks(2), LocalDate.now().plusWeeks(5)))
                        .build(),

                TourPackage.builder()
                        .code("PVP-LIS-001")
                        .title("Escapada urbana a Lisboa")
                        .destination("Lisboa")
                        .country("Portugal")
                        .description("Fin de semana en Lisboa: city tour, fado y degustación de vinos del Duero.")
                        .category("ciudad")
                        .durationDays(3)
                        .basePrice(new BigDecimal("420.00"))
                        .currency("EUR")
                        .maxTravelers(6)
                        .cancelDaysBefore(7)
                        .cancelRefundPercent(50)
                        .rating(new BigDecimal("4.6"))
                        .active(true)
                        .images(List.of("https://picsum.photos/seed/lisboa/600/400"))
                        .startDates(List.of(LocalDate.now().plusDays(10), LocalDate.now().plusDays(24)))
                        .build(),

                TourPackage.builder()
                        .code("PVP-AND-001")
                        .title("Aventura en los Andes")
                        .destination("Cusco")
                        .country("Perú")
                        .description("Trekking a Machu Picchu con guías certificados, camping y transporte incluido.")
                        .category("aventura")
                        .durationDays(6)
                        .basePrice(new BigDecimal("980.00"))
                        .currency("EUR")
                        .maxTravelers(8)
                        .cancelDaysBefore(21)
                        .cancelRefundPercent(100)
                        .rating(new BigDecimal("4.9"))
                        .active(true)
                        .images(List.of("https://picsum.photos/seed/cusco/600/400"))
                        .startDates(List.of(LocalDate.now().plusWeeks(3), LocalDate.now().plusWeeks(8)))
                        .build(),

                TourPackage.builder()
                        .code("PVP-BCN-001")
                        .title("Costa Brava en familia")
                        .destination("Costa Brava")
                        .country("España")
                        .description("Semana de descanso en la Costa Brava con actividades familiares y media pensión.")
                        .category("familiar")
                        .durationDays(7)
                        .basePrice(new BigDecimal("780.00"))
                        .currency("EUR")
                        .maxTravelers(6)
                        .cancelDaysBefore(10)
                        .cancelRefundPercent(75)
                        .rating(new BigDecimal("4.4"))
                        .active(true)
                        .images(List.of("https://picsum.photos/seed/brava/600/400"))
                        .startDates(List.of(LocalDate.now().plusDays(15), LocalDate.now().plusDays(30)))
                        .build()));
    }
}