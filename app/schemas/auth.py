from pydantic import BaseModel, EmailStr, ConfigDict

class UserCreate(BaseModel): 
    name: str 
    email: EmailStr 
    phone: str 
    password: str 
    
class UserOut(BaseModel): 
    name: str 
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)
    
class UserLogin(BaseModel): 
    email: EmailStr 
    password: str 
    
class TokenResponse(BaseModel): 
    access_token: str 
    refresh_token: str 
    user_id: str
    type: str = "bearer"
    role: str
    
class Token(BaseModel): 
    content: str