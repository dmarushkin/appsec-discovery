import json
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from datetime import datetime, timedelta
from datetime import timezone 
from typing import List, Optional
from models import ScoreRule, Token, UserData
from services.db_service import create_db_and_tables, get_db_session
from config import UI_ADMIN_EMAIL, UI_ADMIN_PASSWORD, UI_JWT_KEY, ALGORITHM


# Create database and tables
create_db_and_tables()

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Auth flow

def authenticate_user(username: str, password: str):

    admin_email = UI_ADMIN_EMAIL
    admin_password = UI_ADMIN_PASSWORD

    if username == admin_email and password == admin_password :
        return UserData(username=admin_email)
    return False

def create_access_token(username: str):

    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    expire_unix = int(expire.timestamp())

    to_encode = {'sub': username, "exp": expire_unix}

    encoded_jwt = jwt.encode(to_encode, UI_JWT_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, UI_JWT_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user_data = UserData(username=username)
    except JWTError:
        raise credentials_exception
    return user_data

def get_current_active_user(current_user: UserData = Depends(get_current_user)):
    if current_user.username != UI_ADMIN_EMAIL:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


# CRUDS
@app.post("/score_rules", response_model=ScoreRule)
def create_rule( rule: ScoreRule, 
                       db: Session = Depends(get_db_session), 
                       current_user: UserData = Depends(get_current_active_user)):
    db_rule = ScoreRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@app.delete("/score_rules/{rule_id}", response_model=ScoreRule)
async def delete_rule(rule_id: int, 
                      db: Session = Depends(get_db_session), 
                      current_user: UserData = Depends(get_current_active_user)):
    db_rule = db.query(ScoreRule).filter(ScoreRule.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(db_rule)
    db.commit()
    return db_rule


@app.get("/score_rules", response_model=List[ScoreRule])
def get_rules(
    response: Response,
    db: Session = Depends(get_db_session),
    current_user: UserData = Depends(get_current_active_user),
    range: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    filter: Optional[str] = Query(None)
):
    query = db.query(ScoreRule)

    if filter:
        filter_params = json.loads(filter)
        for key, value in filter_params.items():
            query = query.filter(getattr(ScoreRule, key).ilike(f"%{value}%"))

    if sort:
        sort_field, sort_order = json.loads(sort)
        if sort_order == "ASC":
            query = query.order_by(asc(getattr(ScoreRule, sort_field)))
        else:
            query = query.order_by(desc(getattr(ScoreRule, sort_field)))

    if range:
        range_start, range_end = json.loads(range)
        query = query.offset(range_start).limit(range_end - range_start + 1)
        total = db.query(ScoreRule).count()
        response.headers["Content-Range"] = f"hosts {range_start}-{range_end}/{total}"

    rules = query.all()
    return rules

