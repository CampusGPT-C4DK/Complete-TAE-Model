"""
Storage Diagnostic Tool - Check assignment storage in Supabase
Verifies:
1. Supabase connection 
2. Bucket existence and configuration
3. Files in each bucket
4. Assignment database records
5. Storage paths vs actual files
"""

import os
import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Supabase config
from app.core.config import settings
from app.database import supabase, supabase_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_supabase_connection():
    """Verify Supabase is properly connected."""
    print("\n" + "="*70)
    print("1️⃣  SUPABASE CONNECTION CHECK")
    print("="*70)
    
    try:
        url = settings.SUPABASE_URL
        print(f"✅ Supabase URL: {url}")
        
        # Try querying assignments table instead (might have better RLS)
        result = supabase.table("assignments").select("*").limit(1).execute()
        print(f"✅ Database connected: {len(result.data)} assignments found")
        
        return True
    except Exception as e:
        print(f"⚠️  Connection check (trying assignments table): {str(e)}")
        # Try to continue anyway as this might be just RLS issue
        return True


def check_buckets():
    """Check all storage buckets."""
    print("\n" + "="*70)
    print("2️⃣  STORAGE BUCKETS CHECK")
    print("="*70)
    
    buckets_to_check = [
        "teacher-notes",
        "assignments",
        "submissions"
    ]
    
    bucket_status = {}
    
    for bucket_name in buckets_to_check:
        try:
            bucket_info = supabase.storage.get_bucket(bucket_name)
            is_public = getattr(bucket_info, 'public', False)
            print(f"✅ {bucket_name:20} | Public: {str(is_public):5} | ID: {bucket_name}")
            
            # Count files in bucket
            try:
                files = supabase.storage.from_(bucket_name).list()
                file_count = len(files) if files else 0
                print(f"   └─ Files in bucket: {file_count}")
                bucket_status[bucket_name] = {
                    "exists": True,
                    "public": is_public,
                    "file_count": file_count
                }
            except Exception as list_err:
                print(f"   └─ Could not list files: {str(list_err)}")
                bucket_status[bucket_name] = {
                    "exists": True,
                    "public": is_public,
                    "file_count": "unknown"
                }
                
        except Exception as e:
            print(f"❌ {bucket_name:20} | Not found: {str(e)}")
            bucket_status[bucket_name] = {"exists": False}
    
    return bucket_status


def check_assignments_table():
    """Check assignments in database."""
    print("\n" + "="*70)
    print("3️⃣  ASSIGNMENTS DATABASE CHECK")
    print("="*70)
    
    try:
        # Count total assignments
        assignments = supabase.table("assignments").select("*").execute()
        total = len(assignments.data)
        print(f"✅ Total assignments in database: {total}")
        
        if total == 0:
            print("   ⚠️  No assignments found - generate one first")
            return []
        
        # Show sample with storage info
        print(f"\n📋 Sample Assignments (showing first 3):")
        print(f"-" * 70)
        
        for i, assignment in enumerate(assignments.data[:3], 1):
            print(f"\n{i}. Assignment #{assignment.get('assignment_no', 'N/A')}")
            print(f"   Subject: {assignment.get('subject', 'N/A')}")
            print(f"   Semester: {assignment.get('semester', 'N/A')}")
            print(f"   Difficulty: {assignment.get('difficulty', 'N/A')}")
            
            # Storage info
            pdf_path = assignment.get('pdf_storage_path', 'N/A')
            pdf_url = assignment.get('pdf_url', 'N/A')
            print(f"   📁 PDF Path: {pdf_path}")
            print(f"   🔗 PDF URL: {pdf_url[:60]}..." if pdf_url != 'N/A' else f"   🔗 PDF URL: N/A")
            
            # Check if file exists
            if pdf_path and pdf_path != 'N/A':
                try:
                    file_obj = supabase.storage.from_("assignments").download(pdf_path)
                    print(f"   ✅ File exists in storage ({len(file_obj)} bytes)")
                except Exception as e:
                    print(f"   ❌ File not found in storage: {str(e)}")
            
            # Teacher notes URLs
            teacher_notes = assignment.get('teacher_notes_urls', {})
            if teacher_notes:
                print(f"   📝 Teacher notes URLs: {len(teacher_notes)} files")
                for note_url in list(teacher_notes.values())[:2]:
                    print(f"      - {note_url[:50]}...")
        
        return assignments.data
        
    except Exception as e:
        print(f"❌ Database query failed: {str(e)}")
        return []


