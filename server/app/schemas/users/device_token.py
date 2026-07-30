# app/schemas/device_token.py
from typing import Literal
from pydantic import BaseModel, Field

class DeviceTokenCreate(BaseModel):
    token: str = Field(min_length=10, max_length=255)
    platform: Literal["ios", "android"]

class DeviceTokenDelete(BaseModel):
    token: str = Field(min_length=10, max_length=255)