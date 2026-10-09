from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routers import auth, users, events, bookings, tickets, notifications, organizer, admin
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema if needed
    Base.metadata.create_all(bind=engine)
    
    # Initialize Default Admin
    from app.core.database import SessionLocal
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    from app.core.config import settings
    import os
    
    db = SessionLocal()
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if not admin_user:
        hashed_pw = get_password_hash(admin_pass)
        new_admin = User(
            username="admin",
            email=admin_email,
            hashed_password=hashed_pw,
            role=UserRole.ADMIN
        )
        db.add(new_admin)
        db.commit()
    db.close()
    
    yield

app = FastAPI(
    title="SmartEvent API",
    description="Backend REST API for Event Discovery & Ticket Booking System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(bookings.router)
app.include_router(tickets.router)
app.include_router(notifications.router)
app.include_router(organizer.router)
app.include_router(admin.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "SmartEvent Backend"}
