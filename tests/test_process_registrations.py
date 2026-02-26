"""Tests for process_registrations."""

import json
import pytest
from pathlib import Path
from scripts.process_registrations import process_registrations


def test_process_registrations_basic(tmp_path):
    """Flattens a JSONL file into a processed JSONL with normalised columns."""
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "output" / "result.jsonl"

    records = [
        {"id": "abc", "attributes": {"title": "Study 1", "year": 2020}},
        {"id": "def", "attributes": {"title": "Study 2", "year": 2021}},
    ]
    input_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    process_registrations(input_file, output_file)

    assert output_file.exists()
    lines = [json.loads(l) for l in output_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    assert lines[0]["id"] == "abc"
    assert lines[0]["attributes.title"] == "Study 1"


def test_process_registrations_creates_output_dir(tmp_path):
    """Output directory is created automatically."""
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "nested" / "deep" / "out.jsonl"
    input_file.write_text(json.dumps({"id": "x"}) + "\n")

    process_registrations(input_file, output_file)

    assert output_file.exists()


def test_process_registrations_empty_input(tmp_path):
    """Empty input produces an empty output file without error."""
    input_file = tmp_path / "empty.jsonl"
    output_file = tmp_path / "out.jsonl"
    input_file.write_text("")

    process_registrations(input_file, output_file)

    assert output_file.exists()
    lines = [l for l in output_file.read_text().splitlines() if l.strip()]
    assert lines == []
