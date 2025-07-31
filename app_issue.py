#!/usr/bin/env python3
"""Diagnose why app.py isn't starting"""

import sys
import ast

print("🔍 Diagnosing app.py issues...")
print("="*60)

# 1. Check if file ends with app creation
print("\n1. Checking last lines of app.py:")
with open('app.py', 'r') as f:
    lines = f.readlines()

# Show last 10 non-empty lines
non_empty = [(i, line.rstrip()) for i, line in enumerate(lines, 1) if line.strip()]
print("\nLast 10 non-empty lines:")
for line_num, line in non_empty[-10:]:
    print(f"{line_num}: {line[:80]}{'...' if len(line) > 80 else ''}")

# Check for app = App(...)
app_found = False
app_line_num = None
for i, line in enumerate(lines, 1):
    if 'app = App(' in line:
        app_found = True
        app_line_num = i
        break

if app_found:
    print(f"\n✅ Found 'app = App(...)' at line {app_line_num}")
else:
    print("\n❌ MISSING: app = App(app_ui, server)")
    print("   This MUST be at the end of the file!")

# 2. Try to parse the file
print("\n2. Checking for syntax errors:")
try:
    with open('app.py', 'r') as f:
        ast.parse(f.read())
    print("✅ No syntax errors")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
    print(f"   {e.text}")
    print(f"   {' ' * (e.offset - 1)}^")

# 3. Try importing
print("\n3. Testing import:")
try:
    # Remove app from sys.modules if it exists
    if 'app' in sys.modules:
        del sys.modules['app']
    
    import app
    print("✅ Import successful")
    
    # Check what's in the module
    if hasattr(app, 'app'):
        print("✅ app object exists")
    else:
        print("❌ No 'app' object in module")
        attrs = [x for x in dir(app) if not x.startswith('_')]
        print(f"   Available: {attrs[:10]}")
        
except Exception as e:
    print(f"❌ Import failed: {e}")

# 4. Check if __name__ == "__main__" block exists
print("\n4. Checking for main block:")
main_block = any('if __name__' in line for line in lines)
if main_block:
    print("⚠️  Found __name__ == '__main__' block")
    print("   This might be interfering with Shiny")

# 5. Provide the fix
print("\n" + "="*60)
print("\n📋 TO FIX:")

if not app_found:
    print("\nAdd these lines at the VERY END of app.py:")
    print("-"*40)
    print("# Create the app")
    print("app = App(app_ui, server)")
    print("-"*40)
    
print("\nAlso make sure:")
print("1. There's no code after 'app = App(app_ui, server)'")
print("2. Remove any 'if __name__ == \"__main__\":' blocks")
print("3. The file ends with just the app creation line")

# 6. Create a minimal test
print("\n" + "="*60)
print("\n🧪 Creating minimal test app...")

test_code = '''from shiny import App, ui, render

app_ui = ui.page_fluid(
    ui.h1("Test - If you see this, Shiny works!")
)

def server(input, output, session):
    pass

app = App(app_ui, server)
'''

with open('test_minimal.py', 'w') as f:
    f.write(test_code)
    
print("✅ Created test_minimal.py")
print("\nTry: python -m shiny run test_minimal.py --port 8001")
print("If this works, the issue is with app.py structure")