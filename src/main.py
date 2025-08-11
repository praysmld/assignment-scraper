"""Main FastAPI application."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config.settings import settings
from .infrastructure.database.database import get_db_session, db_manager
from .infrastructure.database.models import Base
from .infrastructure.repositories.scraping_repository_impl import (
    SQLAlchemyScrapingJobRepository,
    SQLAlchemyScrapedDataRepository
)
from .infrastructure.services.web_scraper_impl import (
    HttpWebScraperService,
    ZendriverScraperService,
    ModernJobListingScraperService
)
from .application.use_cases.scraping_use_cases import (
    CreateScrapingJobUseCase,
    ExecuteScrapingJobUseCase,
    GetScrapingJobUseCase,
    ListScrapingJobsUseCase,
    DeleteScrapingJobUseCase,
    GetScrapedDataUseCase,
    ValidateUrlUseCase,
    BulkScrapingUseCase
)
from .api.models.scraping_models import (
    CreateScrapingJobRequest,
    ScrapingJobResponse,
    ScrapingJobListResponse,
    ScrapedDataResponse,
    UrlValidationRequest,
    UrlValidationResponse,
    BulkScrapingRequest,
    ErrorResponse,
    HealthCheckResponse,
    MetricsResponse,
    SearchJobsRequest,
    JobListingResponse
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("Starting Assignment Scraper API...")
    
    # Initialize database tables
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully")
    yield
    
    # Shutdown
    print("Shutting down Assignment Scraper API...")
    await db_manager.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Advanced web scraping solution for multiple website data extraction",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection functions
def get_job_repository(session=Depends(get_db_session)):
    """Get job repository instance."""
    return SQLAlchemyScrapingJobRepository(session)


def get_data_repository(session=Depends(get_db_session)):
    """Get data repository instance."""
    return SQLAlchemyScrapedDataRepository(session)


async def get_web_scraper():
    """Get web scraper service instance."""
    return HttpWebScraperService()


async def get_zendriver_scraper():
    """Get Zendriver scraper service instance."""
    return ZendriverScraperService()


async def get_job_scraper():
    """Get job listing scraper service instance."""
    return ModernJobListingScraperService()


# Use case dependency injection
def get_create_job_use_case(
    job_repo=Depends(get_job_repository)
):
    """Get create job use case."""
    return CreateScrapingJobUseCase(job_repo)


def get_execute_job_use_case(
    job_repo=Depends(get_job_repository),
    data_repo=Depends(get_data_repository),
):
    """Get execute job use case."""
    # Use Zendriver as primary scraper for undetectable scraping
    web_scraper = ZendriverScraperService()
    job_scraper = ModernJobListingScraperService()
    club_scraper = None  # Would be implemented
    resource_scraper = None  # Would be implemented
    
    return ExecuteScrapingJobUseCase(
        job_repo, data_repo, web_scraper, job_scraper, club_scraper, resource_scraper
    )


def get_get_job_use_case(
    job_repo=Depends(get_job_repository)
):
    """Get job use case."""
    return GetScrapingJobUseCase(job_repo)


def get_list_jobs_use_case(
    job_repo=Depends(get_job_repository)
):
    """Get list jobs use case."""
    return ListScrapingJobsUseCase(job_repo)


def get_delete_job_use_case(
    job_repo=Depends(get_job_repository)
):
    """Get delete job use case."""
    return DeleteScrapingJobUseCase(job_repo)


def get_get_data_use_case(
    data_repo=Depends(get_data_repository)
):
    """Get data use case."""
    return GetScrapedDataUseCase(data_repo)


# API Routes

@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint with health check."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        database="connected",
        cache="connected"
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        database="connected",
        cache="connected"
    )


@app.post(
    "/api/v1/jobs",
    response_model=ScrapingJobResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_scraping_job(
    request: CreateScrapingJobRequest,
    use_case: CreateScrapingJobUseCase = Depends(get_create_job_use_case)
):
    """Create a new scraping job."""
    try:
        # Convert request to use case format
        targets_data = []
        for target in request.targets:
            targets_data.append({
                "url": str(target.url),
                "data_type": target.data_type,
                "selectors": target.selectors,
                "headers": target.headers,
                "cookies": target.cookies,
                "javascript_required": target.javascript_required
            })
        
        job = await use_case.execute(
            name=request.name,
            targets=targets_data,
            config=request.config
        )
        
        return _convert_job_to_response(job)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/v1/jobs", response_model=ScrapingJobListResponse)
async def list_scraping_jobs(
    limit: int = 100,
    offset: int = 0,
    status_filter: Optional[str] = None,
    use_case: ListScrapingJobsUseCase = Depends(get_list_jobs_use_case)
):
    """List scraping jobs with pagination."""
    try:
        jobs = await use_case.execute(limit, offset, status_filter)
        
        return ScrapingJobListResponse(
            jobs=[_convert_job_to_response(job) for job in jobs],
            total=len(jobs),  # In real app, would get actual total count
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/jobs/{job_id}", response_model=ScrapingJobResponse)
async def get_scraping_job(
    job_id: UUID,
    use_case: GetScrapingJobUseCase = Depends(get_get_job_use_case)
):
    """Get a specific scraping job."""
    try:
        job = await use_case.execute(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return _convert_job_to_response(job)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/jobs/{job_id}/execute", response_model=ScrapingJobResponse)
async def execute_scraping_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    use_case: ExecuteScrapingJobUseCase = Depends(get_execute_job_use_case)
):
    """Execute a scraping job."""
    try:
        # Execute in background
        background_tasks.add_task(_execute_job_background, use_case, job_id)
        
        # Return current job status
        get_use_case = GetScrapingJobUseCase(use_case.job_repository)
        job = await get_use_case.execute(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return _convert_job_to_response(job)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/api/v1/jobs/{job_id}")
async def delete_scraping_job(
    job_id: UUID,
    use_case: DeleteScrapingJobUseCase = Depends(get_delete_job_use_case)
):
    """Delete a scraping job."""
    try:
        success = await use_case.execute(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return {"message": "Job deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/jobs/{job_id}/data", response_model=List[ScrapedDataResponse])
async def get_job_scraped_data(
    job_id: UUID,
    use_case: GetScrapedDataUseCase = Depends(get_get_data_use_case)
):
    """Get scraped data for a specific job."""
    try:
        data_list = await use_case.execute_by_job_id(job_id)
        
        return [_convert_data_to_response(data) for data in data_list]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/data", response_model=List[ScrapedDataResponse])
async def get_scraped_data(
    data_type: Optional[str] = None,
    source_url: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    use_case: GetScrapedDataUseCase = Depends(get_get_data_use_case)
):
    """Get scraped data with filters."""
    try:
        if source_url:
            data_list = await use_case.execute_by_source_url(source_url)
        elif data_type:
            data_list = await use_case.execute_by_data_type(data_type, limit, offset)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either data_type or source_url must be provided"
            )
        
        return [_convert_data_to_response(data) for data in data_list]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/validate-url", response_model=UrlValidationResponse)
async def validate_url(request: UrlValidationRequest):
    """Validate if a URL is accessible for scraping."""
    try:
        async with HttpWebScraperService() as scraper:
            is_valid = await scraper.validate_url(str(request.url))
        
        return UrlValidationResponse(
            url=str(request.url),
            is_valid=is_valid,
            message="URL is accessible" if is_valid else "URL is not accessible"
        )
    
    except Exception as e:
        return UrlValidationResponse(
            url=str(request.url),
            is_valid=False,
            message=f"Error validating URL: {str(e)}"
        )


@app.post("/api/v1/bulk-scrape", response_model=ScrapingJobResponse)
async def bulk_scrape(
    request: BulkScrapingRequest,
    background_tasks: BackgroundTasks
):
    """Perform bulk scraping operation."""
    try:
        # Convert request targets to domain entities
        from .domain.entities.scraping import ScrapingTarget, DataType
        
        targets = []
        for target_req in request.targets:
            target = ScrapingTarget(
                url=str(target_req.url),
                data_type=DataType(target_req.data_type),
                selectors=target_req.selectors,
                headers=target_req.headers,
                cookies=target_req.cookies,
                javascript_required=target_req.javascript_required
            )
            targets.append(target)
        
        # Create and execute bulk scraping job
        # Note: In a real implementation, this would use proper DI
        async with get_db_session() as session:
            job_repo = SQLAlchemyScrapingJobRepository(session)
            web_scraper = HttpWebScraperService()
            
            bulk_use_case = BulkScrapingUseCase(job_repo, web_scraper)
            
            # Execute in background
            background_tasks.add_task(
                _execute_bulk_scraping_background,
                bulk_use_case,
                targets,
                request.job_name
            )
            
            # Return initial job status
            job = await bulk_use_case.execute(targets, request.job_name)
            return _convert_job_to_response(job)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/search-jobs", response_model=List[JobListingResponse])
async def search_jobs(request: SearchJobsRequest):
    """Search for job listings on job boards."""
    try:
        job_scraper = ModernJobListingScraperService()
        
        jobs = await job_scraper.search_jobs(
            base_url=str(request.base_url),
            query=request.query,
            location=request.location
        )
        
        # Limit results
        jobs = jobs[:request.max_results]
        
        return [
            JobListingResponse(
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                salary=job.salary,
                requirements=job.requirements,
                benefits=job.benefits,
                employment_type=job.employment_type,
                experience_level=job.experience_level,
                posted_date=job.posted_date,
                application_url=job.application_url
            )
            for job in jobs
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Helper functions

def _convert_job_to_response(job) -> ScrapingJobResponse:
    """Convert domain job to response model."""
    from .api.models.scraping_models import ScrapingTargetResponse
    
    return ScrapingJobResponse(
        id=job.id,
        name=job.name,
        status=job.status.value,
        targets=[
            ScrapingTargetResponse(
                url=target.url,
                data_type=target.data_type.value,
                selectors=target.selectors,
                headers=target.headers,
                cookies=target.cookies,
                javascript_required=target.javascript_required
            )
            for target in job.targets
        ],
        results=[_convert_data_to_response(data) for data in job.results],
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        config=job.config,
        duration=job.duration,
        success_rate=job.success_rate
    )


def _convert_data_to_response(data) -> ScrapedDataResponse:
    """Convert domain data to response model."""
    return ScrapedDataResponse(
        source_url=data.source_url,
        data_type=data.data_type.value,
        content=data.content,
        metadata=data.metadata,
        scraped_at=data.scraped_at
    )


async def _execute_job_background(use_case, job_id):
    """Execute job in background."""
    try:
        await use_case.execute(job_id)
    except Exception as e:
        print(f"Background job execution failed: {e}")


async def _execute_bulk_scraping_background(use_case, targets, job_name):
    """Execute bulk scraping in background."""
    try:
        await use_case.execute(targets, job_name)
    except Exception as e:
        print(f"Background bulk scraping failed: {e}")


# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An internal server error occurred"
        ).dict()
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 