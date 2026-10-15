# SmartEvent Backend – Phase 4

SmartEvent is a complete, production-ready REST & WebSocket API for an event discovery, ticket booking, real-time collaboration, and AI-assisted platform.
This project is **STRICTLY BACKEND ONLY** (FastAPI + MySQL).

---

## Features Overview

- **Phase 1 (Core Booking Platform):**
  - User Authentication (JWT, bcrypt password hashing).
  - Event Discovery, Pagination, and Details.
  - Concurrency-safe Booking System with Ticket Quantity updates.
  - Automatic QR Code Generation for confirmed tickets.
  - In-app Notification System.

- **Phase 2 (Role-Based Management & Lifecycle):**
  - Role-Based Access Control: `USER`, `ORGANIZER`, `ADMIN`.
  - Organizer Event Management (Create, Update, Cancel own events).
  - Organizer Booking Analytics and Ticket Sales.
  - Event Lifecycle Management (`UPCOMING` → `ONGOING` → `COMPLETED` / `CANCELLED`).
  - Admin User & Event Management, plus Platform Revenue Analytics.
  - Event Cancellation & Update Notifications.

- **Phase 3 (Enterprise Payments, Discounts, Ratings & Discovery):**
  - **Module 12: Event Payment System** (`POST /payments/checkout`, simulation & Stripe webhook).
  - **Module 13: Coupon and Discount System** (`POST /coupons/validate`, Admin management).
  - **Module 14: Event Feedback and Ratings** (`POST /events/{id}/reviews`, ratings & statistics).
  - **Module 15: Advanced Notification System** (`EVENT`, `BOOKING`, `PAYMENT`, `SYSTEM`).
  - **Module 16: Advanced Event Search and Filtering** (multi-parameter querying, popularity sort).

- **Phase 4 (Real-Time Experience, Personalization & AI Features):**
  - **Module 18: Real-Time Seat Availability and Booking Updates**
    - Instant ticket availability endpoint: `GET /events/{id}/availability`.
    - Live WebSocket channel: `WS /ws/events/{id}/availability` broadcasting real-time seat decrement / release upon booking confirmation or cancellation.
    - Prevents overbooking with concurrency-safe calculations and instant UI synchronization.
  - **Module 19: Personalized Event Recommendations**
    - Track event interactions: `POST /events/{id}/view` (authenticated or guest session).
    - Intelligent user recommendations: `GET /recommendations/for-you` (analyzes booking history, category preferences, and user location).
    - Trending events feed: `GET /recommendations/trending` (algorithmic weighting of confirmed tickets and recent view volume).
    - Similar events engine: `GET /recommendations/similar/{event_id}` (category, price point, and proximity matching).
  - **Module 20: Wishlist / Save Events**
    - Save favorite events: `POST /wishlist` and remove via `DELETE /wishlist/{event_id}`.
    - Fetch user's active saved events: `GET /wishlist` (with event details and availability).
    - Instant status check: `GET /wishlist/{event_id}/status`.
  - **Module 21: Live Event Updates & Announcements**
    - Organizer & Admin announcements: `POST /events/{id}/updates`.
    - Retrieve timeline: `GET /events/{id}/updates`.
    - Edit / delete updates: `PUT /event-updates/{id}`, `DELETE /event-updates/{id}`.
    - Live WebSocket announcements feed: `WS /ws/events/{id}/updates`.
    - Automatically dispatches in-app notifications to all confirmed attendees.
  - **Module 22: User Profile Enhancements**
    - Extended profiles: `full_name`, `phone_number`, `location`, `bio`.
    - Profile management: `GET /users/me`, `PATCH /users/me`.
    - Comprehensive booking summary: `GET /users/me/booking-summary` (total bookings, tickets, spend, active vs cancelled).
    - User activity timeline: `GET /users/me/activity` (combined chronologic log of bookings, reviews, wishlists, and views).
  - **Module 23: Advanced Search & Smart Filters**
    - Retains full backward compatibility with Phase 3 search features (`GET /events`).
    - Robust parameter validation, multi-criteria filtering, price/date ranges, and sorting.
  - **Module 24: AI Chatbot Assistant**
    - Intelligent conversational assistant: `POST /chatbot/chat`.
    - Answers booking, cancellation, refund, payment, and coupon FAQs.
    - Resolves real-time event recommendations, trending highlights, and user booking summaries directly from database state.
    - Chat history persistence: `GET /chatbot/history`, `DELETE /chatbot/history`.
    - Health check: `GET /chatbot/health`.