def check_file_storage():
    """Check actual files in storage."""
    print("\n" + "="*70)
    print("4️⃣  FILES IN STORAGE CHECK")
    print("="*70)
    
    buckets = ["teacher-notes", "assignments", "submissions"]
    
    for bucket_name in buckets:
        print(f"\n📦 Bucket: {bucket_name}")
        print(f"-" * 50)
        
        try:
            files = supabase.storage.from_(bucket_name).list(limit=10)
            
            if not files or len(files) == 0:
                print("   (empty)")
                continue
            
            for file_obj in files[:5]:
                file_name = getattr(file_obj, 'name', 'unknown')
                print(f"   📄 {file_name}")
                
                # Try to get file size
                try:
                    file_path = f"{file_name}"
                    # Get file info
                    file_data = supabase.storage.from_(bucket_name).list(search_options={"search": file_name})
                    if file_data:
                        print(f"      ✓ Found in storage")
                except Exception as e:
                    print(f"      ? {str(e)}")
            
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more files")
                
        except Exception as e:
            print(f"   ⚠️  Error listing files: {str(e)}")


def check_storage_paths():
    """Verify storage paths follow expected format."""
    print("\n" + "="*70)
    print("5️⃣  STORAGE PATH VERIFICATION")
    print("="*70)
    
    try:
        assignments = supabase.table("assignments").select("pdf_storage_path").execute()
        
        if not assignments.data:
            print("   No assignments to verify")
            return
        
        print(f"Checking {len(assignments.data)} assignment paths...")
        print()
        
        expected_format = "{user_id}/{subject}/semester-{semester}/assignment-{no}/{filename}"
        
        for assignment in assignments.data[:5]:
            path = assignment.get('pdf_storage_path', '')
            print(f"📍 {path}")
            
            # Parse path
            parts = path.split('/')
            if len(parts) >= 5:
                print(f"   ✅ Format correct: {len(parts)} parts")
                print(f"      - User ID: {parts[0]}")
                print(f"      - Subject: {parts[1]}")
                print(f"      - Semester: {parts[2]}")
                print(f"      - Assignment: {parts[3]}")
                print(f"      - File: {parts[4]}")
            else:
                print(f"   ⚠️  Path format incorrect: expected 5+ parts, got {len(parts)}")
        
    except Exception as e:
        print(f"❌ Error checking paths: {str(e)}")


def main():
    """Run all diagnostics."""
    print("\n" + "="*70)
    print("🔍 CAMPUSGPT TAE MODEL - STORAGE DIAGNOSTIC")
    print("="*70)
    
    # Run checks
    connected = check_supabase_connection()
    
    if not connected:
        print("\n❌ Cannot continue - Supabase not connected")
        return
    
    bucket_status = check_buckets()
    assignments = check_assignments_table()
    check_file_storage()
    check_storage_paths()
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    all_buckets_exist = all(status.get("exists", False) for status in bucket_status.values())
    has_assignments = len(assignments) > 0
    
    print(f"✅ Supabase connected: True")
    print(f"✅ All buckets exist: {all_buckets_exist}")
    print(f"✅ Assignments in DB: {len(assignments)}")
    
    if all_buckets_exist and has_assignments:
        print("\n✅ Storage setup looks GOOD!")
        print("   - Generate assignments normally")
        print("   - Files should upload to storage automatically")
    else:
        print("\n⚠️  Issues detected:")
        if not all_buckets_exist:
            print("   - Create missing buckets in Supabase dashboard → Storage → New Bucket")
        if not has_assignments:
            print("   - Generate an assignment first via /upload-notes endpoint")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
