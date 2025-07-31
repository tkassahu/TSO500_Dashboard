#!/usr/bin/env python3
"""
Performance profiling script for Memgraph queries
Tests query performance as data scales from 1 to 20,000 patients
As requested by mentors in the meeting
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from neo4j import GraphDatabase
import time
import os
import sys
from datetime import datetime
import json

# Set up plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Test sizes as specified by mentors: 1 to 20,000
TEST_SIZES = [1, 10, 50, 100, 500, 1000, 2000, 5000, 10000, 15000, 20000]

# Number of times to run each query for statistics
RUNS_PER_QUERY = 10

# Memgraph connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = ""
NEO4J_PASSWORD = ""

# Output directory for results
OUTPUT_DIR = "performance_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# QUERY DEFINITIONS - Meaningful queries from the app
# ═══════════════════════════════════════════════════════════════

QUERIES = {
    "simple_patient_count": {
        "name": "Simple Patient Count",
        "description": "Count all patients",
        "query": """
            MATCH (p:Patient)
            RETURN count(p) as patient_count
        """
    },
    
    "patients_with_gene_mutation": {
        "name": "Patients with Specific Gene Mutation",
        "description": "Find patients with KRAS mutations",
        "query": """
            MATCH (p:Patient)-[:HAS_VARIANT]->(v:Variant)
            WHERE v.gene = 'KRAS'
            RETURN count(DISTINCT p) as patient_count
        """
    },
    
    "multi_hop_clinical_trial": {
        "name": "Multi-hop Clinical Trial Query",
        "description": "Find female patients with KRAS mutations on immunotherapy",
        "query": """
            MATCH (p:Patient)-[:HAS_VARIANT]->(v:Variant)
            WHERE p.sex = 'female' AND v.gene = 'KRAS'
            MATCH (p)-[:ENROLLED_AS]->(cts:ClinicalTrialSubject)-[:RECEIVED_INTERVENTION]->(i:Intervention)
            WHERE i.intervention_category = 'Immunotherapy'
            RETURN count(DISTINCT p) as patient_count
        """
    },
    
    "complex_aggregation": {
        "name": "Complex Aggregation Query",
        "description": "Count variants by gene for patients in Phase III trials with adverse events",
        "query": """
            MATCH (p:Patient)-[:ENROLLED_AS]->(cts:ClinicalTrialSubject)-[:IN_PROTOCOL]->(pr:Protocol)
            WHERE pr.phase = 'Phase III'
            MATCH (cts)-[:EXPERIENCED_AE]->(ae:AdverseEvent)
            WHERE ae.grade >= 3
            MATCH (p)-[:HAS_VARIANT]->(v:Variant)
            RETURN v.gene, count(v) as variant_count
            ORDER BY variant_count DESC
            LIMIT 10
        """
    }
}

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def clear_database(driver):
    """Clear all data from Memgraph"""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("✅ Cleared database")

def load_data_for_size(driver, n_patients):
    """Load data for specific number of patients"""
    print(f"\n📥 Loading data for {n_patients} patients...")
    
    # First, ensure data files exist
    data_dir = f"test_data_{n_patients}pts"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory {data_dir} not found!")
        print(f"   Run: python updated_data_generation.py and choose option 2")
        return False
    
    # Load each file type
    files_to_load = [
        ("clean_demographics", "csv", load_patients),
        ("variants_with_50_demo_mrn", "csv", load_variants),
        ("protocols", "csv", load_protocols),
        ("clinical_trial_subjects", "csv", load_clinical_trial_subjects),
        ("interventions", "csv", load_interventions),
        ("adverse_events", "csv", load_adverse_events)
    ]
    
    with driver.session() as session:
        for base_name, ext, load_func in files_to_load:
            filepath = os.path.join(data_dir, f"{base_name}_{n_patients}pts.{ext}")
            if os.path.exists(filepath):
                load_func(session, filepath)
            else:
                print(f"⚠️  Missing file: {filepath}")
    
    return True

def load_patients(session, filepath):
    """Load patient nodes"""
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        session.run("""
            CREATE (p:Patient {mrn: $mrn, age: $age, sex: $sex})
        """, mrn=int(row['mrn']), age=int(row['age']), sex=row['sex'])
    print(f"   ✅ Loaded {len(df)} patients")

def load_variants(session, filepath):
    """Load variant nodes and relationships"""
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        session.run("""
            MATCH (p:Patient {mrn: $mrn})
            CREATE (v:Variant {
                variant_id: $variant_id,
                gene: $gene,
                assessment: $assessment,
                actionability: $actionability,
                allelefraction: $allelefraction
            })
            CREATE (p)-[:HAS_VARIANT]->(v)
        """, 
        mrn=int(row['mrn']),
        variant_id=row['variant_id'],
        gene=row['gene'],
        assessment=row['assessment'],
        actionability=row.get('actionability', ''),
        allelefraction=float(row['allelefraction']))
    print(f"   ✅ Loaded {len(df)} variants")

def load_protocols(session, filepath):
    """Load protocol nodes"""
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        session.run("""
            CREATE (pr:Protocol {
                protocol_id: $protocol_id,
                protocol_name: $protocol_name,
                phase: $phase,
                status: $status
            })
        """,
        protocol_id=row['protocol_id'],
        protocol_name=row['protocol_name'],
        phase=row['phase'],
        status=row['status'])
    print(f"   ✅ Loaded {len(df)} protocols")

def load_clinical_trial_subjects(session, filepath):
    """Load clinical trial subject nodes and relationships"""
    df = pd.read_csv(filepath)
    for _, row in df.iterrows():
        session.run("""
            MATCH (p:Patient {mrn: $mrn})
            MATCH (pr:Protocol {protocol_id: $protocol_id})
            CREATE (cts:ClinicalTrialSubject {
                rave_id: $rave_id,
                enrollment_date: $enrollment_date,
                enrollment_status: $enrollment_status
            })
            CREATE (p)-[:ENROLLED_AS]->(cts)
            CREATE (cts)-[:IN_PROTOCOL]->(pr)
        """,
        mrn=int(row['mrn']),
        protocol_id=row['protocol_id'],
        rave_id=row['rave_id'],
        enrollment_date=str(row['enrollment_date']),
        enrollment_status=row['enrollment_status'])
    print(f"   ✅ Loaded {len(df)} clinical trial subjects")

def load_interventions(session, filepath):
    """Load intervention nodes and relationships"""
    df = pd.read_csv(filepath)
    # Create unique intervention nodes
    for intervention in df['intervention_category'].unique():
        session.run("""
            MERGE (i:Intervention {intervention_category: $intervention_category})
        """, intervention_category=intervention)
    
    # Create relationships
    for _, row in df.iterrows():
        session.run("""
            MATCH (cts:ClinicalTrialSubject {rave_id: $rave_id})
            MATCH (i:Intervention {intervention_category: $intervention_category})
            CREATE (cts)-[r:RECEIVED_INTERVENTION {
                dose_level: $dose_level,
                start_date: $start_date,
                duration_days: $duration_days
            }]->(i)
        """,
        rave_id=row['rave_id'],
        intervention_category=row['intervention_category'],
        dose_level=row['dose_level'],
        start_date=str(row['start_date']),
        duration_days=int(row['duration_days']))
    print(f"   ✅ Loaded intervention relationships")

def load_adverse_events(session, filepath):
    """Load adverse event nodes and relationships"""
    df = pd.read_csv(filepath)
    # Create unique AE nodes
    for ae_system in df['ae_body_system'].unique():
        session.run("""
            MERGE (ae:AdverseEvent {ae_body_system: $ae_body_system})
        """, ae_body_system=ae_system)
    
    # Create relationships
    for _, row in df.iterrows():
        session.run("""
            MATCH (cts:ClinicalTrialSubject {rave_id: $rave_id})
            MATCH (ae:AdverseEvent {ae_body_system: $ae_body_system})
            CREATE (cts)-[r:EXPERIENCED_AE {
                grade: $grade,
                serious: $serious,
                onset_date: $onset_date
            }]->(ae)
        """,
        rave_id=row['rave_id'],
        ae_body_system=row['ae_body_system'],
        grade=int(row['grade']),
        serious=bool(row['serious']),
        onset_date=str(row['onset_date']))
    print(f"   ✅ Loaded adverse event relationships")

def profile_query(driver, query_dict, runs=10):
    """Profile a single query multiple times"""
    times = []
    
    with driver.session() as session:
        # Warm up
        session.run(query_dict['query'])
        
        # Actual profiling
        for _ in range(runs):
            start_time = time.time()
            result = session.run(query_dict['query'])
            # Consume all results to ensure query completes
            _ = list(result)
            end_time = time.time()
            
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds
    
    return {
        'mean': np.mean(times),
        'std': np.std(times),
        'min': np.min(times),
        'max': np.max(times),
        'median': np.median(times),
        'times': times
    }

# ═══════════════════════════════════════════════════════════════
# MAIN PROFILING FUNCTION
# ═══════════════════════════════════════════════════════════════

def run_performance_profiling():
    """Run the complete performance profiling"""
    print("🚀 Starting Memgraph Performance Profiling")
    print("="*60)
    print(f"Test sizes: {TEST_SIZES}")
    print(f"Runs per query: {RUNS_PER_QUERY}")
    print("="*60)
    
    # Connect to Memgraph
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Results storage
    results = {
        'metadata': {
            'test_sizes': TEST_SIZES,
            'runs_per_query': RUNS_PER_QUERY,
            'timestamp': datetime.now().isoformat(),
            'queries': {k: v['description'] for k, v in QUERIES.items()}
        },
        'results': {}
    }
    
    # Run tests for each data size
    for n_patients in TEST_SIZES:
        print(f"\n{'='*60}")
        print(f"📊 Testing with {n_patients} patients")
        print(f"{'='*60}")
        
        # Clear and load data
        clear_database(driver)
        
        if not load_data_for_size(driver, n_patients):
            print(f"❌ Skipping {n_patients} patients due to missing data")
            continue
        
        # Profile each query
        results['results'][n_patients] = {}
        
        for query_key, query_dict in QUERIES.items():
            print(f"\n⏱️  Profiling: {query_dict['name']}")
            
            try:
                profile_results = profile_query(driver, query_dict, RUNS_PER_QUERY)
                results['results'][n_patients][query_key] = profile_results
                
                print(f"   Mean: {profile_results['mean']:.2f} ms")
                print(f"   Std:  {profile_results['std']:.2f} ms")
                print(f"   Range: {profile_results['min']:.2f} - {profile_results['max']:.2f} ms")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results['results'][n_patients][query_key] = None
    
    # Close connection
    driver.close()
    
    # Save results
    results_file = os.path.join(OUTPUT_DIR, f"performance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

# ═══════════════════════════════════════════════════════════════
# VISUALIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def create_performance_plots(results):
    """Create performance visualization plots"""
    print("\n📊 Creating performance plots...")
    
    # Extract data for plotting
    plot_data = {}
    for query_key in QUERIES.keys():
        plot_data[query_key] = {
            'sizes': [],
            'means': [],
            'stds': []
        }
    
    for size, size_results in results['results'].items():
        for query_key, query_results in size_results.items():
            if query_results:
                plot_data[query_key]['sizes'].append(size)
                plot_data[query_key]['means'].append(query_results['mean'])
                plot_data[query_key]['stds'].append(query_results['std'])
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.flatten()
    
    # Plot each query
    for idx, (query_key, query_info) in enumerate(QUERIES.items()):
        ax = axes[idx]
        data = plot_data[query_key]
        
        # Plot with error bars
        ax.errorbar(data['sizes'], data['means'], yerr=data['stds'],
                   marker='o', markersize=8, linewidth=2.5, 
                   capsize=5, capthick=2, label=query_info['name'])
        
        ax.set_xlabel('Number of Patients', fontsize=12, fontweight='bold')
        ax.set_ylabel('Query Time (ms)', fontsize=12, fontweight='bold')
        ax.set_title(query_info['name'], fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')
        ax.set_yscale('log')
        
        # Add value labels
        for x, y in zip(data['sizes'], data['means']):
            if x in [1, 100, 1000, 10000, 20000]:  # Label key points
                ax.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                           xytext=(0,10), ha='center', fontsize=9)
    
    plt.suptitle('Memgraph Query Performance vs Data Size', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    plot_file = os.path.join(OUTPUT_DIR, f"performance_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"✅ Plot saved to: {plot_file}")
    
    # Create summary plot - all queries on one graph
    plt.figure(figsize=(12, 8))
    
    colors = ['#0068B1', '#E83E48', '#00A783', '#FF9800']
    
    for idx, (query_key, query_info) in enumerate(QUERIES.items()):
        data = plot_data[query_key]
        plt.errorbar(data['sizes'], data['means'], yerr=data['stds'],
                    marker='o', markersize=8, linewidth=2.5, 
                    capsize=5, capthick=2, label=query_info['name'],
                    color=colors[idx % len(colors)])
    
    plt.xlabel('Number of Patients', fontsize=14, fontweight='bold')
    plt.ylabel('Query Time (ms)', fontsize=14, fontweight='bold')
    plt.title('Memgraph Query Performance Comparison', fontsize=16, fontweight='bold')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    
    # Save summary plot
    summary_file = os.path.join(OUTPUT_DIR, f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(summary_file, dpi=300, bbox_inches='tight')
    print(f"✅ Summary plot saved to: {summary_file}")
    
    plt.show()

# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Check if test data exists
    missing_data = []
    for size in TEST_SIZES:
        if not os.path.exists(f"test_data_{size}pts"):
            missing_data.append(size)
    
    if missing_data:
        print("❌ Missing test data for sizes:", missing_data)
        print("\nTo generate test data:")
        print("1. Run: python updated_data_generation.py")
        print("2. Choose option 2")
        print("3. Wait for all datasets to be generated")
        sys.exit(1)
    
    # Run profiling
    results = run_performance_profiling()
    
    # Create visualizations
    create_performance_plots(results)
    
    print("\n✅ Performance profiling complete!")
    print(f"📁 Results saved in: {OUTPUT_DIR}/")
    print("\n🎯 Use these results in your presentation to show:")
    print("   - How query performance scales with data size")
    print("   - Which queries are most affected by data growth")
    print("   - The benefits of using a graph database for complex queries")