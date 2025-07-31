import pandas as pd
import numpy as np

def generate_protocols():
    """Generate synthetic protocol data as requested by mentors"""
    np.random.seed(42)
    protocols = []
    
    # Create 50 protocols as suggested
    for i in range(1, 51):
        protocols.append({
            'protocol_id': f"PROT_{i:03d}",
            'protocol_name': f"Protocol {i}",
            'phase': np.random.choice(['Phase I', 'Phase II', 'Phase III']),
            'status': np.random.choice(['Active', 'Completed'], p=[0.7, 0.3])
        })
    
    return pd.DataFrame(protocols)

def generate_clinical_trial_subjects(demo_df):
    """Generate RAVE_ID mappings (patient + protocol = RAVE_ID)"""
    np.random.seed(43)
    protocols_df = generate_protocols()
    subjects = []
    rave_counter = 1000
    
    print(f"Processing {len(demo_df)} patients with MRNs like: {demo_df['mrn'].head(3).tolist()}")
    
    # Each patient can be enrolled in 0-3 protocols
    for mrn in demo_df['mrn']:
        n_enrollments = np.random.choice([0, 1, 2, 3], p=[0.3, 0.4, 0.2, 0.1])
        
        if n_enrollments > 0:
            # Select random protocols for this patient
            selected_protocols = np.random.choice(
                protocols_df['protocol_id'], 
                size=min(n_enrollments, len(protocols_df)), 
                replace=False
            )
            
            for protocol_id in selected_protocols:
                rave_id = f"RAVE_{rave_counter}"
                rave_counter += 1
                subjects.append({
                    'rave_id': rave_id,
                    'mrn': int(mrn),  # Keep as integer to match your demographics file
                    'protocol_id': protocol_id,
                    'enrollment_status': np.random.choice(['Active', 'Completed', 'Withdrawn'], p=[0.5, 0.3, 0.2])
                })
    
    return pd.DataFrame(subjects)

def generate_interventions(subjects_df):
    """Generate intervention data using categories from mentor feedback"""
    np.random.seed(44)
    
    # These are the intervention categories from your mentor's feedback
    intervention_categories = [
        'Immunotherapy', 'Chemotherapy', 'Targeted Therapy', 'Angiogenesis Inhibitors',
        'Radiation Therapy', 'Surgery', 'Stem Cell Transplant', 'Gene Therapy', 'Hormone Therapy'
    ]
    
    interventions = []
    
    for _, subject in subjects_df.iterrows():
        # Each subject gets 1-3 interventions
        n_interventions = np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
        
        selected_interventions = np.random.choice(
            intervention_categories, 
            size=min(n_interventions, len(intervention_categories)), 
            replace=False
        )
        
        for intervention in selected_interventions:
            interventions.append({
                'rave_id': subject['rave_id'],
                'intervention_category': intervention,
                'dose_level': np.random.choice(['Low', 'Medium', 'High'])
            })
    
    return pd.DataFrame(interventions)

def generate_adverse_events(subjects_df):
    """Generate adverse events using CTCAE body systems"""
    np.random.seed(45)
    
    # These are from the CTCAE file you have - simplified body systems
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
        # Each subject has 0-4 adverse events
        n_aes = np.random.choice([0, 1, 2, 3, 4], p=[0.2, 0.3, 0.25, 0.15, 0.1])
        
        if n_aes > 0:
            selected_aes = np.random.choice(
                ae_body_systems, 
                size=min(n_aes, len(ae_body_systems)), 
                replace=False
            )
            
            for ae_system in selected_aes:
                adverse_events.append({
                    'rave_id': subject['rave_id'],
                    'ae_body_system': ae_system,
                    'grade': np.random.choice([1, 2, 3, 4, 5], p=[0.4, 0.3, 0.2, 0.08, 0.02]),
                    'serious': np.random.choice([True, False], p=[0.15, 0.85])
                })
    
    return pd.DataFrame(adverse_events)

if __name__ == "__main__":
    # Load your existing demographics data - IMPORTANT: Use your actual MRNs!
    print("Loading your existing demographics data...")
    demo_df = pd.read_csv("clean_demographics.csv")
    print(f"Found {len(demo_df)} patients with MRNs: {demo_df['mrn'].head().tolist()}...")
    
    # Generate all the clinical trial data using YOUR MRNs
    print("Generating protocols...")
    protocols_df = generate_protocols()
    protocols_df.to_csv("protocols.csv", index=False)
    
    print(f"Generating clinical trial subjects using your {len(demo_df)} existing MRNs...")
    subjects_df = generate_clinical_trial_subjects(demo_df)
    subjects_df.to_csv("clinical_trial_subjects.csv", index=False)
    
    print("Generating interventions...")
    interventions_df = generate_interventions(subjects_df)
    interventions_df.to_csv("interventions.csv", index=False)
    
    print("Generating adverse events...")
    adverse_events_df = generate_adverse_events(subjects_df)
    adverse_events_df.to_csv("adverse_events.csv", index=False)
    
    print("Done! Generated files:")
    print("- protocols.csv")
    print("- clinical_trial_subjects.csv")
    print("- interventions.csv") 
    print("- adverse_events.csv")
    
    # Print some stats
    print(f"\nStatistics:")
    print(f"- {len(protocols_df)} protocols")
    print(f"- {len(subjects_df)} clinical trial subject enrollments")
    print(f"- {len(interventions_df)} interventions")
    print(f"- {len(adverse_events_df)} adverse events")
    
    # Verify MRN linkage
    your_mrns = set(demo_df['mrn'])
    subjects_mrns = set(subjects_df['mrn'])
    print(f"\nMRN Linkage Check:")
    print(f"- Your original MRNs: {len(your_mrns)}")
    print(f"- MRNs in clinical trial subjects: {len(subjects_mrns)}")
    print(f"- Overlap: {len(your_mrns & subjects_mrns)} (should be subset of original)")
    
    # Debug the data types
    print(f"\nData Type Check:")
    print(f"- Original MRN type: {type(demo_df['mrn'].iloc[0])}")
    print(f"- Subjects MRN type: {type(subjects_df['mrn'].iloc[0])}")
    print(f"- Sample original MRNs: {demo_df['mrn'].head(3).tolist()}")
    print(f"- Sample subject MRNs: {subjects_df['mrn'].head(3).tolist()}")
    
    # Show some examples
    print(f"\nExample linkages:")
    sample_subject = subjects_df.head(1).iloc[0]
    print(f"- Patient {sample_subject['mrn']} enrolled in {sample_subject['protocol_id']} as {sample_subject['rave_id']}")
    
    if len(interventions_df) > 0:
        sample_intervention = interventions_df.head(1).iloc[0]
        print(f"- Subject {sample_intervention['rave_id']} receives {sample_intervention['intervention_category']}")
    
    if len(adverse_events_df) > 0:
        sample_ae = adverse_events_df.head(1).iloc[0]
        print(f"- Subject {sample_ae['rave_id']} experienced {sample_ae['ae_body_system']}")