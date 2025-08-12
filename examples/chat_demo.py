#!/usr/bin/env python3
"""
Chat Interface Demo for Assignment Scraper

This script demonstrates how to use the conversational AI interface
to interact with scraped data from the Assignment Scraper.

Requirements:
- Assignment Scraper running on localhost:8000
- Some scraped data in the database

Usage:
    python examples/chat_demo.py
"""

import asyncio
import json
from typing import Dict, Any
import httpx


class ChatDemo:
    """Demo client for the Assignment Scraper chat interface."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id = None
    
    async def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """Send a chat message to the scraper API."""
        url = f"{self.base_url}/api/v1/chat"
        
        payload = {
            "message": message,
            "conversation_id": self.conversation_id,
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                # Store conversation ID for continuity
                self.conversation_id = result.get("conversation_id")
                
                return result
                
            except httpx.RequestError as e:
                return {
                    "response": f"Connection error: {str(e)}",
                    "suggestions": ["Check if the scraper is running on localhost:8000"],
                    "conversation_id": self.conversation_id or "demo",
                    "metadata": {"error": True}
                }
            except httpx.HTTPStatusError as e:
                return {
                    "response": f"API error: {e.response.status_code} - {e.response.text}",
                    "suggestions": ["Check the API documentation"],
                    "conversation_id": self.conversation_id or "demo",
                    "metadata": {"error": True}
                }
    
    async def get_data_summary(self, **kwargs) -> Dict[str, Any]:
        """Get a data summary from the scraper API."""
        url = f"{self.base_url}/api/v1/data-summary"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=kwargs)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def get_suggestions(self) -> Dict[str, Any]:
        """Get chat suggestions from the scraper API."""
        url = f"{self.base_url}/api/v1/chat/suggestions"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"suggestions": [], "error": str(e)}
    
    def print_response(self, result: Dict[str, Any]):
        """Pretty print a chat response."""
        print("\n" + "="*60)
        print("🤖 ASSISTANT:")
        print("-" * 60)
        print(result.get("response", "No response"))
        
        metadata = result.get("metadata", {})
        if metadata:
            print(f"\n📊 Metadata: {metadata}")
        
        suggestions = result.get("suggestions", [])
        if suggestions:
            print("\n💡 Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
        
        data_used = result.get("data_used", [])
        if data_used:
            print(f"\n🔗 Data Used: {len(data_used)} records")
        
        print("="*60)


async def main():
    """Run the chat demo."""
    demo = ChatDemo()
    
    print("🚀 Assignment Scraper Chat Interface Demo")
    print("=" * 60)
    print("This demo shows how to interact with scraped data using natural language.")
    print("Make sure the Assignment Scraper is running on localhost:8000")
    print("=" * 60)
    
    # Get initial suggestions
    print("\n🎯 Getting suggested questions...")
    suggestions = await demo.get_suggestions()
    if "suggestions" in suggestions:
        print("\n💡 Available questions:")
        for i, suggestion in enumerate(suggestions["suggestions"], 1):
            print(f"   {i}. {suggestion}")
    
    # Demo queries
    demo_queries = [
        "Give me a summary of all scraped data",
        "What job listings are available?", 
        "How many positions are there in total?",
        "What are the common job requirements?",
        "Show me recent scraping results",
        "What clubs have been found?",
        "Show me support resources"
    ]
    
    print(f"\n🔍 Running {len(demo_queries)} demo queries...")
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n[{i}/{len(demo_queries)}] 🗣️  USER: {query}")
        
        result = await demo.chat(query)
        demo.print_response(result)
        
        # Small delay between queries
        await asyncio.sleep(1)
    
    # Get data summary
    print("\n📊 Getting comprehensive data summary...")
    summary = await demo.get_data_summary()
    
    if "error" not in summary:
        print("\n📈 DATA SUMMARY:")
        print("-" * 30)
        print(f"Total Records: {summary.get('total_records', 0)}")
        print(f"Time Range: {summary.get('time_range', 'Unknown')}")
        
        data_types = summary.get('data_types', {})
        if data_types:
            print("\nData Types:")
            for dtype, count in data_types.items():
                print(f"  • {dtype.replace('_', ' ').title()}: {count}")
        
        insights = summary.get('key_insights', [])
        if insights:
            print("\nKey Insights:")
            for insight in insights:
                print(f"  • {insight}")
    else:
        print(f"❌ Error getting summary: {summary['error']}")
    
    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("💡 Try running your own queries using:")
    print("   curl -X POST 'http://localhost:8000/api/v1/chat' \\")
    print("     -H 'Content-Type: application/json' \\") 
    print("     -d '{\"message\": \"Your question here\"}'")
    print("="*60)


if __name__ == "__main__":
    print("Starting Assignment Scraper Chat Demo...")
    asyncio.run(main()) 