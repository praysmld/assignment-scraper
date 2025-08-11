"""Domain services for web scraping operations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from ..entities.scraping import (
    ScrapingTarget, 
    ScrapedData, 
    JobListing, 
    MemberClub, 
    SupportResource
)


class WebScraperService(ABC):
    """Abstract service for web scraping operations."""
    
    @abstractmethod
    async def scrape_url(
        self, 
        target: ScrapingTarget
    ) -> Optional[ScrapedData]:
        """Scrape data from a single URL."""
        pass
    
    @abstractmethod
    async def scrape_multiple_urls(
        self, 
        targets: List[ScrapingTarget]
    ) -> List[ScrapedData]:
        """Scrape data from multiple URLs."""
        pass
    
    @abstractmethod
    async def validate_url(self, url: str) -> bool:
        """Validate if a URL is accessible and scrapable."""
        pass


class JobListingScraperService(ABC):
    """Abstract service for job listing scraping."""
    
    @abstractmethod
    async def scrape_job_listings(
        self, 
        url: str, 
        selectors: Dict[str, str]
    ) -> List[JobListing]:
        """Scrape job listings from a URL."""
        pass
    
    @abstractmethod
    async def extract_job_details(
        self, 
        job_url: str
    ) -> Optional[JobListing]:
        """Extract detailed job information from a job posting URL."""
        pass
    
    @abstractmethod
    async def search_jobs(
        self, 
        base_url: str, 
        query: str, 
        location: str = ""
    ) -> List[JobListing]:
        """Search for jobs with specific criteria."""
        pass


class MemberClubScraperService(ABC):
    """Abstract service for member club scraping."""
    
    @abstractmethod
    async def scrape_member_clubs(
        self, 
        url: str, 
        selectors: Dict[str, str]
    ) -> List[MemberClub]:
        """Scrape member club information from a URL."""
        pass
    
    @abstractmethod
    async def extract_club_details(
        self, 
        club_url: str
    ) -> Optional[MemberClub]:
        """Extract detailed club information from a club page URL."""
        pass


class SupportResourceScraperService(ABC):
    """Abstract service for support resource scraping."""
    
    @abstractmethod
    async def scrape_support_resources(
        self, 
        url: str, 
        selectors: Dict[str, str]
    ) -> List[SupportResource]:
        """Scrape support resources from a URL."""
        pass
    
    @abstractmethod
    async def extract_resource_details(
        self, 
        resource_url: str
    ) -> Optional[SupportResource]:
        """Extract detailed resource information from a resource page URL."""
        pass
    
    @abstractmethod
    async def download_resource(
        self, 
        download_url: str, 
        destination: str
    ) -> bool:
        """Download a support resource file."""
        pass


class DataParsingService(ABC):
    """Abstract service for parsing scraped data."""
    
    @abstractmethod
    async def parse_html(
        self, 
        html_content: str, 
        selectors: Dict[str, str]
    ) -> Dict[str, Any]:
        """Parse HTML content using CSS selectors."""
        pass
    
    @abstractmethod
    async def extract_text(
        self, 
        html_content: str, 
        selector: str
    ) -> Optional[str]:
        """Extract text from HTML using a CSS selector."""
        pass
    
    @abstractmethod
    async def extract_links(
        self, 
        html_content: str, 
        base_url: str
    ) -> List[str]:
        """Extract all links from HTML content."""
        pass
    
    @abstractmethod
    async def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        pass


class BrowserService(ABC):
    """Abstract service for browser automation."""
    
    @abstractmethod
    async def create_browser_session(self) -> Any:
        """Create a new browser session."""
        pass
    
    @abstractmethod
    async def navigate_to_url(
        self, 
        session: Any, 
        url: str
    ) -> str:
        """Navigate to a URL and return page content."""
        pass
    
    @abstractmethod
    async def click_element(
        self, 
        session: Any, 
        selector: str
    ) -> bool:
        """Click an element on the page."""
        pass
    
    @abstractmethod
    async def fill_form(
        self, 
        session: Any, 
        form_data: Dict[str, str]
    ) -> bool:
        """Fill out a form on the page."""
        pass
    
    @abstractmethod
    async def wait_for_element(
        self, 
        session: Any, 
        selector: str, 
        timeout: int = 10
    ) -> bool:
        """Wait for an element to appear on the page."""
        pass
    
    @abstractmethod
    async def take_screenshot(
        self, 
        session: Any, 
        filename: str
    ) -> bool:
        """Take a screenshot of the current page."""
        pass
    
    @abstractmethod
    async def close_browser_session(self, session: Any) -> None:
        """Close the browser session."""
        pass


class CacheService(ABC):
    """Abstract service for caching scraped data."""
    
    @abstractmethod
    async def cache_data(
        self, 
        key: str, 
        data: Any, 
        ttl: int = 3600
    ) -> bool:
        """Cache data with a time-to-live."""
        pass
    
    @abstractmethod
    async def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data by key."""
        pass
    
    @abstractmethod
    async def invalidate_cache(self, key: str) -> bool:
        """Invalidate cached data."""
        pass
    
    @abstractmethod
    async def clear_cache(self, pattern: str = "*") -> int:
        """Clear cache entries matching a pattern."""
        pass


class RateLimitService(ABC):
    """Abstract service for rate limiting requests."""
    
    @abstractmethod
    async def is_request_allowed(
        self, 
        identifier: str, 
        requests_per_minute: int = 60
    ) -> bool:
        """Check if a request is allowed based on rate limits."""
        pass
    
    @abstractmethod
    async def record_request(self, identifier: str) -> None:
        """Record a request for rate limiting purposes."""
        pass
    
    @abstractmethod
    async def get_request_count(
        self, 
        identifier: str, 
        window_minutes: int = 1
    ) -> int:
        """Get the number of requests in the time window."""
        pass 