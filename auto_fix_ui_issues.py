#!/usr/bin/env python3
"""
Automatically fix UI issues in app.py:
1. Remove redundant plot titles
2. Fix text cutoff in plots
3. Improve spacing and layout
"""

import re

print("🔧 Fixing UI issues in your dashboard...")
print("="*60)

# Read current app.py
with open('app.py', 'r') as f:
    content = f.read()

# Backup
with open('app.py.before_ui_fixes', 'w') as f:
    f.write(content)
print("✅ Created backup: app.py.before_ui_fixes")

# ════════════════════════════════════════════════════════════════
# 1. Remove redundant plot titles
# ════════════════════════════════════════════════════════════════

print("\n📋 Removing redundant plot titles...")

# List of plot functions and their titles to remove
plot_titles_to_remove = [
    ('age_distribution', 'Age Distribution'),
    ('sex_distribution', 'Sex Distribution'),
    ('assessment_pie', 'Clinical Assessment Distribution'),
    ('gene_bar', 'Top 10 Mutated Genes'),
    ('allele_fraction_hist', 'Allele Fraction Distribution'),
    ('oncoprint', 'Mutation Landscape'),
    ('protocol_enrollment', 'Protocol Enrollment'),
    ('intervention_dist', 'Intervention Distribution'),
    ('ae_grade_dist', 'Adverse Events by Grade'),
    ('ae_system_dist', 'Adverse Events by System'),
    ('survival_curve', 'Kaplan-Meier Survival Analysis')
]

# Remove ax.set_title() calls
for func_name, title in plot_titles_to_remove:
    # Pattern to match ax.set_title lines
    patterns = [
        f"ax\\.set_title\\(['\"].*{re.escape(title)}.*['\"].*?\\)",
        f"ax\\.set_title\\(f['\"].*{re.escape(title)}.*['\"].*?\\)",
        f"apply_plot_style\\(ax, ['\"].*{re.escape(title)}.*['\"]\\)"
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, "", content)

print("✅ Removed redundant plot titles")

# ════════════════════════════════════════════════════════════════
# 2. Fix adverse events system labels
# ════════════════════════════════════════════════════════════════

print("\n📋 Fixing adverse events system labels...")

# Find the ae_system_dist function
ae_system_pattern = r'def ae_system_dist\(\):.*?(?=\n    @|\n\ndef|\Z)'
ae_system_match = re.search(ae_system_pattern, content, re.DOTALL)

if ae_system_match:
    old_func = ae_system_match.group()
    
    # Create improved version with better labels
    new_func = '''def ae_system_dist():
        fig, ax = plt.subplots(figsize=(10, 6))
        
        system_counts = data['adverse_events']['ae_body_system'].value_counts().head(8)
        
        # Create cleaner, shorter labels
        label_mapping = {
            'Respiratory, thoracic and mediastinal disorders': 'Respiratory',
            'Blood and lymphatic system disorders': 'Blood & Lymphatic',
            'Cardiac disorders': 'Cardiac',
            'Gastrointestinal disorders': 'Gastrointestinal',
            'General disorders and administration site conditions': 'General',
            'Hepatobiliary disorders': 'Hepatobiliary',
            'Immune system disorders': 'Immune System',
            'Infections and infestations': 'Infections',
            'Metabolism and nutrition disorders': 'Metabolism',
            'Musculoskeletal and connective tissue disorders': 'Musculoskeletal',
            'Nervous system disorders': 'Nervous System',
            'Skin and subcutaneous tissue disorders': 'Skin'
        }
        
        # Apply label mapping
        clean_labels = []
        for label in system_counts.index:
            clean_label = label_mapping.get(label, label)
            # Further truncate if still too long
            if 'disorders' in clean_label:
                clean_label = clean_label.replace(' disorders', '')
            if 'system' in clean_label.lower() and clean_label != 'Immune System':
                clean_label = clean_label.replace(' system', '')
            clean_labels.append(clean_label)
        
        ax.barh(range(len(system_counts)), system_counts.values, color='#e74c3c', alpha=0.7)
        ax.set_yticks(range(len(system_counts)))
        ax.set_yticklabels(clean_labels, fontsize=11)
        ax.set_xlabel('Number of Events', fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')
        ax.invert_yaxis()
        
        plt.tight_layout()
        return fig'''
    
    content = content.replace(old_func, new_func)
    print("✅ Fixed adverse events system labels")

