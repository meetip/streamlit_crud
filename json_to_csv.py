import json
import csv
from pathlib import Path

"""Convert data.json (Thai text) to a CSV suitable for importing into Google Sheets.

This script:
- Reads `data.json` (expects a list of dicts).
- Normalizes keys across records (collects all keys in order found).
- Writes `export.csv` encoded as UTF-8 with BOM so Google Sheets preserves Thai characters.

Usage:
    python json_to_csv.py

"""


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_csv(records, out_path: Path):
    # Collect keys in insertion order across records
    keys = []
    for r in records:
        for k in r.keys():
            if k not in keys:
                keys.append(k)

    # Ensure 'Chapter' is first (useful ordering) if present
    if 'Chapter' in keys:
        keys.remove('Chapter')
        keys.insert(0, 'Chapter')

    # Write CSV with UTF-8 BOM for Google Sheets compatibility
    with out_path.open('w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            # Convert None to empty string for CSV
            row = {k: ('' if r.get(k) is None else r.get(k)) for k in keys}
            writer.writerow(row)


def main():
    src = Path('data.json')
    out = Path('export.csv')

    if not src.exists():
        print('data.json not found in current directory.')
        return

    records = load_json(src)

    if not isinstance(records, list):
        print('Expected data.json to contain a JSON array (list of objects).')
        return

    # Optional: normalize Chapter to integer where possible
    for r in records:
        if 'Chapter' in r and r['Chapter'] is not None:
            try:
                r['Chapter'] = int(r['Chapter'])
            except Exception:
                pass

    write_csv(records, out)
    print(f'Wrote {len(records)} rows to {out} (UTF-8 with BOM).')


if __name__ == '__main__':
    main()
