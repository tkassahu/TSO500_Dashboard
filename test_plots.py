import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd

# Set matplotlib to use Agg backend
matplotlib.use('Agg')

# Test data
np.random.seed(42)
allele_fractions = np.random.beta(2, 5, 1000)

# Create test plot
fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
ax.hist(allele_fractions, bins=30, color='#00A783', alpha=0.7, edgecolor='black')
ax.set_xlabel('Allele Fraction', fontsize=11)
ax.set_ylabel('Count', fontsize=11)
ax.grid(True, alpha=0.3)

# Try different saving methods
print("Testing different save methods...")

# Method 1: Standard save
fig.savefig('test_plot_standard.png')
print("Saved: test_plot_standard.png")

# Method 2: Tight layout
fig.tight_layout()
fig.savefig('test_plot_tight.png')
print("Saved: test_plot_tight.png")

# Method 3: bbox_inches='tight'
fig.savefig('test_plot_bbox_tight.png', bbox_inches='tight', pad_inches=0.3)
print("Saved: test_plot_bbox_tight.png")

# Method 4: Manual adjustment
fig.subplots_adjust(left=0.15, right=0.98, top=0.95, bottom=0.18)
fig.savefig('test_plot_manual.png')
print("Saved: test_plot_manual.png")

plt.close(fig)

# Create oncoprint test
fig2, ax2 = plt.subplots(figsize=(10, 5), dpi=100)

# Create dummy data
genes = ['TP53', 'KRAS', 'EGFR', 'BRAF', 'PIK3CA']
patients = [f'P{i}' for i in range(20)]

# Plot dummy oncoprint
for i, gene in enumerate(genes):
    for j, patient in enumerate(patients):
        color = np.random.choice(['#e74c3c', '#f39c12', '#95a5a6', '#3498db', '#2ecc71'])
        rect = plt.Rectangle((j, i), 1, 1, facecolor=color, edgecolor='black', linewidth=0.5)
        ax2.add_patch(rect)

ax2.set_xlim(0, len(patients))
ax2.set_ylim(0, len(genes))
ax2.set_xticks(range(len(patients)))
ax2.set_xticklabels(patients, rotation=45, ha='right', fontsize=8)
ax2.set_yticks(range(len(genes)))
ax2.set_yticklabels(genes, fontsize=10)
ax2.set_xlabel('Patients', fontsize=11)
ax2.set_ylabel('Genes', fontsize=11)

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#e74c3c', label='Pathogenic'),
    Patch(facecolor='#f39c12', label='Likely Path.'),
    Patch(facecolor='#95a5a6', label='VUS'),
    Patch(facecolor='#3498db', label='Likely Benign'),
    Patch(facecolor='#2ecc71', label='Benign')
]
ax2.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9)

# Save with different methods
fig2.tight_layout()
fig2.subplots_adjust(right=0.8)
fig2.savefig('test_oncoprint_standard.png')
print("Saved: test_oncoprint_standard.png")

fig2.savefig('test_oncoprint_bbox_tight.png', bbox_inches='tight', pad_inches=0.3)
print("Saved: test_oncoprint_bbox_tight.png")

plt.close(fig2)

print("\nPlease check the generated PNG files to see which method works best.")
print("If all plots look good, the issue is with Shiny's rendering.")
print("If plots are cut off in the PNG files, the issue is with matplotlib settings.")