from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date


class ContactBase(BaseModel):
    name: str = Field(max_length=50, description='Contacts name')
    lastname: str = Field(max_length=50, description='Contacts lastname')
    email: EmailStr = Field(max_length=50, description='Contacts email')
    phone: str = Field(max_length=50, description='Contacts phone number')
    birthday: date = Field(description='Contacts birthday')
    additional: Optional[str] = Field(None, max_length=150, description='Additional information')


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class Contact(ContactBase):
    id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str


class CreateUser(UserBase):
    password: str


class User(UserBase):
    id: int
    contacts: list[Contact] = []
    avatar: str

    class Config:
        from_attributes = True


class RequestEmail(BaseModel):
    email: EmailStr

