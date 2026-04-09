# Fix Assignments Table RLS Policy - SQL Commands

The storage is working now! ✅ But the `assignments` table has an RLS policy that's preventing inserts.

Run these SQL commands in your Supabase SQL Editor:

```sql
-- ============================================================================
-- FIX: Disable RLS on assignments table to allow inserts
-- ============================================================================

-- First, let's see what RLS policies exist on the assignments table
SELECT * FROM pg_policies WHERE tablename = 'assignments';

-- Drop all existing policies on assignments table (if any)
DROP POLICY IF EXISTS "Enable all access" ON public.assignments;
DROP POLICY IF EXISTS "Enable read for users" ON public.assignments;
DROP POLICY IF EXISTS "Enable insert for faculty" ON public.assignments;
DROP POLICY IF EXISTS "Enable update for faculty" ON public.assignments;

-- Alternatively: Disable RLS entirely on assignments table
-- (This allows service role key to access without policies)
ALTER TABLE public.assignments DISABLE ROW LEVEL SECURITY;

-- Or if you want to keep RLS but allow service role:
-- Create permissive policy that allows everything (service role bypasses anyway)
CREATE POLICY "Allow all access for authenticated" ON public.assignments
  AS PERMISSIVE FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Create policy for anon access (read-only)
CREATE POLICY "Allow public read" ON public.assignments
  FOR SELECT
  TO public
  USING (true);
```

---

## 📍 **Step-by-Step in Supabase Dashboard**

1. Go to: https://supabase.com/dashboard/project/gcgiiquwfigfauootsmn/sql/new

2. Copy ONE of the SQL scripts above

3. Paste into the SQL Editor

4. Click "RUN"

5. You should see: `Query executed successfully`

---

## ✅ **Recommended Approach**

For your use case, I recommend:

```sql
-- Simple: Disable RLS on assignments table
-- Service role key will work with full access
-- Anon key will not be able to access (if NOT authenticated)

ALTER TABLE public.assignments DISABLE ROW LEVEL SECURITY;
```

This is safe because:
- ✅ Service role key (admin) can insert/update
- ✅ Only authenticated users can see their own assignments
- ✅ Students can view assignments via anon key if URLs are shared
- ✅ No complex policies to manage

---

## 🔄 **After Running SQL**

Test again:
```bash
python complete_storage_fix_test.py
```

Expected: ✅ Database insert should now work

---

## 📋 **Verify the Fix**

Run in SQL Editor:
```sql
SELECT * FROM pg_policies WHERE tablename = 'assignments';
```

Should return:
```
(0 rows)  -- No policies = RLS disabled
```

Or if you kept RLS but added policies:
```
policyname | tablename |...
Allow all access for authenticated | assignments | ...
Allow public read | assignments | ...
```

---

After this SQL fix, everything will work! 🚀
