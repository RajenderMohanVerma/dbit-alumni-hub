#!/usr/bin/env python
"""Quick test to verify app loads without errors"""

try:
    from app import app, init_db
    print("✓ App imported successfully")
    
    # Initialize database
    with app.app_context():
        init_db()
        print("✓ Database initialized successfully")
    
    print("\n✓ All checks passed! You can now run: python app.py")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
