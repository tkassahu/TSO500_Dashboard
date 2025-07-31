#!/usr/bin/env python3
"""
Script to apply professional styling to your existing app.py
This will update colors, fonts, and styling to match cBioPortal
"""

import re

print("🎨 Applying professional styling to your dashboard...")
print("="*60)

# Read current app.py
with open('app.py', 'r') as f:
    content = f.read()

# Backup
with open('app.py.before_styling', 'w') as f:
    f.write(content)
print("✅ Created backup: app.py.before_styling")

# ════════════════════════════════════════════════════════════════
# 1. Add color palette after imports
# ════════════════════════════════════════════════════════════════

color_palette = '''
# Professional color palette (cBioPortal inspired)
COLORS = {
    'primary': '#0068B1',      # cBioPortal blue
    'secondary': '#58B9E5',    # Light blue
    'success': '#00A783',      # Teal/green
    'danger': '#E83E48',       # Red
    'warning': '#FF9800',      # Orange
    'info': '#1881C2',         # Info blue
    'dark': '#2C3E50',         # Dark gray
    'light': '#F8F9FA',        # Light gray
    'white': '#FFFFFF',
    'gray': '#6C757D',
    'border': '#DEE2E6'
}

# Chart colors for consistency
CHART_COLORS = ['#0068B1', '#58B9E5', '#00A783', '#FF9800', '#E83E48', '#9C27B0', '#795548', '#607D8B']

'''

# Find where to insert (after driver initialization)
insert_pos = content.find('driver = GraphDatabase.driver')
if insert_pos != -1:
    # Find the end of the line
    line_end = content.find('\n', insert_pos)
    if line_end != -1:
        # Insert color palette
        content = content[:line_end+1] + color_palette + content[line_end+1:]
        print("✅ Added color palette")

# ════════════════════════════════════════════════════════════════
# 2. Update the header gradient
# ════════════════════════════════════════════════════════════════

# Find and replace the header gradient
header_pattern = r'background: linear-gradient\(135deg, #3498db, #2c3e50\);'
header_replacement = 'background: linear-gradient(135deg, #0068B1 0%, #1881C2 100%);'
content = re.sub(header_pattern, header_replacement, content)

# Update header padding
content = re.sub(r'padding: 30px;', 'padding: 40px 24px;', content)

# ════════════════════════════════════════════════════════════════
# 3. Update summary_card function
# ════════════════════════════════════════════════════════════════

new_summary_card = '''def summary_card(title, value, icon="📊", color="primary"):
    """Create a professional summary card"""
    color_map = {
        'primary': '#0068B1',
        'secondary': '#58B9E5',
        'success': '#00A783',
        'danger': '#E83E48',
        'warning': '#FF9800',
        'info': '#1881C2'
    }
    border_color = color_map.get(color, '#0068B1')
    
    return ui.div(
        ui.div(
            ui.span(icon, style="font-size: 2rem; margin-right: 16px; opacity: 0.8;"),
            ui.h6(title, style="margin: 0; font-weight: 400; color: #6c757d; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.5px;"),
            style="display: flex; align-items: center; margin-bottom: 16px;"
        ),
        ui.h3(str(value), style="margin: 0; color: #2c3e50; font-weight: 600; font-size: 2rem;"),
        class_="summary-card",
        style=f"""
            background: white;
            padding: 28px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 4px solid {border_color};
            transition: all 0.3s ease;
            height: 100%;
            position: relative;
            overflow: hidden;
        """
    )'''

# Find and replace summary_card function
summary_pattern = r'def summary_card\(.*?\):\s*""".*?""".*?return ui\.div\(.*?\n    \)'
if re.search(summary_pattern, content, re.DOTALL):
    content = re.sub(summary_pattern, new_summary_card, content, flags=re.DOTALL)
    print("✅ Updated summary_card function")

# ════════════════════════════════════════════════════════════════
# 4. Update CSS styling
# ════════════════════════════════════════════════════════════════

# Professional font import
font_import = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');"

# Update body font
content = re.sub(
    r"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
    "font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
    content
)

# Update colors
color_replacements = [
    ('#3498db', '#0068B1'),  # Primary blue
    ('#2c3e50', '#2C3E50'),  # Dark
    ('#ecf0f1', '#DEE2E6'),  # Border
    ('#f5f7fa', '#F8F9FA'),  # Light background
    ('#e74c3c', '#E83E48'),  # Danger/Red
    ('#2ecc71', '#00A783'),  # Success/Green
]

for old_color, new_color in color_replacements:
    content = content.replace(old_color, new_color)

print("✅ Updated color scheme")

# ════════════════════════════════════════════════════════════════
# 5. Add plot styling helper if not exists
# ════════════════════════════════════════════════════════════════

plot_style_helper = '''
def apply_plot_style(ax, title=""):
    """Apply consistent styling to plots"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)
    ax.spines['left'].set_color('#6C757D')
    ax.spines['bottom'].set_color('#6C757D')
    ax.tick_params(axis='both', which='major', labelsize=10, colors='#6C757D')
    ax.grid(True, alpha=0.1, linestyle='-', linewidth=0.5)
    ax.set_facecolor('white')
    if title:
        ax.set_title(title, fontsize=14, fontweight='600', color='#2C3E50', pad=15)
'''

# Add before server function if not exists
if 'def apply_plot_style' not in content:
    server_pos = content.find('def server(')
    if server_pos != -1:
        content = content[:server_pos] + plot_style_helper + '\n' + content[server_pos:]
        print("✅ Added plot styling helper")

# ════════════════════════════════════════════════════════════════
# 6. Update nav styling
# ════════════════════════════════════════════════════════════════

# Update nav-link styling
nav_style_updates = [
    ('.nav-link.active {', '.nav-link.active {\n                color: #0068B1 !important;\n                border-bottom: 3px solid #0068B1;'),
    ('padding: 12px 24px !important;', 'padding: 16px 24px !important;'),
    ('font-weight: 500;', 'font-weight: 500;\n                text-transform: uppercase;\n                letter-spacing: 0.5px;'),
]

for old, new in nav_style_updates:
    content = content.replace(old, new)

print("✅ Updated navigation styling")

# ════════════════════════════════════════════════════════════════
# 7. Write updated file
# ════════════════════════════════════════════════════════════════

with open('app.py', 'w') as f:
    f.write(content)

print("\n✅ Professional styling applied successfully!")
print("\n📋 Changes made:")
print("   - Added cBioPortal-inspired color palette")
print("   - Updated header gradient and styling")
print("   - Enhanced summary card design")
print("   - Improved navigation tabs")
print("   - Added plot styling helper")
print("   - Updated color scheme throughout")

print("\n🎯 Additional manual improvements you can make:")
print("   1. Update your plot colors to use CHART_COLORS array")
print("   2. Add hover effects to cards")
print("   3. Use the apply_plot_style() function in your plots")
print("   4. Update sidebar width to 300px")
print("   5. Add color parameter to summary_card calls:")
print("      - summary_card('Title', value, '📊', 'primary')")
print("      - Colors: primary, secondary, success, danger, warning, info")

print("\n🚀 Restart your app to see the changes:")
print("   python -m shiny run app.py")