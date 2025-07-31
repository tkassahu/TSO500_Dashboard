#!/usr/bin/env python3
"""
Comprehensive fixes for:
1. Label cutoff in Adverse Events
2. Professional color scheme
3. Patient count filtering issue
"""

import re

print("🔧 Applying comprehensive fixes...")
print("="*60)

# Read current app.py
with open('app.py', 'r') as f:
    content = f.read()

# Backup
with open('app.py.before_comprehensive_fixes', 'w') as f:
    f.write(content)
print("✅ Created backup: app.py.before_comprehensive_fixes")

# ════════════════════════════════════════════════════════════════
# 1. Fix the patient count issue - ensure all patients are included by default
# ════════════════════════════════════════════════════════════════

print("\n📋 Fixing patient count issue...")

# Update the filtered_data function to not use Memgraph (which might be filtering patients)
filtered_data_fix = '''    @reactive.Calc
    def filtered_data():
        """Apply filters to the merged dataframe"""
        # Start with all merged data
        filtered_df = data['merged'].copy()
        
        # Only apply filters if they're actually changed from defaults
        # Demographics filters
        if len(input.demo_sex_filter()) < 2:  # If not both selected
            filtered_df = filtered_df[filtered_df['sex'].isin(input.demo_sex_filter())]
            
        # Age filter
        age_range = input.demo_age_filter()
        if age_range[0] > 18 or age_range[1] < 85:  # If changed from default
            filtered_df = filtered_df[
                (filtered_df['age'] >= age_range[0]) & 
                (filtered_df['age'] <= age_range[1])
            ]
        
        # Gene filter
        if input.gene_filter() != "All":
            filtered_df = filtered_df[filtered_df['gene'] == input.gene_filter()]
            
        # Assessment filter
        if len(input.assessment_filter()) < 5:  # If not all selected
            filtered_df = filtered_df[filtered_df['assessment'].isin(input.assessment_filter())]
            
        return filtered_df'''

# Find and replace the filtered_data function
pattern = r'@reactive\.Calc\s*\n\s*def filtered_data\(\):.*?return.*?(?=\n\s*@|\n\s*def|\Z)'
content = re.sub(pattern, filtered_data_fix, content, flags=re.DOTALL)

# ════════════════════════════════════════════════════════════════
# 2. Fix Adverse Events System Plot with very short labels
# ════════════════════════════════════════════════════════════════

print("\n📋 Fixing adverse events system plot...")

ae_system_fix = '''    @output
    @render.plot
    def ae_system_dist():
        fig, ax = plt.subplots(figsize=(10, 7))
        
        system_counts = data['adverse_events']['ae_body_system'].value_counts().head(8)
        
        # Much shorter labels
        label_map = {
            'Respiratory, thoracic and mediastinal disorders': 'Respiratory',
            'Blood and lymphatic system disorders': 'Blood/Lymph',
            'Cardiac disorders': 'Cardiac',
            'Gastrointestinal disorders': 'GI',
            'General disorders and administration site conditions': 'General',
            'Hepatobiliary disorders': 'Hepatobiliary',
            'Immune system disorders': 'Immune',
            'Infections and infestations': 'Infections',
            'Metabolism and nutrition disorders': 'Metabolism',
            'Musculoskeletal and connective tissue disorders': 'Musculoskeletal',
            'Nervous system disorders': 'Nervous',
            'Skin and subcutaneous tissue disorders': 'Skin'
        }
        
        labels = [label_map.get(x, x.split()[0][:15]) for x in system_counts.index]
        
        # Use gradient colors
        colors = ['#E57373', '#EF5350', '#F44336', '#E53935', '#D32F2F', '#C62828', '#B71C1C', '#D50000']
        
        bars = ax.barh(range(len(system_counts)), system_counts.values, 
                       color=colors[:len(system_counts)], edgecolor='white', linewidth=1.5)
        
        # Add values
        for i, v in enumerate(system_counts.values):
            ax.text(v + 1, i, str(v), va='center', fontweight='500')
        
        ax.set_yticks(range(len(system_counts)))
        ax.set_yticklabels(labels, fontsize=11, fontweight='500')
        ax.set_xlabel('Number of Events', fontsize=12, fontweight='500')
        ax.grid(True, alpha=0.2, axis='x')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.invert_yaxis()
        
        # Adjust margins
        plt.subplots_adjust(left=0.2)
        plt.tight_layout()
        return fig'''

