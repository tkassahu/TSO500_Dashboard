#!/usr/bin/env python3
"""Run the Shiny app with proper error handling"""

import sys
import subprocess

print("🚀 Starting Clinical Data Dashboard...")
print("="*60)

# First check if app.py exists
import os
if not os.path.exists('app.py'):
    print("❌ app.py not found in current directory!")
    print(f"📁 Current directory: {os.getcwd()}")
    print("\nFiles in current directory:")
    for f in os.listdir('.'):
        if f.endswith('.py'):
            print(f"  - {f}")
    sys.exit(1)

print("✅ Found app.py")

# Try to run with shiny command
print("\n🔄 Attempting to start Shiny server...")
print("="*60)

try:
    # Run shiny with explicit output
    result = subprocess.run(
        [sys.executable, "-m", "shiny", "run", "app.py", "--port", "8000"],
        capture_output=False,  # Show output directly
        text=True
    )
    
except KeyboardInterrupt:
    print("\n\n⏹️  Dashboard stopped by user")
except Exception as e:
    print(f"\n❌ Error running app: {e}")
    print("\nTrying alternative method...")
    
    # Try running directly
    try:
        subprocess.run([sys.executable, "app.py"])
    except Exception as e2:
        print(f"❌ Alternative method also failed: {e2}")
        
        print("\n📋 Troubleshooting steps:")
        print("1. Make sure Shiny is installed: pip install shiny")
        print("2. Check if all data files exist: python check_data_files.py")
        print("3. Test Memgraph connection: python test_memgraph_connection.py")
        print("4. Check imports: python test_app_imports.py")