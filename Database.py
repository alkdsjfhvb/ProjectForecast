import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float
import datetime as dt
from sqlalchemy import String,Boolean,Float,Integer,ForeignKey,DateTime

engine = db.create_engine('sqlite:///MarketData.db')

Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(db.Integer, primary_key=True)
    username = Column(db.String(50), nullable=False)
    Name = Column(db.String(50), nullable=False)
    email = Column(db.String(50), nullable=False)
    password_hash = Column(String)
    cash_balance = Column(Float, default=10000.0)
    is_admin = Column(Boolean, default=False)

class Transactions(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    share_code = Column(String)
    amount = Column(Float)
    purchase_price = Column(Float)
    timestamp = Column(DateTime, default=dt.datetime.utcnow)



Base.metadata.create_all(engine)



