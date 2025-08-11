#!/usr/bin/env python3
"""
Zendriver Demo - Undetectable Web Scraping

This script demonstrates the advanced, undetectable web scraping capabilities
using Zendriver with the Assignment Scraper solution.
"""

import asyncio
import json
from typing import Dict, Any

from src.infrastructure.services.web_scraper_impl import ZendriverScraperService, HttpWebScraperService
from src.domain.entities.scraping import ScrapingTarget, DataType


async def demo_basic_scraping():
    """Demonstrate basic undetectable scraping with Zendriver."""
    print("🚀 Starting Zendriver Demo - Undetectable Web Scraping")
    print("=" * 60)
    
    # Initialize Zendriver scraper
    async with ZendriverScraperService() as scraper:
        
        # Test 1: Bot Detection Test
        print("\n📊 Test 1: Bot Detection Challenge")
        print("-" * 40)
        
        bot_detection_target = ScrapingTarget(
            url="https://www.browserscan.net/bot-detection",
            data_type=DataType.GENERAL_DATA,
            selectors={
                "detection_result": ".detection-result, .result-text",
                "user_agent": ".user-agent-text",
                "fingerprint": ".fingerprint-summary"
            },
            requires_js=True
        )
        
        try:
            result = await scraper.scrape_url(bot_detection_target)
            print(f"✅ Successfully scraped bot detection site")
            print(f"📄 Detection Result: {result.content.get('detection_result', 'N/A')}")
            print(f"🔍 Method Used: {result.metadata.get('method')}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Job Board Scraping (Indeed)
        print("\n💼 Test 2: Job Board Scraping")
        print("-" * 40)
        
        job_target = ScrapingTarget(
            url="https://www.indeed.com/jobs?q=python+developer&l=San+Francisco",
            data_type=DataType.JOB_LISTING,
            selectors={
                "job_titles": "[data-jk] h2 a span[title]",
                "companies": "[data-testid='company-name']",
                "locations": "[data-testid='job-location']",
                "salaries": "[data-testid='attribute_snippet_testid']"
            },
            requires_js=True
        )
        
        try:
            result = await scraper.scrape_url(job_target)
            print(f"✅ Successfully scraped job listings")
            print(f"📊 Found {len(result.content.get('job_titles', []))} job listings")
            print(f"🏢 Sample companies: {result.content.get('companies', [])[:3]}")
        except Exception as e:
            print(f"❌ Error scraping jobs: {e}")
        
        # Test 3: Dynamic Content (JavaScript-heavy site)
        print("\n⚡ Test 3: JavaScript-Heavy Dynamic Content")
        print("-" * 40)
        
        dynamic_target = ScrapingTarget(
            url="https://httpbin.org/headers",
            data_type=DataType.GENERAL_DATA,
            selectors={
                "headers": "pre, .highlight",
                "user_agent_info": "body"
            },
            requires_js=True
        )
        
        try:
            result = await scraper.scrape_url(dynamic_target)
            print(f"✅ Successfully scraped dynamic content")
            print(f"🌐 Final URL: {result.metadata.get('final_url')}")
            print(f"👤 User Agent: {result.metadata.get('user_agent', '')[:50]}...")
        except Exception as e:
            print(f"❌ Error: {e}")


async def demo_comparison():
    """Compare Zendriver vs HTTP scraping for detection avoidance."""
    print("\n🔍 Comparison: Zendriver vs HTTP Scraping")
    print("=" * 60)
    
    test_url = "https://httpbin.org/user-agent"
    target = ScrapingTarget(
        url=test_url,
        data_type=DataType.GENERAL_DATA,
        selectors={"user_agent": "pre, body"},
        requires_js=False
    )
    
    # Test with HTTP scraper
    print("\n📡 HTTP Scraper Result:")
    print("-" * 30)
    try:
        async with HttpWebScraperService() as http_scraper:
            http_result = await http_scraper.scrape_url(target)
            print(f"Method: {http_result.metadata.get('method', 'http')}")
            print(f"Content: {str(http_result.content)[:100]}...")
    except Exception as e:
        print(f"❌ HTTP Error: {e}")
    
    # Test with Zendriver
    print("\n🚀 Zendriver Result:")
    print("-" * 30)
    try:
        async with ZendriverScraperService() as zen_scraper:
            zen_result = await zen_scraper.scrape_url(target)
            print(f"Method: {zen_result.metadata.get('method', 'zendriver')}")
            print(f"Content: {str(zen_result.content)[:100]}...")
            print(f"User Agent: {zen_result.metadata.get('user_agent', '')[:50]}...")
    except Exception as e:
        print(f"❌ Zendriver Error: {e}")


async def demo_advanced_features():
    """Demonstrate advanced Zendriver features."""
    print("\n🎯 Advanced Features Demo")
    print("=" * 60)
    
    async with ZendriverScraperService() as scraper:
        
        # Test with custom cookies
        print("\n🍪 Test: Custom Cookies & Headers")
        print("-" * 40)
        
        cookie_target = ScrapingTarget(
            url="https://httpbin.org/cookies",
            data_type=DataType.GENERAL_DATA,
            selectors={"cookies": "pre, body"},
            cookies={"test_cookie": "zendriver_demo", "session": "demo123"},
            requires_js=True
        )
        
        try:
            result = await scraper.scrape_url(cookie_target)
            print(f"✅ Cookies test successful")
            print(f"📄 Response: {str(result.content)[:150]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test viewport and browser info
        print("\n🖥️  Test: Browser Fingerprinting")
        print("-" * 40)
        
        fingerprint_target = ScrapingTarget(
            url="https://httpbin.org/headers",
            data_type=DataType.GENERAL_DATA,
            selectors={"headers": "pre, body"},
            requires_js=True
        )
        
        try:
            result = await scraper.scrape_url(fingerprint_target)
            viewport = result.metadata.get('viewport', {})
            print(f"✅ Browser fingerprinting test")
            print(f"🖥️  Viewport: {viewport.get('width', 'N/A')}x{viewport.get('height', 'N/A')}")
            print(f"🌐 User Agent: {result.metadata.get('user_agent', '')[:60]}...")
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all Zendriver demos."""
    print("🎉 Welcome to Assignment Scraper - Zendriver Demo")
    print("This demo showcases undetectable web scraping capabilities")
    print("using Chrome DevTools Protocol via Zendriver.")
    print("\n" + "=" * 80)
    
    try:
        # Run basic scraping demo
        await demo_basic_scraping()
        
        # Run comparison demo
        await demo_comparison()
        
        # Run advanced features demo
        await demo_advanced_features()
        
        print("\n" + "=" * 80)
        print("✅ Demo completed successfully!")
        print("🚀 Zendriver provides undetectable, production-ready web scraping")
        print("📚 Learn more: https://github.com/cdpdriver/zendriver")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main())) 