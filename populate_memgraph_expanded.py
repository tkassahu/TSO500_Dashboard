import os
import pandas as pd
from neo4j import GraphDatabase

# Memgraph connection
MG_URL = os.getenv("MEMGRAPH_URL", "bolt://127.0.0.1:7687")
mg_driver = GraphDatabase.driver(MG_URL, auth=None)

def populate_expanded_schema():
    """Populate Memgraph with the expanded clinical trial schema"""
    
    print("Loading all data files...")
    demo_df = pd.read_csv("clean_demographics.csv")
    variants_df = pd.read_csv("variants_with_50_demo_mrn.csv")
    protocols_df = pd.read_csv("protocols.csv")
    subjects_df = pd.read_csv("clinical_trial_subjects.csv")
    interventions_df = pd.read_csv("interventions.csv")
    adverse_events_df = pd.read_csv("adverse_events.csv")
    
    print(f"Loaded:")
    print(f"  - {len(demo_df)} patients")
    print(f"  - {len(variants_df)} variants") 
    print(f"  - {len(protocols_df)} protocols")
    print(f"  - {len(subjects_df)} enrollments")
    print(f"  - {len(interventions_df)} interventions")
    print(f"  - {len(adverse_events_df)} adverse events")
    
    with mg_driver.session() as sess:
        print("\n🔥 Clearing existing data...")
        sess.run("MATCH (n) DETACH DELETE n")
        
        print("📊 Creating Patient nodes...")
        for _, patient in demo_df.iterrows():
            sess.run("""
                CREATE (p:Patient {
                    mrn: $mrn,
                    age: $age,
                    sex: $sex
                })
            """, {
                'mrn': int(patient['mrn']),
                'age': int(patient['age']),
                'sex': str(patient['sex'])
            })
        
        print("🧬 Creating Variant nodes and relationships...")
        for _, variant in variants_df.iterrows():
            sess.run("""
                MATCH (p:Patient {mrn: $mrn})
                CREATE (v:Variant {
                    variant_id: $variant_id,
                    gene: $gene,
                    assessment: $assessment,
                    actionability: $actionability,
                    allelefraction: $allelefraction
                })
                CREATE (p)-[:HAS_VARIANT]->(v)
            """, {
                'mrn': int(variant['mrn']),
                'variant_id': str(variant['variant_id']),
                'gene': str(variant['gene']),
                'assessment': str(variant['assessment']),
                'actionability': str(variant['actionability']) if pd.notna(variant['actionability']) else 'Unknown',
                'allelefraction': float(variant['allelefraction'])
            })
        
        print("🏥 Creating Protocol nodes...")
        for _, protocol in protocols_df.iterrows():
            sess.run("""
                CREATE (pr:Protocol {
                    protocol_id: $protocol_id,
                    protocol_name: $protocol_name,
                    phase: $phase,
                    status: $status
                })
            """, {
                'protocol_id': str(protocol['protocol_id']),
                'protocol_name': str(protocol['protocol_name']),
                'phase': str(protocol['phase']),
                'status': str(protocol['status'])
            })
        
        print("👥 Creating Clinical_Trial_Subject nodes and relationships...")
        for _, subject in subjects_df.iterrows():
            sess.run("""
                MATCH (p:Patient {mrn: $mrn})
                MATCH (pr:Protocol {protocol_id: $protocol_id})
                CREATE (cts:Clinical_Trial_Subject {
                    rave_id: $rave_id,
                    enrollment_status: $enrollment_status
                })
                CREATE (p)-[:ENROLLED_IN]->(cts)
                CREATE (cts)-[:PARTICIPATES_IN]->(pr)
            """, {
                'mrn': int(subject['mrn']),
                'protocol_id': str(subject['protocol_id']),
                'rave_id': str(subject['rave_id']),
                'enrollment_status': str(subject['enrollment_status'])
            })
        
        print("💊 Creating Intervention nodes and relationships...")
        for _, intervention in interventions_df.iterrows():
            sess.run("""
                MATCH (cts:Clinical_Trial_Subject {rave_id: $rave_id})
                CREATE (i:Intervention {
                    intervention_category: $intervention_category,
                    dose_level: $dose_level
                })
                CREATE (cts)-[:RECEIVES]->(i)
            """, {
                'rave_id': str(intervention['rave_id']),
                'intervention_category': str(intervention['intervention_category']),
                'dose_level': str(intervention['dose_level'])
            })
        
        print("⚠️  Creating Adverse_Event nodes and relationships...")
        for _, ae in adverse_events_df.iterrows():
            sess.run("""
                MATCH (cts:Clinical_Trial_Subject {rave_id: $rave_id})
                CREATE (ae:Adverse_Event {
                    ae_body_system: $ae_body_system,
                    grade: $grade,
                    serious: $serious
                })
                CREATE (cts)-[:EXPERIENCES]->(ae)
            """, {
                'rave_id': str(ae['rave_id']),
                'ae_body_system': str(ae['ae_body_system']),
                'grade': int(ae['grade']),
                'serious': bool(ae['serious'])
            })
    
    print("\n✅ Schema population complete!")
    
    # Test multi-hop queries
    print("\n🧪 Testing Multi-hop Queries:")
    
    with mg_driver.session() as sess:
        # Query 1: Patients on Immunotherapy
        result = sess.run("""
            MATCH (p:Patient)-[:ENROLLED_IN]->(cts:Clinical_Trial_Subject)-[:RECEIVES]->(i:Intervention)
            WHERE i.intervention_category = 'Immunotherapy'
            RETURN count(DISTINCT p) as count
        """)
        count1 = result.single()["count"]
        print(f"  ✓ {count1} patients on Immunotherapy")
        
        # Query 2: Female patients with cardiac adverse events
        result = sess.run("""
            MATCH (p:Patient)-[:ENROLLED_IN]->(cts:Clinical_Trial_Subject)-[:EXPERIENCES]->(ae:Adverse_Event)
            WHERE p.sex = 'female' AND ae.ae_body_system = 'Cardiac disorders'
            RETURN count(DISTINCT p) as count
        """)
        count2 = result.single()["count"]
        print(f"  ✓ {count2} female patients with cardiac adverse events")
        
        # Query 3: Patients with variants in specific protocol
        result = sess.run("""
            MATCH (p:Patient)-[:HAS_VARIANT]->(v:Variant), 
                  (p)-[:ENROLLED_IN]->(cts:Clinical_Trial_Subject)-[:PARTICIPATES_IN]->(pr:Protocol)
            WHERE pr.protocol_id = 'PROT_001'
            RETURN count(DISTINCT p) as count
        """)
        count3 = result.single()["count"]
        print(f"  ✓ {count3} patients with variants in PROT_001")
    
    print(f"\n🎉 SUCCESS! Your multi-hop graph is ready!")
    print(f"Now your app will show real connections between genomics and clinical trials!")

if __name__ == "__main__":
    try:
        populate_expanded_schema()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure Memgraph is running and you have all the CSV files!")