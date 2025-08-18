from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import requests
from beanie import PydanticObjectId
from database import connect_to_mongo, close_mongo_connection, connect_with_retry
from models import User, Package, Investment, Transaction, InvestmentStatus, TransactionType, TransactionStatus

# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 2 * 24 * 60  # 2 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# FastAPI app
app = FastAPI(title="Wealth Investment API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    subscription_plan: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str
    subscription_plan: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None

class AdminUserUpdate(BaseModel):
    is_active: bool

class TransactionUpdate(BaseModel):
    status: TransactionStatus

class PackageResponse(BaseModel):
    id: str
    name: str
    description: str
    min_investment: float
    max_investment: float
    duration_days: int
    roi_percentage: float
    is_active: bool
    
    class Config:
        from_attributes = True

class PackageCreate(BaseModel):
    name: str
    description: str
    min_investment: float
    max_investment: float
    duration_days: int
    roi_percentage: float

class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    min_investment: Optional[float] = None
    max_investment: Optional[float] = None
    duration_days: Optional[int] = None
    roi_percentage: Optional[float] = None
    is_active: Optional[bool] = None

class InvestmentResponse(BaseModel):
    id: str
    amount: float
    package_id: str
    user_id: str
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    package: Optional[PackageResponse] = None
    
    class Config:
        from_attributes = True

class InvestmentCreate(BaseModel):
    amount: float
    package_id: str

class TransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    transaction_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_investments: int
    total_amount_invested: float
    active_investments: int
    total_roi: float
    pending_withdrawals: float

# App lifecycle events
@app.on_event("startup")
async def startup_event():
    try:
        await connect_with_retry()
    except Exception as e:
        print(f"All connection methods failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail="Unable to connect to database."
        )
    
    try:
        ADMIN_EMAIL = "jethrojerrybj@gmail.com"
        ADMIN_USERNAME = "wealthinvestadmins3"
        ADMIN_PASSWORD = "wealthpassword"

        if not await get_user_by_email(ADMIN_EMAIL):
            print(f"Creating default admin: {ADMIN_EMAIL}")
            await User(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                first_name="Admin",
                last_name="User",
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_admin=True,
                subscription_plan="Enterprise"
            ).insert()
            print("Default admin created.")
    except Exception as e:
        print(f"Error creating default admin: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Helper functions
def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user_by_username(username: str):
    return await User.find_one(User.username == username)

async def get_user_by_email(email: str):
    return await User.find_one(User.email == email)

async def authenticate_user(username: str, password: str):
    # Allow user to log in with either email or username
    user = await get_user_by_username(username)
    if not user:
        user = await get_user_by_email(username)
    
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

# Auth endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    if await get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await get_user_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = User(
        **user_data.dict(exclude={"password"}),
        hashed_password=get_password_hash(user_data.password)
    )
    await new_user.insert()
    # Manually construct the response to ensure the ID is a string
    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        username=new_user.username,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        is_active=new_user.is_active,
        is_admin=new_user.is_admin,
        subscription_plan=new_user.subscription_plan,
        created_at=new_user.created_at
    )

# User endpoints
@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # Manually construct the response to ensure the ID is a string
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        subscription_plan=current_user.subscription_plan,
        created_at=current_user.created_at
    )

@app.put("/users/me", response_model=UserResponse)
async def update_user_me(user_data: UserUpdate, current_user: User = Depends(get_current_active_user)):
    update_data = user_data.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    await current_user.update({"$set": update_data})
    updated_user = await User.get(current_user.id)
    
    # Manually construct the response to ensure the ID is a string
    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        username=updated_user.username,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        is_active=updated_user.is_active,
        is_admin=updated_user.is_admin,
        subscription_plan=updated_user.subscription_plan,
        created_at=updated_user.created_at
    )

@app.get("/users/me/dashboard", response_model=DashboardStats)
async def get_user_dashboard(current_user: User = Depends(get_current_active_user)):
    investments = await Investment.find(Investment.user_id == str(current_user.id)).to_list()
    total_roi = 0
    for inv in investments:
        if inv.status == InvestmentStatus.COMPLETED:
            pkg = await Package.get(PydanticObjectId(inv.package_id))
            if pkg:
                total_roi += inv.amount * (pkg.roi_percentage / 100)
    
    pending_withdrawals = await Transaction.find(
        Transaction.user_id == str(current_user.id),
        Transaction.transaction_type == TransactionType.WITHDRAWAL,
        Transaction.status == TransactionStatus.PENDING
    ).sum(Transaction.amount)

    return DashboardStats(
        total_investments=len(investments),
        total_amount_invested=sum(inv.amount for inv in investments),
        active_investments=len([i for i in investments if i.status == InvestmentStatus.ACTIVE]),
        total_roi=total_roi,
        pending_withdrawals=pending_withdrawals or 0
    )

