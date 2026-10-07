from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routers import auth, users, events, bookings, tickets, notifications
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema if needed
    Base.metadata.create_all(bind=engine)
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

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "SmartEvent Backend"}
