"""Domain entities for web scraping."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class ScrapingStatus(str, Enum):
    """Enumeration for scraping task status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataType(str, Enum):
    """Enumeration for data types that can be scraped."""
    
    JOB_LISTING = "job_listing"
    MEMBER_CLUB = "member_club"
    SUPPORT_RESOURCE = "support_resource"
    GENERAL_DATA = "general_data"


@dataclass
class ScrapingTarget:
    """Value object representing a scraping target."""
    
    url: str
    data_type: DataType
    selectors: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    javascript_required: bool = False
    
    def __post_init__(self) -> None:
        """Validate scraping target after initialization."""
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")


@dataclass
class ScrapedData:
    """Value object representing scraped data."""
    
    source_url: str
    data_type: DataType
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate scraped data after initialization."""
        if not self.content:
            raise ValueError("Content cannot be empty")


@dataclass
class ScrapingJob:
    """Aggregate root for scraping operations."""
    
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    targets: List[ScrapingTarget] = field(default_factory=list)
    status: ScrapingStatus = ScrapingStatus.PENDING
    results: List[ScrapedData] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """Start the scraping job."""
        if self.status != ScrapingStatus.PENDING:
            raise ValueError(f"Cannot start job in {self.status} status")
        
        self.status = ScrapingStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Mark the scraping job as completed."""
        if self.status != ScrapingStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete job in {self.status} status")
        
        self.status = ScrapingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def fail(self, error_message: str) -> None:
        """Mark the scraping job as failed."""
        if self.status not in [ScrapingStatus.PENDING, ScrapingStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot fail job in {self.status} status")
        
        self.status = ScrapingStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel the scraping job."""
        if self.status == ScrapingStatus.COMPLETED:
            raise ValueError("Cannot cancel completed job")
        
        self.status = ScrapingStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def add_result(self, scraped_data: ScrapedData) -> None:
        """Add scraped data to the job results."""
        self.results.append(scraped_data)
    
    def add_target(self, target: ScrapingTarget) -> None:
        """Add a scraping target to the job."""
        self.targets.append(target)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of scraping."""
        if not self.targets:
            return 0.0
        return len(self.results) / len(self.targets)


@dataclass
class JobListing:
    """Domain entity for job listing data."""
    
    title: str
    company: str
    location: str
    description: str
    salary: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    posted_date: Optional[datetime] = None
    application_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job listing to dictionary."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "salary": self.salary,
            "requirements": self.requirements,
            "benefits": self.benefits,
            "employment_type": self.employment_type,
            "experience_level": self.experience_level,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "application_url": self.application_url,
        }


@dataclass
class MemberClub:
    """Domain entity for member club data."""
    
    name: str
    location: str
    description: str
    contact_info: Dict[str, str] = field(default_factory=dict)
    website: Optional[str] = None
    established_date: Optional[datetime] = None
    member_count: Optional[int] = None
    categories: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert member club to dictionary."""
        return {
            "name": self.name,
            "location": self.location,
            "description": self.description,
            "contact_info": self.contact_info,
            "website": self.website,
            "established_date": self.established_date.isoformat() 
                if self.established_date else None,
            "member_count": self.member_count,
            "categories": self.categories,
        }


@dataclass
class SupportResource:
    """Domain entity for support resource data."""
    
    title: str
    category: str
    description: str
    resource_type: str
    download_url: Optional[str] = None
    file_size: Optional[str] = None
    version: Optional[str] = None
    compatibility: List[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert support resource to dictionary."""
        return {
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "resource_type": self.resource_type,
            "download_url": self.download_url,
            "file_size": self.file_size,
            "version": self.version,
            "compatibility": self.compatibility,
            "last_updated": self.last_updated.isoformat() 
                if self.last_updated else None,
        } 