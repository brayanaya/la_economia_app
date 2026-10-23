from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)
    nombre: str = Field(min_length=2, max_length=120)
    model_config = ConfigDict(str_strip_whitespace=True)
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold()

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold()

class UserOut(BaseModel):
    id: str
    email: str
    nombre: str

class AuthOut(BaseModel):
    user: UserOut
    csrf_token: str
