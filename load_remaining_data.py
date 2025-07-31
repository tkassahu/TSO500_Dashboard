#!/usr/bin/env python3
"""
Quick script to load all the new data types into Memgraph
Run this after your existing load_to_memgraph.py
"""

import pandas as pd
from neo4j import GraphDatabase
import os

# Connect to Memgraph
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("", ""))

def load_remaining_data():
    """Load protocols, clinical trial subjects, interventions, and adverse events"""
    
    with driver.session() as session:
        
        # ═══════════════════════════════════════════════════════════════
        # 1. Load Protocols
        # ═══════════════════════════════════════════════════════════════
        print("\n🏥 Loading Protocols...")
        protocols_df = pd.read_csv('protocols.csv')
        
        for _, row in protocols_df.iterrows():
            session.run("""
                MERGE (pr:Protocol {protocol_id: $protocol_id})
                SET pr.protocol_name = $protocol_name,
                    pr.phase = $phase,
                    pr.status = $status,
                    pr.target_enrollment = $target_enrollment
            """,
            protocol_id=row['protocol_id'],
            protocol_name=row['protocol_name'],
            phase=row['phase'],
            status=row['status'],
            target_enrollment=int(row['target_enrollment']))
            
        print(f"✅ Loaded {len(protocols_df)} protocols")
        
        # ═══════════════════════════════════════════════════════════════
        # 2. Load Clinical Trial Subjects
        # ═══════════════════════════════════════════════════════════════
        print("\n👥 Loading Clinical Trial Subjects...")
        subjects_df = pd.read_csv('clinical_trial_subjects.csv')
        
        for _, row in subjects_df.iterrows():
            session.run("""
                MATCH (p:Patient {mrn: $mrn})
                MATCH (pr:Protocol {protocol_id: $protocol_id})
                MERGE (cts:ClinicalTrialSubject {rave_id: $rave_id})
                SET cts.enrollment_date = $enrollment_date,
                    cts.enrollment_status = $enrollment_status,
                    cts.mrn = $mrn,
                    cts.protocol_id = $protocol_id
                MERGE (p)-[:ENROLLED_AS]->(cts)
                MERGE (cts)-[:IN_PROTOCOL]->(pr)
            """,
            mrn=int(row['mrn']),
            protocol_id=row['protocol_id'],
            rave_id=row['rave_id'],
            enrollment_date=str(row['enrollment_date']),
            enrollment_status=row['enrollment_status'])
            
        print(f"✅ Loaded {len(subjects_df)} clinical trial subjects")
        
        # ═══════════════════════════════════════════════════════════════
        # 3. Load Interventions
        # ═══════════════════════════════════════════════════════════════
        print("\n💊 Loading Interventions...")
        interventions_df = pd.read_csv('interventions.csv')
        
        # Create unique intervention nodes
        for intervention_cat in interventions_df['intervention_category'].unique():
            session.run("""
                MERGE (i:Intervention {intervention_category: $intervention_category})
            """, intervention_category=intervention_cat)
        
        # Create relationships
        for _, row in interventions_df.iterrows():
            session.run("""
                MATCH (cts:ClinicalTrialSubject {rave_id: $rave_id})
                MATCH (i:Intervention {intervention_category: $intervention_category})
                MERGE (cts)-[r:RECEIVED_INTERVENTION]->(i)
                SET r.dose_level = $dose_level,
                    r.start_date = $start_date,
                    r.duration_days = $duration_days
            """,
            rave_id=row['rave_id'],
            intervention_category=row['intervention_category'],
            dose_level=row['dose_level'],
            start_date=str(row['start_date']),
            duration_days=int(row['duration_days']))
            
        print(f"✅ Loaded {len(interventions_df.intervention_category.unique())} intervention types")
        print(f"✅ Created {len(interventions_df)} intervention relationships")
        
        # ═══════════════════════════════════════════════════════════════
        # 4. Load Adverse Events
        # ═══════════════════════════════════════════════════════════════
        print("\n⚠️  Loading Adverse Events...")
        ae_df = pd.read_csv('adverse_events.csv')
        
        # Create unique AE nodes
        for ae_system in ae_df['ae_body_system'].unique():
            session.run("""
                MERGE (ae:AdverseEvent {ae_body_system: $ae_body_system})
            """, ae_body_system=ae_system)
        
        # Create relationships
        for _, row in ae_df.iterrows():
            session.run("""
                MATCH (cts:ClinicalTrialSubject {rave_id: $rave_id})
                MATCH (ae:AdverseEvent {ae_body_system: $ae_body_system})
                MERGE (cts)-[r:EXPERIENCED_AE]->(ae)
                SET r.grade = $grade,
                    r.serious = $serious,
                    r.onset_date = $onset_date
            """,
            rave_id=row['rave_id'],
            ae_body_system=row['ae_body_system'],
            grade=int(row['grade']),
            serious=bool(row['serious']),
            onset_date=str(row['onset_date']))
            
        print(f"✅ Loaded {len(ae_df.ae_body_system.unique())} adverse event types")
        print(f"✅ Created {len(ae_df)} adverse event relationships")
        
        # ═══════════════════════════════════════════════════════════════
        # 5. Verify Complete Graph
        # ═══════════════════════════════════════════════════════════════
        print("\n🔍 Verifying complete graph structure...")
        
        queries = [
            ("Patients", "MATCH (n:Patient) RETURN count(n) as count"),
            ("Variants", "MATCH (n:Variant) RETURN count(n) as count"),
            ("Protocols", "MATCH (n:Protocol) RETURN count(n) as count"),
            ("Clinical Trial Subjects", "MATCH (n:ClinicalTrialSubject) RETURN count(n) as count"),
            ("Interventions", "MATCH (n:Intervention) RETURN count(n) as count"),
            ("Adverse Events", "MATCH (n:AdverseEvent) RETURN count(n) as count"),
        ]
        
        print("\nNode counts:")
        for label, query in queries:
            result = session.run(query)
            count = result.single()['count']
            print(f"  {label}: {count}")
            
        # Count relationships
        rel_queries = [
            ("HAS_VARIANT", "MATCH ()-[r:HAS_VARIANT]->() RETURN count(r) as count"),
            ("ENROLLED_AS", "MATCH ()-[r:ENROLLED_AS]->() RETURN count(r) as count"),
            ("IN_PROTOCOL", "MATCH ()-[r:IN_PROTOCOL]->() RETURN count(r) as count"),
            ("RECEIVED_INTERVENTION", "MATCH ()-[r:RECEIVED_INTERVENTION]->() RETURN count(r) as count"),
            ("EXPERIENCED_AE", "MATCH ()-[r:EXPERIENCED_AE]->() RETURN count(r) as count"),
        ]
        
        print("\nRelationship counts:")
        for rel_type, query in rel_queries:
            result = session.run(query)
            count = result.single()['count']
            print(f"  {rel_type}: {count}")
            
        # Example multi-hop query
        print("\n🔗 Testing multi-hop query example...")
        result = session.run("""
            MATCH (p:Patient)-[:ENROLLED_AS]->(cts:ClinicalTrialSubject)-[:RECEIVED_INTERVENTION]->(i:Intervention)
            WHERE i.intervention_category = 'Immunotherapy'
            RETURN count(DISTINCT p) as patient_count
        """)
        immunotherapy_patients = result.single()['patient_count']
        print(f"  Patients on Immunotherapy: {immunotherapy_patients}")


def main():
    print("🚀 Loading additional data into Memgraph...")
    print("="*60)
    
    try:
        load_remaining_data()
        print("\n✅ Successfully loaded all additional data!")
        print("="*60)
        print("\n📊 Your Memgraph database now contains the complete graph with:")
        print("  - Patients with demographics")
        print("  - Variants linked to patients") 
        print("  - Clinical trial protocols")
        print("  - Patient enrollments in trials")
        print("  - Interventions received by patients")
        print("  - Adverse events experienced")
        print("\n🎯 Ready to run your updated dashboard!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all CSV files are present")
        print("2. Check that patient MRNs in new files match existing patients")
        print("3. Verify Memgraph is running on bolt://localhost:7687")
        
    finally:
        driver.close()