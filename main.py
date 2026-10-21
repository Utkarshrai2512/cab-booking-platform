from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import Base, engine, get_db
from app.models import User, Driver, Ride, Review
from app.schemas import RegisterIn, LoginIn, TokenOut, DriverCreate, AvailabilityIn, RideEstimateIn, RideOut, StatusIn, ReviewIn
from app.security import hash_password, verify_password, create_access_token, current_user, require_role

FARE_BASE = 50.0
FARE_PER_KM = 14.0
VALID_STATUSES = {"accepted", "ongoing", "completed", "cancelled"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Cab Booking Platform API",
    description="Student backend project using FastAPI, PostgreSQL, JWT and Docker.",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/")
def root():
    return {"message": "Cab Booking Platform API is running", "docs": "/docs"}

@app.post("/auth/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.role not in {"rider", "driver"}:
        raise HTTPException(400, "Role must be rider or driver")
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email is already registered")
    user = User(name=data.name.strip(), email=data.email.lower(),
                password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id, user.role)}

@app.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_access_token(user.id, user.role)}

@app.get("/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

@app.post("/drivers/profile", status_code=201)
def create_driver_profile(data: DriverCreate, db: Session = Depends(get_db),
                          user: User = Depends(require_role("driver"))):
    existing = db.scalar(select(Driver).where(Driver.user_id == user.id))
    if existing:
        raise HTTPException(409, "Driver profile already exists")
    driver = Driver(user_id=user.id, vehicle_number=data.vehicle_number.upper(),
                    vehicle_type=data.vehicle_type, is_available=False)
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return {"id": driver.id, "vehicle_number": driver.vehicle_number,
            "vehicle_type": driver.vehicle_type, "is_available": driver.is_available}

@app.patch("/drivers/availability")
def set_availability(data: AvailabilityIn, db: Session = Depends(get_db),
                     user: User = Depends(require_role("driver"))):
    driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
    if not driver:
        raise HTTPException(404, "Create a driver profile first")
    driver.is_available = data.is_available
    db.commit()
    return {"is_available": driver.is_available}

@app.get("/drivers/available")
def available_drivers(db: Session = Depends(get_db), user: User = Depends(current_user)):
    drivers = db.scalars(select(Driver).where(Driver.is_available.is_(True))).all()
    return [{"id": d.id, "name": d.user.name, "vehicle_type": d.vehicle_type,
             "vehicle_number": d.vehicle_number} for d in drivers]

@app.post("/rides/estimate")
def estimate(data: RideEstimateIn, user: User = Depends(current_user)):
    fare = round(FARE_BASE + FARE_PER_KM * data.distance_km, 2)
    return {"pickup": data.pickup, "destination": data.destination,
            "distance_km": data.distance_km, "base_fare": FARE_BASE,
            "rate_per_km": FARE_PER_KM, "estimated_fare": fare, "currency": "INR"}

@app.post("/rides/request", response_model=RideOut, status_code=201)
def request_ride(data: RideEstimateIn, db: Session = Depends(get_db),
                 user: User = Depends(require_role("rider"))):
    fare = round(FARE_BASE + FARE_PER_KM * data.distance_km, 2)
    ride = Ride(rider_id=user.id, pickup=data.pickup, destination=data.destination,
                distance_km=data.distance_km, fare=fare, status="requested")
    db.add(ride)
    db.commit()
    db.refresh(ride)
    return ride

@app.post("/rides/{ride_id}/accept", response_model=RideOut)
def accept_ride(ride_id: int, db: Session = Depends(get_db),
                user: User = Depends(require_role("driver"))):
    driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
    if not driver or not driver.is_available:
        raise HTTPException(400, "Create a driver profile and set availability to true")
    ride = db.get(Ride, ride_id)
    if not ride:
        raise HTTPException(404, "Ride not found")
    if ride.status != "requested" or ride.driver_id is not None:
        raise HTTPException(409, "Ride is no longer available")
    ride.driver_id = driver.id
    ride.status = "accepted"
    driver.is_available = False
    db.commit()
    db.refresh(ride)
    return ride

@app.patch("/rides/{ride_id}/status", response_model=RideOut)
def update_ride_status(ride_id: int, data: StatusIn, db: Session = Depends(get_db),
                       user: User = Depends(current_user)):
    if data.status not in VALID_STATUSES:
        raise HTTPException(400, f"Status must be one of {sorted(VALID_STATUSES)}")
    ride = db.get(Ride, ride_id)
    if not ride:
        raise HTTPException(404, "Ride not found")
    if user.role == "rider" and ride.rider_id != user.id:
        raise HTTPException(403, "You can only update your own rides")
    if user.role == "driver":
        driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
        if not driver or ride.driver_id != driver.id:
            raise HTTPException(403, "This ride is not assigned to you")
    if ride.status in {"completed", "cancelled"}:
        raise HTTPException(409, "Ride is already closed")
    if data.status == "ongoing" and ride.status != "accepted":
        raise HTTPException(409, "Only accepted rides can become ongoing")
    if data.status == "completed" and ride.status != "ongoing":
        raise HTTPException(409, "Only ongoing rides can be completed")
    if data.status == "accepted":
        raise HTTPException(400, "Use the accept endpoint")
    ride.status = data.status
    if data.status in {"completed", "cancelled"} and ride.driver_id:
        driver = db.get(Driver, ride.driver_id)
        if driver:
            driver.is_available = True
    db.commit()
    db.refresh(ride)
    return ride

@app.get("/rides/history", response_model=list[RideOut])
def ride_history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role == "rider":
        rides = db.scalars(select(Ride).where(Ride.rider_id == user.id).order_by(Ride.created_at.desc())).all()
    else:
        driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
        if not driver:
            return []
        rides = db.scalars(select(Ride).where(Ride.driver_id == driver.id).order_by(Ride.created_at.desc())).all()
    return rides

@app.post("/reviews", status_code=201)
def create_review(data: ReviewIn, db: Session = Depends(get_db),
                  user: User = Depends(require_role("rider"))):
    ride = db.get(Ride, data.ride_id)
    if not ride or ride.rider_id != user.id:
        raise HTTPException(404, "Ride not found for this rider")
    if ride.status != "completed" or not ride.driver_id:
        raise HTTPException(400, "Only completed rides can be reviewed")
    if db.scalar(select(Review).where(Review.ride_id == ride.id)):
        raise HTTPException(409, "This ride already has a review")
    review = Review(ride_id=ride.id, reviewer_id=user.id, driver_id=ride.driver_id,
                    rating=data.rating, comment=data.comment)
    db.add(review)
    db.commit()
    return {"message": "Review submitted", "rating": review.rating}

@app.get("/reviews/driver/{driver_id}")
def driver_reviews(driver_id: int, db: Session = Depends(get_db),
                   user: User = Depends(current_user)):
    reviews = db.scalars(select(Review).where(Review.driver_id == driver_id).order_by(Review.created_at.desc())).all()
    return [{"rating": r.rating, "comment": r.comment, "ride_id": r.ride_id} for r in reviews]
