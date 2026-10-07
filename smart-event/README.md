# SmartEvent Backend

SmartEvent is a REST API for a real-world event discovery and ticket booking platform.

## Features
- User Registration & Authentication (JWT, bcrypt)
- Event Discovery (Pagination, Search, Category Filtering)
- Secure Ticket Booking System
- Automatic QR Code Generation for Tickets
- Booking Management & Cancellation
- Notification System
- Robust Database Design with SQLAlchemy & MySQL

## Technology Stack
- **Python 3.11+**
- **FastAPI** & **Uvicorn**
- **MySQL** & **PyMySQL**
- **SQLAlchemy ORM**
- **Pydantic** for validation
- **pytest** for testing

## Folder Structure
```
smart-event/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── qr_codes/
│   ├── .env
│   ├── .env.example
│   └── requirements.txt
└── database/
    └── smart_event.sql
```

## MySQL Setup
1. Create a database named `smart_event` in MySQL.
2. You can use the provided SQL file:
```powershell
mysql -u root -p < database/smart_event.sql
```

## Environment Configuration
1. Navigate to the `backend` folder.
2. Copy `.env.example` to `.env` if not already created.
3. Update `.env` with your actual MySQL credentials and generate a strong `SECRET_KEY`.

## Installation & Running (Windows PowerShell)

```powershell
# Navigate to project
cd smart-event/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt

# Run the application
python -m uvicorn app.main --reload
```

## Swagger Documentation
Once the application is running, access the interactive API docs at:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Testing
Run the test suite using `pytest`. The tests use an in-memory SQLite database to avoid modifying your actual data.

```powershell
# Ensure virtual environment is active
.\venv\Scripts\activate

# Run tests
pytest
```

## API Workflows

### 🔐 Authentication Flow
1. **User Registration:** Client sends `POST /auth/register` with `username`, `email`, and `password`. Backend hashes the password using `bcrypt` and stores the user.
2. **User Login:** Client sends `POST /auth/login` (OAuth2 Form Data). Backend verifies credentials and returns a signed **JWT Access Token**.
3. **Authorized Requests:** Client includes `Authorization: Bearer <token>` in the header for all protected routes (e.g., viewing tickets, booking events). Backend decodes the JWT to identify the `current_user`.

### 🎟️ Booking Flow
1. **Browse Events:** Client fetches available events via `GET /events`.
2. **Initiate Booking:** Client sends `POST /bookings` with `event_id` and `ticket_quantity`.
3. **Transaction Execution (Atomic):**
   - Backend validates the event and checks `available_tickets >= ticket_quantity`.
   - Backend calculates `total_price` safely.
   - Backend creates the `Booking` record with `CONFIRMED` status.
   - Backend deducts `ticket_quantity` from the event's `available_tickets`.
   - Backend generates the Ticket & QR Code.
   - Backend generates a confirmation Notification.
   - Database transaction is **committed**.

### 📱 QR Ticket Flow
1. **Ticket Generation:** Upon a successful booking, a unique `ticket_code` (e.g., `TKT-A1B2C3D4`) is generated securely.
2. **QR Code Creation:** The backend serializes the ticket data to JSON and uses the `qrcode` library to generate a PNG image, saving it to `/qr_codes/`.
3. **Ticket Retrieval:** Client calls `GET /tickets/my`. The backend returns the tickets along with the `qr_code_url`.
4. **Verification:** Event staff scans the QR code, triggering a request to `GET /tickets/verify/{ticket_code}`. The backend returns whether the ticket is valid and if the booking is active.

### 🔔 Notification Flow
1. **System Triggers:** When specific actions occur (like booking an event or cancelling one), the respective backend service automatically creates a `Notification` record in the database for the user.
2. **Fetching Notifications:** The client polls or fetches `GET /notifications` and `GET /notifications/unread-count` to display alerts to the user.
3. **Marking as Read:** Once viewed, the client calls `PATCH /notifications/{notification_id}/read` to update the state.
