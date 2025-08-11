"""Use cases for scraping operations."""

import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.scraping import (
    ScrapingJob, 
    ScrapingTarget, 
    ScrapedData, 
    DataType,
    JobListing,
    MemberClub,
    SupportResource
)
from ...domain.repositories.scraping_repository import (
    ScrapingJobRepository, 
    ScrapedDataRepository
)
from ...domain.services.scraper_service import (
    WebScraperService,
    JobListingScraperService,
    MemberClubScraperService,
    SupportResourceScraperService
)


class CreateScrapingJobUseCase:
    """Use case for creating a new scraping job."""
    
    def __init__(self, job_repository: ScrapingJobRepository) -> None:
        """Initialize use case with dependencies."""
        self.job_repository = job_repository
    
    async def execute(
        self, 
        name: str, 
        targets: List[Dict[str, Any]],
        config: Dict[str, Any] = None
    ) -> ScrapingJob:
        """Execute the use case to create a scraping job."""
        # Convert target dictionaries to ScrapingTarget entities
        scraping_targets = []
        for target_data in targets:
            target = ScrapingTarget(
                url=target_data["url"],
                data_type=DataType(target_data["data_type"]),
                selectors=target_data.get("selectors", {}),
                headers=target_data.get("headers", {}),
                cookies=target_data.get("cookies", {}),
                javascript_required=target_data.get("javascript_required", False)
            )
            scraping_targets.append(target)
        
        # Create the scraping job
        job = ScrapingJob(
            name=name,
            targets=scraping_targets,
            config=config or {}
        )
        
        # Save the job
        return await self.job_repository.save(job)


class ExecuteScrapingJobUseCase:
    """Use case for executing a scraping job."""
    
    def __init__(
        self,
        job_repository: ScrapingJobRepository,
        data_repository: ScrapedDataRepository,
        web_scraper: WebScraperService,
        job_scraper: JobListingScraperService,
        club_scraper: MemberClubScraperService,
        resource_scraper: SupportResourceScraperService
    ) -> None:
        """Initialize use case with dependencies."""
        self.job_repository = job_repository
        self.data_repository = data_repository
        self.web_scraper = web_scraper
        self.job_scraper = job_scraper
        self.club_scraper = club_scraper
        self.resource_scraper = resource_scraper
    
    async def execute(self, job_id: UUID) -> ScrapingJob:
        """Execute the scraping job."""
        # Get the job
        job = await self.job_repository.find_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        
        # Start the job
        job.start()
        await self.job_repository.update(job)
        
        try:
            # Execute scraping for each target
            for target in job.targets:
                scraped_data = await self._scrape_target(target)
                if scraped_data:
                    job.add_result(scraped_data)
            
            # Mark job as completed
            job.complete()
            
        except Exception as e:
            # Mark job as failed
            job.fail(str(e))
        
        # Update the job
        return await self.job_repository.update(job)
    
    async def _scrape_target(self, target: ScrapingTarget) -> Optional[ScrapedData]:
        """Scrape a single target based on its data type."""
        try:
            if target.data_type == DataType.JOB_LISTING:
                return await self._scrape_job_listing(target)
            elif target.data_type == DataType.MEMBER_CLUB:
                return await self._scrape_member_club(target)
            elif target.data_type == DataType.SUPPORT_RESOURCE:
                return await self._scrape_support_resource(target)
            else:
                return await self.web_scraper.scrape_url(target)
        
        except Exception as e:
            print(f"Error scraping target {target.url}: {e}")
            return None
    
    async def _scrape_job_listing(self, target: ScrapingTarget) -> Optional[ScrapedData]:
        """Scrape job listing data."""
        job_listings = await self.job_scraper.scrape_job_listings(
            target.url, 
            target.selectors
        )
        
        if job_listings:
            content = {
                "jobs": [job.to_dict() for job in job_listings],
                "count": len(job_listings)
            }
            
            return ScrapedData(
                source_url=target.url,
                data_type=target.data_type,
                content=content
            )
        
        return None
    
    async def _scrape_member_club(self, target: ScrapingTarget) -> Optional[ScrapedData]:
        """Scrape member club data."""
        clubs = await self.club_scraper.scrape_member_clubs(
            target.url, 
            target.selectors
        )
        
        if clubs:
            content = {
                "clubs": [club.to_dict() for club in clubs],
                "count": len(clubs)
            }
            
            return ScrapedData(
                source_url=target.url,
                data_type=target.data_type,
                content=content
            )
        
        return None
    
    async def _scrape_support_resource(self, target: ScrapingTarget) -> Optional[ScrapedData]:
        """Scrape support resource data."""
        resources = await self.resource_scraper.scrape_support_resources(
            target.url, 
            target.selectors
        )
        
        if resources:
            content = {
                "resources": [resource.to_dict() for resource in resources],
                "count": len(resources)
            }
            
            return ScrapedData(
                source_url=target.url,
                data_type=target.data_type,
                content=content
            )
        
        return None


