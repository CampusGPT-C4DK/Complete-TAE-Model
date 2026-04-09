# 📦 Supabase Storage Buckets - Manual Creation Guide

**Created**: April 6, 2026  
**Purpose**: Step-by-step guide to create storage buckets in Supabase Dashboard  
**Status**: Complete & Ready to Follow

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Instructions](#step-by-step-instructions)
4. [Bucket Details](#bucket-details)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

You need to create **3 storage buckets** in Supabase to store:
- **Teacher Notes** (uploaded PDF files)
- **Generated Assignments** (assignment PDFs)
- **Student Submissions** (optional - for student work)

All buckets will be **PRIVATE** (not publicly accessible).

---

## ✅ Prerequisites

Before starting, make sure you have:
- [x] Supabase account
- [x] Your project created and active
- [x] Admin access to the project
- [x] Browser with internet connection

---

## 🚀 Step-by-Step Instructions

### **Initial Setup**

#### Step 1: Login to Supabase Dashboard

1. Open your web browser
2. Go to: **https://app.supabase.com**
3. Enter your email and password
4. Click **"Sign in"**

**You should see**: Supabase dashboard with your projects list

---

#### Step 2: Select Your Project

1. Look at the left sidebar
2. Find your project: **CampusGPT2.0** (or your backend project name)
3. Click on it to select it

**You should see**: Project dashboard loading

---

#### Step 3: Navigate to Storage

1. On the left sidebar, find **"Storage"**
2. Click on **"Storage"**

**You should see**: Storage main page with "Files" section

```
Dashboard
├── Home
├── Editor
├── SQL Editor
├── Realtime
├── Storage ← Click Here
├── Authentication
└── Settings
```

---

### **Create Bucket #1: teacher-notes**

#### Step 4a: Open Create Bucket Dialog

1. Make sure you're in **Storage** section
2. Click on the **"Files"** tab (if not already selected)
3. Look for the **"+ New bucket"** button (green/blue color, top right)
4. Click it

**You should see**: A dialog box appears asking for bucket details

```
┌─────────────────────────────────────────┐
│        Create a new bucket              │
├─────────────────────────────────────────┤
│                                         │
│  Bucket name                            │
│  [____________________________]          │
│                                         │
│  ☑️  Make it public                     │
│                                         │
│  [Cancel]      [Create bucket]          │
└─────────────────────────────────────────┘
```

---

#### Step 4b: Enter Bucket Name

1. Click in the **"Bucket name"** field
2. **Type exactly**: `teacher-notes`
3. Make sure it's lowercase with hyphen (not underscore)

**Correct format**: `teacher-notes` ✅  
**Wrong formats**: `TeacherNotes`, `teacher_notes`, `Teacher-Notes` ❌

---

#### Step 4c: Set Privacy

1. Look at the checkbox: **"☑️ Make it public"**
2. The checkbox currently has a checkmark
3. **CLICK the checkbox to UNCHECK it**
4. It should now show: **"☐ Make it public"** (empty)

**Important**: The bucket must be PRIVATE (unchecked)

```
Before:  ☑️ Make it public (CHECKED - public)
After:   ☐ Make it public (UNCHECKED - private) ✅
```

---

#### Step 4d: Create the Bucket

1. Click the blue **"Create bucket"** button
2. Wait for confirmation

**You should see**: 
- Dialog disappears
- New bucket appears in the list
- Success notification (optional)

---

### **Create Bucket #2: assignments**

Repeat the same steps as Bucket #1, but use **`assignments`** as the name:

#### Step 5a: Click "New bucket"

1. Click **"+ New bucket"** button again

#### Step 5b: Enter Name

1. Type: `assignments` (exactly, lowercase with hyphen)

#### Step 5c: Uncheck "Make it public"

1. Make sure the checkbox is **UNCHECKED** ☐
2. Bucket will be PRIVATE

#### Step 5d: Click "Create bucket"

1. Click the blue **"Create bucket"** button

**Result**: Second bucket created ✅

---

### **Create Bucket #3: submissions**

Repeat the same steps as Bucket #1 and #2, but use **`submissions`** as the name:

#### Step 6a: Click "New bucket"

1. Click **"+ New bucket"** button for the third time

#### Step 6b: Enter Name

1. Type: `submissions` (exactly, lowercase with hyphen)

#### Step 6c: Uncheck "Make it public"

1. Make sure the checkbox is **UNCHECKED** ☐
2. Bucket will be PRIVATE

#### Step 6d: Click "Create bucket"

1. Click the blue **"Create bucket"** button

**Result**: Third bucket created ✅

---

## 📊 Bucket Details

### Bucket #1: teacher-notes

**Purpose**: Store uploaded teacher reference materials (PDF files)

**Name**: `teacher-notes`  
**Visibility**: Private (🔒)  
**File Types**: PDF  
**Path Structure**: `{user_id}/{subject}/assignment-{assignment_no}/{filename}`

**Example Path**:
```
550e8400-e29b-41d4-a716-446655440000/DSA/assignment-1/chapter1.pdf
550e8400-e29b-41d4-a716-446655440000/DSA/assignment-1/chapter2.pdf
```

---

### Bucket #2: assignments

**Purpose**: Store generated assignment PDFs

**Name**: `assignments`  
**Visibility**: Private (🔒)  
**File Types**: PDF  
**Path Structure**: `{user_id}/{subject}/semester-{semester}/assignment-{assignment_no}/{filename}`

**Example Path**:
```
550e8400-e29b-41d4-a716-446655440000/DSA/semester-4/assignment-1/assignment.pdf
550e8400-e29b-41d4-a716-446655440000/DSA/semester-4/assignment-2/assignment.pdf
```

---

### Bucket #3: submissions

**Purpose**: Store student submission files (optional, for future use)

**Name**: `submissions`  
**Visibility**: Private (🔒)  
**File Types**: PDF, DOC, DOCX, TXT  
**Path Structure**: `{assignment_id}/{student_id}/{filename}`

**Example Path**:
```
660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/submission.pdf
```

---

## ✅ Verification

### Step 7: Verify All Buckets Created

After creating all 3 buckets:

1. Go to **Storage** → **Files** tab
2. Look at the buckets list
3. You should see:

```
BUCKETS
─────────────────────────┐
📁 documents             │ (existing - PUBLIC)
📁 embeddings            │ (existing - PUBLIC)
📁 teacher-notes         │ (NEW - PRIVATE) ✅
📁 assignments           │ (NEW - PRIVATE) ✅
📁 submissions           │ (NEW - PRIVATE) ✅
─────────────────────────┘
```

### Check Each Bucket

For each new bucket, verify:

| Property | Expected |
|----------|----------|
| Name | Correct (teacher-notes, assignments, submissions) |
| Status | Created |
| Visibility | 🔒 Private |
| POLICIES | 0 |
| FILE SIZE LIMIT | Unset (50 MB) |
| ALLOWED MIME TYPES | Any |

---

## 🔍 How to Check Bucket Details

1. Click on a bucket name (e.g., `teacher-notes`)
2. You'll see the bucket details page:

```
┌─────────────────────────────────────┐
│ teacher-notes                       │
├─────────────────────────────────────┤
│ Policies │ Settings │ Objects       │
├─────────────────────────────────────┤
│                                     │
│ POLICIES: 0                         │
│ FILE SIZE LIMIT: Unset (50 MB)      │
│ ALLOWED MIME TYPES: Any             │
│                                     │
└─────────────────────────────────────┘
```

This confirms the bucket is set up correctly.

---

## 🐛 Troubleshooting

### Issue #1: Buckets Not Appearing

**Symptom**: Created buckets but don't see them in the list

**Solution**:
1. Refresh the page: Press **F5**
2. Wait 2-3 seconds for page to reload
3. Check if buckets appear now
4. If still not visible, refresh again

---

### Issue #2: Bucket Name Already Exists

**Symptom**: Error message "Bucket with this name already exists"

**Solution**:
1. This bucket was already created before
2. You don't need to create it again
3. Skip to the next bucket
4. Or check if the bucket exists in your list

---

### Issue #3: Cannot Uncheck "Make it public"

**Symptom**: Checkbox won't uncheck

**Solution**:
1. Click directly on the checkbox ☑️
2. Make sure you click the checkbox itself, not the text
3. It should change to ☐ (empty)
4. If still checked, try clicking again

---

### Issue #4: Wrong Project Selected

**Symptom**: Buckets you create don't match your project

**Solution**:
1. Check the project name at the top left
2. Make sure it says: **CampusGPT2.0** (or your project name)
3. If wrong, click the dropdown and select the correct project
4. Create buckets again in the correct project

---

### Issue #5: Buckets Appear But Can't Upload

**Symptom**: Buckets created but application can't upload files

**Solution**:
1. Make sure buckets are PRIVATE (☐ Make it public = unchecked)
2. Check your API key in `.env` file is correct
3. Verify Supabase connection in your application
4. Check application logs for error messages

---

## ✨ Summary

### Created Buckets ✅

| # | Name | Type | Status |
|---|------|------|--------|
| 1 | teacher-notes | Private | ✅ Created |
| 2 | assignments | Private | ✅ Created |
| 3 | submissions | Private | ✅ Created |

### Quick Overview

```
TAE Model Storage Architecture
────────────────────────────────────

Supabase Project
├── Storage
│   ├── teacher-notes (PRIVATE)
│   │   └─ {user_id}/{subject}/assignment-{no}/{file}
│   │
│   ├── assignments (PRIVATE)
│   │   └─ {user_id}/{subject}/semester-{sem}/assignment-{no}/{file}
│   │
│   └── submissions (PRIVATE)
│       └─ {assignment_id}/{student_id}/{file}
│
└── Database
    ├── assignments (table)
    ├── submissions (table)
    └── evaluations (table)
```

---

## 🎯 Next Steps

After verifying all buckets are created:

1. **Run your TAE Model server**:
   ```bash
   cd d:\CampusGPT_2.0\tae_model
   python run.py
   ```

2. **Access Swagger UI**:
   - Open: http://localhost:8000/docs

3. **Test the system**:
   - Register faculty
   - Login
   - Upload notes
   - Files should appear in buckets

---

## 📞 Support

### Common Questions

**Q: Why are buckets private?**  
A: Private buckets ensure only authorized users can access files. Public buckets would expose all files to the internet.

**Q: Can I change privacy later?**  
A: Yes, go to bucket → Settings → change visibility.

**Q: What's the file size limit?**  
A: Default is 50 MB per file. You can increase in Settings.

**Q: Can I use different bucket names?**  
A: You can, but you must update the application code (storage_service.py) with new names.

---

## ✅ Completion Checklist

- [x] Logged into Supabase Dashboard
- [x] Selected correct project
- [x] Created `teacher-notes` bucket (PRIVATE)
- [x] Created `assignments` bucket (PRIVATE)
- [x] Created `submissions` bucket (PRIVATE)
- [x] Verified all buckets appear in list
- [x] Confirmed all buckets are PRIVATE
- [x] Ready to use with TAE Model application

---

**Status**: ✅ Documentation Complete  
**Last Updated**: April 6, 2026  
**Version**: 1.0

For issues or questions, refer to the Troubleshooting section above.
