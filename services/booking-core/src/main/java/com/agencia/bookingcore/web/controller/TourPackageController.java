package com.agencia.bookingcore.web.controller;

import com.agencia.bookingcore.dto.TourPackageRequest;
import com.agencia.bookingcore.dto.TourPackageResponse;
import com.agencia.bookingcore.dto.TourPackageSyncRequest;
import com.agencia.bookingcore.service.TourPackageService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/packages")
@RequiredArgsConstructor
public class TourPackageController {

    private final TourPackageService tourPackageService;

    @GetMapping
    public List<TourPackageResponse> listPackages(
            @RequestParam(required = false) String destination,
            @RequestParam(required = false) String category) {
        return tourPackageService.listAll(destination, category);
    }

    @GetMapping("/{id}")
    public TourPackageResponse getPackage(@PathVariable String id) {
        return tourPackageService.getByIdentifier(id);
    }

    @PostMapping("/sync")
    public TourPackageResponse syncPackage(@Valid @RequestBody TourPackageSyncRequest request) {
        return tourPackageService.sync(request);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasRole('ADMIN')")
    public TourPackageResponse createPackage(@Valid @RequestBody TourPackageRequest request) {
        return tourPackageService.create(request);
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public TourPackageResponse updatePackage(@PathVariable Long id,
                                             @Valid @RequestBody TourPackageRequest request) {
        return tourPackageService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @PreAuthorize("hasRole('ADMIN')")
    public void deletePackage(@PathVariable Long id) {
        tourPackageService.delete(id);
    }
}