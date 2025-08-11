"""
Implementation of web scraping services using various libraries.
"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from playwright.async_api import async_playwright, Browser, Page
from tenacity import retry, stop_after_attempt, wait_exponential
import zendriver as zd

from src.config.settings import get_settings
from src.domain.entities.scraping import ScrapedData, ScrapingTarget, DataType, JobListing
from src.domain.services.scraper_service import WebScraperService, JobListingScraperService

settings = get_settings()


class HttpWebScraperService(WebScraperService):
    """HTTP-based web scraper using httpx and BeautifulSoup."""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.user_agent = UserAgent()
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.scraping_timeout),
                follow_redirects=True,
                headers={
                    'User-Agent': self.user_agent.random,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
            )
        return self.client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def scrape_url(self, target: ScrapingTarget) -> ScrapedData:
        """Scrape a single URL using HTTP requests."""
        try:
            client = await self._get_client()
            
            headers = {}
            if target.headers:
                headers.update(target.headers)
            if target.user_agent:
                headers['User-Agent'] = target.user_agent
            
            response = await client.get(
                target.url,
                headers=headers,
                cookies=target.cookies or {}
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            extracted_data = {}
            
            # Extract data using selectors
            if target.selectors:
                for key, selector in target.selectors.items():
                    elements = soup.select(selector)
                    if elements:
                        if len(elements) == 1:
                            extracted_data[key] = self._clean_text(elements[0].get_text())
                        else:
                            extracted_data[key] = [
                                self._clean_text(elem.get_text()) for elem in elements
                            ]
            
            # If no selectors provided, extract basic page info
            if not extracted_data:
                title = soup.find('title')
                extracted_data = {
                    'title': self._clean_text(title.get_text()) if title else '',
                    'content': self._clean_text(soup.get_text())[:1000],  # First 1000 chars
                }
            
            metadata = {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'scraped_at': response.headers.get('date', ''),
                'method': 'http'
            }
            
            return ScrapedData(
                source_url=target.url,
                data_type=target.data_type,
                content=extracted_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error scraping {target.url}: {e}")
            raise
    
    async def scrape_multiple_urls(self, targets: List[ScrapingTarget]) -> List[ScrapedData]:
        """Scrape multiple URLs concurrently."""
        semaphore = asyncio.Semaphore(settings.scraping_max_concurrent)
        
        async def scrape_with_semaphore(target: ScrapingTarget) -> ScrapedData:
            async with semaphore:
                await asyncio.sleep(settings.scraping_delay)  # Rate limiting
                return await self.scrape_url(target)
        
        tasks = [scrape_with_semaphore(target) for target in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scraped_data = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in batch scraping: {result}")
            else:
                scraped_data.append(result)
        
        return scraped_data
    
    async def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible."""
        try:
            client = await self._get_client()
            response = await client.head(url, timeout=10.0)
            return response.status_code < 400
        except Exception:
            return False
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = re.sub(r'[^\w\s\-.,!?():]', '', text)
        
        return text
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()


