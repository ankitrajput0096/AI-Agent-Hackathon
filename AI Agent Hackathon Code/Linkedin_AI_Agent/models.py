from typing import List, Optional
from pydantic import BaseModel, Field

class SearchQuery(BaseModel):
    company: Optional[str] = Field(None, description="Company name if mentioned")
    role: Optional[str] = Field(None, description="Job role or position")
    purpose: Optional[str] = Field(None, description="Purpose of connection (e.g., referral, networking)")
    location: Optional[str] = Field(None, description="Location if mentioned")
    experience_level: Optional[str] = Field(None, description="Experience level if mentioned")

class LinkedInProfile(BaseModel):
    name: str = Field(..., description="Full name of the person")
    headline: str = Field(..., description="Profile headline/title")
    profile_url: str = Field(..., description="URL to LinkedIn profile")

class SearchParameters(BaseModel):
    keywords: str = Field(..., description="Search keywords")
    connection_degree: List[str] = Field(default=["2nd"])
    network_depth: str = Field(default="S")
    origin: str = Field(default="SEARCH_RESULTS")
    current_company: Optional[str] = None
    location: Optional[str] = None
    experience_level: Optional[str] = None
    title_roles: Optional[List[str]] = None

class ConnectionMessage(BaseModel):
    message: str = Field(..., description="Personalized connection message")
    context: dict = Field(default_factory=dict, description="Context used to generate the message") 