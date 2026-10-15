-- Phase 2 Update Script
-- Run this script on your existing 'smart_event' database to apply Phase 2 changes without losing data.

USE smart_event;

-- 1. Update Users Table (Add Role)
ALTER TABLE users
ADD COLUMN role ENUM('USER', 'ORGANIZER', 'ADMIN') NOT NULL DEFAULT 'USER';

-- 2. Update Events Table (Add Organizer and Status)
ALTER TABLE events
ADD COLUMN organizer_id INT NULL,
ADD COLUMN event_status ENUM('UPCOMING', 'ONGOING', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'UPCOMING';

ALTER TABLE events
ADD CONSTRAINT fk_event_organizer
FOREIGN KEY (organizer_id)
REFERENCES users(id)
ON DELETE SET NULL;

-- 3. Performance Indexes (For RBAC and Analytics)
CREATE INDEX idx_users_role ON users(role);

CREATE INDEX idx_events_organizer ON events(organizer_id);
CREATE INDEX idx_events_status ON events(event_status);
CREATE INDEX idx_events_date ON events(event_date);

CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_event ON bookings(event_id);
CREATE INDEX idx_bookings_status ON bookings(booking_status);

CREATE INDEX idx_tickets_booking ON tickets(booking_id);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- 4. Create Default Admin and Organizer (Optional, for testing)
INSERT IGNORE INTO users (username, email, hashed_password, role) VALUES
('admin', 'admin@example.com', '$2b$12$ThmVoNWcIzR/L67p9oZlEuOKcnt6tiwUC/E.6g/9u7xy7xylUR8CC', 'ADMIN'),
('organizer', 'org@example.com', '$2b$12$ThmVoNWcIzR/L67p9oZlEuOKcnt6tiwUC/E.6g/9u7xy7xylUR8CC', 'ORGANIZER');

-- 5. Assign existing events to the test organizer (Assuming organizer user has ID = 2 or higher)
-- You can modify this ID if your organizer account has a different ID
UPDATE events SET organizer_id = (SELECT id FROM users WHERE email = 'org@example.com' LIMIT 1) WHERE organizer_id IS NULL;
