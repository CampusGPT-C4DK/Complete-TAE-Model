# 🚀 TAE Model - Pre-Launch Checklist

**Quick verification before going live**

---

## ✅ Database Setup

- [ ] Opened Supabase SQL Editor
- [ ] Copied SUPABASE_SCHEMA.sql
- [ ] Executed the entire script
- [ ] Verified: 8 tables created
- [ ] Verified: 2 views created
- [ ] Verified: All indexes present

**Tables to verify in Supabase Dashboard**:
```
✓ public.faculty_metadata
✓ public.assignments
✓ public.submissions
✓ public.evaluations
✓ public.answer_comparisons
✓ public.audit_log
✓ public.notification_preferences
✓ public.system_config
```

---

## ✅ Storage Setup

- [ ] Created bucket: `teacher-notes` (PRIVATE)
- [ ] Created bucket: `assignments` (PRIVATE)
- [ ] Created bucket: `submissions` (PRIVATE)

**Verify in Supabase Dashboard → Storage → Files**:
```
Files showing:
├── teacher-notes     (PRIVATE)
├── assignments       (PRIVATE)
└── submissions       (PRIVATE)
```

---

## ✅ Environment Configuration

- [ ] .env file contains SUPABASE_URL
- [ ] .env file contains SUPABASE_KEY
- [ ] URL points to backend Supabase project
- [ ] Key is the public anon key (not the secret)

```bash
# Check .env file contains:
SUPABASE_URL=https://[your-project].supabase.co
SUPABASE_KEY=eyJhbG...
USE_GEMINI=true  # or your chosen LLM
GEMINI_API_KEY=...
```

---

## ✅ Code Files Verified

- [ ] app/routes/student.py - Uses AuthService
- [ ] app/routes/evaluation.py - Has 5 endpoints
- [ ] app/routes/dashboard.py - Fixed queries
- [ ] app/services/storage_service.py - Has submissions method
- [ ] app/services/auth_service.py - Connected to backend
- [ ] app/core/security.py - Has is_student_role()

---

## ✅ Server Startup

```bash
cd d:\CampusGPT_2.0\tae_model

# If using virtual environment:
python run.py

# Or directly:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Monitor output for:
```
✓ Uvicorn running on http://0.0.0.0:8000
✓ "📦 Checking storage buckets..."
✓ "✓ Bucket exists: teacher-notes"
✓ "✓ Bucket exists: assignments"
✓ "✓ Bucket exists: submissions"
✓ "✅ All buckets ready"
✓ Application startup complete
```

---

## ✅ Test Swagger UI

- [ ] Open browser: http://localhost:8000/docs
- [ ] See all 19 endpoints listed
- [ ] See "Student", "Teacher", "Evaluation", "Dashboard" tags

---

## ✅ Quick Endpoint Tests

### Test 1: Student Registration
```bash
POST /student/register

Body (form data):
- email: testuser@test.com
- password: TestPass123
- full_name: Test User

Expected Response: 200
{
  "status": "success",
  "user_id": "...",
  "access_token": "..."
}
```

### Test 2: Student Login
```bash
POST /student/login

Body (form data):
- email: testuser@test.com
- password: TestPass123

Expected Response: 200
{
  "status": "success",
  "access_token": "..."
}
```

### Test 3: Faculty Registration
```bash
POST /teacher/register

Body (form data):
- email: faculty@test.com
- password: TestPass123
- full_name: Dr. Test
- subject: Data Structures

Expected Response: 200
```

### Test 4: Faculty Login
```bash
POST /teacher/login

Body (form data):
- email: faculty@test.com
- password: TestPass123

Expected Response: 200
{
  "status": "success",
  "access_token": "..."
}
```

### Test 5: View Assignments (Student)
```bash
GET /student/assignments

Headers:
- Authorization: Bearer {student_token}

Expected Response: 200
{
  "status": "success",
  "count": 0,
  "data": []
}
(Empty initially, will have assignments after faculty creates)
```

### Test 6: Dashboard (Student)
```bash
GET /dashboard/student-dashboard

Headers:
- Authorization: Bearer {student_token}

Expected Response: 200
{
  "status": "success",
  "statistics": {
    "total_submissions": 0,
    "graded_submissions": 0,
    ...
  }
}
```

### Test 7: Dashboard (Faculty)
```bash
GET /dashboard/faculty-dashboard

Headers:
- Authorization: Bearer {faculty_token}

