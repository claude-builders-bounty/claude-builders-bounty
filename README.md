# json_to_csv

Convert a JSON array of flat objects into a CSV file. Python 3.10+, standard library only.

## Usage

```bash
python json_to_csv.py input.json output.csv
```

`input.json` must contain an array of objects, e.g.:

```json
[
  {"name": "Ada", "age": 36},
  {"name": "Linus"}
]
```

Produces `output.csv`:

```csv
name,age
Ada,36
Linus,
```

## Behavior

- **Header** = union of all keys across every object, in first-seen order (stable output).
- **Missing keys** are filled with an empty string.
- **`null`** becomes an empty string; booleans render as `true`/`false`.
- Quotes, commas, and newlines inside values are escaped per RFC 4180 (via Python's `csv` module).

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Usage error (wrong number of arguments) |
| 2 | Input not found / invalid JSON / not an array of objects |

## Tests

```bash
pip install pytest
pytest -q
```

Covers: header union ordering, missing-key fill, `null`/bool normalization,
special-character round-trip, non-array rejection, and a full CLI end-to-end run.