# ════════════════════════════════════════════════════════════════
# 3. Fix intervention distribution labels
# ════════════════════════════════════════════════════════════════

print("\n📋 Fixing intervention distribution labels...")

# Pattern to find intervention_dist function
intervention_pattern = r'def intervention_dist\(\):.*?ax\.barh.*?return fig'
intervention_match = re.search(intervention_pattern, content, re.DOTALL)

if intervention_match:
    # Add label shortening
    content = re.sub(
        r"(intervention_counts\.index\[::-1\])",
        "[i.replace(' Therapy', '').replace('Angiogenesis Inhibitors', 'Angiogenesis Inh.') for i in intervention_counts.index[::-1]]",
        content
    )
    print("✅ Fixed intervention labels")

# ════════════════════════════════════════════════════════════════
# 4. Improve figure sizes
# ════════════════════════════════════════════════════════════════

print("\n📋 Improving figure sizes...")

# Increase figure sizes for better spacing
size_replacements = [
    (r'figsize=\(8, 6\)', 'figsize=(9, 6)'),  # Standard plots
    (r'figsize=\(10, 6\)', 'figsize=(10, 7)'),  # Wide plots
    (r'figsize=\(10, 8\)', 'figsize=(12, 8)'),  # Oncoprint
]

for old_size, new_size in size_replacements:
    content = re.sub(old_size, new_size, content)

print("✅ Improved figure sizes")

# ════════════════════════════════════════════════════════════════
# 5. Fix plot spacing
# ════════════════════════════════════════════════════════════════

print("\n📋 Improving plot spacing...")

# Ensure all plots have tight_layout()
if 'plt.tight_layout()' not in content:
    # Add tight_layout before return fig in plot functions
    content = re.sub(
        r'(return fig)',
        r'plt.tight_layout()\n        \1',
        content
    )

# ════════════════════════════════════════════════════════════════
# 6. Fix x-axis label rotation
# ════════════════════════════════════════════════════════════════

print("\n📋 Fixing x-axis label rotation...")

# Fix rotation for better readability
content = re.sub(
    r"rotation=45\)",
    "rotation=45, ha='right')",
    content
)

# ════════════════════════════════════════════════════════════════
# 7. Update oncoprint legend
# ════════════════════════════════════════════════════════════════

print("\n📋 Updating oncoprint legend...")

# Make legend labels shorter
content = re.sub(
    r"'Likely Pathogenic': 'Likely Pathogenic'",
    "'Likely Pathogenic': 'Likely Path.'",
    content
)

# ════════════════════════════════════════════════════════════════
# Write updated file
# ════════════════════════════════════════════════════════════════

with open('app.py', 'w') as f:
    f.write(content)

print("\n✅ UI fixes applied successfully!")
print("\n📋 Changes made:")
print("   - Removed redundant plot titles")
print("   - Fixed adverse events system label cutoff")
print("   - Shortened intervention labels")
print("   - Improved figure sizes")
print("   - Fixed x-axis label rotation")
print("   - Enhanced plot spacing")

print("\n🎯 Next steps:")
print("1. Restart your app: python -m shiny run app.py")
print("2. Check that labels are no longer cut off")
print("3. Verify plot titles aren't duplicated")
print("4. Then apply the professional styling")

print("\n💡 Additional manual improvements:")
print("   - Consider using icons instead of text for some labels")
print("   - Add tooltips for truncated text")
print("   - Use consistent color scheme across all plots")