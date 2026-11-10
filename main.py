from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from passlib.context import CryptContext
from database import engine
from forecast import forecast


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    username: str
    Name: str
    email: str
    password: str
#so the UserCreate is temporary and is just for storing the information temporary before adding it to the actual db

class UserLogin(BaseModel):
    username: str
    password: str

# the same  applies to userlogin


# ==================== API ENDPOINTS ====================

@app.get("/")
def read_root():
    return {"message": "Market Forecast API is running!"}


# 2. Register API Request (Saves to your MarketData.db via databas  e.py)
@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = pwd_context.hash(user.password)

    new_user = User(
        username=user.username,
        Name=user.Name,
        email=user.email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully!", "username": new_user.username}


# 3. Forecast API Request (Runs your forecasting.py script)
@app.get("/forecast/{ticker}")
def get_stock_forecast(ticker: str):
    try:
        result = forecast(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    # 1. Search the database for the username
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # 2. Verify the plain password against the secure hash stored in the database
    is_password_valid = pwd_context.verify(user.password, db_user.password_hash)
    if not is_password_valid:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # 3. If everything matches, return success and basic user details for the frontend
    return {
        "message": "Login successful!",
        "username": db_user.username,
        "name": db_user.Name,
        "cash_balance": db_user.cash_balance
    }