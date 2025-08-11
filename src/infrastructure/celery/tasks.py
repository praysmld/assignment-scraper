"""Celery tasks for background scraping operations."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from celery import Task
from celery.utils.log import get_task_logger

from .worker import celery_app, run_async_task
from ...infrastructure.database.database import db_manager
from ...infrastructure.repositories.scraping_repository_impl import (
    SQLAlchemyScrapingJobRepository,
    SQLAlchemyScrapedDataRepository
)
from ...infrastructure.services.web_scraper_impl import (
    HttpWebScraperService,
    ModernJobListingScraperService
)
from ...application.use_cases.scraping_use_cases import (
    ExecuteScrapingJobUseCase,
    BulkScrapingUseCase
)
from ...domain.entities.scraping import ScrapingTarget, DataType

logger = get_task_logger(__name__)


class DatabaseTask(Task):
    """Base task class with database session management."""
    
    _db_session = None
    
    @property
    def db_session(self):
        if self._db_session is None:
            self._db_session = db_manager.get_session()
        return self._db_session


@celery_app.task(bind=True, base=DatabaseTask)
def execute_scraping_job(self, job_id: str):
    """Execute a scraping job in the background."""
    logger.info(f"Starting execution of scraping job: {job_id}")
    
    async def _execute():
        async with db_manager.get_session() as session:
            job_repo = SQLAlchemyScrapingJobRepository(session)
            data_repo = SQLAlchemyScrapedDataRepository(session)
            
            web_scraper = HttpWebScraperService()
            job_scraper = ModernJobListingScraperService()
            
            use_case = ExecuteScrapingJobUseCase(
                job_repo, data_repo, web_scraper, job_scraper, None, None
            )
            
            try:
                result = await use_case.execute(UUID(job_id))
                logger.info(f"Successfully completed scraping job: {job_id}")
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "scraped_items": len(result.results) if result else 0
                }
            except Exception as e:
                logger.error(f"Failed to execute scraping job {job_id}: {str(e)}")
                raise
    
    return run_async_task(_execute())


@celery_app.task(bind=True, base=DatabaseTask)
def bulk_scrape_urls(self, targets_data: List[Dict[str, Any]], job_name: str = None):
    """Perform bulk scraping of multiple URLs."""
    logger.info(f"Starting bulk scraping of {len(targets_data)} URLs")
    
    async def _bulk_scrape():
        async with db_manager.get_session() as session:
            job_repo = SQLAlchemyScrapingJobRepository(session)
            web_scraper = HttpWebScraperService()
            
            # Convert target data to domain entities
            targets = []
            for target_data in targets_data:
                target = ScrapingTarget(
                    url=target_data["url"],
                    data_type=DataType(target_data["data_type"]),
                    selectors=target_data.get("selectors", {}),
                    headers=target_data.get("headers", {}),
                    cookies=target_data.get("cookies", {}),
                    javascript_required=target_data.get("javascript_required", False)
                )
                targets.append(target)
            
            use_case = BulkScrapingUseCase(job_repo, web_scraper)
            
            try:
                result = await use_case.execute(targets, job_name)
                logger.info(f"Successfully completed bulk scraping: {len(targets)} URLs")
                return {
                    "job_id": str(result.id),
                    "status": "completed",
                    "targets_processed": len(targets)
                }
            except Exception as e:
                logger.error(f"Failed bulk scraping: {str(e)}")
                raise
    
    return run_async_task(_bulk_scrape())


@celery_app.task(bind=True)
def validate_urls(self, urls: List[str]):
    """Validate multiple URLs for accessibility."""
    logger.info(f"Validating {len(urls)} URLs")
    
    async def _validate():
        web_scraper = HttpWebScraperService()
        results = {}
        
        async with web_scraper:
            for url in urls:
                try:
                    is_valid = await web_scraper.validate_url(url)
                    results[url] = {
                        "is_valid": is_valid,
                        "message": "URL is accessible" if is_valid else "URL not accessible"
                    }
                except Exception as e:
                    results[url] = {
                        "is_valid": False,
                        "message": f"Validation error: {str(e)}"
                    }
        
        logger.info(f"URL validation completed: {len(results)} results")
        return results
    
    return run_async_task(_validate())


@celery_app.task(bind=True, base=DatabaseTask)
def cleanup_old_jobs(self):
    """Clean up old completed jobs and their data."""
    logger.info("Starting cleanup of old jobs")
    
    async def _cleanup():
        async with db_manager.get_session() as session:
            job_repo = SQLAlchemyScrapingJobRepository(session)
            data_repo = SQLAlchemyScrapedDataRepository(session)
            
            # Delete jobs older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            try:
                # This would need to be implemented in the repository
                # deleted_jobs = await job_repo.delete_older_than(cutoff_date)
                # deleted_data = await data_repo.delete_older_than(cutoff_date)
                
                logger.info("Cleanup completed")
                return {
                    "status": "completed",
                    "cutoff_date": cutoff_date.isoformat()
                }
            except Exception as e:
                logger.error(f"Cleanup failed: {str(e)}")
                raise
    
    return run_async_task(_cleanup())


@celery_app.task(bind=True)
def health_check(self):
    """Perform health check of the worker."""
    logger.info("Performing worker health check")
    
    try:
        # Test database connection
        async def _test_db():
            async with db_manager.get_session() as session:
                # Simple query to test connection
                await session.execute("SELECT 1")
                return True
        
        db_healthy = run_async_task(_test_db())
        
        # Test web scraping capability
        async def _test_scraping():
            web_scraper = HttpWebScraperService()
            async with web_scraper:
                return await web_scraper.validate_url("https://httpbin.org/get")
        
        scraping_healthy = run_async_task(_test_scraping())
        
        result = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_healthy,
            "scraping": scraping_healthy
        }
        
        logger.info("Health check completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@celery_app.task(bind=True, base=DatabaseTask)
def search_jobs_task(self, query: str, location: str = None, max_results: int = 50):
    """Search for job listings asynchronously."""
    logger.info(f"Searching for jobs: query='{query}', location='{location}'")
    
    async def _search_jobs():
        job_scraper = ModernJobListingScraperService()
        
        try:
            # This would need a base URL - in real implementation, 
            # you'd have configured job board URLs
            jobs = await job_scraper.search_jobs(
                base_url="https://jobs.example.com",  # Replace with actual job board
                query=query,
                location=location
            )
            
            # Limit results
            jobs = jobs[:max_results]
            
            result = []
            for job in jobs:
                result.append({
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "description": job.description[:500] if job.description else None,
                    "salary": job.salary,
                    "employment_type": job.employment_type,
                    "experience_level": job.experience_level,
                    "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                    "application_url": job.application_url
                })
            
            logger.info(f"Found {len(result)} job listings")
            return result
            
        except Exception as e:
            logger.error(f"Job search failed: {str(e)}")
            raise
    
    return run_async_task(_search_jobs())


@celery_app.task(bind=True)
def extract_data_from_url(self, url: str, data_type: str, selectors: Dict[str, str] = None):
    """Extract specific data from a single URL."""
    logger.info(f"Extracting {data_type} data from: {url}")
    
    async def _extract():
        web_scraper = HttpWebScraperService()
        
        target = ScrapingTarget(
            url=url,
            data_type=DataType(data_type),
            selectors=selectors or {},
            headers={},
            cookies={},
            javascript_required=False
        )
        
        try:
            async with web_scraper:
                scraped_data = await web_scraper.scrape_url(target)
                
                if scraped_data:
                    result = {
                        "source_url": scraped_data.source_url,
                        "data_type": scraped_data.data_type.value,
                        "content": scraped_data.content,
                        "metadata": scraped_data.metadata,
                        "scraped_at": scraped_data.scraped_at.isoformat()
                    }
                    logger.info(f"Successfully extracted data from: {url}")
                    return result
                else:
                    logger.warning(f"No data extracted from: {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Data extraction failed for {url}: {str(e)}")
            raise
    
    return run_async_task(_extract()) 