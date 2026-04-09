# 🚀 TAE Model - Integration with Backend Supabase

## Complete Setup Guide

This guide walks you through integrating the TAE Model with your Backend Supabase project using unified authentication and storage.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Setup Steps](#setup-steps)
4. [Database Schema](#database-schema)
5. [Environment Configuration](#environment-configuration)
6. [API Endpoints](#api-endpoints)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│         TAE Model (Assignment Generator & Evaluator)   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Authentication                Storage                  │
│  ├─ Supabase Auth        ├─ Teacher Notes             │
│  └─ user_profiles table  └─ Generated Assignments     │
│                                                         │
│  (Both shared with Backend)                            │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│          BACKEND SUPABASE PROJECT                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  auth.users (Supabase Auth)                           │
│  public.user_profiles (shared table)                   │
│  public.documents, chat_history, etc.                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Features

✅ **Unified Authentication**: Same login for both backend and TAE model
✅ **Supabase Storage**: All files stored in Supabase (not local)
✅ **user_profiles Sync**: Uses backend's user_profiles table
✅ **Role-Based Access**: Faculty and student roles automatically managed
✅ **LLM Integration**: Gemini/Ollama for auto-evaluation

---

## 📋 Prerequisites

- ✅ Backend project running with Supabase
- ✅ Supabase project URL and API key
- ✅ Python 3.9+
- ✅ Supabase Python SDK: `pip install supabase`

---

## 🔧 Setup Steps

### Step 1: Clone/Update TAE Model

```bash
cd d:\CampusGPT_2.0\tae_model
git pull  # or set up fresh
```

### Step 2: Update Dependencies

```bash
pip install -r requirements.txt
pip install supabase
```

### Step 3: Configure Environment Variables

Update `.env` file with your backend Supabase credentials:

```env
# Supabase Connection (from Backend project)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Model Configuration
USE_GEMINI=true           # or USE_PHI3_MINI=true, USE_MISTRAL=true
USE_PHI3_MINI=false
USE_MISTRAL=false

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash

# Ollama (if using local model)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3:mini
```

### Step 4: Create Supabase Schema

Run the SQL schema in your Supabase project:

**Option A: Using Supabase Dashboard**
1. Go to **SQL Editor**
2. Click **New Query**
3. Paste contents of `SUPABASE_SCHEMA.sql`
4. Click **Run**

**Option B: Using Python Script**
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

with open('SUPABASE_SCHEMA.sql', 'r') as f:
    sql = f.read()

# Split by semicolon and execute each statement
for statement in sql.split(';'):
    if statement.strip():
        supabase.rpc('execute_sql', {'sql': statement}).execute()
```

### Step 5: Create Storage Buckets

Run this Python code or use Supabase dashboard:

```python
from app.services.storage_service import StorageService

# Create buckets
StorageService.ensure_buckets_exist()
```

Or manually in Supabase Dashboard:
1. **Storage** → **Create new bucket**
   - Name: `teacher-notes` (private)
   - Name: `assignments` (private)
   - Name: `submissions` (private)

### Step 6: Verify Database Connection

```bash
python -c "from app.database import supabase; print('✅ Connected!' if supabase else '❌ Failed')"
```

### Step 7: Run the Server

```bash
python run.py
```

You should see:
```
✓ Supabase connected
✓ Buckets verified
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 📊 Database Schema

### Tables Created

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `faculty_metadata` | Faculty info | user_id, subject, department |
| `assignments` | Generated assignments | faculty_id, pdf_url, pdf_storage_path |
| `submissions` | Student submissions | assignment_id, student_id, submitted_file_path |
| `evaluations` | Evaluation results | submission_id, marks_obtained, feedback |
| `answer_comparisons` | Plagiarism detection | student1_id, student2_id, similarity_score |
| `audit_log` | System audit trail | user_id, action, entity_type |
| `notification_preferences` | User preferences | user_id, email_on_submission |

### Views Created

- `assignment_stats` - Assignment statistics
- `student_performance` - Student grades summary

---

## 🔐 Environment Configuration

### Complete .env Example

```env
# ============ SUPABASE (from Backend) ============
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret

# ============ MODEL SELECTION ============
USE_GEMINI=true
USE_PHI3_MINI=false
USE_MISTRAL=false

# ============ GEMINI CONFIG ============
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.0-flash

# ============ OLLAMA CONFIG (local) ============
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3:mini

# ============ MISTRAL CONFIG ============
MISTRAL_API_KEY=sk-...

# ============ APPLICATION ============
DEBUG=true
LOG_LEVEL=INFO
```

---

## 📡 API Endpoints

### Authentication Endpoints

#### Register Faculty
```bash
POST /teacher/register
Content-Type: application/json

{
  "email": "faculty@example.com",
  "password": "secure_password",
  "full_name": "Dr. John Smith",
  "subject": "Computer Science"
}
```

**Response:**
```json
{
  "status": "success",
  "user_id": "uuid-here",
  "access_token": "eyJhbGc...",
  "refresh_token": "...",
  "expires_in": 3600
}
```

#### Faculty Login
```bash
POST /teacher/login
Content-Type: application/x-www-form-urlencoded

email=faculty@example.com&password=password
```

**Response:**
```json
{
  "status": "success",
  "user_id": "uuid-here",
  "email": "faculty@example.com",
  "full_name": "Dr. John Smith",
  "role": "faculty",
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Assignment Endpoints

#### Upload Notes & Generate Assignment
```bash
POST /teacher/upload-notes
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf]
difficulty: "medium"
assignment_no: "1"
subject: "Data Structures"
branch: "CSE"
semester: "4"
faculty: "Dr. Smith"
given_date: "2026-04-06"
submission_date: "2026-04-13"
```

**Response:**
```json
{
  "status": "success",
  "assignment_id": "uuid-here",
  "pdf_url": "https://supabase.../assignments/uuid-here/...",
  "storage_path": "user_id/subject/semester-4/assignment-1/file.pdf"
}
```

#### View My Assignments
```bash
GET /teacher/my-assignments
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "data": [
    {
      "id": "uuid-here",
      "assignment_no": "1",
      "subject": "Data Structures",
      "pdf_url": "...",
      "created_at": "2026-04-06T10:30:00Z"
    }
  ]
}
```

#### Track Submissions
```bash
GET /teacher/track-submissions/{assignment_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "success",
  "count": 45,
  "data": [
    {
      "student_id": "uuid",
      "student_name": "John Doe",
      "email": "john@example.com",
      "marks": 85,
      "status": "graded",
      "submitted_at": "2026-04-11T15:30:00Z"
    }
  ]
}
```

---

## 🧪 Testing

### Test 1: Upload Notes and Generate Assignment

```bash
curl -X POST http://localhost:8000/teacher/upload-notes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@notes1.pdf" \
  -F "files=@notes2.pdf" \
  -F "difficulty=medium" \
  -F "assignment_no=1" \
  -F "subject=DSA" \
  -F "branch=CSE" \
  -F "semester=4" \
  -F "faculty=Dr. Smith" \
  -F "given_date=2026-04-06" \
  -F "submission_date=2026-04-13"
```

### Test 2: Check Storage Upload

1. Go to Supabase Dashboard
2. Navigate to **Storage**
3. Check `teacher-notes` bucket - should see uploaded files
4. Check `assignments` bucket - should see generated PDF

### Test 3: Verify Database

```sql
-- Check assignments table
SELECT id, assignment_no, subject, pdf_url 
FROM public.assignments 
ORDER BY created_at DESC
LIMIT 5;

-- Check submissions
SELECT s.id, a.assignment_no, s.student_id, s.status
FROM public.submissions s
JOIN public.assignments a ON s.assignment_id = a.id;
```

---

## 📝 Common Operations

### Store Faculty Metadata

```python
from app.database import supabase

supabase.table("faculty_metadata").insert({
    "user_id": "uuid-here",
    "subject": "Data Structures",
    "department": "Computer Science",
    "is_verified": True,
    "phone": "+91-9876543210"
}).execute()
```

### Retrieve Assignment Statistics

```python
from app.database import supabase

stats = supabase.table("assignment_stats") \
    .select("*") \
    .eq("faculty_id", "uuid-here") \
    .execute()

for row in stats.data:
    print(f"Assignment {row['assignment_no']}: {row['submitted_count']}/{row['total_submissions']} submitted")
```

### Query Student Performance

```python
performance = supabase.table("student_performance") \
    .select("*") \
    .eq("student_id", "uuid-here") \
    .execute()

print(f"Average: {performance.data[0]['avg_percentage']}%")
```

---

## 🐛 Troubleshooting

### Error: "Invalid token"
- ❌ Token expired - ask user to re-login
- ❌ Token format wrong - should be "Bearer {token}"
- ✅ Pass token in Authorization header

### Error: "Only faculty can access"
- ❌ User role is not "faculty"
- ✅ Register with role="faculty" explicitly
- ✅ Check Supabase user_profiles table for role

### Error: "Storage bucket not found"
- ❌ Buckets not created
- ✅ Run `StorageService.ensure_buckets_exist()`
- ✅ Manually create in Supabase Dashboard

### Error: "Connection refused - Gemini"
- ❌ API key invalid
- ✅ Verify `GEMINI_API_KEY` in .env
- ✅ Get key from https://aistudio.google.com/app/apikeys

### Error: "Text extraction failed"
- ❌ PDF corrupted or text-locked
- ✅ Use standard PDF format
- ✅ Test with different PDF

### Large File Uploads Failing
- ❌ File exceeds 50MB limit
- ✅ Split into smaller files
- ✅ Adjust `max_file_upload_size_mb` in system_config

---

## 🔄 Workflow Example

### Complete Assignment Generation Workflow

```
1. Faculty Logs In
   └─ POST /teacher/login
      └─ Get access_token

2. Upload Reference Notes
   └─ POST /teacher/upload-notes (with token)
      ├─ Extract text from PDFs
      ├─ Store in Supabase (teacher-notes bucket)
      ├─ Generate questions with LLM
      └─ Generate assignment PDF

3. System Stores:
   └─ Metadata in `assignments` table
   └─ PDF in Supabase (assignments bucket)
   └─ URLs in database

4. View All Assignments
   └─ GET /teacher/my-assignments
      └─ List all created assignments

5. Track Submissions
   └─ GET /teacher/track-submissions/{id}
      └─ See student submissions for assignment

6. Auto-Evaluate (Optional)
   └─ LLM evaluates submissions
   └─ Scores stored in `evaluations` table
```

---

## 📚 Supporting Files

- `SUPABASE_SCHEMA.sql` - Complete database schema
- `app/services/auth_service.py` - Authentication logic
- `app/services/storage_service.py` - Storage management
- `app/routes/teacher.py` - Faculty endpoints
- `.env` - Configuration file

---

## ✅ Verification Checklist

- [ ] Supabase credentials in `.env`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database schema created (run SQL script)
- [ ] Storage buckets created
- [ ] Server running (`python run.py`)
- [ ] Test faculty login
- [ ] Test upload notes endpoint
- [ ] Verify files in Supabase Storage
- [ ] Check database for records
- [ ] Test LLM evaluation

---

## 🎯 Next Steps

1. **Connect Frontend**: Update Flutter/web app to use new endpoints
2. **Student Routes**: Update student submission endpoints
3. **Evaluation System**: Integrate LLM-based evaluation
4. **Analytics**: Use views for dashboards
5. **Notifications**: Implement email/SMS notifications

---

## 📞 Support

For issues:
1. Check logs: `python run.py` (watch console)
2. Verify Supabase connectivity
3. Check `.env` file configuration
4. Review API endpoint format
5. Check RLS policies in Supabase

---

**Status**: ✅ Ready for production
**Last Updated**: April 6, 2026
**Version**: 2.0 (Backend Integrated)