class ZendriverScraperService(WebScraperService):
    """Undetectable web scraper using Zendriver (Chrome DevTools Protocol)."""
    
    def __init__(self):
        self.browser: Optional[zd.Browser] = None
    
    async def _get_browser(self) -> zd.Browser:
        """Get or create browser instance."""
        if self.browser is None:
            self.browser = await zd.start(
                headless=settings.browser_headless,
                user_data_dir=None,  # Use fresh profile
                browser_args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                ]
            )
        return self.browser
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def scrape_url(self, target: ScrapingTarget) -> ScrapedData:
        """Scrape a single URL using Zendriver."""
        try:
            browser = await self._get_browser()
            page = await browser.get(target.url)
            
            # Set cookies if provided
            if target.cookies:
                for name, value in target.cookies.items():
                    await page.set_cookie(name=name, value=value)
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Handle JavaScript-heavy pages
            if target.requires_js:
                await asyncio.sleep(5)  # Additional wait for JS
            
            extracted_data = {}
            
            # Extract data using selectors
            if target.selectors:
                for key, selector in target.selectors.items():
                    try:
                        elements = await page.find_all(selector, timeout=5)
                        if elements:
                            if len(elements) == 1:
                                text = await elements[0].text
                                extracted_data[key] = self._clean_text(text)
                            else:
                                texts = []
                                for elem in elements:
                                    text = await elem.text
                                    texts.append(self._clean_text(text))
                                extracted_data[key] = texts
                    except Exception as e:
                        logger.debug(f"Could not find selector {selector}: {e}")
            
            # If no selectors provided, extract basic page info
            if not extracted_data:
                title_elem = await page.find('title', timeout=5)
                title = await title_elem.text if title_elem else ''
                
                body_elem = await page.find('body', timeout=5)
                content = await body_elem.text if body_elem else ''
                
                extracted_data = {
                    'title': self._clean_text(title),
                    'content': self._clean_text(content)[:1000],  # First 1000 chars
                }
            
            # Get page metadata
            current_url = await page.url
            
            metadata = {
                'final_url': current_url,
                'method': 'zendriver',
                'user_agent': await page.evaluate('navigator.userAgent'),
                'viewport': await page.evaluate('({width: window.innerWidth, height: window.innerHeight})'),
            }
            
            return ScrapedData(
                source_url=target.url,
                data_type=target.data_type,
                content=extracted_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error scraping {target.url} with Zendriver: {e}")
            raise
    
    async def scrape_multiple_urls(self, targets: List[ScrapingTarget]) -> List[ScrapedData]:
        """Scrape multiple URLs using the same browser instance."""
        results = []
        
        for target in targets:
            try:
                await asyncio.sleep(settings.scraping_delay)  # Rate limiting
                result = await self.scrape_url(target)
                results.append(result)
            except Exception as e:
                logger.error(f"Error scraping {target.url}: {e}")
        
        return results
    
    async def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible using Zendriver."""
        try:
            browser = await self._get_browser()
            page = await browser.get(url)
            await asyncio.sleep(1)
            current_url = await page.url
            return bool(current_url)
        except Exception:
            return False
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters (but keep more than HTTP scraper)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    async def close(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.stop()
            self.browser = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class ModernJobListingScraperService(JobListingScraperService):
    """Modern job listing scraper using Zendriver for undetectable scraping."""
    
    def __init__(self):
        self.scraper = ZendriverScraperService()
    
    async def scrape_job_listings(self, url: str, selectors: Dict[str, str]) -> List[JobListing]:
        """Scrape job listings from a job board."""
        try:
            target = ScrapingTarget(
                url=url,
                data_type=DataType.JOB_LISTING,
                selectors=selectors,
                requires_js=True  # Most job boards use JavaScript
            )
            
            scraped_data = await self.scraper.scrape_url(target)
            
            # Parse the scraped content into JobListing objects
            job_listings = []
            content = scraped_data.content
            
            # Handle different data structures
            if isinstance(content.get('titles'), list):
                # Multiple job listings found
                titles = content.get('titles', [])
                companies = content.get('companies', [])
                locations = content.get('locations', [])
                descriptions = content.get('descriptions', [])
                
                for i in range(len(titles)):
                    job_listing = JobListing(
                        title=titles[i] if i < len(titles) else '',
                        company=companies[i] if i < len(companies) else '',
                        location=locations[i] if i < len(locations) else '',
                        description=descriptions[i] if i < len(descriptions) else '',
                        source_url=url
                    )
                    job_listings.append(job_listing)
            else:
                # Single job listing or different structure
                job_listing = JobListing(
                    title=content.get('title', ''),
                    company=content.get('company', ''),
                    location=content.get('location', ''),
                    description=content.get('description', ''),
                    source_url=url
                )
                job_listings.append(job_listing)
            
            return job_listings
            
        except Exception as e:
            logger.error(f"Error scraping job listings from {url}: {e}")
            return []
    
    async def extract_job_details(self, job_url: str) -> Optional[JobListing]:
        """Extract detailed information from a job posting URL."""
        try:
            # Common selectors for job details
            selectors = {
                'title': 'h1, .job-title, [data-testid="job-title"]',
                'company': '.company-name, .employer-name, [data-testid="company-name"]',
                'location': '.job-location, .location, [data-testid="job-location"]',
                'description': '.job-description, .description, [data-testid="job-description"]',
                'salary': '.salary, .compensation, [data-testid="salary"]',
                'requirements': '.requirements, .qualifications, [data-testid="requirements"]'
            }
            
            target = ScrapingTarget(
                url=job_url,
                data_type=DataType.JOB_LISTING,
                selectors=selectors,
                requires_js=True
            )
            
            scraped_data = await self.scraper.scrape_url(target)
            content = scraped_data.content
            
            return JobListing(
                title=content.get('title', ''),
                company=content.get('company', ''),
                location=content.get('location', ''),
                description=content.get('description', ''),
                salary=content.get('salary', ''),
                requirements=content.get('requirements', ''),
                source_url=job_url
            )
            
        except Exception as e:
            logger.error(f"Error extracting job details from {job_url}: {e}")
            return None
    
    async def search_jobs(self, query: str, location: str = "", max_results: int = 50) -> List[JobListing]:
        """Search for jobs using common job board patterns."""
        job_listings = []
        
        # Common job board URLs and search patterns
        job_boards = [
            {
                'name': 'Indeed',
                'search_url': f'https://www.indeed.com/jobs?q={query}&l={location}',
                'selectors': {
                    'titles': '[data-jk] h2 a span',
                    'companies': '[data-testid="company-name"]',
                    'locations': '[data-testid="job-location"]',
                    'descriptions': '.slider_container .slider_item'
                }
            },
            {
                'name': 'LinkedIn',
                'search_url': f'https://www.linkedin.com/jobs/search/?keywords={query}&location={location}',
                'selectors': {
                    'titles': '.job-search-card__title',
                    'companies': '.job-search-card__subtitle-primary-grouping',
                    'locations': '.job-search-card__subtitle-secondary-grouping',
                    'descriptions': '.job-search-card__list-item'
                }
            }
        ]
        
        for board in job_boards:
            try:
                listings = await self.scrape_job_listings(
                    board['search_url'], 
                    board['selectors']
                )
                job_listings.extend(listings[:max_results//len(job_boards)])
                
                if len(job_listings) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error searching {board['name']}: {e}")
        
        return job_listings[:max_results]
    
    async def close(self):
        """Close the underlying scraper."""
        await self.scraper.close() 