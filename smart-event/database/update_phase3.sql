-- Phase 3 Incremental Update Script for MySQL
-- Safe for MySQL Workbench (handles Safe Update Mode)

USE smart_event;

-- Disable Safe Update Mode temporarily for data migration
SET SQL_SAFE_UPDATES = 0;

-- 1. Create Coupons Table (if not exists)
CREATE TABLE IF NOT EXISTS coupons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coupon_code VARCHAR(50) NOT NULL UNIQUE,
    discount_type ENUM('PERCENTAGE', 'FIXED') NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL CHECK (discount_value > 0),
    minimum_booking_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (minimum_booking_amount >= 0),
    expiry_date DATETIME NOT NULL,
    usage_limit INT NULL,
    used_count INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_coupons_active (is_active)
);

-- 2. Populate final_amount for existing bookings (using primary key id > 0)
UPDATE bookings 
SET final_amount = total_price 
WHERE id > 0 AND (final_amount IS NULL OR final_amount = 0.00);

-- Foreign key & index for coupon_id on bookings
ALTER TABLE bookings
ADD CONSTRAINT fk_booking_coupon
FOREIGN KEY (coupon_id) REFERENCES coupons(id)
ON DELETE SET NULL;

CREATE INDEX idx_bookings_coupon ON bookings(coupon_id);

-- 3. Update Notifications Table with PAYMENT type & notification_type column
ALTER TABLE notifications
MODIFY COLUMN type ENUM('EVENT', 'BOOKING', 'PAYMENT', 'SYSTEM') NOT NULL;

ALTER TABLE notifications
ADD COLUMN notification_type ENUM('EVENT', 'BOOKING', 'PAYMENT', 'SYSTEM') NULL;

-- 4. Create Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    payment_method VARCHAR(50) NOT NULL DEFAULT 'simulation',
    payment_status ENUM('PENDING', 'SUCCESS', 'FAILED') NOT NULL DEFAULT 'PENDING',
    transaction_id VARCHAR(255) NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    INDEX idx_payments_booking (booking_id),
    INDEX idx_payments_status (payment_status),
    INDEX idx_payments_transaction (transaction_id)
);

-- 5. Create Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_event_review UNIQUE (user_id, event_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    INDEX idx_reviews_user (user_id),
    INDEX idx_reviews_event (event_id)
);

-- 6. Insert Default Sample Coupons
INSERT IGNORE INTO coupons (coupon_code, discount_type, discount_value, minimum_booking_amount, expiry_date, usage_limit, is_active) VALUES
('WELCOME10', 'PERCENTAGE', 10.00, 50.00, '2030-12-31 23:59:59', 100, TRUE),
('FLAT50', 'FIXED', 50.00, 100.00, '2030-12-31 23:59:59', 50, TRUE);

-- Re-enable Safe Update Mode
SET SQL_SAFE_UPDATES = 1;
