from pydantic import BaseModel, Field
from typing import Optional


class Constraints(BaseModel):
    time_budget: str = Field(default="半天", description="时间预算：半天/一天/两天")
    start_time: Optional[str] = Field(default=None, description="出发时间 HH:MM")
    budget_per_person: int = Field(default=200, description="人均预算(元)")
    preferences: list[str] = Field(default_factory=list, description="偏好标签")
    people_count: int = Field(default=2, description="人数")


class RouteRequest(BaseModel):
    user_input: str = Field(description="用户自然语言输入")
    constraints: Constraints = Field(default_factory=Constraints)


class Location(BaseModel):
    lat: float
    lng: float
    address: str = ""


class POI(BaseModel):
    id: str
    name: str
    category: str
    sub_category: str = ""
    rating: float = 0.0
    avg_cost: int = 0
    arrival_time: str = ""
    duration_minutes: int = 60
    stay_reason: str = ""
    location: Optional[Location] = None
    business_hours: str = ""


class RouteResponse(BaseModel):
    success: bool = True
    route_name: str = ""
    pois: list[POI] = Field(default_factory=list)
    total_cost_per_person: int = 0
    total_duration_minutes: int = 0
    summary: str = ""
    ai_reasoning: str = ""
    error: Optional[str] = None


class AdjustRequest(BaseModel):
    original_route: RouteResponse
    user_feedback: str
    constraints: Constraints = Field(default_factory=Constraints)