---

## Technology Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI & Starlette
- **Real-Time Communication:** WebSockets (`fastapi.WebSocket`, asyncio broadcast manager)
- **ASGI Server:** Uvicorn
- **Database:** MySQL 8.0+
- **Driver & ORM:** PyMySQL, SQLAlchemy 2.0+
- **Data Validation:** Pydantic V2 & Pydantic-Settings
- **Security:** Python-JOSE (JWT), bcrypt
- **Payments:** Stripe SDK & Built-in Payment Simulator
- **QR Codes:** qrcode, Pillow
- **Testing:** pytest, httpx

---

## Project Structure

```text
smart-event/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   ├── booking.py
│   │   │   ├── ticket.py
│   │   │   ├── notification.py
│   │   │   ├── payment.py
│   │   │   ├── coupon.py
│   │   │   ├── review.py
│   │   │   ├── wishlist.py          # Phase 4
│   │   │   ├── event_update.py      # Phase 4
│   │   │   ├── event_view.py        # Phase 4
│   │   │   └── chat_history.py      # Phase 4
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── user.py              # Phase 4 profile schemas
│   │   │   ├── event.py
│   │   │   ├── booking.py
│   │   │   ├── ticket.py
│   │   │   ├── notification.py
│   │   │   ├── organizer.py
│   │   │   ├── admin.py
│   │   │   ├── payment.py
│   │   │   ├── coupon.py
│   │   │   ├── review.py
│   │   │   ├── wishlist.py          # Phase 4
│   │   │   ├── event_update.py      # Phase 4
│   │   │   └── chatbot.py           # Phase 4
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py             # Phase 4 profile endpoints
│   │   │   ├── events.py            # Phase 4 availability & view endpoints
│   │   │   ├── bookings.py
│   │   │   ├── tickets.py
│   │   │   ├── notifications.py
│   │   │   ├── organizer.py
│   │   │   ├── admin.py
│   │   │   ├── payments.py
│   │   │   ├── coupons.py
│   │   │   ├── reviews.py
│   │   │   ├── websockets.py        # Phase 4 WebSockets
│   │   │   ├── wishlist.py          # Phase 4
│   │   │   ├── event_updates.py     # Phase 4
│   │   │   ├── recommendations.py   # Phase 4
│   │   │   └── chatbot.py           # Phase 4
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── booking_service.py
│   │   │   ├── ticket_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── event_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── payment_service.py
│   │   │   ├── coupon_service.py
│   │   │   ├── review_service.py
│   │   │   ├── availability_service.py    # Phase 4
│   │   │   ├── recommendation_service.py  # Phase 4
│   │   │   └── chatbot_service.py         # Phase 4
│   │   └── utils/
│   │       ├── dependencies.py
│   │       ├── qr_generator.py
│   │       └── websocket_manager.py       # Phase 4
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_authorization.py
│   │   ├── test_rbac.py
│   │   ├── test_events.py
│   │   ├── test_event_search.py
│   │   ├── test_bookings.py
│   │   ├── test_tickets.py
│   │   ├── test_notifications.py
│   │   ├── test_organizer.py
│   │   ├── test_admin.py
│   │   ├── test_payments.py
│   │   ├── test_coupons.py
│   │   ├── test_reviews.py
│   │   ├── test_availability.py           # Phase 4
│   │   ├── test_recommendations.py        # Phase 4
│   │   ├── test_wishlist.py               # Phase 4
│   │   ├── test_event_updates.py          # Phase 4
│   │   ├── test_profile.py                # Phase 4
│   │   └── test_chatbot.py                # Phase 4
│   ├── qr_codes/
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
├── database/
│   ├── smart_event.sql       # Unified SQL schema (Phases 1-4)
│   ├── update_phase2.sql     # Migration Phase 1 -> Phase 2
│   ├── update_phase3.sql     # Migration Phase 2 -> Phase 3
│   └── update_phase4.sql     # Migration Phase 3 -> Phase 4
├── schema.sql                # Root schema copy
└── README.md
```

---

## Database Setup & Migrations

### Option A: Complete Database Setup (Fresh Install)
Run the complete unified SQL script:
```powershell
mysql -u root -p < database/smart_event.sql
```

