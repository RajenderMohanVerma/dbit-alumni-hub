#!/usr/bin/env python
"""
Test CSV download functionality
Run this while the Flask app is running
"""

import requests
import json
from requests.auth import HTTPBasicAuth

# Test credentials (you may need to update these)
BASE_URL = "http://127.0.0.1:5000"

# First, login to get session
session = requests.Session()

# Test data
login_data = {
    'username': 'admin',
    'password': 'admin123'  # Change this to actual admin password
}

print("=" * 60)
print("Testing CSV Download Functionality")
print("=" * 60)

# Try to login first
print("\n1. Attempting to login as admin...")
login_response = session.post(f"{BASE_URL}/login", data=login_data)

if login_response.status_code == 200:
    print("✅ Login successful!")
    
    # Test student CSV download
    print("\n2. Testing Student CSV download...")
    student_response = session.get(f"{BASE_URL}/api/download-csv/student")
    
    if student_response.status_code == 200:
        print("✅ Student CSV download SUCCESS!")
        print(f"   Content-Type: {student_response.headers.get('Content-Type')}")
        print(f"   Content-Disposition: {student_response.headers.get('Content-Disposition')}")
        print(f"   Data size: {len(student_response.content)} bytes")
        print(f"   First 200 chars: {student_response.text[:200]}")
    else:
        print(f"❌ Student CSV download FAILED! Status: {student_response.status_code}")
        print(f"   Response: {student_response.text[:500]}")
    
    # Test alumni CSV download
    print("\n3. Testing Alumni CSV download...")
    alumni_response = session.get(f"{BASE_URL}/api/download-csv/alumni")
    
    if alumni_response.status_code == 200:
        print("✅ Alumni CSV download SUCCESS!")
        print(f"   Content-Type: {alumni_response.headers.get('Content-Type')}")
        print(f"   Data size: {len(alumni_response.content)} bytes")
    else:
        print(f"❌ Alumni CSV download FAILED! Status: {alumni_response.status_code}")
    
    # Test faculty CSV download
    print("\n4. Testing Faculty CSV download...")
    faculty_response = session.get(f"{BASE_URL}/api/download-csv/faculty")
    
    if faculty_response.status_code == 200:
        print("✅ Faculty CSV download SUCCESS!")
        print(f"   Data size: {len(faculty_response.content)} bytes")
    else:
        print(f"❌ Faculty CSV download FAILED! Status: {faculty_response.status_code}")
    
    # Test all users CSV download
    print("\n5. Testing All Users CSV download...")
    all_response = session.get(f"{BASE_URL}/api/download-csv/all")
    
    if all_response.status_code == 200:
        print("✅ All Users CSV download SUCCESS!")
        print(f"   Data size: {len(all_response.content)} bytes")
    else:
        print(f"❌ All Users CSV download FAILED! Status: {all_response.status_code}")
        
else:
    print(f"❌ Login failed! Status: {login_response.status_code}")
    print(f"   Response: {login_response.text[:500]}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
