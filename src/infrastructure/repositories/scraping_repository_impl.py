"""Concrete repository implementations for scraping domain."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, delete, and_
from sqlalchemy.orm import Session, selectinload

from ...domain.entities.scraping import ScrapingJob, ScrapedData, ScrapingStatus, DataType
from ...domain.repositories.scraping_repository import (
    ScrapingJobRepository, 
    ScrapedDataRepository
)
from ..database.models import ScrapingJobModel, ScrapedDataModel


class SQLAlchemyScrapingJobRepository(ScrapingJobRepository):
    """SQLAlchemy implementation of scraping job repository."""
    
    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        self.session = session
    
    async def save(self, job: ScrapingJob) -> ScrapingJob:
        """Save a scraping job."""
        # Convert domain entity to database model
        job_model = ScrapingJobModel(
            id=job.id,
            name=job.name,
            status=job.status.value,
            targets=[
                {
                    "url": target.url,
                    "data_type": target.data_type.value,
                    "selectors": target.selectors,
                    "headers": target.headers,
                    "cookies": target.cookies,
                    "javascript_required": target.javascript_required,
                }
                for target in job.targets
            ],
            config=job.config,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        
        self.session.add(job_model)
        self.session.flush()
        
        return self._model_to_entity(job_model)
    
    async def find_by_id(self, job_id: UUID) -> Optional[ScrapingJob]:
        """Find a scraping job by ID."""
        query = select(ScrapingJobModel).where(
            ScrapingJobModel.id == job_id
        ).options(selectinload(ScrapingJobModel.scraped_data))
        
        job_model = self.session.execute(query).scalar_one_or_none()
        
        if job_model:
            return self._model_to_entity(job_model)
        return None
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[ScrapingJob]:
        """Find all scraping jobs with pagination."""
        query = select(ScrapingJobModel).offset(offset).limit(limit).options(
            selectinload(ScrapingJobModel.scraped_data)
        ).order_by(ScrapingJobModel.created_at.desc())
        
        job_models = self.session.execute(query).scalars().all()
        
        return [self._model_to_entity(model) for model in job_models]
    
    async def find_by_status(
        self, 
        status: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ScrapingJob]:
        """Find scraping jobs by status."""
        query = select(ScrapingJobModel).where(
            ScrapingJobModel.status == status
        ).offset(offset).limit(limit).options(
            selectinload(ScrapingJobModel.scraped_data)
        ).order_by(ScrapingJobModel.created_at.desc())
        
        job_models = self.session.execute(query).scalars().all()
        
        return [self._model_to_entity(model) for model in job_models]
    
    async def update(self, job: ScrapingJob) -> ScrapingJob:
        """Update an existing scraping job."""
        query = select(ScrapingJobModel).where(ScrapingJobModel.id == job.id)
        job_model = self.session.execute(query).scalar_one_or_none()
        
        if job_model:
            job_model.name = job.name
            job_model.status = job.status.value
            job_model.targets = [
                {
                    "url": target.url,
                    "data_type": target.data_type.value,
                    "selectors": target.selectors,
                    "headers": target.headers,
                    "cookies": target.cookies,
                    "javascript_required": target.javascript_required,
                }
                for target in job.targets
            ]
            job_model.config = job.config
            job_model.error_message = job.error_message
            job_model.started_at = job.started_at
            job_model.completed_at = job.completed_at
            
            self.session.flush()
            
            return self._model_to_entity(job_model)
        
        raise ValueError(f"Job with ID {job.id} not found")
    
    async def delete(self, job_id: UUID) -> bool:
        """Delete a scraping job."""
        query = delete(ScrapingJobModel).where(ScrapingJobModel.id == job_id)
        result = self.session.execute(query)
        
        return result.rowcount > 0
    
    def _model_to_entity(self, model: ScrapingJobModel) -> ScrapingJob:
        """Convert database model to domain entity."""
        from ...domain.entities.scraping import ScrapingTarget
        
        # Convert targets from JSON to domain objects
        targets = []
        for target_data in model.targets:
            target = ScrapingTarget(
                url=target_data["url"],
                data_type=DataType(target_data["data_type"]),
                selectors=target_data.get("selectors", {}),
                headers=target_data.get("headers", {}),
                cookies=target_data.get("cookies", {}),
                javascript_required=target_data.get("javascript_required", False),
            )
            targets.append(target)
        
        # Convert scraped data if available
        results = []
        if hasattr(model, 'scraped_data') and model.scraped_data:
            for data_model in model.scraped_data:
                scraped_data = ScrapedData(
                    source_url=data_model.source_url,
                    data_type=DataType(data_model.data_type),
                    content=data_model.content,
                    metadata=data_model.extra_metadata,
                    scraped_at=data_model.scraped_at,
                )
                results.append(scraped_data)
        
        return ScrapingJob(
            id=model.id,
            name=model.name,
            targets=targets,
            status=ScrapingStatus(model.status),
            results=results,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error_message=model.error_message,
            config=model.config,
        )


class SQLAlchemyScrapedDataRepository(ScrapedDataRepository):
    """SQLAlchemy implementation of scraped data repository."""
    
    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        self.session = session
    
    async def save(self, data: ScrapedData) -> ScrapedData:
        """Save scraped data."""
        # Note: We need to associate with a job_id, but ScrapedData doesn't have it
        # This would need to be handled differently in a real implementation
        data_model = ScrapedDataModel(
            source_url=data.source_url,
            data_type=data.data_type.value,
            content=data.content,
            extra_metadata=data.metadata,
            scraped_at=data.scraped_at,
        )
        
        self.session.add(data_model)
        self.session.flush()
        
        return self._model_to_entity(data_model)
    
    async def find_by_job_id(self, job_id: UUID) -> List[ScrapedData]:
        """Find scraped data by job ID."""
        query = select(ScrapedDataModel).where(ScrapedDataModel.job_id == job_id)
        data_models = self.session.execute(query).scalars().all()
        
        return [self._model_to_entity(model) for model in data_models]
    
    async def find_by_source_url(self, source_url: str) -> List[ScrapedData]:
        """Find scraped data by source URL."""
        query = select(ScrapedDataModel).where(
            ScrapedDataModel.source_url == source_url
        )
        data_models = self.session.execute(query).scalars().all()
        
        return [self._model_to_entity(model) for model in data_models]
    
    async def find_by_data_type(
        self, 
        data_type: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ScrapedData]:
        """Find scraped data by data type."""
        query = select(ScrapedDataModel).where(
            ScrapedDataModel.data_type == data_type
        ).offset(offset).limit(limit).order_by(
            ScrapedDataModel.scraped_at.desc()
        )
        
        data_models = self.session.execute(query).scalars().all()
        
        return [self._model_to_entity(model) for model in data_models]
    
    async def delete_old_data(self, days: int = 30) -> int:
        """Delete scraped data older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = delete(ScrapedDataModel).where(
            ScrapedDataModel.scraped_at < cutoff_date
        )
        
        result = self.session.execute(query)
        
        return result.rowcount
    
    def _model_to_entity(self, model: ScrapedDataModel) -> ScrapedData:
        """Convert database model to domain entity."""
        return ScrapedData(
            source_url=model.source_url,
            data_type=DataType(model.data_type),
            content=model.content,
            metadata=model.extra_metadata,
            scraped_at=model.scraped_at,
        ) 