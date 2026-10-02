CREATE TABLE app_user (
    id            BIGSERIAL PRIMARY KEY,
    user_sub      VARCHAR(256) NOT NULL UNIQUE,
    email         VARCHAR(256),
    display_name  VARCHAR(256),
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE tour_package (
    id                   BIGSERIAL PRIMARY KEY,
    code                 VARCHAR(64) NOT NULL UNIQUE,
    title                VARCHAR(256) NOT NULL,
    destination          VARCHAR(128) NOT NULL,
    country              VARCHAR(128) NOT NULL,
    description          TEXT NOT NULL,
    category             VARCHAR(64) NOT NULL,
    duration_days        INT NOT NULL,
    base_price           NUMERIC(12, 2) NOT NULL,
    currency             VARCHAR(8) NOT NULL DEFAULT 'EUR',
    max_travelers        INT NOT NULL DEFAULT 8,
    cancel_days_before   INT NOT NULL DEFAULT 15,
    cancel_refund_percent INT NOT NULL DEFAULT 100,
    rating               NUMERIC(3, 2) NOT NULL DEFAULT 4.5,
    active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE tour_package_image (
    id          BIGSERIAL PRIMARY KEY,
    package_id  BIGINT NOT NULL REFERENCES tour_package(id) ON DELETE CASCADE,
    position    INT NOT NULL,
    url         VARCHAR(512) NOT NULL
);

CREATE TABLE tour_package_start_date (
    id          BIGSERIAL PRIMARY KEY,
    package_id  BIGINT NOT NULL REFERENCES tour_package(id) ON DELETE CASCADE,
    start_date  DATE NOT NULL
);

CREATE TABLE booking (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES app_user(id),
    status      VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    currency    VARCHAR(8) NOT NULL DEFAULT 'EUR',
    total_price NUMERIC(12, 2) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE booking_item (
    id            BIGSERIAL PRIMARY KEY,
    booking_id    BIGINT NOT NULL REFERENCES booking(id) ON DELETE CASCADE,
    package_id    BIGINT NOT NULL REFERENCES tour_package(id),
    package_title VARCHAR(256) NOT NULL,
    start_date    DATE NOT NULL,
    travelers     INT NOT NULL,
    unit_price    NUMERIC(12, 2) NOT NULL,
    subtotal      NUMERIC(12, 2) NOT NULL
);

CREATE INDEX idx_booking_user ON booking(user_id);
CREATE INDEX idx_booking_item_booking ON booking_item(booking_id);
CREATE INDEX idx_tour_package_destination ON tour_package(destination);
CREATE INDEX idx_tour_package_category ON tour_package(category);