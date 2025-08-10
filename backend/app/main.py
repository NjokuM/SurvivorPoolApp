from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

SECRET_KEY=os.getenv("SECRET_KEY")

app=FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

from app.api import user_routes, auth

app.include_router(user_routes.router)
app.include_router(auth.router)
#app.include_router(team_routes.router)
#app.include_router(league.routes.router)


