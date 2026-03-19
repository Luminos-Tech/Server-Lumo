from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- DEVICE SCHEMAS ---
class DeviceCreate(BaseModel):
    device_name: str
    device_code: str
    location: Optional[str] = None
    device_variant: Optional[str] = "standard"

class DeviceResponse(BaseModel):
    device_id: int
    device_name: str
    device_code: str
    status: str
    location: Optional[str]

    class Config:
        from_attributes = True

# --- BUTTON EVENT SCHEMAS (Dành cho ESP32 gửi lên) ---
class EventCreate(BaseModel):
    device_code: str  # ESP32 thường gửi mã thiết bị thay vì ID
    button_state: str
    event_type: Optional[str] = "press"
    event_value: Optional[str] = None
    user_id: Optional[int] = None

class EventResponse(BaseModel):
    event_id: int
    device_id: int
    button_state: str
    created_at: datetime

    class Config:
        from_attributes = True