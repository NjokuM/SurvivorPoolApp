from app.routers import competition_router
from app.routers import auth_router
from app.routers import user_router
from app.routers import pool_router
from app.routers import pick_router
from app.routers import admin_routes
from app.routers import external_football_router
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

SECRET_KEY=os.getenv("SECRET_KEY")

app=FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(competition_router.router)
app.include_router(pool_router.router)
app.include_router(pick_router.router)
app.include_router(admin_routes.router)
app.include_router(external_football_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)