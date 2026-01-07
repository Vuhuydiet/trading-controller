from pydantic import BaseModel, EmailStr

class ForgotPasswordRequest(BaseModel):
    username: str