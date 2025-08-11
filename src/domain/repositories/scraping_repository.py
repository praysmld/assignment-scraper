"""Repository interfaces for scraping domain."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.scraping import ScrapingJob, ScrapedData


class ScrapingJobRepository(ABC):
    """Abstract repository for scraping jobs."""
    
    @abstractmethod
    async def save(self, job: ScrapingJob) -> ScrapingJob:
        """Save a scraping job."""
        pass
    
    @abstractmethod
    async def find_by_id(self, job_id: UUID) -> Optional[ScrapingJob]:
        """Find a scraping job by ID."""
        pass
    
    @abstractmethod
    async def find_all(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ScrapingJob]:
        """Find all scraping jobs with pagination."""
        pass
    
    @abstractmethod
    async def find_by_status(
        self, 
        status: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ScrapingJob]:
        """Find scraping jobs by status."""
        pass
    
    @abstractmethod
    async def update(self, job: ScrapingJob) -> ScrapingJob:
        """Update an existing scraping job."""
        pass
    
    @abstractmethod
    async def delete(self, job_id: UUID) -> bool:
        """Delete a scraping job."""
        pass


class ScrapedDataRepository(ABC):
    """Abstract repository for scraped data."""
    
    @abstractmethod
    async def save(self, data: ScrapedData) -> ScrapedData:
        """Save scraped data."""
        pass
    
    @abstractmethod
    async def find_by_job_id(self, job_id: UUID) -> List[ScrapedData]:
        """Find scraped data by job ID."""
        pass
    
    @abstractmethod
    async def find_by_source_url(self, source_url: str) -> List[ScrapedData]:
        """Find scraped data by source URL."""
        pass
    
    @abstractmethod
    async def find_by_data_type(
        self, 
        data_type: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ScrapedData]:
        """Find scraped data by data type."""
        pass
    
    @abstractmethod
    async def delete_old_data(self, days: int = 30) -> int:
        """Delete scraped data older than specified days."""
        pass 