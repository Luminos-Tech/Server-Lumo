from sqlalchemy.orm import Session
from ServerDB import models, schemas

# --- CRUD FOR USERS ---
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# --- CRUD FOR DEVICES ---
def create_device(db: Session, device: schemas.DeviceCreate):
    db_device = models.Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

def get_devices(db: Session):
    return db.query(models.Device).all()

def delete_device(db: Session, device_id: int):
    db_device = db.query(models.Device).filter(models.Device.device_id == device_id).first()
    if db_device:
        db.delete(db_device)
        db.commit()
    return db_device

# --- CRUD FOR EVENTS (ESP32) ---
def create_event(db: Session, event: schemas.EventCreate):
    # Tìm device_id từ device_code mà ESP32 gửi lên
    device = db.query(models.Device).filter(models.Device.device_code == event.device_code).first()
    if not device:
        return None # Hoặc raise Exception

    db_event = models.ButtonEvent(
        device_id=device.device_id,
        user_id=event.user_id,
        button_state=event.button_state,
        event_type=event.event_type,
        event_value=event.event_value
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_events(db: Session, limit: int = 50):
    return db.query(models.ButtonEvent).order_by(models.ButtonEvent.created_at.desc()).limit(limit).all()