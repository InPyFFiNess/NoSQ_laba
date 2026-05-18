import asyncio
import csv
import datetime
from datetime import timedelta
from contextlib import asynccontextmanager
from functools import wraps
import hashlib
import os
import ssl
import uuid
from typing import Annotated, Union

import pandas as pd
import redis.asyncio as aioredis  # Используем асинентный клиент Redis
from fastapi import Cookie, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.responses import Response
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(
        "redis://localhost:6379", 
        decode_responses=True 
    )
    yield
    await app.state.redis.close()


app = FastAPI(lifespan=lifespan)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('security/cert.pem', keyfile='security/key.pem')
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="sorces/images"), name="images")
templates = Jinja2Templates(directory="templates")

USERS = "users.csv"
SESSION_TTL = timedelta(minutes=3)
white_urls = ["/", "/login", "/logout", "/register"]
LOG_FILE = 'log.csv'    

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Дата', 'Время', 'Функция', 'Пользователь', 'Статус'])

def log(func):
    def _write_log(request, response, func_name):
        username = request.cookies.get("username") if request else None
        if not username:
            username = "anonymous"
        
        status_code = response.status_code if isinstance(response, Response) else ""
        now = datetime.datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        with open(LOG_FILE, mode='a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow([date_str, time_str, func_name, username, status_code])

    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or next((arg for arg in args if isinstance(arg, Request)), None)
            response = await func(*args, **kwargs)
            _write_log(request, response, func.__name__)
            return response
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or next((arg for arg in args if isinstance(arg, Request)), None)
            response = func(*args, **kwargs)
            _write_log(request, response, func.__name__)
            return response
        return sync_wrapper

@app.middleware("http")
@log
async def check_session(request: Request, call_next):
    if request.url.path.startswith("/static") or request.url.path in white_urls:
        return await call_next(request)
    
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")

    session_exists = await request.app.state.redis.exists(session_id)
    if not session_exists:
        response = RedirectResponse(url="/")
        response.delete_cookie("session_id")
        return response

    await request.app.state.redis.expire(session_id, int(SESSION_TTL.total_seconds()))

    return await call_next(request) 

@app.get("/", response_class=HTMLResponse)
@app.get("/register", response_class=HTMLResponse)
@log
def get_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
@log
def register(request: Request,
             username: str = Form(...),
             password: str = Form(...),
             confirm_password: str = Form(...)):
    users = pd.read_csv(USERS, encoding='utf-8-sig')
    if username.strip() in users['user'].str.strip().values:
        return templates.TemplateResponse("register.html",
                                          {"request": request, "error": "Такой пользователь уже существует"})
    
    if password != confirm_password:
        return templates.TemplateResponse("register.html",
                                          {"request": request, "error": "Пароли не совпадают"})
    
    copy_password = password.encode()
    salt = username.encode()
    hash_password = hashlib.pbkdf2_hmac('sha256', copy_password, salt, 100)
    new_user = pd.DataFrame([{"user": username.strip(), "password": hash_password, "role": "user"}])
    new_user.to_csv(USERS, mode='a', header=False, index=False)
    return templates.TemplateResponse("login.html",
                                      {"request": request, "message": "Регистрация успешна. Теперь войдите"})


@app.get("/login", response_class=HTMLResponse)
@log
def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
@log
def get_home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/admins", response_class=HTMLResponse)
@log
def get_admin_page(request: Request):
    role = str(request.cookies.get("role"))
    if role == "admin":
        return templates.TemplateResponse("admins.html", {"request": request})
    else:
        return templates.TemplateResponse("403.html", {"request": request})


@app.post("/login")
@log
async def login(request: Request,
                username: str = Form(...),
                password: str = Form(...)):
    users = pd.read_csv(USERS, encoding='utf-8-sig')
    user_row = users.loc[users['user'].str.strip() == username]
    if not user_row.empty:
        stored_password = str(user_row['password'].values[0])
        stored_role = str(user_row['role'].values[0])
        copy_password = password.encode()
        salt = username.encode()
        hash_password = hashlib.pbkdf2_hmac('sha256', copy_password, salt, 100)
        
        if stored_password == str(hash_password):
            session_id = str(uuid.uuid4())
            
            # Сохраняем сессию в Redis с автоматическим TTL
            await request.app.state.redis.set(
                session_id, 
                username, 
                ex=int(SESSION_TTL.total_seconds())
            )
            
            response = RedirectResponse(url="/home", status_code=302)
            response.set_cookie(key="session_id", value=session_id)
            response.set_cookie(key="role", value=stored_role)
            response.set_cookie(key="username", value=username)
            return response

    return templates.TemplateResponse("login.html",
                                      {"request": request, "error": "Неверный логин или пароль"})


@app.get("/logout", response_class=HTMLResponse)
@log
async def logout(request: Request):
    session_id = request.cookies.get("session_id")

    if session_id:
        await request.app.state.redis.delete(session_id)

    response = templates.TemplateResponse("login.html", {
        "request": request,
        "message": "Сессия завершена",
        "url": "/login"
    })
    response.delete_cookie("session_id")
    response.delete_cookie("username")
    response.delete_cookie("role")
    return response


@app.get("/404", response_class=HTMLResponse)
@log
def get_404_page(request: Request):
    return templates.TemplateResponse("404.html", {"request": request})


@app.exception_handler(404)
@log
async def not_found_page(request: Request, exc):
    session_id = request.cookies.get("session_id")
    
    if session_id and await request.app.state.redis.exists(session_id):
        return RedirectResponse(url="/404")
    else:
        return RedirectResponse(url="/")
    
@app.get("/403", response_class=HTMLResponse)
@log
def get_403_page(request: Request):
    return templates.TemplateResponse("403.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=443,
        ssl_certfile='security/cert.pem',
        ssl_keyfile='security/key.pem',
    )