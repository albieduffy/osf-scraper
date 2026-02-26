import json
from pathlib import Path
import argparse
import pandas as pd


def process_registrations(input_file: Path, output_file: Path):
    """Convert JSONL to flattened DataFrame and save as JSONL."""
    with open(input_file, "r") as f:
        data = [json.loads(line) for line in f if line.strip()]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df = pd.json_normalize(data)
    df.to_json(output_file, orient="records", lines=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flatten JSONL registrations into a DataFrame")
    parser.add_argument("--input", type=Path, default=Path("data/raw/preregistrations.jsonl"),
                        help="Input JSONL file (default: data/raw/preregistrations.jsonl)")
    parser.add_argument("--output", type=Path, default=Path("data/processed/preregistrations.jsonl"),
                        help="Output JSONL file (default: data/processed/preregistrations.jsonl)")
    args = parser.parse_args()
    process_registrations(args.input, args.output)
