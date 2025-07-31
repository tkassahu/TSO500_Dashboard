#!/usr/bin/env python3
"""
load_to_memgraph.py

Loads cleaned demographics and remapped TSO500 variants into Memgraph using the Neo4j Bolt driver, linking via demographic MRN.
Usage:
  # install driver: python -m pip install neo4j
  python load_to_memgraph.py
"""

import pandas as pd
from neo4j import GraphDatabase


def load_variants_and_link(driver, demo_df):
    """
    Read remapped variants, drop synthetic MRN, create nodes and relationships in Memgraph.
    """
    # 1) Read remapped variant data (contains both 'MRN' and demographic 'mrn')
    variants_df = pd.read_csv("variants_with_50_demo_mrn.csv")

    # 2) Drop the synthetic MRN column; keep only demographic 'mrn'
    variants_df.drop(columns=["MRN"], inplace=True, errors="ignore")

    # 3) Ensure 'mrn' exists
    if "mrn" not in variants_df.columns:
        raise KeyError("Expected column 'mrn' not found in variants CSV")

    # 4) Create a unique variant_id if missing
    if "variant_id" not in variants_df.columns:
        variants_df["variant_id"] = variants_df.apply(
            lambda row: f"{row['mrn']}_{row['gene']}_{row.name}", axis=1
        )

    # 5) Prepare Cypher queries in batches
    patient_queries = [
        ("MERGE (p:Patient {mrn: $mrn}) ON CREATE SET p.age = $age, p.sex = $sex",
         {"mrn": row["mrn"], "age": int(row["age"]), "sex": row["sex"]})
        for _, row in demo_df.iterrows()
    ]

    variant_queries = [
        ("MERGE (v:Variant {id: $vid}) ON CREATE SET v.gene = $gene, v.assessment = $assessment, v.allele_fraction = $af WITH v MATCH (p:Patient {mrn: $mrn}) MERGE (p)-[:HAS_VARIANT]->(v)",
         {"vid": row["variant_id"], "gene": row.get("gene"), "assessment": row.get("assessment"), "af": float(row.get("allelefraction", 0)), "mrn": row["mrn"]})
        for _, row in variants_df.iterrows()
    ]

    # Execute in batches
    with driver.session() as session:
        print(f"Executing {len(patient_queries)} patient MERGE queries...")
        for query, params in patient_queries:
            session.run(query, params)

        print(f"Executing {len(variant_queries)} variant MERGE queries...")
        for query, params in variant_queries:
            session.run(query, params)

        # Verification summary
        result = session.run(
            "MATCH (p:Patient)-[:HAS_VARIANT]->(v) RETURN count(DISTINCT p) AS patients, count(v) AS variants"
        )
        record = result.single()
        print(f"In Memgraph: patients={record['patients']}, variants={record['variants']}")


def main():
    # 1) Ensure neo4j driver is installed:
    #    python -m pip install neo4j

    # 2) Connect to the local Memgraph instance (Bolt protocol)
    uri = "bolt://127.0.0.1:7687"
    driver = GraphDatabase.driver(uri, auth=None)
    print(f"Connected to Memgraph at {uri}")

    # 3) Load cleaned demographics
    demo_df = pd.read_csv("clean_demographics.csv")
    print(f"Loaded {len(demo_df)} demographic rows")

    # 4) Load variants and create graph relationships
    load_variants_and_link(driver, demo_df)

    # 5) Close driver
    driver.close()


if __name__ == "__main__":
    main()