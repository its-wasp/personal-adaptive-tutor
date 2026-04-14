from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserCreateDTO(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str


class UserResponseDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str


class AuthResponseDTO(BaseModel):
    user: UserResponseDTO
    access_token: str
