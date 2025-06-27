#!/usr/bin/env python3
"""
Test script to verify the cursor fix for file uploads
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_sheet_uploader import MultiSheetExcelUploader
from user_service import UserSession
import pandas as pd

def test_upload_fix():
    """Test the upload fix with a simple Excel file."""
    try:
        # Create a test user session
        user_session = UserSession("test@example.com", "test_database")
        
        # Create uploader
        uploader = MultiSheetExcelUploader()
        
        # Test with the existing test file
        file_path = "test_upload.xlsx"
        
        if not os.path.exists(file_path):
            print(f"❌ Test file {file_path} not found")
            return False
        
        print(f"🔄 Testing upload of {file_path}...")
        
        # Try to upload
        result = uploader.upload_file_with_sheets(file_path, user_session)
        
        print(f"📊 Upload result: {result}")
        
        if result.get('success'):
            print("✅ Upload successful!")
            print(f"Tables created: {result.get('tables_created', [])}")
            print(f"Total rows: {result.get('total_rows', 0)}")
            return True
        else:
            print("❌ Upload failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if 'errors' in result:
                print(f"Errors: {result['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_upload_fix()
    sys.exit(0 if success else 1)
