from beanie import Document, Indexed
from pydantic import EmailStr, Field
from typing import Optional, List
from datetime import datetime
from pymongo import IndexModel
from enum import Enum

class InvestmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INVESTMENT = "investment"
    ROI = "roi"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Document):
    email: Indexed(EmailStr, unique=True)
    username: Indexed(str, unique=True)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    subscription_plan: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", 1)], unique=True),
            IndexModel([("username", 1)], unique=True),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "subscription_plan": "Basic"
            }
        }

class Package(Document):
    name: Indexed(str)
    description: str
    min_investment: float
    max_investment: float
    duration_days: int
    roi_percentage: float
    is_active: bool = True

    class Settings:
        name = "packages"
        indexes = [
            IndexModel([("name", 1)]),
            IndexModel([("is_active", 1)]),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Basic Plan",
                "description": "A basic investment package",
                "min_investment": 100.0,
                "max_investment": 1000.0,
                "duration_days": 30,
                "roi_percentage": 5.0,
                "is_active": True
            }
        }

class Investment(Document):
    amount: float
    package_id: str  # Reference to Package document ID
    user_id: str     # Reference to User document ID
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    status: InvestmentStatus = InvestmentStatus.ACTIVE

    class Settings:
        name = "investments"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("package_id", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("start_date", -1)]),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 500.0,
                "package_id": "60f8f9b8c8d8e8f8g8h8i8j8",
                "user_id": "60f8f9b8c8d8e8f8g8h8i8j9",
                "status": "active"
            }
        }

class Transaction(Document):
    user_id: str  # Reference to User document ID
    amount: float
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    investment_id: Optional[str] = None  # Reference to Investment if applicable
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:
        name = "transactions"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("transaction_type", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("created_at", -1)]),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "60f8f9b8c8d8e8f8g8h8i8j9",
                "amount": 100.0,
                "transaction_type": "deposit",
                "status": "completed"
            }
        }