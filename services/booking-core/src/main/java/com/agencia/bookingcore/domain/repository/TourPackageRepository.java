package com.agencia.bookingcore.domain.repository;

import com.agencia.bookingcore.domain.entity.TourPackage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface TourPackageRepository extends JpaRepository<TourPackage, Long> {

    List<TourPackage> findByActiveTrue();

    Optional<TourPackage> findByIdAndActiveTrue(Long id);

    List<TourPackage> findByActiveTrueAndDestinationContainingIgnoreCase(String destination);

    @Query("""
            select p from TourPackage p
            where p.active = true
              and (:destination is null or lower(p.destination) like lower(concat('%', :destination, '%')))
              and (:category is null or lower(p.category) = lower(:category))
            order by p.rating desc
            """)
    List<TourPackage> search(@Param("destination") String destination,
                             @Param("category") String category);

    List<TourPackage> findByActiveTrueOrderByIdDesc();

    Optional<TourPackage> findByCode(String code);
}