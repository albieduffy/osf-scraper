import json
from pathlib import Path
import pandas as pd


def analyse_registrations(input_file: Path, output_file: Path):
    """Analyse processed registrations and extract column names."""
    with open(input_file, "r") as f:
        data = [json.loads(line) for line in f]

    df = pd.DataFrame(data)
    
    with open(output_file, "w") as f:
        json.dump(df.columns.tolist(), f, indent=4)

    print(f"Analysed {len(data)} registrations")
    print(f"Columns: {len(df.columns)}")
    print(f"Saved column names to {output_file}")


if __name__ == "__main__":
    analyse_registrations(
        Path("data/processed/preregistrations.jsonl"),
        Path("data/analysed/columns.json")
    )
