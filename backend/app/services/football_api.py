from fastapi import FastAPI
from dotenv import load_dotenv
import httpx
import os
from app.schemas.competition_schema import TeamFilters, LeagueFilters, FixtureFilters
app=FastAPI()

load_dotenv()

RAPIDAPI_KEY= os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

BASE_URL = os.getenv("BASE_URL")

def get_headers():
    if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
        raise RuntimeError("RAPIDAPI_KEY or RAPIDAPI_HOST not set in environment")
    return{
        "x-rapidapi-key" : RAPIDAPI_KEY,
        "x-rapidapi-host" : RAPIDAPI_HOST
    }

async def get_fixtures(filters : FixtureFilters):
    url = f"{BASE_URL}/fixtures"
    params = filters.dict(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()

        api_response = response.json()
        return api_response

async def get_fixtures_by_id(fixture_id: int):

    url = f"{BASE_URL}/fixtures"

    params = {"id":fixture_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()

        api_response = response.json()
        return api_response
    
async def get_teams(filters: TeamFilters):
    url = f"{BASE_URL}/teams"

    params = filters.dict(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        
        api_response = response.json()
        return api_response
    
async def get_teams_by_id(team_id: int):
    url = f"{BASE_URL}/teams"

    params = {"id": team_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()
        
        api_response = response.json()
        return api_response

async def get_competitions(filters: LeagueFilters):

    url = f"{BASE_URL}/leagues"

    params = filters.dict(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()
        
        api_response = response.json()
        return  api_response

async def get_competition_by_id(competition_id: int):

    url = f"{BASE_URL}/leagues"

    params = {"id":competition_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()
        
        api_response = response.json()
        return api_response
    
