-- Add missing RLS policies for students on submissions table
-- This allows students to insert and update their own submissions

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Students create submissions" ON public.submissions;
DROP POLICY IF EXISTS "Students update own submissions" ON public.submissions;

-- Students can insert their own submissions
CREATE POLICY "Students create submissions" ON public.submissions
  FOR INSERT WITH CHECK (student_id = auth.uid());

-- Students can update their own submissions
CREATE POLICY "Students update own submissions" ON public.submissions
  FOR UPDATE USING (student_id = auth.uid());
