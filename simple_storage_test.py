"""
Simple Storage Test - Direct bucket access verification
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from supabase import create_client

print("="*70)
print("🧪 SIMPLE STORAGE TEST")
print("="*70)

# Create client directly
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

print(f"\n✅ Supabase URL: {settings.SUPABASE_URL}")
print(f"✅ Anon Key: {settings.SUPABASE_KEY[:30]}...")
print(f"✅ Service Key: {settings.SUPABASE_SERVICE_KEY[:30]}...")

print("\n" + "-"*70)
print("Testing bucket access...")
print("-"*70)

buckets_to_test = ["teacher-notes", "assignments", "submissions"]

for bucket_name in buckets_to_test:
    print(f"\n📦 Testing: {bucket_name}")
    
    # Test 1: Try to list files with anon key
    try:
        files = supabase.storage.from_(bucket_name).list()
        print(f"   ✅ Anon access (list): {len(files) if files else 0} files")
    except Exception as e:
        print(f"   ❌ Anon access failed: {str(e)[:50]}")
    
    # Test 2: Try to list files with service role key
    try:
        files = supabase_admin.storage.from_(bucket_name).list()
        print(f"   ✅ Admin access (list): {len(files) if files else 0} files")
    except Exception as e:
        print(f"   ❌ Admin access failed: {str(e)[:50]}")
    
    # Test 3: Try to get public URL
    try:
        test_path = f"test/{bucket_name}/test.txt"
        url = supabase.storage.from_(bucket_name).get_public_url(test_path)
        print(f"   ✅ Public URL generation: Works")
        print(f"      URL: {url[:60]}...")
    except Exception as e:
        print(f"   ❌ Public URL failed: {str(e)[:50]}")

print("\n" + "="*70)
print("📝 COMMON ISSUES & FIXES")
print("="*70)

print("""
If buckets are NOT accessible:

1. ✅ Buckets showing in screenshot but API says "not found"
   Solution: Use exact bucket names (case-sensitive!)
   
2. ✅ Getting 404 errors
   Solution: Check bucket policies in Supabase → Storage → Policies
   
3. ✅ Upload fails even though bucket exists
   Solution: Check RLS policies on storage buckets
   
4. ✅ Files not showing after upload
   Solution: Verify storage path matches database records

NEXT STEPS:
1. Create a test file upload to verify storage works
2. Check Supabase dashboard for:
   - Bucket policies (should allow public access if public=true)
   - RLS policies on storage
   - CORS settings if needed
""")

print("="*70)
