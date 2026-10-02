package com.agencia.bookingcore.domain.entity;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OrderColumn;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "tour_package")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TourPackage {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 64)
    private String code;

    @Column(nullable = false, length = 256)
    private String title;

    @Column(nullable = false, length = 128)
    private String destination;

    @Column(nullable = false, length = 128)
    private String country;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String description;

    @Column(nullable = false, length = 64)
    private String category;

    @Column(name = "duration_days", nullable = false)
    private Integer durationDays;

    @Column(name = "base_price", nullable = false)
    private BigDecimal basePrice;

    @Column(nullable = false, length = 8)
    private String currency;

    @Column(name = "max_travelers", nullable = false)
    private Integer maxTravelers;

    @Column(name = "cancel_days_before", nullable = false)
    private Integer cancelDaysBefore;

    @Column(name = "cancel_refund_percent", nullable = false)
    private Integer cancelRefundPercent;

    @Column(nullable = false)
    private BigDecimal rating;

    @Column(nullable = false)
    private Boolean active;

    @Column(nullable = false, length = 32)
    @Builder.Default
    private String source = "MANUAL";

    @ElementCollection
    @CollectionTable(name = "tour_package_image", joinColumns = @JoinColumn(name = "package_id"))
    @OrderColumn(name = "position")
    @Column(name = "url", nullable = false, length = 512)
    private List<String> images = new ArrayList<>();

    @ElementCollection
    @CollectionTable(name = "tour_package_start_date", joinColumns = @JoinColumn(name = "package_id"))
    @Column(name = "start_date", nullable = false)
    private List<LocalDate> startDates = new ArrayList<>();
}