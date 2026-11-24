from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from passlib.context import CryptContext
from database import engine
from forecast import forecast
import yfinance as yf


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

class TradeRequest(BaseModel):
    username: str
    share_code: str
    amount: float  # Number of shares (e.g., 5.0)
    action: str  # Either "BUY" or "SELL"

# and for TradeRequest(it uses data temporary before actuallt saving it to the databse)


# ==================== API ENDPOINTS ====================

@app.get("/")
def read_root():
    return {"message": "Market Forecast API is running!"}


#----------------- registration

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



#--------------- forecast
@app.get("/forecast/{ticker}")
def get_stock_forecast(ticker: str):
    try:
        result = forecast(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



#--------------- login

@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    #search
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

  # check pass
    is_password_valid = pwd_context.verify(user.password, db_user.password_hash)
    if not is_password_valid:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # return the info
    return {
        "message": "Login successful!",
        "username": db_user.username,
        "name": db_user.Name,
        "cash_balance": db_user.cash_balance
    }



#----------see portfolio

@app.get("/portfolio/{username}")
def get_user_portfolio(username: str, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    #find all the transactions of this user
    user_transactions = db.query(Transactions).filter(Transactions.user_id == db_user.id).all()


    transactions_list = [
        {
            "id": tx.id,
            "share_code": tx.share_code,
            "amount": tx.amount,
            "purchase_price": tx.purchase_price,
            "timestamp": tx.timestamp
        }
        for tx in user_transactions
    ]


    return {
        "username": db_user.username,
        "name": db_user.Name,
        "email": db_user.email,
        "cash_balance": db_user.cash_balance,
        "transactions": transactions_list
    }


#------- see price; buy and sell

@app.post("/trade")
def execute_trade(trade: TradeRequest, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.username == trade.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    symbol = trade.share_code.upper()

    # live price
    try:
        ticker_obj = yf.Ticker(symbol)
        todays_data = ticker_obj.history(period="1d")
        if todays_data.empty:
            raise ValueError(f"No market data found for ticker: {symbol}")
        current_price = float(todays_data['Close'].iloc[-1])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch price for {symbol}: {str(e)}")

    total_cost = trade.amount * current_price
    action = trade.action.upper()


    if action == "BUY":
        # Check if the user has enough money

        #no
        if db_user.cash_balance < total_cost:
            raise HTTPException(status_code=400, detail="Insufficient cash balance for this trade")

        #yes
        db_user.cash_balance -= total_cost
        stored_amount = trade.amount  # Positive amount indicates shares owned

    elif action == "SELL":
        # Add cash back
        db_user.cash_balance += total_cost
        stored_amount = -trade.amount  # Negative amount indicates shares sold/removed

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'BUY' or 'SELL'.")

    #Save the transaction
    new_transaction = Transactions(
        user_id=db_user.id,
        share_code=symbol,
        amount=stored_amount,
        purchase_price=current_price
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(db_user)

    return {
        "message": f"Successfully executed {action} order for {trade.amount} shares of {symbol}",
        "execution_price": current_price,
        "total_amount": total_cost,
        "new_cash_balance": db_user.cash_balance
    }