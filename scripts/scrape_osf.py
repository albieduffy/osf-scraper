#!/usr/bin/env python3
"""Async OSF scraper for processing large batches of IDs in batches."""

import argparse
import asyncio
import aiohttp
import aiofiles
import json
import os
import random
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_URL = "https://api.osf.io/v2/"
ENDPOINT_TEMPLATE = "registrations/{}/"
INITIAL_MAX_CONCURRENT_REQUESTS = 10
MIN_CONCURRENT_REQUESTS = 5
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1.0
REQUEST_DELAY = 0.1
BATCH_SIZE = 100
TIMEOUT_SECONDS = 30
RATE_LIMIT_WINDOW = 100
RATE_LIMIT_THRESHOLD = 0.3


async def fetch_with_retry(
    session: aiohttp.ClientSession,
    osf_id: str,
    semaphore: asyncio.Semaphore,
    rate_limit_tracker: list[bool],
) -> tuple[str, dict | None, bool]:
    """Fetch a single OSF registration with retry logic.
    
    Returns: (osf_id, response_data, was_rate_limited)
    """
    url = BASE_URL + ENDPOINT_TEMPLATE.format(osf_id)
    was_rate_limited = False
    
    async with semaphore:
        await asyncio.sleep(REQUEST_DELAY)
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)) as response:
                    status_code = response.status
                    
                    if status_code == 200:
                        data = await response.json()
                        return (osf_id, data.get("data"), was_rate_limited)
                    
                    elif status_code == 429:  # Rate limited
                        was_rate_limited = True
                        retry_after_str = response.headers.get("Retry-After", "")
                        if retry_after_str:
                            try:
                                retry_after = float(retry_after_str)
                            except ValueError:
                                retry_after = INITIAL_RETRY_DELAY * (2 ** attempt)
                        else:
                            retry_after = INITIAL_RETRY_DELAY * (2 ** attempt)
                        
                        base_delay = max(retry_after, INITIAL_RETRY_DELAY * (2 ** attempt))
                        jitter = random.uniform(0, base_delay * 0.1)
                        retry_after = base_delay + jitter
                        
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            return (osf_id, None, was_rate_limited)
                    
                    else:
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(INITIAL_RETRY_DELAY * (2 ** attempt))
                            continue
                        else:
                            return (osf_id, None, was_rate_limited)
                            
            except (asyncio.TimeoutError, aiohttp.ClientError):
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(INITIAL_RETRY_DELAY * (2 ** attempt))
                    continue
                else:
                    return (osf_id, None, was_rate_limited)
            except Exception:
                return (osf_id, None, was_rate_limited)
    
    return (osf_id, None, was_rate_limited)


async def process_batch(
    session: aiohttp.ClientSession,
    batch_ids: list[str],
    batch_num: int,
    output_file: Path,
    successful_ids_file: Path,
    current_max_concurrent: list[int],
    rate_limit_tracker: list[bool],
) -> dict:
    """Process a batch of IDs and return batch statistics."""
    semaphore = asyncio.Semaphore(current_max_concurrent[0])
    write_lock = asyncio.Lock()
    batch_results = {
        'batch_num': batch_num,
        'total': len(batch_ids),
        'successful': 0,
        'failed': 0,
        'successful_ids': [],
    }
    
    async def process_id(osf_id: str) -> None:
        osf_id = osf_id.strip()
        if not osf_id:
            return
        
        _, response_data, was_rate_limited = await fetch_with_retry(session, osf_id, semaphore, rate_limit_tracker)
        
        # Track rate limit events for adaptive concurrency
        rate_limit_tracker.append(was_rate_limited)
        if len(rate_limit_tracker) > RATE_LIMIT_WINDOW:
            rate_limit_tracker.pop(0)
        
        if response_data is not None:
            async with write_lock:
                async with aiofiles.open(output_file, "a", encoding="utf-8") as f:
                    # Write as JSONL (one JSON object per line)
                    await f.write(json.dumps(response_data, ensure_ascii=False) + "\n")
                    await f.flush()
            
            batch_results['successful'] += 1
            batch_results['successful_ids'].append(osf_id)
        else:
            batch_results['failed'] += 1
    
    # Process all IDs in the batch concurrently
    tasks = [process_id(osf_id) for osf_id in batch_ids]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Write successful IDs to the successful IDs file
    if batch_results['successful_ids']:
        async with aiofiles.open(successful_ids_file, "a", encoding="utf-8") as f:
            for osf_id in batch_results['successful_ids']:
                await f.write(f"{osf_id}\n")
            await f.flush()
    
    return batch_results


