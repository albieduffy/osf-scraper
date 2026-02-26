#!/usr/bin/env python3
"""CLI script to discover preregistration IDs from OSF API"""

import argparse
from pathlib import Path

from src.osf.id_scraper import OSFIDScraper


def main():
    parser = argparse.ArgumentParser(
        description="Discover preregistration IDs from OSF registrations endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python scripts/discover_ids.py
        python scripts/discover_ids.py --output data/osf_ids.txt
        python scripts/discover_ids.py --max-results 1000
        python scripts/discover_ids.py --no-filter
        python scripts/discover_ids.py --token YOUR_TOKEN
        """,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/osf_ids.txt"),
        help="Output file for OSF IDs (default: data/osf_ids.txt)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum number of IDs to discover (default: all)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        default=False,
        help="Include all registrations, not just preregistrations",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="OSF API token (overrides OSF_API_TOKEN env var)",
    )

    args = parser.parse_args()

    scraper = OSFIDScraper(api_token=args.token)

    print("=" * 60)
    print("OSF Preregistration ID Discovery")
    print("=" * 60)
    print()

    ids = scraper.discover_preregistration_ids(
        max_results=args.max_results,
        filter_category=not args.no_filter,
    )

    scraper.save_ids(ids, args.output)

    print(f"\n{'=' * 60}")
    print("Discovery complete!")
    print(f"Total IDs found: {len(ids)}")
    print(f"Output file: {args.output}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
