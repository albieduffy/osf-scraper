import json
from pathlib import Path
import argparse
import pandas as pd


def analyse_registrations(input_file: Path, output_file: Path):
    """Analyse processed registrations and extract column names."""
    with open(input_file, "r") as f:
        data = [json.loads(line) for line in f]

    df = pd.DataFrame(data)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(df.columns.tolist(), f, indent=4)

    print(f"Analysed {len(data)} registrations")
    print(f"Columns: {len(df.columns)}")
    print(f"Saved column names to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract column names from processed registrations")
    parser.add_argument("--input", type=Path, default=Path("data/processed/preregistrations.jsonl"),
                        help="Input JSONL file (default: data/processed/preregistrations.jsonl)")
    parser.add_argument("--output", type=Path, default=Path("data/analysed/columns.json"),
                        help="Output JSON file (default: data/analysed/columns.json)")
    args = parser.parse_args()
    analyse_registrations(args.input, args.output)
