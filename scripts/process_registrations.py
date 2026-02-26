import json
from pathlib import Path
import pandas as pd


def process_registrations(input_file: Path, output_file: Path):
    """Convert JSON array to flattened DataFrame and save as JSONL."""
    with open(input_file, "r") as f:
        data = json.load(f)

    df = pd.json_normalize(data)
    df.to_json(output_file, orient="records", lines=True)


if __name__ == "__main__":
    process_registrations(
        Path("data/raw/preregistrations.json"),
        Path("data/processed/preregistrations.jsonl")
    )
