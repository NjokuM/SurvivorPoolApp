from fastapi import FastAPI
from app.api import user_routes
#from app.api import auth

app=FastAPI()

app.include_router(user_routes.router)
#app.include_router(auth.router)
#app.include_router(team_routes.router)
#app.include_router(league.routes.router)


