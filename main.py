from typing import Optional , List
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine,Column,Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import bcrypt

DATABASE_URL = "mysql+mysqlconnector://root:@localhost/learnfastapi"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


app = FastAPI()

Base = declarative_base()

class  Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    role_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role_id: int

class UserResponse(BaseModel    ):
    id: int
    name: str
    email: str
    role_id: int
    created_at: datetime
    deleted_at: Optional[datetime]
    
class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[str]
    password: Optional[str]
    role_id: Optional[int]
    
@app.get("/users",response_model=List[UserResponse])
def readAll():
    with SessionLocal() as session:
        user = session.query(Users).filter(Users.deleted_at.is_(None)).all()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

@app.post("/users/store",response_model=UserCreate)
def create_user(user: UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    user_dict = user.dict()
    user_dict['password'] = hashed_password.decode('utf-8')
    db_user = Users(**user_dict)
    with SessionLocal() as session:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user

@app.get("/users/find/{user_id}", response_model=UserResponse)
def read_user(user_id: int):
    with SessionLocal() as session:
        user = session.query(Users).filter(Users.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

@app.put("/users/update/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate):
    with SessionLocal() as session:
        db_user = session.query(Users).filter(Users.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        for key, value in user.dict().items():
            setattr(db_user, key, value)
        session.commit()
        session.refresh(db_user)
        return db_user

@app.delete("/users/delete/{user_id}", response_model=UserResponse)
def delete_user(user_id: int):
    with SessionLocal() as session:
        db_user = session.query(Users).filter(Users.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        db_user.deleted_at = datetime.utcnow()
        session.commit()
        
        updated_user = session.query(Users).filter(Users.id == user_id).first()
        
        return updated_user