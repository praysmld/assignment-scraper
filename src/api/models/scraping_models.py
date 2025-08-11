"""Pydantic models for scraping API."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator


class ScrapingTargetRequest(BaseModel):
    """Request model for scraping target."""
    
    url: HttpUrl = Field(..., description="URL to scrape")
    data_type: str = Field(..., description="Type of data to scrape")
    selectors: Dict[str, str] = Field(
        default_factory=dict, 
        description="CSS selectors for data extraction"
    )
    headers: Dict[str, str] = Field(
        default_factory=dict, 
        description="HTTP headers to use"
    )
    cookies: Dict[str, str] = Field(
        default_factory=dict, 
        description="Cookies to send with request"
    )
    javascript_required: bool = Field(
        default=False, 
        description="Whether JavaScript is required"
    )
    
    @validator("data_type")
    def validate_data_type(cls, v):
        """Validate data type."""
        allowed_types = ["job_listing", "member_club", "support_resource", "general_data"]
        if v not in allowed_types:
            raise ValueError(f"data_type must be one of {allowed_types}")
        return v


class CreateScrapingJobRequest(BaseModel):
    """Request model for creating a scraping job."""
    
    name: str = Field(..., description="Name of the scraping job")
    targets: List[ScrapingTargetRequest] = Field(
        ..., 
        description="List of targets to scrape"
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Job configuration"
    )
    
    @validator("targets")
    def validate_targets(cls, v):
        """Validate targets list."""
        if not v:
            raise ValueError("At least one target is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 targets allowed per job")
        return v


class ScrapingTargetResponse(BaseModel):
    """Response model for scraping target."""
    
    url: str
    data_type: str
    selectors: Dict[str, str]
    headers: Dict[str, str]
    cookies: Dict[str, str]
    javascript_required: bool


class ScrapedDataResponse(BaseModel):
    """Response model for scraped data."""
    
    source_url: str
    data_type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    scraped_at: datetime


class ScrapingJobResponse(BaseModel):
    """Response model for scraping job."""
    
    id: UUID
    name: str
    status: str
    targets: List[ScrapingTargetResponse]
    results: List[ScrapedDataResponse]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    config: Dict[str, Any]
    duration: Optional[float]
    success_rate: float


class ScrapingJobListResponse(BaseModel):
    """Response model for listing scraping jobs."""
    
    jobs: List[ScrapingJobResponse]
    total: int
    limit: int
    offset: int


class JobListingResponse(BaseModel):
    """Response model for job listing."""
    
    title: str
    company: str
    location: str
    description: str
    salary: Optional[str]
    requirements: List[str]
    benefits: List[str]
    employment_type: Optional[str]
    experience_level: Optional[str]
    posted_date: Optional[datetime]
    application_url: Optional[str]


class MemberClubResponse(BaseModel):
    """Response model for member club."""
    
    name: str
    location: str
    description: str
    contact_info: Dict[str, str]
    website: Optional[str]
    established_date: Optional[datetime]
    member_count: Optional[int]
    categories: List[str]


class SupportResourceResponse(BaseModel):
    """Response model for support resource."""
    
    title: str
    category: str
    description: str
    resource_type: str
    download_url: Optional[str]
    file_size: Optional[str]
    version: Optional[str]
    compatibility: List[str]
    last_updated: Optional[datetime]


class BulkScrapingRequest(BaseModel):
    """Request model for bulk scraping."""
    
    targets: List[ScrapingTargetRequest] = Field(
        ..., 
        description="List of targets to scrape"
    )
    job_name: str = Field(
        default="Bulk Scraping Job", 
        description="Name for the bulk scraping job"
    )
    
    @validator("targets")
    def validate_targets(cls, v):
        """Validate targets list."""
        if not v:
            raise ValueError("At least one target is required")
        if len(v) > 1000:
            raise ValueError("Maximum 1000 targets allowed for bulk scraping")
        return v


class UrlValidationRequest(BaseModel):
    """Request model for URL validation."""
    
    url: HttpUrl = Field(..., description="URL to validate")


class UrlValidationResponse(BaseModel):
    """Response model for URL validation."""
    
    url: str
    is_valid: bool
    message: Optional[str]


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    
    status: str
    timestamp: datetime
    version: str
    database: str
    cache: str


class MetricsResponse(BaseModel):
    """Response model for metrics."""
    
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_scraped_items: int
    average_job_duration: float
    success_rate: float


class SearchJobsRequest(BaseModel):
    """Request model for searching jobs."""
    
    base_url: HttpUrl = Field(..., description="Base URL of job board")
    query: str = Field(..., description="Job search query")
    location: str = Field(default="", description="Location filter")
    max_results: int = Field(default=50, description="Maximum results to return")
    
    @validator("max_results")
    def validate_max_results(cls, v):
        """Validate max results."""
        if v < 1 or v > 500:
            raise ValueError("max_results must be between 1 and 500")
        return v


class ScrapingConfigRequest(BaseModel):
    """Request model for scraping configuration."""
    
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retries: int = Field(default=3, description="Number of retries")
    delay: float = Field(default=1.0, description="Delay between requests")
    user_agent: Optional[str] = Field(None, description="Custom user agent")
    javascript_enabled: bool = Field(default=False, description="Enable JavaScript")
    
    @validator("timeout")
    def validate_timeout(cls, v):
        """Validate timeout."""
        if v < 1 or v > 300:
            raise ValueError("timeout must be between 1 and 300 seconds")
        return v
    
    @validator("retries")
    def validate_retries(cls, v):
        """Validate retries."""
        if v < 0 or v > 10:
            raise ValueError("retries must be between 0 and 10")
        return v
    
    @validator("delay")
    def validate_delay(cls, v):
        """Validate delay."""
        if v < 0 or v > 60:
            raise ValueError("delay must be between 0 and 60 seconds")
        return v 