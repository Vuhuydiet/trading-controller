from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    username: str 
    full_name: str
    password: str