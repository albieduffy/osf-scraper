#!/usr/bin/env python3
"""Script to find remaining IDs from OSF IDs"""

import argparse
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description="Compute remaining unprocessed OSF IDs")
    parser.add_argument("--all-ids", type=Path, default=Path("data/osf_ids.txt"),
                        help="File with all OSF IDs (default: data/osf_ids_remaining.txt)")
    parser.add_argument("--successful-ids", type=Path, default=Path("data/raw/successful_ids-total.txt"),
                        help="File with successfully processed IDs (default: data/raw/successful_ids-total.txt)")
    parser.add_argument("--output", type=Path, default=Path("data/osf_ids_remaining.txt"),
                        help="Output file for remaining IDs (default: data/osf_ids_remaining.txt)")
    args = parser.parse_args()

    try:
        with open(args.successful_ids, "r") as f:
            successful_ids = set(sf.strip("\n") for sf in f)
    except FileNotFoundError:
        print(f"Error: {args.successful_ids} not found")
        sys.exit(1)

    try:
        with open(args.all_ids, "r") as f:
            all_ids = set(sf.strip("\n") for sf in f)
    except FileNotFoundError:
        print(f"Error: {args.all_ids} not found")
        sys.exit(1)

    remaining_ids = all_ids - successful_ids

    print(f"Remaining IDs: {len(remaining_ids)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        for id in remaining_ids:
            f.write(id + "\n")

if __name__ == "__main__":
    main()