# ⚡ TAE Model - Quick Start Checklist

## 🎯 Get Running in 5 Minutes

### Before Starting
- [ ] Backend Supabase project running
- [ ] Have your Supabase URL and API Key
- [ ] Python 3.9+ installed
- [ ] Git cloned / folder ready

---

## 1️⃣ Install Dependencies (2 min)

```bash
cd d:\CampusGPT_2.0\tae_model
pip install -r requirements.txt
```

**Expected**: No errors, all packages installed

---

## 2️⃣ Configure .env (1 min)

Copy and paste into `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGc...
USE_GEMINI=true
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.0-flash
```

**Get these from**:
- SUPABASE_URL & KEY: Backend project → Settings → API
- GEMINI_API_KEY: https://aistudio.google.com/app/apikeys

---

## 3️⃣ Create Database Schema (1 min)

**Option A: GUI (Easiest)**
1. Go to Supabase → SQL Editor
2. Copy-paste entire `SUPABASE_SCHEMA.sql`
3. Click "Run"
4. ✅ Done!

**Option B: Python Script**
```bash
cd d:\CampusGPT_2.0\tae_model
python -c "from app.services.storage_service import StorageService; StorageService.ensure_buckets_exist()"
```

---

## 4️⃣ Start Server (30 sec)

```bash
python run.py
```

**Expected output:**
```
✓ Supabase connected
✓ Buckets verified
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 5️⃣ Test in Swagger UI (30 sec)

Open Chrome → `http://localhost:8000/docs`

1. Scroll to `/teacher/login`
2. Click "Try it out"
3. Enter:
   ```
   email: your-faculty@example.com
   password: your-password
   ```
4. Click "Execute"

**Expected**: 200 status with access_token

---

## ✅ You're Done!

Your TAE Model is now:
- ✅ Connected to backend Supabase
- ✅ Using unified authentication
- ✅ Ready for file uploads to Supabase Storage
- ✅ Ready for assignment generation with LLM

---

## 📡 Next: Test Upload Endpoint

```bash
curl -X POST http://localhost:8000/teacher/upload-notes \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "files=@sample.pdf" \
  -F "difficulty=medium" \
  -F "assignment_no=1" \
  -F "subject=DSA" \
  -F "branch=CSE" \
  -F "semester=4" \
  -F "faculty=Dr. Smith" \
  -F "given_date=2026-04-06" \
  -F "submission_date=2026-04-13"
```

---

## 🐛 Troubleshooting Quick Fix

| Error | Fix |
|-------|-----|
| "Invalid credentials" | Check SUPABASE_URL and SUPABASE_KEY in .env |
| "No module named 'supabase'" | Run `pip install supabase` |
| "Storage bucket not found" | Create storage buckets in Supabase UI |
| "GEMINI_API_KEY not found" | Add GEMINI_API_KEY to .env |
| "Connection refused" | Check if Supabase project is online |

---

## 📚 Full Documentation

See `TAE_SETUP_GUIDE.md` for complete setup and API documentation.

---

**Status**: ✅ Ready to go!