### Option B: Incremental Migration on Existing Database
If you already ran Phase 1, Phase 2, and Phase 3, apply the Phase 4 incremental migration script safely without losing data:
```powershell
mysql -u root -p < database/update_phase4.sql
```
*(The script uses idempotent procedures so it will not cause duplicate column errors if executed multiple times.)*

---

## Environment Configuration

Create or update `smart-event/backend/.env`:
```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/smart_event
TEST_DATABASE_URL=sqlite:///./test.db
SECRET_KEY=replace-with-a-secure-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
QR_CODE_DIR=qr_codes

# Default Admin (automatically seeded on startup if not present)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# Phase 3: Payment Configuration
PAYMENT_PROVIDER=simulation
PAYMENT_SIMULATION_ENABLED=true

# Stripe (Optional - for live test mode)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_SUCCESS_URL=http://localhost:8000/payments/success
STRIPE_CANCEL_URL=http://localhost:8000/payments/cancel

# Phase 4: AI & Real-Time Configuration
AI_PROVIDER=fallback
AI_API_KEY=
AI_MODEL=gemini-1.5-flash
```

---

## Installation & Running (Windows PowerShell)

```powershell
# 1. Navigate to backend directory
cd "smart-event\backend"

# 2. Activate virtual environment
.\venv\Scripts\activate

# 3. Install dependencies
python -m pip install -r requirements.txt

# 4. Start the application
python -m uvicorn app.main:app --reload
```

Interactive API documentation:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Phase 4 API Reference

### 1. Real-Time Seat Availability
- `GET /events/{id}/availability`: Get remaining tickets, total capacity, and tickets sold.
- `WS /ws/events/{id}/availability`: WebSocket connection sending real-time seat updates when tickets are booked or released.

### 2. Personalized Recommendations & Views
- `POST /events/{id}/view`: Register an event view.
- `GET /recommendations/for-you`: Get personalized event suggestions based on booking history and location.
- `GET /recommendations/trending`: Get trending events scored by confirmed ticket sales and view volume.
- `GET /recommendations/similar/{event_id}`: Get similar events by category and price tier.

### 3. Wishlist Management
- `POST /wishlist`: Save an event to user wishlist (`{"event_id": 1}`).
- `GET /wishlist`: Retrieve all saved events for current user.
- `GET /wishlist/{event_id}/status`: Check if event is bookmarked (`{"is_wishlisted": true/false}`).
- `DELETE /wishlist/{event_id}`: Remove an event from wishlist.

### 4. Live Event Updates & Announcements
- `POST /events/{id}/updates`: Post an announcement (Organizer of event or Admin).
- `GET /events/{id}/updates`: View chronological list of announcements for an event.
- `PUT /event-updates/{update_id}`: Edit an existing announcement.
- `DELETE /event-updates/{update_id}`: Delete an announcement.
- `WS /ws/events/{id}/updates`: WebSocket connection for real-time live announcements.

### 5. User Profile Enhancements
- `GET /users/me`: View enhanced profile (`full_name`, `phone_number`, `location`, `bio`).
- `PATCH /users/me`: Update profile fields.
- `GET /users/me/booking-summary`: Aggregate statistics (total bookings, tickets, amount spent).
- `GET /users/me/activity`: Chronological user activity stream (bookings, reviews, wishlist saves, views).

### 6. AI Chatbot Assistant
- `POST /chatbot/chat`: Send prompt to chatbot. Supports FAQs, booking status queries, and recommendations.
- `GET /chatbot/history`: Retrieve past conversation history.
- `DELETE /chatbot/history`: Clear chat logs.
- `GET /chatbot/health`: Check chatbot system status.

---

## Automated Testing

Run the full pytest suite:
```powershell
python -m pytest
```

All **42 automated test suites** execute against an isolated SQLite test database covering:
- Authentication & RBAC permissions (`USER`, `ORGANIZER`, `ADMIN`).
- Payment checkout, simulation, idempotency, and anti-duplicate rules.
- Coupon calculations, expiration, usage limits, and booking integration.
- Attendee review submission, ratings, and attendance verification.
- Notification dispatching, reading, and unread filtering.
- Advanced event search, price/date validation, and popularity sorting.
- Real-time seat availability REST & WebSockets.
- Personalized recommendations, trending events, and similar events.
- Wishlist add, remove, and status queries.
- Live event announcements and WebSocket feed.
- User profile updates, booking summary, and activity timeline.
- AI Chatbot queries, FAQs, history logging, and health checks.
