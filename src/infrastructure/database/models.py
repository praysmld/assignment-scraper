"""SQLAlchemy models for scraping entities."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column, String, DateTime, JSON, Boolean, Integer, Text, 
    ForeignKey, Float, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ScrapingJobModel(Base):
    """SQLAlchemy model for scraping jobs."""
    
    __tablename__ = "scraping_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, default="")
    status = Column(String(50), nullable=False, default="pending")
    targets = Column(JSON, nullable=False, default=list)
    config = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    scraped_data = relationship(
        "ScrapedDataModel", 
        back_populates="job",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<ScrapingJob(id={self.id}, name={self.name}, status={self.status})>"


class ScrapedDataModel(Base):
    """SQLAlchemy model for scraped data."""
    
    __tablename__ = "scraped_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=False)
    source_url = Column(String(2048), nullable=False)
    data_type = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    extra_metadata = Column(JSON, nullable=False, default=dict)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    job = relationship("ScrapingJobModel", back_populates="scraped_data")
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<ScrapedData(id={self.id}, source_url={self.source_url[:50]}...)>"


class JobListingModel(Base):
    """SQLAlchemy model for job listings."""
    
    __tablename__ = "job_listings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    salary = Column(String(100), nullable=True)
    requirements = Column(JSON, nullable=False, default=list)
    benefits = Column(JSON, nullable=False, default=list)
    employment_type = Column(String(50), nullable=True)
    experience_level = Column(String(50), nullable=True)
    posted_date = Column(DateTime, nullable=True)
    application_url = Column(String(2048), nullable=True)
    source_url = Column(String(2048), nullable=False)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<JobListing(id={self.id}, title={self.title}, company={self.company})>"


class MemberClubModel(Base):
    """SQLAlchemy model for member clubs."""
    
    __tablename__ = "member_clubs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    contact_info = Column(JSON, nullable=False, default=dict)
    website = Column(String(2048), nullable=True)
    established_date = Column(DateTime, nullable=True)
    member_count = Column(Integer, nullable=True)
    categories = Column(JSON, nullable=False, default=list)
    source_url = Column(String(2048), nullable=False)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<MemberClub(id={self.id}, name={self.name}, location={self.location})>"


class SupportResourceModel(Base):
    """SQLAlchemy model for support resources."""
    
    __tablename__ = "support_resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    resource_type = Column(String(50), nullable=False)
    download_url = Column(String(2048), nullable=True)
    file_size = Column(String(50), nullable=True)
    version = Column(String(50), nullable=True)
    compatibility = Column(JSON, nullable=False, default=list)
    last_updated = Column(DateTime, nullable=True)
    source_url = Column(String(2048), nullable=False)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<SupportResource(id={self.id}, title={self.title}, category={self.category})>"


class ScrapingMetricsModel(Base):
    """SQLAlchemy model for scraping metrics."""
    
    __tablename__ = "scraping_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<ScrapingMetrics(job_id={self.job_id}, metric={self.metric_name}={self.metric_value})>"


class ScrapingLogModel(Base):
    """SQLAlchemy model for scraping logs."""
    
    __tablename__ = "scraping_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<ScrapingLog(job_id={self.job_id}, level={self.level}, message={self.message[:50]}...)>" 