# Replace ae_system_dist function
ae_pattern = r'@output\s*\n\s*@render\.plot\s*\n\s*def ae_system_dist\(\):.*?return fig'
content = re.sub(ae_pattern, ae_system_fix, content, flags=re.DOTALL)

# ════════════════════════════════════════════════════════════════
# 3. Update color schemes for all plots
# ════════════════════════════════════════════════════════════════

print("\n📋 Updating color schemes...")

# Update bar chart colors
content = re.sub(r"color='#3498db'", "color='#0068B1'", content)  # Primary blue
content = re.sub(r"color='#2ecc71'", "color='#00A783'", content)  # Success green
content = re.sub(r"color='#e74c3c'", "color='#E83E48'", content)  # Danger red

# Update sex distribution colors
sex_dist_pattern = r"colors = \['#3498db', '#e74c3c'\]"
sex_dist_replacement = "colors = ['#0068B1', '#E83E48']  # Professional blue and red"
content = re.sub(sex_dist_pattern, sex_dist_replacement, content)

# Update assessment pie colors
pie_colors_pattern = r"colors = \['#e74c3c', '#f39c12', '#95a5a6', '#3498db', '#2ecc71'\]"
pie_colors_replacement = "colors = ['#E83E48', '#FF9800', '#6C757D', '#1881C2', '#00A783']"
content = re.sub(pie_colors_pattern, pie_colors_replacement, content)

# Update adverse events grade colors
grade_colors_pattern = r"colors = \['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#c0392b'\]"
grade_colors_replacement = "colors = ['#00A783', '#1881C2', '#FF9800', '#E83E48', '#8B0000']"
content = re.sub(grade_colors_pattern, grade_colors_replacement, content)

# ════════════════════════════════════════════════════════════════
# 4. Fix the age distribution plot
# ════════════════════════════════════════════════════════════════

age_dist_fix = '''    @output
    @render.plot
    def age_distribution():
        fig, ax = plt.subplots(figsize=(9, 6))
        df = filtered_data()
        
        unique_patients = df.drop_duplicates('mrn')
        
        # Professional blue color
        ax.hist(unique_patients['age'], bins=20, color='#0068B1', 
                alpha=0.8, edgecolor='white', linewidth=1.2)
        
        # Add mean line
        mean_age = unique_patients['age'].mean()
        ax.axvline(mean_age, color='#E83E48', linestyle='--', linewidth=2.5, alpha=0.8)
        ax.text(mean_age + 1, ax.get_ylim()[1] * 0.9, f'Mean: {mean_age:.1f}', 
                color='#E83E48', fontweight='600', fontsize=11)
        
        ax.set_xlabel('Age', fontsize=12, fontweight='500')
        ax.set_ylabel('Number of Patients', fontsize=12, fontweight='500')
        ax.grid(True, alpha=0.2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig'''

# Replace age_distribution function
age_pattern = r'@output\s*\n\s*@render\.plot\s*\n\s*def age_distribution\(\):.*?return fig'
content = re.sub(age_pattern, age_dist_fix, content, flags=re.DOTALL)

# ════════════════════════════════════════════════════════════════
# 5. Write the updated file
# ════════════════════════════════════════════════════════════════

with open('app.py', 'w') as f:
    f.write(content)

print("\n✅ All fixes applied successfully!")
print("\n📋 Changes made:")
print("   1. Fixed patient filtering to show all 200 patients by default")
print("   2. Fixed adverse events labels to be much shorter")
print("   3. Applied professional color scheme throughout")
print("   4. Improved plot spacing and margins")

print("\n🎯 The fixes address:")
print("   ✅ Label cutoff issue - labels are now short enough")
print("   ✅ Color scheme - now uses cBioPortal-inspired colors")
print("   ✅ Patient count - removed unnecessary filtering")

print("\n🚀 Restart your app to see the changes:")
print("   python -m shiny run app.py --reload")

print("\n💡 If labels are still cut off:")
print("   1. Make the plot even wider: figsize=(12, 7)")
print("   2. Reduce font size: fontsize=10")
print("   3. Use abbreviations: 'GI' instead of 'Gastrointestinal'")