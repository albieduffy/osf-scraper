#!/usr/bin/env python3
"""Test script to check OSF API rate limits."""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def find_rate_limit_threshold():
    api_token = os.getenv("OSF_API_TOKEN")
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    
    url = "https://api.osf.io/v2/registrations/49dae/"
    
    for concurrency in [5, 10, 15, 20, 25, 30, 40, 50]:
        print(f"\nTesting with {concurrency} concurrent requests...")
        semaphore = asyncio.Semaphore(concurrency)
        rate_limited_count = 0
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async def make_request(i):
                async with semaphore:
                    async with session.get(url) as response:
                        if response.status == 429:
                            return True
                        return False
            
            tasks = [make_request(i) for i in range(100)]
            results = await asyncio.gather(*tasks)
        rate_limited_count = sum(results)
        
        rate_limit_rate = rate_limited_count / 100
        print(f"  Rate limited: {rate_limited_count}/100 ({rate_limit_rate:.1%})")
        
        if rate_limit_rate > 0.1:  # More than 10% rate limited
            print(f"  → Rate limit threshold appears to be around {concurrency-5} concurrent requests")
            break

if __name__ == "__main__":
    asyncio.run(find_rate_limit_threshold())