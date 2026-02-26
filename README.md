# Preregistration Quality LLM Evaluation

A Python repository for evaluating preregistration quality using LLM scoring and human scoring. This project is being developed in phases.

## Setup

1. **Install the package and dependencies:**
   ```bash
   pip install -e .
   ```

2. **Install development dependencies** (for running tests):
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up OSF API token** (recommended — authenticated requests have higher rate limits):
   ```bash
   cp .env.example .env
   # Edit .env and set OSF_API_TOKEN=your_token_here
   ```
   Get your token at: https://osf.io/settings/tokens

---

## Phase 0: OSF ID Discovery

Phase 0 discovers OSF preregistration IDs from the OSF registrations endpoint.

### Usage

```bash
# Discover all preregistration IDs
python scripts/discover_ids.py

# Limit results
python scripts/discover_ids.py --max-results 1000

# Include all registrations (not just preregistrations)
python scripts/discover_ids.py --no-filter

# Use a specific API token
python scripts/discover_ids.py --token YOUR_TOKEN

# Specify output file
python scripts/discover_ids.py --output data/osf_ids.txt
```

### Output

Discovered IDs are saved to `data/osf_ids.txt` (one per line). Existing IDs are deduplicated on append.

---

## Phase 1: OSF Preregistration Scraper

Phase 1 fetches full preregistration data from the OSF API using the IDs from Phase 0.

### Usage

```bash
# Scrape from a file of IDs
python scripts/scrape_osf.py --file data/osf_ids.txt

# Specify output file
python scripts/scrape_osf.py --file data/osf_ids.txt --output data/raw/preregistrations.jsonl

# Resume a previous run (append to existing output instead of overwriting)
python scripts/scrape_osf.py --file data/osf_ids.txt --resume
```

### Output

Saves each preregistration as a JSONL record (one JSON object per line) to `data/raw/preregistrations.jsonl`. Successfully processed IDs are tracked in `data/raw/successful_ids.txt`.

### Compute remaining IDs (after a partial run)

```bash
python scripts/remaining_ids.py
# or with custom paths:
python scripts/remaining_ids.py --all-ids data/osf_ids.txt --successful-ids data/raw/successful_ids.txt --output data/osf_ids_remaining.txt
```

---

## Processing & Analysis

### Flatten raw JSONL into a normalised DataFrame

```bash
python scripts/process_registrations.py
# or with custom paths:
python scripts/process_registrations.py --input data/raw/preregistrations.jsonl --output data/processed/preregistrations.jsonl
```

### Extract column names from processed data

```bash
python scripts/analyse.py
# or with custom paths:
python scripts/analyse.py --input data/processed/preregistrations.jsonl --output data/analysed/columns.json
```

---

## Typical Workflow

```bash
# 1. Discover IDs
python scripts/discover_ids.py --output data/osf_ids.txt

# 2. Scrape registration data
python scripts/scrape_osf.py --file data/osf_ids.txt

# 3. If interrupted, compute remaining IDs and resume
python scripts/remaining_ids.py
python scripts/scrape_osf.py --file data/osf_ids_remaining.txt --resume

# 4. Flatten to DataFrame
python scripts/process_registrations.py

# 5. Analyse columns
python scripts/analyse.py
```

---

## Running Tests

```bash
pytest
```

---

## Project Structure

```
prereg-quality-llm/
├── src/
│   └── osf/
│       ├── __init__.py
│       └── id_scraper.py         # OSF ID discovery module
├── scripts/
│   ├── discover_ids.py           # Phase 0: discover preregistration IDs
│   ├── scrape_osf.py             # Phase 1: scrape registration data
│   ├── process_registrations.py  # Flatten JSONL to normalised DataFrame
│   ├── analyse.py                # Extract column names from processed data
│   ├── remaining_ids.py          # Compute unprocessed IDs after partial run
│   └── test_rate_limit.py        # Manual rate limit threshold testing
├── tests/
│   ├── test_id_scraper.py
│   ├── test_token_bucket.py
│   └── test_process_registrations.py
├── data/
│   ├── osf_ids.txt               # Discovered IDs (Phase 0 output)
│   ├── osf_ids_remaining.txt     # Remaining IDs after partial scrape
│   ├── raw/                      # Raw scraped JSONL data
│   ├── processed/                # Normalised JSONL data
│   └── analysed/                 # Analysis outputs
├── .env.example                  # Environment variable template
├── pyproject.toml                # Project metadata and dependencies
└── README.md                     # This file
```

---

## Future Phases

- **Phase 2:** Text cleaning and preprocessing
- **Phase 3:** LLM-based quality scoring
- **Phase 4:** Human scoring integration
- **Phase 5:** Statistical analysis and evaluation

## Requirements

- Python 3.8+
- Dependencies managed via `pyproject.toml` — install with `pip install -e .`

## License

[Add your license here]
