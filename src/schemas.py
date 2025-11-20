import enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=6, max_length=72)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AnalysisBase(BaseModel):
    analysis_id: int
    original_image_url: str
    processed_image_url: Optional[str]
    status: str
    created_at: datetime
    processing_time: Optional[float]
    detections_summary: Optional[Dict[str, Any]]


class AnalysisList(BaseModel):
    analyses: List[AnalysisBase]
    total: int


class UserResponse(BaseModel):
    email: EmailStr
    username: str
    created_at: datetime
    subscription_type: str


class InterviewRequest(BaseModel):
    interview_type: str
    job_position: str
    company: str
