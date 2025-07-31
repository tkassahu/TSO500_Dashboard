import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta

def generate_scalable_synthetic_data(n_patients, output_dir="./"):
    """
    Generate synthetic data based on mentor specifications
    
    Parameters from mentor meeting:
    - Patients: 1 to 20,000 (main variable)
    - Variants: 20-50 per patient
    - Protocols: 20-300 patients per protocol
    - Clinical Trial Subjects: 1-3 protocols per patient
    - Interventions: 1-3 per clinical trial subject
    - Adverse Events: 1-10 per clinical trial subject
    """
    
    print(f"🔄 Generating synthetic data for {n_patients} patients...")
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # ═══════════════════════════════════════════════════════════════
    # 1. PATIENTS (Demographics)
    # ═══════════════════════════════════════════════════════════════
    
    print("   📊 Generating patient demographics...")
    patients = []
    for i in range(n_patients):
        patients.append({
            'mrn': 1000000 + i,  # Sequential MRNs starting at 1000000
            'age': np.random.randint(18, 85),
            'sex': np.random.choice(['male', 'female'])
        })
    
    patients_df = pd.DataFrame(patients)
    
    # ═══════════════════════════════════════════════════════════════
    # 2. VARIANTS (20-50 per patient)
    # ═══════════════════════════════════════════════════════════════
    
    print("   🧬 Generating variants (20-50 per patient)...")
    
    # Realistic gene list from TSO-500 panel
    genes = [
        'TP53', 'PIK3CA', 'KRAS', 'EGFR', 'BRAF', 'ERBB2', 'AKT1', 'NRAS', 
        'MET', 'ALK', 'ROS1', 'RET', 'BRCA1', 'BRCA2', 'ATM', 'CDKN2A',
        'FGFR1', 'FGFR2', 'FGFR3', 'IDH1', 'IDH2', 'NOTCH1', 'PTEN', 'STK11'
    ]
    
    assessments = ['Pathogenic', 'Likely Pathogenic', 'VUS', 'Likely Benign', 'Benign']
    actionability_levels = ['1A', '2C', '3', '', '']  # Some have actionability, some don't
    
    variants = []
    variant_id_counter = 1
    
    for patient in patients:
        mrn = patient['mrn']
        # 20-50 variants per patient as specified
        n_variants = np.random.randint(20, 51)
        
        for v in range(n_variants):
            gene = np.random.choice(genes)
            assessment = np.random.choice(assessments, p=[0.15, 0.10, 0.50, 0.15, 0.10])
            
            variants.append({
                'variant_id': f"VAR_{variant_id_counter:08d}",
                'mrn': mrn,
                'gene': gene,
                'assessment': assessment,
                'actionability': np.random.choice(actionability_levels),
                'allelefraction': np.random.uniform(0.05, 0.95),
                'chromosome': np.random.choice(range(1, 23)),
                'position': np.random.randint(1000000, 250000000),
                'protein_change': f"p.{np.random.choice(['Arg', 'Leu', 'Gly', 'Val'])}{np.random.randint(1, 1000)}{np.random.choice(['His', 'Asp', 'Glu', 'Met'])}"
            })
            variant_id_counter += 1
    
    variants_df = pd.DataFrame(variants)
    
    # ═══════════════════════════════════════════════════════════════
    # 3. PROTOCOLS (20-300 patients each)
    # ═══════════════════════════════════════════════════════════════
    
    print("   🏥 Generating protocols...")
    
    # Calculate number of protocols needed
    # If each protocol has 20-300 patients, and each patient is in 1-3 protocols
    # We need enough protocols to accommodate the enrollments
    
    # Estimate: if average patient is in 2 protocols, and average protocol has 160 patients
    # We need roughly (n_patients * 2) / 160 protocols
    estimated_protocols = max(10, min(200, (n_patients * 2) // 160))
    
    protocols = []
    for i in range(estimated_protocols):
        protocols.append({
            'protocol_id': f"PROT_{i+1:03d}",
            'protocol_name': f"Clinical Trial Protocol {i+1}",
            'phase': np.random.choice(['Phase I', 'Phase II', 'Phase III'], p=[0.3, 0.5, 0.2]),
            'status': np.random.choice(['Active', 'Completed'], p=[0.7, 0.3]),
            'target_enrollment': np.random.randint(20, 301)  # 20-300 as specified
        })
    
    protocols_df = pd.DataFrame(protocols)
    
    # ═══════════════════════════════════════════════════════════════
    # 4. CLINICAL TRIAL SUBJECTS (1-3 protocols per patient)
    # ═══════════════════════════════════════════════════════════════
    
    print("   👥 Generating clinical trial subjects (1-3 protocols per patient)...")
    
    clinical_trial_subjects = []
    rave_id_counter = 100000
    
    for patient in patients:
        mrn = patient['mrn']
        
        # Each patient enrolled in 1-3 protocols as specified
        n_enrollments = np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
        
        # Select random protocols for this patient
        available_protocols = protocols_df['protocol_id'].tolist()
        selected_protocols = np.random.choice(
            available_protocols, 
            size=min(n_enrollments, len(available_protocols)), 
            replace=False
        )
        
        for protocol_id in selected_protocols:
            clinical_trial_subjects.append({
                'rave_id': f"RAVE_{rave_id_counter}",
                'mrn': mrn,
                'protocol_id': protocol_id,
                'enrollment_date': np.random.choice(pd.date_range('2020-01-01', '2024-12-31')),
                'enrollment_status': np.random.choice(['Active', 'Completed', 'Withdrawn'], p=[0.5, 0.3, 0.2])
            })
            rave_id_counter += 1
    
    subjects_df = pd.DataFrame(clinical_trial_subjects)
    
    # ═══════════════════════════════════════════════════════════════
    # 5. INTERVENTIONS (1-3 per clinical trial subject)
    # ═══════════════════════════════════════════════════════════════
    
    print("   💊 Generating interventions (1-3 per clinical trial subject)...")
    
    intervention_categories = [
        'Immunotherapy', 'Chemotherapy', 'Targeted Therapy', 'Angiogenesis Inhibitors',
        'Radiation Therapy', 'Surgery', 'Stem Cell Transplant', 'Gene Therapy', 
        'Hormone Therapy', 'CAR-T Cell Therapy'
    ]
    
    interventions = []
    
    for _, subject in subjects_df.iterrows():
        rave_id = subject['rave_id']
        
        # 1-3 interventions per clinical trial subject as specified
        n_interventions = np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
        
        selected_interventions = np.random.choice(
            intervention_categories,
            size=min(n_interventions, len(intervention_categories)),
            replace=False
        )
        
        for intervention in selected_interventions:
            interventions.append({
                'rave_id': rave_id,
                'intervention_category': intervention,
                'dose_level': np.random.choice(['Low', 'Medium', 'High']),
                'start_date': subject['enrollment_date'] + pd.Timedelta(days=np.random.randint(0, 30)),
                'duration_days': np.random.randint(30, 365)
            })
    
    interventions_df = pd.DataFrame(interventions)
    
    # ═══════════════════════════════════════════════════════════════
    # 6. ADVERSE EVENTS (1-10 per clinical trial subject)
    # ═══════════════════════════════════════════════════════════════
    
    print("   ⚠️  Generating adverse events (1-10 per clinical trial subject)...")
    
    ae_body_systems = [
        'Blood and lymphatic system disorders',
        'Cardiac disorders',
        'Gastrointestinal disorders', 
        'General disorders and administration site conditions',
        'Hepatobiliary disorders',
        'Immune system disorders',
        'Infections and infestations',
        'Metabolism and nutrition disorders',
        'Musculoskeletal and connective tissue disorders',
        'Nervous system disorders',
        'Respiratory, thoracic and mediastinal disorders',
        'Skin and subcutaneous tissue disorders'
    ]
    
    adverse_events = []
    
    for _, subject in subjects_df.iterrows():
        rave_id = subject['rave_id']
        
        # 1-10 adverse events per clinical trial subject as specified
        n_adverse_events = np.random.choice(range(1, 11), p=[0.2, 0.2, 0.15, 0.15, 0.1, 0.08, 0.05, 0.03, 0.02, 0.02])
        
        selected_aes = np.random.choice(
            ae_body_systems,
            size=min(n_adverse_events, len(ae_body_systems)),
            replace=True  # Can have multiple AEs in same body system
        )
        
        for ae_system in selected_aes:
            adverse_events.append({
                'rave_id': rave_id,
                'ae_body_system': ae_system,
                'grade': np.random.choice([1, 2, 3, 4, 5], p=[0.4, 0.3, 0.2, 0.08, 0.02]),
                'serious': np.random.choice([True, False], p=[0.15, 0.85]),
                'onset_date': subject['enrollment_date'] + pd.Timedelta(days=np.random.randint(1, 200))
            })
    
    adverse_events_df = pd.DataFrame(adverse_events)
    
    # ═══════════════════════════════════════════════════════════════
    # 7. SAVE ALL DATA
    # ═══════════════════════════════════════════════════════════════
    

    print("   💾 Saving data files...")

# Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    patients_df.to_csv(f"{output_dir}/clean_demographics_{n_patients}pts.csv", index=False)
# ... rest of the save operations
    
    
    print("   💾 Saving data files...")
    
    patients_df.to_csv(f"{output_dir}/clean_demographics_{n_patients}pts.csv", index=False)
    variants_df.to_csv(f"{output_dir}/variants_with_50_demo_mrn_{n_patients}pts.csv", index=False)
    protocols_df.to_csv(f"{output_dir}/protocols_{n_patients}pts.csv", index=False)
    subjects_df.to_csv(f"{output_dir}/clinical_trial_subjects_{n_patients}pts.csv", index=False)
    interventions_df.to_csv(f"{output_dir}/interventions_{n_patients}pts.csv", index=False)
    adverse_events_df.to_csv(f"{output_dir}/adverse_events_{n_patients}pts.csv", index=False)
    
    # ═══════════════════════════════════════════════════════════════
    # 8. SUMMARY STATISTICS
    # ═══════════════════════════════════════════════════════════════
    
    print(f"\n✅ Successfully generated data for {n_patients} patients!")
    print(f"📊 Summary Statistics:")
    print(f"   - Patients: {len(patients_df):,}")
    print(f"   - Variants: {len(variants_df):,} ({len(variants_df)/len(patients_df):.1f} per patient)")
    print(f"   - Protocols: {len(protocols_df):,}")
    print(f"   - Clinical Trial Subjects: {len(subjects_df):,} ({len(subjects_df)/len(patients_df):.1f} per patient)")
    print(f"   - Interventions: {len(interventions_df):,} ({len(interventions_df)/len(subjects_df):.1f} per subject)")
    print(f"   - Adverse Events: {len(adverse_events_df):,} ({len(adverse_events_df)/len(subjects_df):.1f} per subject)")
    print(f"   - Total database records: {len(patients_df) + len(variants_df) + len(protocols_df) + len(subjects_df) + len(interventions_df) + len(adverse_events_df):,}")
    
    return {
        'patients': patients_df,
        'variants': variants_df,
        'protocols': protocols_df,
        'subjects': subjects_df,
        'interventions': interventions_df,
        'adverse_events': adverse_events_df
    }


def generate_test_datasets():
    """Generate datasets for performance testing at different scales"""
    
    # Test sizes as suggested by mentors: 1 to 20,000
    test_sizes = [1, 10, 50, 100, 500, 1000, 2000, 5000, 10000, 15000, 20000]
    
    print("🚀 Generating test datasets for performance study...")
    print(f"📈 Scales to test: {test_sizes}")
    
    for n_patients in test_sizes:
        print(f"\n{'='*60}")
        print(f"📊 Generating dataset for {n_patients:,} patients")
        print(f"{'='*60}")
        
        try:
            generate_scalable_synthetic_data(n_patients, output_dir=f"./test_data_{n_patients}pts")
            print(f"✅ Successfully created test dataset for {n_patients:,} patients")
            
        except Exception as e:
            print(f"❌ Failed to generate dataset for {n_patients:,} patients: {e}")
            break
    
    print(f"\n🎉 Test dataset generation complete!")


if __name__ == "__main__":
    # Option 1: Generate single dataset for current app
    print("Choose generation mode:")
    print("1. Generate single dataset for current app (200 patients)")
    print("2. Generate all test datasets for performance study (1 to 20,000 patients)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        # Generate data for current app
        generate_scalable_synthetic_data(200)
        print("\n✅ Generated updated data for current app!")
        print("Files created:")
        print("- clean_demographics_200pts.csv")
        print("- variants_with_50_demo_mrn_200pts.csv") 
        print("- protocols_200pts.csv")
        print("- clinical_trial_subjects_200pts.csv")
        print("- interventions_200pts.csv")
        print("- adverse_events_200pts.csv")
        print("\n📝 Next steps:")
        print("1. Rename files to remove '_200pts' suffix for your current app")
        print("2. Test your app with the new data")
        print("3. Proceed with performance testing using generate_test_datasets()")
        
    elif choice == "2":
        # Generate all test datasets
        generate_test_datasets()
        
    else:
        print("❌ Invalid choice. Run script again and choose 1 or 2.")