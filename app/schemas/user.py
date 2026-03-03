from pydantic import BaseModel, Field, EmailStr, ConfigDict

class UserCreate(BaseModel): 
    name: str 
    email: EmailStr
    phone: str 
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel): 
    name: str 
    email: EmailStr 
    phone: str
    model_config = ConfigDict(from_attributes=True)