Expected Response: 200
{
  "status": "success",
  "assignment_statistics": {...},
  "submission_statistics": {...}
}
```

---

## ✅ Database Verification

After tests, verify data was created:

**Check in Supabase Dashboard → SQL Editor**:

```sql
-- Check users registered
SELECT id, email, role FROM user_profiles LIMIT 5;

-- Check assignments (if created)
SELECT id, assignment_no, subject FROM assignments LIMIT 5;

-- Check submissions (if created)
SELECT id, assignment_id, status FROM submissions LIMIT 5;

-- Check evaluations (if created)
SELECT id, marks_obtained FROM evaluations LIMIT 5;
```

---

## ✅ Storage Verification

Verify files uploaded to Supabase Storage:

**In Supabase Dashboard → Storage → Files**:

- [ ] Files appear in folders (not at root)
- [ ] Correct folder structure created
- [ ] Files are readable/downloadable
- [ ] File sizes are correct

---

## ✅ All 19 Endpoints Working

**Student Endpoints (6)**
- [ ] POST /student/register
- [ ] POST /student/login
- [ ] GET /student/assignments
- [ ] POST /student/submit-assignment
- [ ] GET /student/my-submissions
- [ ] GET /student/submission/{id}

**Teacher Endpoints (5)**
- [ ] POST /teacher/register
- [ ] POST /teacher/login
- [ ] POST /teacher/upload-notes
- [ ] GET /teacher/my-assignments
- [ ] GET /teacher/track-submissions/{id}

**Evaluation Endpoints (5)**
- [ ] GET /evaluation/pending-submissions
- [ ] GET /evaluation/submission/{id}
- [ ] POST /evaluation/grade-submission
- [ ] GET /evaluation/results/{id}
- [ ] GET /evaluation/assignment-stats/{id}

**Dashboard Endpoints (3)**
- [ ] GET /dashboard/student-dashboard
- [ ] GET /dashboard/faculty-dashboard
- [ ] GET /dashboard/student-performance

---

## ✅ Error Handling

Test error cases:

```bash
# Test 1: Invalid login
POST /student/login
email: nouser@test.com
password: wrongpassword

Expected: 400 Status, error message

# Test 2: Missing token
GET /student/assignments
(No Authorization header)

Expected: 401 Unauthorized

# Test 3: Invalid file type
POST /student/submit-assignment
file: document.txt  (not .pdf)

Expected: 400 Bad request
```

---

## ✅ Logs Verification

Watch server logs for:

```
✓ "🔐 Registering user: ..." messages
✓ "✅ Registration successful" confirmations
✓ "📤 Uploading to Supabase Storage..." messages
✓ "✓ File uploaded: ..." confirmations
✓ "📤 Student X submitting assignment Y" messages
✓ No ERROR or ❌ messages
```

---

## 🚨 Troubleshooting

### Issue: Supabase connection error
```
Solution: Check SUPABASE_URL and SUPABASE_KEY in .env
Goal: http://localhost:8000/docs should load
```

### Issue: Buckets not found
```
Solution: Run: python create_buckets.py
Or: Manually create in Supabase Dashboard
```

### Issue: File upload fails
```
Solution: Check bucket names are PRIVATE (not public)
Check storage_service.py method names
```

### Issue: Authentication fails
```
Solution: Ensure user_profiles table exists in database
Check user is created in auth.users
Verify role is set correctly
```

---

## ✅ Final Status Check

```
System Status:
├── 🟢 Backend connected ✓
├── 🟢 Database schema ready ✓
├── 🟢 Storage buckets created ✓
├── 🟢 19 endpoints working ✓
├── 🟢 Authentication functional ✓
├── 🟢 File storage working ✓
├── 🟢 Error handling in place ✓
└── 🟢 Ready for users ✓

SYSTEM IS GO FOR LAUNCH! 🚀
```

---

## 📝 Keep These Documents Handy

1. **COMPLETE_SYSTEM_VERIFICATION.md** - Full system audit
2. **FIXES_APPLIED_SUMMARY.md** - What was fixed
3. **TAE_SETUP_GUIDE.md** - Detailed setup
4. **STORAGE_BUCKETS_GUIDE.md** - Storage setup
5. **README.md** - Quick start

---

**Next Step**: Run SUPABASE_SCHEMA.sql, create buckets, start server!

✅ **All systems ready. You're good to go!**
