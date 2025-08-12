"""Use cases for scraping operations."""

import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID
from uuid import uuid4

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


class SearchJobListingsUseCase:
    """Use case for searching job listings."""
    
    def __init__(self, data_repository: ScrapedDataRepository):
        self.data_repository = data_repository
    
    async def execute(self, query: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for job listings based on query."""
        # Implementation for searching job listings
        # This would involve querying the scraped data repository
        return []

# Chat Use Cases
class ChatUseCase:
    """Use case for handling chat interactions with scraped data."""
    
    def __init__(
        self,
        data_repository: ScrapedDataRepository,
        job_repository: ScrapingJobRepository,
    ):
        self.data_repository = data_repository
        self.job_repository = job_repository
    
    async def execute(
        self,
        message: str,
        job_id: Optional[UUID] = None,
        data_type: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process chat message and return response."""
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid4())
            
            # Analyze user intent
            intent = await self._analyze_intent(message)
            
            # Get relevant data based on intent and filters
            relevant_data = await self._get_relevant_data(
                intent, job_id, data_type
            )
            
            # Generate response based on intent and data
            response = await self._generate_response(
                intent, message, relevant_data
            )
            
            # Generate suggestions for follow-up questions
            suggestions = self._generate_suggestions(intent, relevant_data)
            
            return {
                "response": response,
                "data_used": [item["id"] for item in relevant_data],
                "suggestions": suggestions,
                "conversation_id": conversation_id,
                "metadata": {
                    "intent": intent,
                    "data_count": len(relevant_data),
                }
            }
        
        except Exception as e:
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "data_used": [],
                "suggestions": [
                    "Can you help me understand the available data?",
                    "What types of information have been scraped?"
                ],
                "conversation_id": conversation_id or str(uuid4()),
                "metadata": {"error": str(e)}
            }
    
    async def _analyze_intent(self, message: str) -> str:
        """Analyze user message to determine intent."""
        message_lower = message.lower()
        
        # Job-related queries
        if any(word in message_lower for word in ["job", "position", "work", "career", "employment"]):
            if any(word in message_lower for word in ["count", "how many", "number"]):
                return "count_jobs"
            elif any(word in message_lower for word in ["requirement", "skill", "qualification"]):
                return "job_requirements"
            elif any(word in message_lower for word in ["salary", "pay", "wage", "compensation"]):
                return "job_salary"
            elif any(word in message_lower for word in ["location", "where", "place"]):
                return "job_location"
            else:
                return "search_jobs"
        
        # Club/organization queries
        elif any(word in message_lower for word in ["club", "organization", "member", "association"]):
            return "search_clubs"
        
        # Support/resource queries
        elif any(word in message_lower for word in ["support", "help", "driver", "download"]):
            return "search_support"
        
        # Summary/overview queries
        elif any(word in message_lower for word in ["summary", "overview", "total", "all"]):
            return "data_summary"
        
        # Latest/recent queries
        elif any(word in message_lower for word in ["latest", "recent", "new", "last"]):
            return "recent_data"
        
        # Default to general search
        else:
            return "general_search"
    
    async def _get_relevant_data(
        self,
        intent: str,
        job_id: Optional[UUID] = None,
        data_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get relevant scraped data based on intent and filters."""
        try:
            # Get data from repository
            all_data = await self.data_repository.get_all()
            
            # Filter by job_id if specified
            if job_id:
                all_data = [d for d in all_data if d.job_id == job_id]
            
            # Filter by data_type if specified
            if data_type:
                all_data = [d for d in all_data if d.data_type == data_type]
            
            # Apply intent-specific filtering
            if intent.startswith("job"):
                all_data = [d for d in all_data if d.data_type == "job_listing"]
            elif intent.startswith("club"):
                all_data = [d for d in all_data if d.data_type == "member_club"]
            elif intent.startswith("support"):
                all_data = [d for d in all_data if d.data_type == "support_resource"]
            
            # Convert to dict format
            return [
                {
                    "id": data.id,
                    "content": data.content,
                    "data_type": data.data_type,
                    "source_url": data.source_url,
                    "scraped_at": data.scraped_at,
                    "metadata": data.extra_metadata
                }
                for data in all_data[:50]  # Limit to 50 results
            ]
        
        except Exception as e:
            print(f"Error getting relevant data: {e}")
            return []
    
    async def _generate_response(
        self,
        intent: str,
        message: str,
        relevant_data: List[Dict[str, Any]]
    ) -> str:
        """Generate response based on intent and data."""
        
        if not relevant_data:
            return "I couldn't find any relevant data for your query. You might want to run some scraping jobs first."
        
        data_count = len(relevant_data)
        
        if intent == "count_jobs":
            return f"I found {data_count} job listings in the scraped data."
        
        elif intent == "search_jobs":
            if data_count == 0:
                return "No job listings found matching your criteria."
            
            sample_jobs = relevant_data[:3]
            response = f"I found {data_count} job listings. Here are the top 3:\n\n"
            
            for i, job in enumerate(sample_jobs, 1):
                content = job["content"]
                title = content.get("title", "Unknown Position")
                company = content.get("company", "Unknown Company")
                location = content.get("location", "Unknown Location")
                response += f"{i}. **{title}** at {company}\n   📍 {location}\n\n"
            
            if data_count > 3:
                response += f"... and {data_count - 3} more positions."
            
            return response
        
        elif intent == "job_requirements":
            skills = set()
            for job in relevant_data:
                job_skills = job["content"].get("requirements", [])
                if isinstance(job_skills, list):
                    skills.update(job_skills)
                elif isinstance(job_skills, str):
                    skills.add(job_skills)
            
            if skills:
                return f"Common job requirements I found:\n• " + "\n• ".join(list(skills)[:10])
            else:
                return "I couldn't extract specific requirements from the job listings."
        
        elif intent == "search_clubs":
            if data_count == 0:
                return "No club information found."
            
            response = f"I found {data_count} clubs/organizations:\n\n"
            for i, club in enumerate(relevant_data[:5], 1):
                content = club["content"]
                name = content.get("name", "Unknown Club")
                location = content.get("location", "Unknown Location")
                response += f"{i}. {name} - {location}\n"
            
            return response
        
        elif intent == "search_support":
            response = f"I found {data_count} support resources:\n\n"
            for i, resource in enumerate(relevant_data[:5], 1):
                content = resource["content"]
                title = content.get("title", "Support Resource")
                category = content.get("category", "General")
                response += f"{i}. {title} ({category})\n"
            
            return response
        
        elif intent == "data_summary":
            job_count = sum(1 for d in relevant_data if d["data_type"] == "job_listing")
            club_count = sum(1 for d in relevant_data if d["data_type"] == "member_club")
            support_count = sum(1 for d in relevant_data if d["data_type"] == "support_resource")
            
            return f"""📊 **Data Summary**
            
**Total Records:** {data_count}
• Job Listings: {job_count}
• Clubs/Organizations: {club_count}  
• Support Resources: {support_count}

Most recent scraping: {max(d['scraped_at'] for d in relevant_data).strftime('%Y-%m-%d %H:%M')}"""
        
        elif intent == "recent_data":
            # Sort by scraped_at descending
            sorted_data = sorted(relevant_data, key=lambda x: x["scraped_at"], reverse=True)
            recent_data = sorted_data[:5]
            
            response = "🕒 **Recent Scraped Data:**\n\n"
            for i, item in enumerate(recent_data, 1):
                content = item["content"]
                title = content.get("title") or content.get("name", "Unknown")
                data_type = item["data_type"].replace("_", " ").title()
                scraped_time = item["scraped_at"].strftime('%H:%M')
                response += f"{i}. {title} ({data_type}) - {scraped_time}\n"
            
            return response
        
        else:
            # General search
            response = f"I found {data_count} items related to your query:\n\n"
            for i, item in enumerate(relevant_data[:3], 1):
                content = item["content"]
                title = content.get("title") or content.get("name", "Item")
                data_type = item["data_type"].replace("_", " ").title()
                response += f"{i}. {title} ({data_type})\n"
            
            return response
    
    def _generate_suggestions(
        self,
        intent: str,
        relevant_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate follow-up suggestions based on intent and data."""
        
        if intent.startswith("job"):
            return [
                "Show me the salary ranges for these positions",
                "What are the common requirements?",
                "Which locations have the most jobs?",
                "Show me the latest job postings"
            ]
        elif intent.startswith("club"):
            return [
                "How many clubs are in each location?",
                "What types of clubs are available?",
                "Show me club contact information"
            ]
        elif intent.startswith("support"):
            return [
                "What categories of support are available?",
                "Show me the most popular downloads",
                "Are there any recent updates?"
            ]
        else:
            return [
                "Give me a summary of all data",
                "What job listings are available?",
                "Show me recent scraping results",
                "What clubs have been found?"
            ]


class DataSummaryUseCase:
    """Use case for generating data summaries."""
    
    def __init__(
        self,
        data_repository: ScrapedDataRepository,
        job_repository: ScrapingJobRepository,
    ):
        self.data_repository = data_repository
        self.job_repository = job_repository
    
    async def execute(
        self,
        data_type: Optional[str] = None,
        job_id: Optional[UUID] = None,
        date_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive data summary."""
        try:
            # Get all data
            all_data = await self.data_repository.get_all()
            
            # Apply filters
            if job_id:
                all_data = [d for d in all_data if d.job_id == job_id]
            if data_type:
                all_data = [d for d in all_data if d.data_type == data_type]
            
            # Calculate date range
            if date_range and all_data:
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                
                if date_range == "last_week":
                    cutoff = now - timedelta(weeks=1)
                elif date_range == "last_month":
                    cutoff = now - timedelta(days=30)
                elif date_range == "last_day":
                    cutoff = now - timedelta(days=1)
                else:
                    cutoff = None
                
                if cutoff:
                    all_data = [d for d in all_data if d.scraped_at >= cutoff]
            
            # Count by data types
            data_types = {}
            for data in all_data:
                data_type_name = data.data_type
                data_types[data_type_name] = data_types.get(data_type_name, 0) + 1
            
            # Get recent jobs
            recent_jobs = await self.job_repository.get_recent(limit=5)
            job_names = [job.name for job in recent_jobs]
            
            # Generate insights
            insights = []
            
            if "job_listing" in data_types:
                insights.append(f"Found {data_types['job_listing']} job opportunities")
            
            if "member_club" in data_types:
                insights.append(f"Discovered {data_types['member_club']} clubs/organizations")
            
            if "support_resource" in data_types:
                insights.append(f"Collected {data_types['support_resource']} support resources")
            
            if all_data:
                latest_scrape = max(d.scraped_at for d in all_data)
                insights.append(f"Most recent data from {latest_scrape.strftime('%Y-%m-%d %H:%M')}")
            
            return {
                "total_records": len(all_data),
                "data_types": data_types,
                "recent_jobs": job_names,
                "key_insights": insights,
                "time_range": date_range or "all_time"
            }
        
        except Exception as e:
            return {
                "total_records": 0,
                "data_types": {},
                "recent_jobs": [],
                "key_insights": [f"Error generating summary: {str(e)}"],
                "time_range": date_range or "all_time"
            } 