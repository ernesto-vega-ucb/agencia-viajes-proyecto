package com.agencia.bookingcore.service;

import com.agencia.bookingcore.domain.entity.TourPackage;
import com.agencia.bookingcore.domain.repository.TourPackageRepository;
import com.agencia.bookingcore.dto.TourPackageRequest;
import com.agencia.bookingcore.dto.TourPackageResponse;
import com.agencia.bookingcore.dto.TourPackageSyncRequest;
import com.agencia.bookingcore.error.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class TourPackageService {

    private final TourPackageRepository packageRepository;
    private final BookingMapper mapper;

    @Transactional(readOnly = true)
    public List<TourPackageResponse> listAll(String destination, String category) {
        List<TourPackage> packages;
        if (destination != null || category != null) {
            packages = packageRepository.search(destination, category);
        } else {
            packages = packageRepository.findByActiveTrueOrderByIdDesc();
        }
        return packages.stream().map(mapper::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public TourPackageResponse getById(Long id) {
        TourPackage tourPackage = packageRepository.findByIdAndActiveTrue(id)
                .orElseThrow(() -> new ResourceNotFoundException("Paquete no encontrado: " + id));
        return mapper.toResponse(tourPackage);
    }

    @Transactional(readOnly = true)
    public TourPackageResponse getByIdentifier(String identifier) {
        String code = identifier;
        if (identifier != null && identifier.matches("\\d+")) {
            Long id = Long.parseLong(identifier);
            Optional<TourPackage> byId = packageRepository.findByIdAndActiveTrue(id);
            if (byId.isPresent()) {
                return mapper.toResponse(byId.get());
            }
            code = codeForEngineId(id);
        }
        if (code == null) {
            throw new ResourceNotFoundException("Paquete no encontrado: " + identifier);
        }
        return packageRepository.findByCode(code)
                .filter(tourPackage -> Boolean.TRUE.equals(tourPackage.getActive()))
                .map(mapper::toResponse)
                .orElseThrow(() -> new ResourceNotFoundException("Paquete no encontrado: " + identifier));
    }

    private String codeForEngineId(long id) {
        if (id >= 9000 && id <= 9899) {
            return String.format("EXT-%03d", id - 9000);
        }
        if (id >= 8000 && id <= 8899) {
            return String.format("SYN-%03d", id - 8000);
        }
        return null;
    }

    @Transactional
    public TourPackageResponse create(TourPackageRequest request) {
        TourPackage tourPackage = TourPackage.builder()
                .code(request.code())
                .title(request.title())
                .destination(request.destination())
                .country(request.country())
                .description(request.description())
                .category(request.category())
                .durationDays(request.durationDays())
                .basePrice(request.basePrice())
                .currency(request.currency() == null ? "EUR" : request.currency())
                .maxTravelers(request.maxTravelers())
                .cancelDaysBefore(request.cancelDaysBefore())
                .cancelRefundPercent(request.cancelRefundPercent())
                .rating(request.rating())
                .active(true)
                .source(request.source() == null ? "MANUAL" : request.source())
                .images(request.images() == null ? List.of() : request.images())
                .startDates(request.startDates() == null ? List.of() : request.startDates())
                .build();
        return mapper.toResponse(packageRepository.save(tourPackage));
    }

    @Transactional
    public TourPackageResponse sync(TourPackageSyncRequest request) {
        TourPackage tourPackage = packageRepository.findByCode(request.code())
                .orElseGet(() -> TourPackage.builder().code(request.code()).build());
        tourPackage.setTitle(request.title());
        tourPackage.setDestination(request.destination());
        tourPackage.setCountry(request.country());
        tourPackage.setDescription(request.description());
        tourPackage.setCategory(request.category());
        tourPackage.setDurationDays(request.durationDays());
        tourPackage.setBasePrice(request.basePrice());
        tourPackage.setCurrency(request.currency() == null ? "EUR" : request.currency());
        tourPackage.setRating(request.rating());
        tourPackage.setMaxTravelers(request.maxTravelers() == null ? 8 : request.maxTravelers());
        tourPackage.setCancelDaysBefore(request.cancelDaysBefore() == null ? 15 : request.cancelDaysBefore());
        tourPackage.setCancelRefundPercent(request.cancelRefundPercent() == null ? 100 : request.cancelRefundPercent());
        tourPackage.setSource(request.source() == null ? "EXTERNO" : request.source());
        if (tourPackage.getActive() == null) {
            tourPackage.setActive(true);
        }
        tourPackage.setImages(request.images() == null ? List.of() : List.copyOf(request.images()));
        tourPackage.setStartDates(request.startDates() == null ? List.of() : List.copyOf(request.startDates()));
        return mapper.toResponse(packageRepository.save(tourPackage));
    }

    @Transactional
    public TourPackageResponse update(Long id, TourPackageRequest request) {
        TourPackage tourPackage = packageRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Paquete no encontrado: " + id));
        tourPackage.setCode(request.code());
        tourPackage.setTitle(request.title());
        tourPackage.setDestination(request.destination());
        tourPackage.setCountry(request.country());
        tourPackage.setDescription(request.description());
        tourPackage.setCategory(request.category());
        tourPackage.setDurationDays(request.durationDays());
        tourPackage.setBasePrice(request.basePrice());
        tourPackage.setCurrency(request.currency() == null ? "EUR" : request.currency());
        tourPackage.setMaxTravelers(request.maxTravelers());
        tourPackage.setCancelDaysBefore(request.cancelDaysBefore());
        tourPackage.setCancelRefundPercent(request.cancelRefundPercent());
        tourPackage.setRating(request.rating());
        tourPackage.setActive(true);
        tourPackage.setSource(request.source() == null ? "MANUAL" : request.source());
        tourPackage.setImages(request.images() == null ? List.of() : request.images());
        tourPackage.setStartDates(request.startDates() == null ? List.of() : request.startDates());
        return mapper.toResponse(packageRepository.save(tourPackage));
    }

    @Transactional
    public void delete(Long id) {
        TourPackage tourPackage = packageRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Paquete no encontrado: " + id));
        tourPackage.setActive(false);
        packageRepository.save(tourPackage);
    }
}