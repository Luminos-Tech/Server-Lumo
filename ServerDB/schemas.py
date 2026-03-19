from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    passWord: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True