# Package endpoints
@app.get("/packages", response_model=List[PackageResponse])
async def get_investment_packages():
    packages = await Package.find(Package.is_active == True).to_list()
    # Convert ObjectId to string for each package
    return [
        PackageResponse(
            id=str(pkg.id),
            name=pkg.name,
            description=pkg.description,
            min_investment=pkg.min_investment,
            max_investment=pkg.max_investment,
            duration_days=pkg.duration_days,
            roi_percentage=pkg.roi_percentage,
            is_active=pkg.is_active
        ) for pkg in packages
    ]

# Investment endpoints
@app.post("/investments", response_model=InvestmentResponse)
async def create_investment(inv_data: InvestmentCreate, current_user: User = Depends(get_current_active_user)):
    pkg = await Package.get(PydanticObjectId(inv_data.package_id))
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    if not (pkg.min_investment <= inv_data.amount <= pkg.max_investment):
        raise HTTPException(status_code=400, detail="Investment amount is outside package limits")

    new_investment = Investment(
        amount=inv_data.amount,
        package_id=inv_data.package_id,
        user_id=str(current_user.id),
        end_date=datetime.utcnow() + timedelta(days=pkg.duration_days),
    )
    await new_investment.insert()

    await Transaction(
        user_id=str(current_user.id),
        amount=inv_data.amount,
        transaction_type=TransactionType.INVESTMENT,
        status=TransactionStatus.COMPLETED,
        investment_id=str(new_investment.id)
    ).insert()
    
    # Manually construct the response to ensure the ID is a string
    return InvestmentResponse(
        id=str(new_investment.id),
        amount=new_investment.amount,
        package_id=new_investment.package_id,
        user_id=new_investment.user_id,
        start_date=new_investment.start_date,
        end_date=new_investment.end_date,
        status=new_investment.status,
        package=PackageResponse(
            id=str(pkg.id),
            name=pkg.name,
            description=pkg.description,
            min_investment=pkg.min_investment,
            max_investment=pkg.max_investment,
            duration_days=pkg.duration_days,
            roi_percentage=pkg.roi_percentage,
            is_active=pkg.is_active
        )
    )

@app.get("/investments/me", response_model=List[InvestmentResponse])
async def get_my_investments(current_user: User = Depends(get_current_active_user)):
    investments = await Investment.find(Investment.user_id == str(current_user.id)).to_list()
    result = []
    for inv in investments:
        pkg = await Package.get(PydanticObjectId(inv.package_id))
        result.append(InvestmentResponse(
            id=str(inv.id),
            amount=inv.amount,
            package_id=inv.package_id,
            user_id=inv.user_id,
            start_date=inv.start_date,
            end_date=inv.end_date,
            status=inv.status,
            package=PackageResponse(
                id=str(pkg.id),
                name=pkg.name,
                description=pkg.description,
                min_investment=pkg.min_investment,
                max_investment=pkg.max_investment,
                duration_days=pkg.duration_days,
                roi_percentage=pkg.roi_percentage,
                is_active=pkg.is_active
            ) if pkg else None
        ))
    return result

# Transaction endpoints
@app.get("/transactions/me", response_model=List[TransactionResponse])
async def get_my_transactions(current_user: User = Depends(get_current_active_user)):
    transactions = await Transaction.find(Transaction.user_id == str(current_user.id)).to_list()
    # Convert ObjectId to string for each transaction
    return [
        TransactionResponse(
            id=str(txn.id),
            user_id=txn.user_id,
            amount=txn.amount,
            transaction_type=txn.transaction_type,
            status=txn.status,
            created_at=txn.created_at,
            updated_at=txn.updated_at
        ) for txn in transactions
    ]

@app.post("/transactions/withdraw", response_model=TransactionResponse)
async def create_withdrawal(amount_model: dict, current_user: User = Depends(get_current_active_user)):
    amount = amount_model.get("amount")
    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Withdrawal amount must be positive")
    
    transaction = Transaction(
        user_id=str(current_user.id),
        amount=amount,
        transaction_type=TransactionType.WITHDRAWAL,
        status=TransactionStatus.PENDING
    )
    await transaction.insert()
    
    # Manually construct the response to ensure the ID is a string
    return TransactionResponse(
        id=str(transaction.id),
        user_id=transaction.user_id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        status=transaction.status,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )

