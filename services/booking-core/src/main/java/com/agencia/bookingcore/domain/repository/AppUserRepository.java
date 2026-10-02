package com.agencia.bookingcore.domain.repository;

import com.agencia.bookingcore.domain.entity.AppUser;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AppUserRepository extends JpaRepository<AppUser, Long> {

    Optional<AppUser> findByUserSub(String userSub);
}