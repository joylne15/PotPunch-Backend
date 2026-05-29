from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    total_paid = Column(Float, default=0.0)
    remaining = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, server_default=func.now())
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(255), nullable=False)