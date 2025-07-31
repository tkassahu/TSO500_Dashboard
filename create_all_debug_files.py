#!/usr/bin/env python3
"""Create all the debug files needed"""

# File 1: test_all_stratifications.py
test_all_stratifications_code = '''#!/usr/bin/env python3
"""Test all survival stratification options to see what data is available"""

import pandas as pd
import os

print("🔍 Testing All Survival Stratification Data")
print("="*60)

# 1. Test Gene stratification
print("\\n1. GENE STRATIFICATION TEST:")
try:
    # Load variants data
    if os.path.exists('variants_with_50_demo_mrn_200pts.csv'):
        variants_df = pd.read_csv('variants_with_50_demo_mrn_200pts.csv')
    elif os.path.exists('TSO500_Synthetic_Final.csv'):
        variants_df = pd.read_csv('TSO500_Synthetic_Final.csv')
    else:
        variants_df = pd.read_csv('variants_with_50_demo_mrn.csv')
    
    top_genes = variants_df['gene'].value_counts().head(5)
    print(f"✅ Gene data available!")
    print(f"   Top 5 genes:")
    for gene, count in top_genes.items():
        patients = variants_df[variants_df['gene'] == gene]['mrn'].nunique()
        print(f"   - {gene}: {count} variants in {patients} patients")
        
except Exception as e:
    print(f"❌ Error with gene data: {e}")

# 2. Test Sex stratification
print("\\n2. SEX STRATIFICATION TEST:")
try:
    demo_df = pd.read_csv('clean_demographics.csv')
    sex_counts = demo_df['sex'].value_counts()
    print(f"✅ Sex data available!")
    print(f"   Distribution:")
    for sex, count in sex_counts.items():
        print(f"   - {sex}: {count} patients")
        
except Exception as e:
    print(f"❌ Error with sex data: {e}")

# 3. Test Protocol stratification
print("\\n3. PROTOCOL STRATIFICATION TEST:")
try:
    subjects_df = pd.read_csv('clinical_trial_subjects.csv')
    protocols_df = pd.read_csv('protocols.csv')
    
    protocol_counts = subjects_df['protocol_id'].value_counts().head(5)
    print(f"✅ Protocol data available!")
    print(f"   Top 5 protocols:")
    for protocol_id, count in protocol_counts.items():
        # Get phase info
        phase_info = protocols_df[protocols_df['protocol_id'] == protocol_id]
        phase = phase_info['phase'].iloc[0] if len(phase_info) > 0 else "Unknown"
        print(f"   - {protocol_id} ({phase}): {count} patients")
        
except Exception as e:
    print(f"❌ Error with protocol data: {e}")
    print("   Run: python load_remaining_data.py")

# 4. Test Intervention stratification
print("\\n4. INTERVENTION STRATIFICATION TEST:")
try:
    subjects_df = pd.read_csv('clinical_trial_subjects.csv')
    interventions_df = pd.read_csv('interventions.csv')
    
    intervention_counts = interventions_df['intervention_category'].value_counts()
    print(f"✅ Intervention data available!")
    print(f"   Intervention types:")
    for intervention, count in intervention_counts.items():
        # Get unique patients
        intervention_raves = interventions_df[
            interventions_df['intervention_category'] == intervention
        ]['rave_id'].unique()
        
        patient_count = subjects_df[
            subjects_df['rave_id'].isin(intervention_raves)
        ]['mrn'].nunique()
        
        print(f"   - {intervention}: {patient_count} patients")
        
except Exception as e:
    print(f"❌ Error with intervention data: {e}")
    print("   Run: python load_remaining_data.py")

print("\\n" + "="*60)

# 5. Test data connectivity
print("\\n5. DATA CONNECTIVITY TEST:")
try:
    # Check if MRNs match across files
    demo_mrns = set(demo_df['mrn'].values)
    variant_mrns = set(variants_df['mrn'].unique())
    
    if os.path.exists('clinical_trial_subjects.csv'):
        subject_mrns = set(subjects_df['mrn'].unique())
        print(f"\\n   MRN overlap:")
        print(f"   - Demographics: {len(demo_mrns)} patients")
        print(f"   - Variants: {len(variant_mrns)} patients")
        print(f"   - Clinical trials: {len(subject_mrns)} patients")
        print(f"   - Common to all: {len(demo_mrns & variant_mrns & subject_mrns)} patients")
    else:
        print(f"\\n   MRN overlap (no clinical data):")
        print(f"   - Demographics: {len(demo_mrns)} patients")
        print(f"   - Variants: {len(variant_mrns)} patients")
        print(f"   - Common: {len(demo_mrns & variant_mrns)} patients")
        
except Exception as e:
    print(f"❌ Error checking connectivity: {e}")

print("\\n" + "="*60)
print("\\n📋 Summary:")
print("If any tests failed, the corresponding stratification won't work.")
print("Make sure all data files are present and properly linked.")
'''

