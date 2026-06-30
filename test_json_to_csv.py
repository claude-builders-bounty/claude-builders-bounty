"""Tests for json_to_csv. Run: pytest -q"""
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

from json_to_csv import collect_fieldnames, json_to_csv, normalize


def test_collect_fieldnames_union_first_seen_order():
    records = [{"a": 1, "b": 2}, {"b": 3, "c": 4}, {"a": 5}]
    assert collect_fieldnames(records) == ["a", "b", "c"]


def test_missing_keys_filled_empty():
    records = [{"name": "Ada", "age": 36}, {"name": "Linus"}]
    buf = io.StringIO()
    json_to_csv(records, buf)
    rows = list(csv.DictReader(io.StringIO(buf.getvalue())))
    assert rows[0] == {"name": "Ada", "age": "36"}
    assert rows[1] == {"name": "Linus", "age": ""}  # missing -> empty


def test_none_becomes_empty_and_bool_lowercased():
    assert normalize(None) == ""
    assert normalize(True) == "true"
    assert normalize(False) == "false"
    assert normalize(10) == "10"


def test_special_characters_round_trip():
    records = [{"text": 'he said "hi", then left\nnewline'}]
    buf = io.StringIO()
    json_to_csv(records, buf)
    rows = list(csv.DictReader(io.StringIO(buf.getvalue())))
    assert rows[0]["text"] == 'he said "hi", then left\nnewline'


def test_non_list_raises():
    import pytest
    with pytest.raises(ValueError):
        json_to_csv({"not": "a list"}, io.StringIO())


def test_cli_end_to_end(tmp_path: Path):
    data = [{"id": 1, "city": "Madrid"}, {"id": 2}]
    inp = tmp_path / "in.json"
    out = tmp_path / "out.csv"
    inp.write_text(json.dumps(data), encoding="utf-8")
    script = Path(__file__).parent / "json_to_csv.py"
    r = subprocess.run([sys.executable, str(script), str(inp), str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader(out.read_text(encoding="utf-8").splitlines()))
    assert rows == [{"id": "1", "city": "Madrid"}, {"id": "2", "city": ""}]
