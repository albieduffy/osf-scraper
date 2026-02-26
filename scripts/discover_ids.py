#!/usr/bin/env python3
"""CLI script to discover preregistration IDs from OSF API"""

import argparse
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.osf.id_scraper import OSFIDScraper


def main():
    parser = argparse.ArgumentParser(
        description="Discover preregistration IDs from OSF registrations endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python scripts/discover_ids.py
        python scripts/discover_ids.py --output data/osf_ids.txt
        """,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/osf_ids.txt"),
        help="Output file for OSF IDs (default: data/osf_ids.txt)",
    )

    args = parser.parse_args()

    scraper = OSFIDScraper()

    print("=" * 60)
    print("OSF Preregistration ID Discovery")
    print("=" * 60)
    print()

    ids = scraper.discover_preregistration_ids()

    scraper.save_ids(ids, args.output)

    print(f"\n{'=' * 60}")
    print("Discovery complete!")
    print(f"Total IDs found: {len(ids)}")
    print(f"Output file: {args.output}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
