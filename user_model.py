from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional




class User(Document):
    email: EmailStr
    password: str  # hashed password!

    class Settings:
        name = "users"