CREATE DATABASE IF NOT EXISTS smart_event;
USE smart_event;

-- 1. USERS
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('USER', 'ORGANIZER', 'ADMIN') NOT NULL DEFAULT 'USER',
    phone_number VARCHAR(20) NULL,
    location VARCHAR(100) NULL,
    full_name VARCHAR(100) NULL,
    bio TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- 2. EVENTS
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category ENUM('Music', 'Tech', 'Sports', 'Business') NOT NULL,
    location VARCHAR(255) NOT NULL,
    event_date DATETIME NOT NULL,
    ticket_price DECIMAL(10, 2) NOT NULL CHECK (ticket_price >= 0),
    total_tickets INT NOT NULL CHECK (total_tickets > 0),
    available_tickets INT NOT NULL CHECK (available_tickets >= 0),
    banner_image VARCHAR(255),
    organizer_id INT,
    event_status ENUM('UPCOMING', 'ONGOING', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'UPCOMING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tickets CHECK (available_tickets <= total_tickets),
    FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX idx_events_organizer ON events(organizer_id);
CREATE INDEX idx_events_status ON events(event_status);
CREATE INDEX idx_events_date ON events(event_date);

-- 3. COUPONS
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_coupons_code ON coupons(coupon_code);
CREATE INDEX idx_coupons_active ON coupons(is_active);

-- 4. BOOKINGS
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    ticket_quantity INT NOT NULL CHECK (ticket_quantity > 0),
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    coupon_id INT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    final_amount DECIMAL(10, 2) NOT NULL CHECK (final_amount >= 0),
    booking_status ENUM('PENDING', 'CONFIRMED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (coupon_id) REFERENCES coupons(id) ON DELETE SET NULL
);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_event ON bookings(event_id);
CREATE INDEX idx_bookings_status ON bookings(booking_status);
CREATE INDEX idx_bookings_coupon ON bookings(coupon_id);

-- 5. TICKETS
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    ticket_code VARCHAR(100) NOT NULL UNIQUE,
    qr_code_url VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);
CREATE INDEX idx_tickets_booking ON tickets(booking_id);
CREATE INDEX idx_tickets_code ON tickets(ticket_code);

-- 6. NOTIFICATIONS
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('EVENT', 'BOOKING', 'PAYMENT', 'SYSTEM') NOT NULL,
    notification_type ENUM('EVENT', 'BOOKING', 'PAYMENT', 'SYSTEM') NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- 7. PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    payment_method VARCHAR(50) NOT NULL DEFAULT 'simulation',
    payment_status ENUM('PENDING', 'SUCCESS', 'FAILED') NOT NULL DEFAULT 'PENDING',
    transaction_id VARCHAR(255) NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);
CREATE INDEX idx_payments_booking ON payments(booking_id);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_payments_transaction ON payments(transaction_id);

-- 8. REVIEWS
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
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_event ON reviews(event_id);

-- 9. WISHLISTS
CREATE TABLE IF NOT EXISTS wishlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_event_wishlist UNIQUE (user_id, event_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX idx_wishlists_user ON wishlists(user_id);
CREATE INDEX idx_wishlists_event ON wishlists(event_id);

-- 10. EVENT UPDATES
CREATE TABLE IF NOT EXISTS event_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX idx_event_updates_event ON event_updates(event_id);

-- 11. EVENT VIEWS
CREATE TABLE IF NOT EXISTS event_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    user_id INT NULL,
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX idx_event_views_event ON event_views(event_id);
CREATE INDEX idx_event_views_user ON event_views(user_id);

-- 12. CHAT HISTORY
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_chat_history_user ON chat_history(user_id);

-- Sample Initial Data
INSERT IGNORE INTO users (username, email, hashed_password, role) VALUES
('admin', 'admin@example.com', '$2b$12$ThmVoNWcIzR/L67p9oZlEuOKcnt6tiwUC/E.6g/9u7xy7xylUR8CC', 'ADMIN'),
('organizer', 'org@example.com', '$2b$12$ThmVoNWcIzR/L67p9oZlEuOKcnt6tiwUC/E.6g/9u7xy7xylUR8CC', 'ORGANIZER'),
('user', 'user@example.com', '$2b$12$ThmVoNWcIzR/L67p9oZlEuOKcnt6tiwUC/E.6g/9u7xy7xylUR8CC', 'USER');

INSERT IGNORE INTO coupons (coupon_code, discount_type, discount_value, minimum_booking_amount, expiry_date, usage_limit, is_active) VALUES
('WELCOME10', 'PERCENTAGE', 10.00, 50.00, '2030-12-31 23:59:59', 100, TRUE),
('FLAT50', 'FIXED', 50.00, 100.00, '2030-12-31 23:59:59', 50, TRUE);

INSERT IGNORE INTO events (title, description, category, location, event_date, ticket_price, total_tickets, available_tickets, organizer_id, event_status)
VALUES 
('Summer Music Festival', 'The biggest music festival of the year.', 'Music', 'Central Park', '2026-08-15 18:00:00', 50.00, 1000, 1000, 2, 'COMPLETED'),
('Tech Conference 2026', 'Future of AI and Web Development.', 'Tech', 'Convention Center', '2026-09-10 09:00:00', 150.00, 500, 500, 2, 'COMPLETED'),
('Local Marathon', 'Annual city marathon.', 'Sports', 'City Square', '2026-10-05 06:00:00', 20.00, 2000, 2000, 2, 'COMPLETED'),
('Startup Pitch Night', 'Watch startups pitch their ideas.', 'Business', 'Innovation Hub', '2026-11-20 19:00:00', 15.00, 200, 200, 2, 'UPCOMING');
