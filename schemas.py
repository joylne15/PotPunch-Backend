from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- Member schemas ---

class MemberCreate(BaseModel):
    name: str
    phone: Optional[str] = None


class MemberResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    total_paid: float
    remaining: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Payment schemas ---

class PaymentCreate(BaseModel):
    member_id: int
    amount: float
    note: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    member_id: int
    amount: float
    date: datetime
    note: Optional[str]

    class Config:
        from_attributes = True


# --- Settings schemas ---

class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingResponse(BaseModel):
    id: int
    key: str
    value: str

    class Config:
        from_attributes = True