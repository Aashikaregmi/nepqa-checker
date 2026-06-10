"""
Run extraction on one PDF and save the record to output/.

Usage:
    python3 run_extract.py sources/188_1115.pdf
"""
import json
import os
import sys

from src.extract import extract


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 run_extract.py <path-to-pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    record = extract(pdf_path)

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = f"output/{base}_record.json"
    with open(out_path, "w") as f:
        json.dump(record.model_dump(), f, indent=2)

    print(f"Saved to {out_path}")
    print(record)


if __name__ == "__main__":
    main()