# Crypto price endpoint
@app.get("/crypto-prices")
async def get_crypto_prices():
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,binancecoin,cardano,solana", "vs_currencies": "usd", "include_24hr_change": "true"}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Unable to fetch crypto prices")

# Admin endpoints
@app.get("/admin/users", response_model=List[UserResponse], dependencies=[Depends(get_current_admin_user)])
async def get_all_users():
    users = await User.find_all().to_list()
    # Convert ObjectId to string for each user
    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            subscription_plan=user.subscription_plan,
            created_at=user.created_at
        ) for user in users
    ]

@app.put("/admin/users/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_admin_user)])
async def update_user_status(user_id: str, update_data: AdminUserUpdate):
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.update({"$set": update_data.dict()})
    updated_user = await User.get(PydanticObjectId(user_id))
    
    # Manually construct the response to ensure the ID is a string
    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        username=updated_user.username,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        is_active=updated_user.is_active,
        is_admin=updated_user.is_admin,
        subscription_plan=updated_user.subscription_plan,
        created_at=updated_user.created_at
    )

@app.delete("/admin/users/{user_id}", status_code=204, dependencies=[Depends(get_current_admin_user)])
async def delete_user(user_id: str):
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return None

@app.get("/admin/investments", response_model=List[InvestmentResponse], dependencies=[Depends(get_current_admin_user)])
async def get_all_investments():
    investments = await Investment.find_all().to_list()
    result = []
    for inv in investments:
        pkg = await Package.get(PydanticObjectId(inv.package_id))
        result.append(InvestmentResponse(
            id=str(inv.id),
            amount=inv.amount,
            package_id=inv.package_id,
            user_id=inv.user_id,
            start_date=inv.start_date,
            end_date=inv.end_date,
            status=inv.status,
            package=PackageResponse(
                id=str(pkg.id),
                name=pkg.name,
                description=pkg.description,
                min_investment=pkg.min_investment,
                max_investment=pkg.max_investment,
                duration_days=pkg.duration_days,
                roi_percentage=pkg.roi_percentage,
                is_active=pkg.is_active
            ) if pkg else None
        ))
    return result

@app.get("/admin/transactions", response_model=List[TransactionResponse], dependencies=[Depends(get_current_admin_user)])
async def get_all_transactions():
    transactions = await Transaction.find_all().to_list()
    # Convert ObjectId to string for each transaction
    return [
        TransactionResponse(
            id=str(txn.id),
            user_id=txn.user_id,
            amount=txn.amount,
            transaction_type=txn.transaction_type,
            status=txn.status,
            created_at=txn.created_at,
            updated_at=txn.updated_at
        ) for txn in transactions
    ]

@app.put("/admin/transactions/{transaction_id}", response_model=TransactionResponse, dependencies=[Depends(get_current_admin_user)])
async def update_transaction_status(transaction_id: str, update_data: TransactionUpdate):
    transaction = await Transaction.get(PydanticObjectId(transaction_id))
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    transaction.status = update_data.status
    transaction.updated_at = datetime.utcnow()
    await transaction.save()
    
    # Manually construct the response to ensure the ID is a string
    return TransactionResponse(
        id=str(transaction.id),
        user_id=transaction.user_id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        status=transaction.status,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )

@app.post("/admin/packages", response_model=PackageResponse, dependencies=[Depends(get_current_admin_user)])
async def create_package(package_data: PackageCreate):
    new_package = Package(**package_data.dict())
    await new_package.insert()
    
    # Manually construct the response to ensure the ID is a string
    return PackageResponse(
        id=str(new_package.id),
        name=new_package.name,
        description=new_package.description,
        min_investment=new_package.min_investment,
        max_investment=new_package.max_investment,
        duration_days=new_package.duration_days,
        roi_percentage=new_package.roi_percentage,
        is_active=new_package.is_active
    )

@app.put("/admin/packages/{package_id}", response_model=PackageResponse, dependencies=[Depends(get_current_admin_user)])
async def update_package(package_id: str, package_data: PackageUpdate):
    package = await Package.get(PydanticObjectId(package_id))
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    update_data = package_data.dict(exclude_unset=True)
    await package.update({"$set": update_data})
    updated_package = await Package.get(PydanticObjectId(package_id))
    
    # Manually construct the response to ensure the ID is a string
    return PackageResponse(
        id=str(updated_package.id),
        name=updated_package.name,
        description=updated_package.description,
        min_investment=updated_package.min_investment,
        max_investment=updated_package.max_investment,
        duration_days=updated_package.duration_days,
        roi_percentage=updated_package.roi_percentage,
        is_active=updated_package.is_active
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
