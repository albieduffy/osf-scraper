#!/usr/bin/env python3
"""Script to find remaining IDs from OSF IDs"""

import argparse
from pathlib import Path
import sys

def main():
    with open("data/raw/successful_ids.txt", "r") as f:
        successful_ids = set(sf.strip("\n") for sf in f)
    
    with open("data/osf_ids.txt", "r") as f:
        all_ids = set(sf.strip("\n") for sf in f)
    
    remaining_ids = all_ids - successful_ids
    
    print(f"Remaining IDs: {len(remaining_ids)}")
    
    with open("data/osf_ids_remaining.txt", "w") as f:
        for id in remaining_ids:
            f.write(id + "\n")

if __name__ == "__main__":
    main()