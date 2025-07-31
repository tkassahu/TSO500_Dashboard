import pandas as pd
import numpy as np

def generate_realistic_survival_data():
    """Generate realistic survival data linked to patient characteristics"""
    
    # Load your actual data
    demo_df = pd.read_csv("clean_demographics.csv")
    variants_df = pd.read_csv("variants_with_50_demo_mrn.csv")
    
    # Load clinical trial data if available
    try:
        subjects_df = pd.read_csv("clinical_trial_subjects.csv")
        interventions_df = pd.read_csv("interventions.csv")
        adverse_events_df = pd.read_csv("adverse_events.csv")
        clinical_data_available = True
    except:
        clinical_data_available = False
    
    # Merge patient data with variants
    patient_variant_summary = variants_df.groupby('mrn').agg({
        'gene': 'count',  # number of variants
        'assessment': lambda x: (x.isin(['Pathogenic', 'Likely Pathogenic'])).sum(),  # actionable variants
        'allelefraction': 'mean'  # average allele fraction
    }).rename(columns={
        'gene': 'total_variants',
        'assessment': 'actionable_variants',
        'allelefraction': 'avg_allele_fraction'
    }).reset_index()
    
    # Merge with demographics
    survival_data = demo_df.merge(patient_variant_summary, on='mrn', how='left')
    survival_data = survival_data.fillna(0)  # Patients with no variants
    
    # Add clinical trial information if available
    if clinical_data_available:
        # Get intervention information for each patient
        patient_interventions = []
        for mrn in survival_data['mrn']:
            patient_subjects = subjects_df[subjects_df['mrn'] == mrn]
            if len(patient_subjects) > 0:
                patient_raves = patient_subjects['rave_id'].tolist()
                patient_interventions_list = interventions_df[
                    interventions_df['rave_id'].isin(patient_raves)
                ]['intervention_category'].tolist()
                
                # Check for specific beneficial interventions
                has_immunotherapy = 'Immunotherapy' in patient_interventions_list
                has_targeted_therapy = 'Targeted Therapy' in patient_interventions_list
                intervention_count = len(set(patient_interventions_list))
            else:
                has_immunotherapy = False
                has_targeted_therapy = False
                intervention_count = 0
                
            patient_interventions.append({
                'mrn': mrn,
                'has_immunotherapy': has_immunotherapy,
                'has_targeted_therapy': has_targeted_therapy,
                'intervention_count': intervention_count
            })
        
        intervention_df = pd.DataFrame(patient_interventions)
        survival_data = survival_data.merge(intervention_df, on='mrn', how='left')
        survival_data = survival_data.fillna(False)
    else:
        # Add dummy columns if no clinical trial data
        survival_data['has_immunotherapy'] = False
        survival_data['has_targeted_therapy'] = False
        survival_data['intervention_count'] = 0
    
    # Generate realistic survival times based on patient characteristics
    np.random.seed(42)  # For reproducibility
    
    survival_times = []
    events = []
    
    for _, patient in survival_data.iterrows():
        # Base survival time (in months)
        base_survival = 24  # 2 years baseline
        
        # Age effect: older patients have shorter survival
        age_factor = 1 - (patient['age'] - 50) * 0.01  # Decrease by 1% per year over 50
        age_factor = max(0.5, age_factor)  # Cap at 50% of baseline
        
        # Sex effect: slight difference
        sex_factor = 1.1 if patient['sex'] == 'female' else 1.0
        
        # Variant burden effect: more variants = worse prognosis
        variant_factor = 1 - (patient['total_variants'] * 0.05)  # 5% decrease per variant
        variant_factor = max(0.6, variant_factor)  # Cap at 60% of baseline
        
        # Actionable variants effect: actionable variants can be good (targetable) or bad
        if patient['actionable_variants'] > 0:
            actionable_factor = 0.9  # Slightly worse initially
        else:
            actionable_factor = 1.0
        
        # Treatment effects (if clinical trial data available)
        treatment_factor = 1.0
        if clinical_data_available:
            if patient['has_immunotherapy']:
                treatment_factor *= 1.3  # 30% improvement with immunotherapy
            if patient['has_targeted_therapy']:
                treatment_factor *= 1.2  # 20% improvement with targeted therapy
            if patient['intervention_count'] > 2:
                treatment_factor *= 0.9  # Multiple treatments might indicate more aggressive disease
        
        # Calculate final survival time
        final_survival = base_survival * age_factor * sex_factor * variant_factor * actionable_factor * treatment_factor
        
        # Add some random variation
        random_factor = np.random.lognormal(0, 0.3)  # Log-normal distribution for variation
        final_survival *= random_factor
        
        # Ensure minimum survival time
        final_survival = max(1, final_survival)  # At least 1 month
        
        # Convert to days
        survival_time_days = final_survival * 30.44  # Average days per month
        
        # Determine if event occurred or patient was censored
        # Higher-risk patients more likely to have events
        risk_score = (
            (80 - patient['age']) / 80 +  # Higher age = higher risk
            patient['total_variants'] * 0.1 +  # More variants = higher risk
            (1 - treatment_factor) * 2  # Less treatment benefit = higher risk
        )
        
        event_probability = min(0.8, max(0.2, risk_score))  # Between 20% and 80%
        event = np.random.random() < event_probability
        
        survival_times.append(survival_time_days)
        events.append(int(event))
    
    # Add survival data to dataframe
    survival_data['survival_time_days'] = survival_times
    survival_data['event'] = events
    survival_data['survival_time_months'] = survival_data['survival_time_days'] / 30.44
    
    # Save to CSV
    survival_data.to_csv("realistic_survival_data.csv", index=False)
    
    print("✅ Generated realistic survival data!")
    print(f"📊 Summary:")
    print(f"   - {len(survival_data)} patients")
    print(f"   - {survival_data['event'].sum()} events ({survival_data['event'].mean()*100:.1f}%)")
    print(f"   - Median survival: {survival_data['survival_time_months'].median():.1f} months")
    print(f"   - Survival range: {survival_data['survival_time_months'].min():.1f} - {survival_data['survival_time_months'].max():.1f} months")
    
    if clinical_data_available:
        immunotherapy_patients = survival_data[survival_data['has_immunotherapy']]
        if len(immunotherapy_patients) > 0:
            print(f"   - Patients with immunotherapy: {len(immunotherapy_patients)}")
            print(f"   - Median survival (immunotherapy): {immunotherapy_patients['survival_time_months'].median():.1f} months")
    
    return survival_data

if __name__ == "__main__":
    generate_realistic_survival_data()