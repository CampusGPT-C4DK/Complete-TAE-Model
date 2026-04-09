# Supabase Storage RLS Policy Fix - Visual Step-by-Step Guide

## 🎯 Goal
Add RLS policies to allow authenticated file uploads to storage buckets.

---

## 📍 Location in Supabase Menu

```
Dashboard Home
  ↓
Left Sidebar → Storage
  ↓
"Policies" Tab (next to "Files" and "Settings")
  ↓
Click "teacher-notes" bucket
  ↓
Add 3 policies (SELECT, INSERT, UPDATE)
```

**Direct URL:**
```
https://supabase.com/dashboard/project/gcgiiquwfigfauootsmn/storage/policies
```

---

## 🔧 Detailed Steps

### BUCKET 1: teacher-notes

#### Policy 1: SELECT (Allow public read)

**Step 1:** Click on "teacher-notes" bucket in the policies list
```
┌─────────────────────────────────────────────┐
│ Buckets                                     │
├─────────────────────────────────────────────┤
│ □ teacher-notes  ← Click this               │
│ □ assignments                               │
│ □ submissions                               │
└─────────────────────────────────────────────┘
```

**Step 2:** Click "New policy" button
```
┌─────────────────────────────────────────────┐
│ [New policy ▼]  ← Click here                │
│ ┌──────────────┐                           │
│ │ For SELECT   │ ← Select this              │
│ │ For INSERT   │                           │
│ │ For UPDATE   │                           │
│ │ For DELETE   │                           │
│ └──────────────┘                           │
└─────────────────────────────────────────────┘
```

**Step 3:** Click "For SELECT"

**Step 4:** Fill in the form
```
┌────────────────────────────────────────────────┐
│ New policy for teacher-notes                   │
├────────────────────────────────────────────────┤
│ Name: [Allow public read              ]        │
│                                                │
│ Where applicable:                              │
│     [true                            ]         │
│                                                │
│ [Save policy] [Cancel]                       │
└────────────────────────────────────────────────┘
```

**Step 5:** Click "Save policy"

---

#### Policy 2: INSERT (Allow authenticated upload)

**Step 1:** Click "New policy" again
**Step 2:** Click "For INSERT"

**Step 3:** Fill in the form
```
┌────────────────────────────────────────────────┐
│ New policy for teacher-notes                   │
├────────────────────────────────────────────────┤
│ Name: [Allow authenticated insert      ]       │
│                                                │
│ Where applicable:                              │
│     [auth.uid() is not null          ]         │
│                                                │
│ [Save policy] [Cancel]                       │
└────────────────────────────────────────────────┘
```

**Step 4:** Click "Save policy"

---

#### Policy 3: UPDATE (Allow owner update)

**Step 1:** Click "New policy" again
**Step 2:** Click "For UPDATE"

**Step 3:** Fill in the form
```
┌────────────────────────────────────────────────┐
│ New policy for teacher-notes                   │
├────────────────────────────────────────────────┤
│ Name: [Allow owner update              ]       │
│                                                │
│ Where applicable:                              │
│     [auth.uid() = owner              ]         │
│                                                │
│ [Save policy] [Cancel]                       │
└────────────────────────────────────────────────┘
```

**Step 4:** Click "Save policy"

---

### BUCKET 2: assignments

**Repeat the same 3 policies:**
1. SELECT: `true`
2. INSERT: `auth.uid() is not null`
3. UPDATE: `auth.uid() = owner`

---

### BUCKET 3: submissions

**Repeat the same 3 policies:**
1. SELECT: `true`
2. INSERT: `auth.uid() is not null`
3. UPDATE: `auth.uid() = owner`

---

## ✅ Completion Checklist

After adding all policies, verify:

```
✅ teacher-notes bucket (3 policies):
   □ SELECT - Allow public read
   □ INSERT - Allow authenticated insert
   □ UPDATE - Allow owner update

✅ assignments bucket (3 policies):
   □ SELECT - Allow public read
   □ INSERT - Allow authenticated insert
   □ UPDATE - Allow owner update

✅ submissions bucket (3 policies):
   □ SELECT - Allow public read
   □ INSERT - Allow authenticated insert
   □ UPDATE - Allow owner update
```

---

## 🎯 Expected Results

After policies are added, you should see:

**In Dashboard - Policies tab:**
```
teacher-notes
├─ Allow public read (SELECT)
├─ Allow authenticated insert (INSERT)
└─ Allow owner update (UPDATE)

assignments
├─ Allow public read (SELECT)
├─ Allow authenticated insert (INSERT)
└─ Allow owner update (UPDATE)

submissions
├─ Allow public read (SELECT)
├─ Allow authenticated insert (INSERT)
└─ Allow owner update (UPDATE)
```

**Total: 9 policies (3 per bucket)**

---

## 🧪 Test After Setup

Once policies are added:

```bash
# Test upload
python test_upload.py

# Expected output:
# ✅ Test PDF created
# ✅ Upload successful (teacher notes)
# ✅ Upload successful (assignment PDF)
# ✅ File verified in storage
```

---

## 🆘 If Something Goes Wrong

### Error: "Policy Already Exists"
- Solution: Policy with that name already exists
- Action: Skip or delete the old one first

### Error: "Can't add policy to bucket"
- Solution: You might not have admin permissions
- Action: Check if logged in as project owner

### Error: "Policy syntax error"
- Solution: Check the formula is correct
- Action: Copy exact text: `auth.uid() is not null`

---

## ⏱️ Time Estimate
- Per bucket: ~2 minutes (3 policies)
- Total: ~6 minutes (3 buckets × 2 min)

---

## 📱 Visual Dashboard View

After all policies are added, Supabase dashboard should show:

```
┌──────────────────────────────────────────────────────┐
│ STORAGE / POLICIES                                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│ ≡ teacher-notes (3 policies enabled)            ✓   │
│ ≡ assignments (3 policies enabled)              ✓   │
│ ≡ submissions (3 policies enabled)              ✓   │
│ ≡ documents                                          │
│ ≡ embeddings                                        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

All buckets showing "3 policies enabled" ✓

---

## 🎉 Next Step

Once policies are set:

```bash
# Generate your first assignment
cd d:\CampusGPT_2.0\tae_model
python run.py

# Visit: http://localhost:7000/docs
# POST /upload-notes
# Upload files and generate assignment
# Check files in Supabase Storage dashboard
```

---

**Total Setup Time: ~6 minutes** ⏱️  
**Result: Production-ready storage** 🚀
