from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer,unique=True,nullable=False)
    name = Column(String, unique=True, nullable=False)
    season=Column(Integer)
    country = Column(String)
    type = Column(String)
    logo = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    teams = relationship("Team", back_populates="competition")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer,unique=True,nullable=False)
    name = Column(String, nullable=False)
    short_name = Column(String)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    venue_name = Column(String, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    competition = relationship("Competition", back_populates="teams")

    __table_args__ = (
        UniqueConstraint("name", "competition_id", name="uq_team_name_competition"),
    )

class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)
    external_id =Column(Integer, unique=True, nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    gameweek = Column(Integer, nullable=False)
    kickoff_time = Column(DateTime(timezone=True), nullable=False)
    status=Column(String)
    home_goals=Column(Integer)
    away_goals=Column(Integer)
    referee=Column(String)
    updated_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("competition_id", "home_team_id", "away_team_id", "kickoff_time", name="uq_fixture"),
    )

    competition = relationship("Competition")
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])