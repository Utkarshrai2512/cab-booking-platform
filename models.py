from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="rider")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    driver: Mapped["Driver"] = relationship(back_populates="user", uselist=False)

class Driver(Base):
    __tablename__ = "drivers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    vehicle_number: Mapped[str] = mapped_column(String(30))
    vehicle_type: Mapped[str] = mapped_column(String(40), default="Sedan")
    is_available: Mapped[bool] = mapped_column(Boolean, default=False)
    user: Mapped["User"] = relationship(back_populates="driver")

class Ride(Base):
    __tablename__ = "rides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    pickup: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    distance_km: Mapped[float] = mapped_column(Float)
    fare: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="requested")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ride_id: Mapped[int] = mapped_column(ForeignKey("rides.id"), unique=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
