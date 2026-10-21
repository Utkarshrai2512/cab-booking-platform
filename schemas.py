from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "rider"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DriverCreate(BaseModel):
    vehicle_number: str = Field(min_length=3, max_length=30)
    vehicle_type: str = "Sedan"

class AvailabilityIn(BaseModel):
    is_available: bool

class RideEstimateIn(BaseModel):
    pickup: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    distance_km: float = Field(gt=0, le=1000)

class RideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rider_id: int
    driver_id: int | None
    pickup: str
    destination: str
    distance_km: float
    fare: float
    status: str

class StatusIn(BaseModel):
    status: str

class ReviewIn(BaseModel):
    ride_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)