class GetScrapingJobUseCase:
    """Use case for retrieving a scraping job."""
    
    def __init__(self, job_repository: ScrapingJobRepository) -> None:
        """Initialize use case with dependencies."""
        self.job_repository = job_repository
    
    async def execute(self, job_id: UUID) -> Optional[ScrapingJob]:
        """Execute the use case to get a scraping job."""
        return await self.job_repository.find_by_id(job_id)


class ListScrapingJobsUseCase:
    """Use case for listing scraping jobs."""
    
    def __init__(self, job_repository: ScrapingJobRepository) -> None:
        """Initialize use case with dependencies."""
        self.job_repository = job_repository
    
    async def execute(
        self, 
        limit: int = 100, 
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[ScrapingJob]:
        """Execute the use case to list scraping jobs."""
        if status:
            return await self.job_repository.find_by_status(status, limit, offset)
        else:
            return await self.job_repository.find_all(limit, offset)


class DeleteScrapingJobUseCase:
    """Use case for deleting a scraping job."""
    
    def __init__(self, job_repository: ScrapingJobRepository) -> None:
        """Initialize use case with dependencies."""
        self.job_repository = job_repository
    
    async def execute(self, job_id: UUID) -> bool:
        """Execute the use case to delete a scraping job."""
        return await self.job_repository.delete(job_id)


class GetScrapedDataUseCase:
    """Use case for retrieving scraped data."""
    
    def __init__(self, data_repository: ScrapedDataRepository) -> None:
        """Initialize use case with dependencies."""
        self.data_repository = data_repository
    
    async def execute_by_job_id(self, job_id: UUID) -> List[ScrapedData]:
        """Get scraped data by job ID."""
        return await self.data_repository.find_by_job_id(job_id)
    
    async def execute_by_data_type(
        self, 
        data_type: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ScrapedData]:
        """Get scraped data by data type."""
        return await self.data_repository.find_by_data_type(data_type, limit, offset)
    
    async def execute_by_source_url(self, source_url: str) -> List[ScrapedData]:
        """Get scraped data by source URL."""
        return await self.data_repository.find_by_source_url(source_url)


class ValidateUrlUseCase:
    """Use case for validating URLs before scraping."""
    
    def __init__(self, web_scraper: WebScraperService) -> None:
        """Initialize use case with dependencies."""
        self.web_scraper = web_scraper
    
    async def execute(self, url: str) -> bool:
        """Execute URL validation."""
        return await self.web_scraper.validate_url(url)


class BulkScrapingUseCase:
    """Use case for bulk scraping operations."""
    
    def __init__(
        self,
        job_repository: ScrapingJobRepository,
        web_scraper: WebScraperService
    ) -> None:
        """Initialize use case with dependencies."""
        self.job_repository = job_repository
        self.web_scraper = web_scraper
    
    async def execute(
        self, 
        targets: List[ScrapingTarget],
        job_name: str = "Bulk Scraping Job"
    ) -> ScrapingJob:
        """Execute bulk scraping operation."""
        # Create a new job for bulk operation
        job = ScrapingJob(name=job_name, targets=targets)
        job = await self.job_repository.save(job)
        
        # Start the job
        job.start()
        await self.job_repository.update(job)
        
        try:
            # Execute scraping for all targets
            scraped_data_list = await self.web_scraper.scrape_multiple_urls(targets)
            
            # Add results to job
            for scraped_data in scraped_data_list:
                job.add_result(scraped_data)
            
            # Mark job as completed
            job.complete()
            
        except Exception as e:
            # Mark job as failed
            job.fail(str(e))
        
        # Update and return the job
        return await self.job_repository.update(job) 