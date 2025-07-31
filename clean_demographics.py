#!/usr/bin/env python3
"""
clean_demographics.py

Script to clean and transform the raw demographics CSV for Memgraph ingestion.
Usage: python clean_demographics.py --input demographics.csv --output clean_demographics.csv
"""

import pandas as pd
import argparse
from datetime import datetime


def compute_age(dob, reference_date=None):
    """Compute age in years given a date of birth."""
    if reference_date is None:
        reference_date = datetime.today()
    return (reference_date - dob).days // 365


def main():
    parser = argparse.ArgumentParser(
        description="Clean demographics CSV for Memgraph ingestion"
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to the raw demographics CSV"
    )
    parser.add_argument(
        "--output", "-o", default="clean_demographics.csv",
        help="Path to save the cleaned CSV"
    )
    args = parser.parse_args()

    # 1) Load raw CSV
    df = pd.read_csv(args.input)

    # 2) Standardize column names
    df.rename(columns=lambda c: c.strip(), inplace=True)

    # 3) Clean MRN column
    #    Strip whitespace and remove any "-DEMO" suffix
    df["mrn"] = (
        df["Mrn"].astype(str)
        .str.strip()
        .str.replace(r"-DEMO$", "", regex=True)
    )

    # 4) Compute age from Date Of Birth
    df["dob"] = pd.to_datetime(df.get("Date Of Birth", df.get("DOB")), errors="coerce")
    df["age"] = df["dob"].apply(lambda x: compute_age(x) if pd.notnull(x) else None)

    # 5) Normalize sex values
    df["sex"] = (
        df["Sex"].astype(str)
        .str.strip()
        .str.lower()
    )

    # 6) Select only the needed columns and drop rows missing MRN or sex
    clean_df = df[["mrn", "age", "sex"]].dropna(subset=["mrn", "sex"])

    # 7) Write out cleaned CSV
    clean_df.to_csv(args.output, index=False)
    print(f"✅ Wrote {len(clean_df)} rows to {args.output}")


if __name__ == "__main__":
    main()
