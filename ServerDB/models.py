from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ServerDB.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ 1-n: 1 User có nhiều Event
    events = relationship("ButtonEvent", back_populates="user")

class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String, nullable=False)
    device_code = Column(String, unique=True, index=True, nullable=False)
    location = Column(String)
    status = Column(String, default="active")
    device_variant = Column(String, default="standard")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Quan hệ 1-n: 1 Device có nhiều Event
    events = relationship("ButtonEvent", back_populates="device")

class ButtonEvent(Base):
    __tablename__ = "button_events"

    event_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Có thể null nếu chỉ test thiết bị
    button_state = Column(String, nullable=False)
    event_type = Column(String)
    event_value = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="events")
    user = relationship("User", back_populates="events")