# File 2: debug_survival_stratification.py
debug_survival_code = '''#!/usr/bin/env python3
"""Debug why survival stratification isn't working for all options"""

from neo4j import GraphDatabase
import pandas as pd

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("", ""))

print("🔍 Debugging Survival Stratification Issues")
print("="*60)

with driver.session() as session:
    # 1. Check if protocols exist and are linked to patients
    print("\\n1. Checking Protocol Data:")
    result = session.run("""
        MATCH (p:Patient)-[:ENROLLED_AS]->(cts:ClinicalTrialSubject)-[:IN_PROTOCOL]->(pr:Protocol)
        RETURN count(DISTINCT p) as patient_count, 
               count(DISTINCT pr) as protocol_count,
               collect(DISTINCT pr.protocol_id)[0..5] as sample_protocols
    """)
    data = result.single()
    print(f"   Patients in protocols: {data['patient_count']}")
    print(f"   Unique protocols: {data['protocol_count']}")
    print(f"   Sample protocols: {data['sample_protocols']}")
    
    # 2. Check if interventions are properly linked
    print("\\n2. Checking Intervention Data:")
    result = session.run("""
        MATCH (p:Patient)-[:ENROLLED_AS]->(cts:ClinicalTrialSubject)-[:RECEIVED_INTERVENTION]->(i:Intervention)
        RETURN count(DISTINCT p) as patient_count,
               count(DISTINCT i) as intervention_count,
               collect(DISTINCT i.intervention_category)[0..5] as sample_interventions
    """)
    data = result.single()
    print(f"   Patients with interventions: {data['patient_count']}")
    print(f"   Unique intervention types: {data['intervention_count']}")
    print(f"   Sample interventions: {data['sample_interventions']}")
    
    # 3. Check patient data for gene stratification
    print("\\n3. Checking Patient-Variant Data:")
    result = session.run("""
        MATCH (p:Patient)-[:HAS_VARIANT]->(v:Variant)
        RETURN count(DISTINCT p) as patient_count,
               count(DISTINCT v.gene) as gene_count,
               collect(DISTINCT v.gene)[0..5] as sample_genes
    """)
    data = result.single()
    print(f"   Patients with variants: {data['patient_count']}")
    print(f"   Unique genes: {data['gene_count']}")
    print(f"   Sample genes: {data['sample_genes']}")
    
    # 4. Check patient demographics
    print("\\n4. Checking Patient Demographics:")
    result = session.run("""
        MATCH (p:Patient)
        RETURN count(p) as total_patients,
               count(DISTINCT p.sex) as sex_values,
               collect(DISTINCT p.sex) as sex_list
    """)
    data = result.single()
    print(f"   Total patients: {data['total_patients']}")
    print(f"   Sex values: {data['sex_list']}")
    
    # 5. Test specific queries used in survival function
    print("\\n5. Testing Survival Function Queries:")
    
    # Test protocol query
    print("\\n   Testing protocol query for MRN 1000000:")
    result = session.run("""
        MATCH (p:Patient {mrn: 1000000})-[:ENROLLED_AS]->(cts:ClinicalTrialSubject)-[:IN_PROTOCOL]->(pr:Protocol)
        RETURN DISTINCT pr.protocol_id as protocol, pr.phase as phase
    """)
    protocols = list(result)
    print(f"   Found {len(protocols)} protocols for patient 1000000")
    if protocols:
        print(f"   Example: {protocols[0]}")

driver.close()

# Also check the CSV files
print("\\n" + "="*60)
print("6. Checking CSV Files:")

try:
    # Check variants file
    variants_df = pd.read_csv('variants_with_50_demo_mrn_200pts.csv')
    print(f"\\n   Variants file:")
    print(f"   - Total rows: {len(variants_df)}")
    print(f"   - Unique MRNs: {variants_df['mrn'].nunique()}")
    print(f"   - Unique genes: {variants_df['gene'].nunique()}")
    print(f"   - Sample genes: {variants_df['gene'].unique()[:5].tolist()}")
except Exception as e:
    print(f"   ❌ Error reading variants file: {e}")

try:
    # Check demographics
    demo_df = pd.read_csv('clean_demographics.csv')
    print(f"\\n   Demographics file:")
    print(f"   - Total patients: {len(demo_df)}")
    print(f"   - Sex distribution: {demo_df['sex'].value_counts().to_dict()}")
except Exception as e:
    print(f"   ❌ Error reading demographics file: {e}")

print("\\n" + "="*60)
print("\\n📋 Recommendations:")
print("1. If protocol/intervention counts are 0, run: python load_remaining_data.py")
print("2. If patient counts don't match, reload all data")
print("3. Check that MRN values match between files")
'''

# Write the files
with open('test_all_stratifications.py', 'w') as f:
    f.write(test_all_stratifications_code)
print("✅ Created: test_all_stratifications.py")

with open('debug_survival_stratification.py', 'w') as f:
    f.write(debug_survival_code)
print("✅ Created: debug_survival_stratification.py")

# Note: apply_survival_fix.py is too long to include here
print("\n⚠️  You still need to manually create 'apply_survival_fix.py' from the artifact above")
print("\n📋 Next steps:")
print("1. Copy the code from 'Apply Simplified Survival Fix Script' artifact")
print("2. Save it as 'apply_survival_fix.py'")
print("3. Run: python test_all_stratifications.py")
print("4. Run: python debug_survival_stratification.py")
print("5. Run: python apply_survival_fix.py")
print("6. Restart your app")