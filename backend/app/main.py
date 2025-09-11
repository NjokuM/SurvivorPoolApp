from app.routers import competition_router
from app.routers import auth_router
from app.routers import user_router
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

SECRET_KEY=os.getenv("SECRET_KEY")

app=FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(competition_router.router)
#app.include_router(team_routes.router)
#app.include_router(league.routes.router)