async def process_ids_in_batches(ids_file: Path, output_file: Path, successful_ids_file: Path) -> None:
    """Process IDs in batches with batch-level tracking."""
    current_max_concurrent = [INITIAL_MAX_CONCURRENT_REQUESTS]
    rate_limit_tracker = []
    batch_stats = []
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    successful_ids_file.parent.mkdir(parents=True, exist_ok=True)
    
    if output_file.exists():
        output_file.unlink()
    if successful_ids_file.exists():
        successful_ids_file.unlink()
    
    connector = aiohttp.TCPConnector(limit=INITIAL_MAX_CONCURRENT_REQUESTS * 2)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
    
    # Set up API token authentication
    api_token = os.getenv("OSF_API_TOKEN")
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
        print("Using OSF API token for authenticated requests")
    else:
        print("Warning: No OSF_API_TOKEN found. Using unauthenticated requests (lower rate limits).")
    
    # Read all IDs first
    with open(ids_file, "r", encoding="utf-8") as f:
        all_ids = [line.strip() for line in f if line.strip()]
    
    total_batches = (len(all_ids) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Total IDs: {len(all_ids)}")
    print(f"Processing in {total_batches} batches of {BATCH_SIZE}")
    print()
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(all_ids))
            batch_ids = all_ids[start_idx:end_idx]
            
            print(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_ids)} IDs)...")
            batch_start_time = time.time()
            
            # Adaptive concurrency: adjust based on recent rate limit events
            if len(rate_limit_tracker) >= 50:
                recent_rate_limit_rate = sum(rate_limit_tracker[-RATE_LIMIT_WINDOW:]) / min(len(rate_limit_tracker), RATE_LIMIT_WINDOW)
                if recent_rate_limit_rate > RATE_LIMIT_THRESHOLD and current_max_concurrent[0] > MIN_CONCURRENT_REQUESTS:
                    current_max_concurrent[0] = max(MIN_CONCURRENT_REQUESTS, int(current_max_concurrent[0] * 0.7))
                    print(f"  Reducing concurrency to {current_max_concurrent[0]} (rate limit rate: {recent_rate_limit_rate:.2%})")
                elif recent_rate_limit_rate < RATE_LIMIT_THRESHOLD * 0.5 and current_max_concurrent[0] < INITIAL_MAX_CONCURRENT_REQUESTS:
                    current_max_concurrent[0] = min(INITIAL_MAX_CONCURRENT_REQUESTS, int(current_max_concurrent[0] * 1.2))
                    print(f"  Increasing concurrency to {current_max_concurrent[0]} (rate limit rate: {recent_rate_limit_rate:.2%})")
            
            # Process the batch
            batch_results = await process_batch(
                session, batch_ids, batch_num + 1, output_file, successful_ids_file,
                current_max_concurrent, rate_limit_tracker
            )
            
            batch_elapsed = time.time() - batch_start_time
            batch_success_rate = (batch_results['successful'] / batch_results['total']) * 100 if batch_results['total'] > 0 else 0
            
            batch_stats.append({
                'batch': batch_num + 1,
                'success_rate': batch_success_rate,
                'successful': batch_results['successful'],
                'failed': batch_results['failed'],
                'time': batch_elapsed,
            })
            
            print(f"  Batch {batch_num + 1} complete: {batch_results['successful']}/{batch_results['total']} successful ({batch_success_rate:.1f}%) in {batch_elapsed:.1f}s")
            print()
    
    # Print summary
    total_successful = sum(s['successful'] for s in batch_stats)
    total_failed = sum(s['failed'] for s in batch_stats)
    total_time = sum(s['time'] for s in batch_stats)
    overall_success_rate = (total_successful / (total_successful + total_failed)) * 100 if (total_successful + total_failed) > 0 else 0
    
    print("=" * 60)
    print("BATCH SUMMARY")
    print("=" * 60)
    print(f"Total batches: {total_batches}")
    print(f"Total successful: {total_successful}")
    print(f"Total failed: {total_failed}")
    print(f"Overall success rate: {overall_success_rate:.1f}%")
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print()
    print("Batch-by-batch breakdown:")
    for stat in batch_stats:
        print(f"  Batch {stat['batch']}: {stat['successful']}/{stat['successful']+stat['failed']} ({stat['success_rate']:.1f}%) - {stat['time']:.1f}s")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape OSF registrations from a list of IDs in batches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/scrape_osf.py --file data/osf_ids_remaining.txt
  python scripts/scrape_osf.py --file data/osf_ids.txt --output data/raw/preregistrations.jsonl
        """,
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/osf_ids_remaining.txt"),
        help="Input file with OSF IDs (one per line) (default: data/osf_ids.txt)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/preregistrations.jsonl"),
        help="Output JSONL file (default: data/raw/preregistrations.jsonl)",
    )
    parser.add_argument(
        "--successful-ids",
        type=Path,
        default=Path("data/raw/successful_ids.txt"),
        help="Output file for successfully processed IDs (default: data/raw/successful_ids.txt)",
    )

    args = parser.parse_args()
    
    if not args.file.exists():
        print(f"Error: {args.file} not found")
        return
    
    print("Starting scraper...")
    print(f"IDs file: {args.file}")
    print(f"Output file: {args.output}")
    print(f"Successful IDs file: {args.successful_ids}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Initial max concurrent requests: {INITIAL_MAX_CONCURRENT_REQUESTS}")
    print(f"Min concurrent requests: {MIN_CONCURRENT_REQUESTS}")
    print(f"Max retries: {MAX_RETRIES}")
    print(f"Adaptive rate limiting: enabled")
    print()
    
    start_time = time.time()
    asyncio.run(process_ids_in_batches(args.file, args.output, args.successful_ids))
    elapsed = time.time() - start_time
    
    print(f"\nTotal elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")


if __name__ == "__main__":
    main()