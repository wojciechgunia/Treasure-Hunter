from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    createAt = Column(DateTime, default=datetime.utcnow)
    isBlocked = Column(Boolean, default=False)

    missions = relationship("Mission", back_populates="user")


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    lastRouteUpdate = Column(DateTime, nullable=True)
    lastRunning = Column(DateTime, nullable=True)
    waypointsNo = Column(Integer, default=0)
    pointsOfInterestsNo = Column(Integer, default=0)
    runningsNo = Column(Integer, default=0)

    user = relationship("User", back_populates="missions")
    waypoints = relationship("Waypoint", back_populates="mission", cascade="all, delete-orphan")
    runnings = relationship("Runnings", back_populates="mission", cascade="all, delete-orphan")
    points_of_interest = relationship("PointsOfInterest", back_populates="mission", cascade="all, delete-orphan")


class Waypoint(Base):
    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True, index=True)
    missionId = Column(Integer, ForeignKey("missions.id"), nullable=False)
    no = Column(Integer, nullable=False)
    lat = Column(String, nullable=False)
    lon = Column(String, nullable=False)
    lastUpdate = Column(DateTime, default=datetime.utcnow)

    mission = relationship("Mission", back_populates="waypoints")


class Runnings(Base):
    __tablename__ = "runnings"

    id = Column(Integer, primary_key=True, index=True)
    missionId = Column(Integer, ForeignKey("missions.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    stats = Column(Text)

    mission = relationship("Mission", back_populates="runnings")


class PointsOfInterest(Base):
    __tablename__ = "points_of_interests"

    id = Column(Integer, primary_key=True, index=True)
    missionId = Column(Integer, ForeignKey("missions.id"), nullable=False)
    createAt = Column(DateTime, default=datetime.utcnow)
    lat = Column(String, nullable=False)
    lon = Column(String, nullable=False)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    pictures = Column(JSON, nullable=True)

    mission = relationship("Mission", back_populates="points_of_interest")