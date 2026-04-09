# Fix Supabase Storage RLS Policies - Assignment Upload Issue

**Error:** `new row violates row-level security policy`

**Cause:** Storage bucket has RLS policies that are too restrictive

**Solution:** Update storage policies to allow authenticated uploads

---

## 🔧 Fix the RLS Policies

### Step 1: Go to Supabase Dashboard
```
https://supabase.com/dashboard/project/gcgiiquwfigfauootsmn/storage/policies
```

### Step 2: Fix Each Bucket (teacher-notes, assignments, submissions)

For each bucket:

#### Bucket: `teacher-notes`

**1. SELECT Policy (Allow Public Read)**
- Click **New policy** → **For SELECT**
- Name: `Allow public read`
- Policy: 
  ```sql
  true
  ```
- Click **Save**

**2. INSERT Policy (Allow Authenticated Upload)**
- Click **New policy** → **For INSERT**
- Name: `Allow authenticated insert`
- Policy:
  ```sql
  auth.uid() is not null
  ```
- Click **Save**

**3. UPDATE Policy (Allow Owner Update)**
- Click **New policy** → **For UPDATE**
- Name: `Allow owner update`
- Policy:
  ```sql
  auth.uid() = owner
  ```
- Click **Save**

#### Bucket: `assignments`

**Apply the same 3 policies as above:**
- SELECT: `true` (public read)
- INSERT: `auth.uid() is not null` (authenticated upload)
- UPDATE: `auth.uid() = owner` (owner can update)

#### Bucket: `submissions`

**Apply the same 3 policies as above:**
- SELECT: `true` (public read)
- INSERT: `auth.uid() is not null` (authenticated upload)
- UPDATE: `auth.uid() = owner` (owner can update)

---

## Alternative: Disable RLS (For Testing)

If you want to quickly test without RLS:

1. Go to **Storage** → Click bucket name
2. Click **Security** tab
3. Toggle **Enable RLS** to OFF
4. **IMPORTANT:** Re-enable after testing!

---

## Quick SQL Fix (If You Have SQL Access)

Run this in Supabase SQL Editor to fix all buckets:

```sql
-- For teacher-notes bucket
CREATE POLICY "Allow public read" ON storage.objects
  FOR SELECT USING (bucket_id = 'teacher-notes');

CREATE POLICY "Allow authenticated insert" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'teacher-notes' AND auth.uid() IS NOT NULL);

CREATE POLICY "Allow owner update" ON storage.objects
  FOR UPDATE USING (bucket_id = 'teacher-notes' AND auth.uid() = owner);

-- For assignments bucket
CREATE POLICY "Allow public read" ON storage.objects
  FOR SELECT USING (bucket_id = 'assignments');

CREATE POLICY "Allow authenticated insert" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'assignments' AND auth.uid() IS NOT NULL);

CREATE POLICY "Allow owner update" ON storage.objects
  FOR UPDATE USING (bucket_id = 'assignments' AND auth.uid() = owner);

-- For submissions bucket
CREATE POLICY "Allow public read" ON storage.objects
  FOR SELECT USING (bucket_id = 'submissions');

CREATE POLICY "Allow authenticated insert" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'submissions' AND auth.uid() IS NOT NULL);

CREATE POLICY "Allow owner update" ON storage.objects
  FOR UPDATE USING (bucket_id = 'submissions' AND auth.uid() = owner);
```

---

## After Fixing Policies

Once you've fixed the RLS policies:

### Test Upload Again
```bash
cd d:\CampusGPT_2.0\tae_model
python test_upload.py
```

Expected output:
```
✅ Test PDF created
✅ Upload successful (teacher notes)
✅ Upload successful (assignment PDF)
✅ Database record created
✅ Verify files in storage: 2 files
```

### Generate Real Assignment
1. Start server: `python run.py`
2. Go to Swagger UI: `http://localhost:7000/docs`
3. POST `/upload-notes`
4. Upload files and generate assignment
5. Check Supabase Storage → Files should appear

---

## 📊 Expected Final State

After properly configured RLS:

```
✅ Public can VIEW files (SELECT)
✅ Authenticated users can UPLOAD (INSERT)
✅ Users can update their own files (UPDATE)
✅ All buckets secure and functional
```

Files should flow:
```
Upload → Storage → Database → Public URL → Download
```

---

## Verification Checklist

- [ ] Went to Supabase Dashboard Storage Policies
- [ ] Added SELECT policy to all 3 buckets
- [ ] Added INSERT policy to all 3 buckets
- [ ] Added UPDATE policy to all 3 buckets
- [ ] Ran test: `python test_upload.py`
- [ ] Test upload succeeded (✅ in all steps)
- [ ] Verified files in Supabase Storage bucket
- [ ] Generated real assignment via API
- [ ] Downloaded assignment PDF from generated URL

---

## Quick Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "violates row-level security policy" | No INSERT policy | Add INSERT policy: `auth.uid() is not null` |
| "Unauthorized" | Missing auth token | Use signed URLs or enable public access |
| "bucket not found" | Wrong bucket name | Use exact name: `teacher-notes`, not `teacher_notes` |
| "File not found after upload" | Upload succeeded but can't download | Check SELECT policy allows public read |

---

**Once RLS is fixed, storage will work perfectly!** 🚀
