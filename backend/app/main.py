from fastapi import FastAPI, HTTPException, Form, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from kafka import KafkaProducer
from passlib.context import CryptContext
from .models import User, Session as UserSession
from . import models, database
from .database import get_db
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timedelta
import uuid
import secrets
import requests
import json

CLIENT_ID = "7419952b6b2b4679a6e1fe8819eecf89"
CLIENT_SECRET = "6bd192efe682404aa763e7e1c3b2037a"
REDIRECT_URI = "http://localhost:8000/auth/yandex/callback"

# Настройка Kafka Producer
KAFKA_BROKER_URL = "kafka:9092"
KAFKA_TOPIC = "user_registration"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_to_kafka(contact: str, message: str):
    producer.send(KAFKA_TOPIC, {"contact": contact, "message": message})
    producer.flush()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterUserRequest(BaseModel):
    user_login: str
    user_password: str
    telegram_contact: str

class LoginUserRequest(BaseModel):
    user_login: str
    user_password: str

@app.on_event("startup")
async def startup():
    db = next(get_db())
    database.init_db(db) 

@app.post("/register/")
async def register_user(request: RegisterUserRequest, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(request.user_password)
    new_user = User(user_login=request.user_login, user_password=hashed_password, user_role="user")

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    send_to_kafka(request.telegram_contact, f"Новый пользователь зарегистрировался! Логин: {request.user_login}")

    return {"message": "User registered successfully"}

@app.post("/login/")
async def login(response: Response, request: LoginUserRequest, db: Session = Depends(get_db)):
    user = database.get_user_by_login(db, request.user_login)
    if user is None or not database.verify_password(request.user_password, user.user_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    session_token = uuid.uuid4()

    session = models.Session(
        session_token=session_token,
        user_id=user.user_id,
        session_start=datetime.utcnow(),
    )
    db.add(session)
    db.commit()

    response.set_cookie(key="session_token", value=str(session_token), max_age=86400, httponly=True)

    return {"message": "Login successful"}

@app.get("/check_session/")
async def check_session(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=400, detail="Session not found")

    session = database.get_session_by_token(db, session_token)
    if not session or session.session_end:
        raise HTTPException(status_code=400, detail="Session expired")

    database.register_visit(db, session.user_id)

    return {"message": "Session is active"}

@app.post("/logout/")
async def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=400, detail="No session found")

    session = database.get_session_by_token(db, session_token)
    if session:
        session.session_end = datetime.utcnow()
        db.commit()

    response.delete_cookie(key="session_token")

    return {"message": "Logged out successfully"}

@app.get("/auth/yandex")
async def auth_yandex():
    auth_url = f"https://oauth.yandex.ru/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=login:email"
    return RedirectResponse(url=auth_url)

@app.get("/auth/yandex/callback")
async def yandex_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Code not found")

    token_url = "https://oauth.yandex.ru/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(token_url, data=token_data)
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    access_token = token_response.json().get("access_token")

    user_info_url = "https://login.yandex.ru/info"
    user_info_params = {"oauth_token": access_token}
    user_info_response = requests.get(user_info_url, params=user_info_params)

    if user_info_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user information")

    user_info = user_info_response.json()
    yandex_email = user_info.get("default_email")

    if not yandex_email:
        raise HTTPException(status_code=400, detail="Email not found")

    user = database.get_user_by_login(db, yandex_email)

    if not user:
        random_password = secrets.token_hex(16)
        hashed_password = pwd_context.hash(random_password)
        new_user = models.User(
            user_login=yandex_email,
            user_password=hashed_password,
            user_role="user"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        send_to_kafka("", f"Новый пользователь зарегистрировался! Логин: {new_user.user_login}")
        return RedirectResponse(url="http://localhost:3000/")

    session_token = str(uuid.uuid4())
    session = models.Session(
        session_token=session_token,
        user_id=user.user_id,
        session_start=datetime.utcnow(),
    )
    db.add(session)
    db.commit()

    response = RedirectResponse(url="http://localhost:3000/")
    response.set_cookie(key="session_token", value=session_token, max_age=86400, httponly=True)

    return response

@app.get("/api/get_user_role")
async def get_user_role(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Сессия недействительна")

    user = db.query(User).filter(User.user_id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {"role": user.user_role}

@app.get("/api/get_visits")
async def get_visits(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Сессия недействительна")

    user = db.query(User).filter(User.user_id == session.user_id).first()
    if not user or user.user_role != "admin":
        raise HTTPException(status_code=403, detail="У вас недостаточно мощи")

    # Если передан user_id — фильтруем по нему, иначе выводим всех
    query = db.query(UserSession, User.user_login).join(User, User.user_id == UserSession.user_id)
    if user_id:
        query = query.filter(UserSession.user_id == user_id)

    visits = query.all()
    return [
        {
            "user_id": visit.UserSession.user_id,
            "user_login": visit.user_login,
            "session_start": visit.UserSession.session_start.isoformat(),
        }
        for visit in visits
    ]
