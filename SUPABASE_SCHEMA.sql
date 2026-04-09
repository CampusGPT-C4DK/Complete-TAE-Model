-- =====================================================================
-- SUPABASE SCHEMA FOR TAE MODEL
-- Complete SQL Schema for Teacher Assignment Evaluation System
-- Connected to Backend user_profiles table
-- =====================================================================

-- =====================================================================
-- 1. USER PROFILES TABLE (FROM BACKEND - DO NOT RECREATE)
-- =====================================================================
-- This table is managed by the backend system
-- It uses Supabase Auth and sync from auth.users

-- Reference structure:
-- CREATE TABLE public.user_profiles (
--   id uuid NOT NULL PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
--   email text NOT NULL UNIQUE,
--   full_name text,
--   role text DEFAULT 'student'::text,  -- 'student', 'faculty', 'admin'
--   is_active boolean DEFAULT true,
--   created_at timestamp DEFAULT now(),
--   updated_at timestamp DEFAULT now(),
--   features_access jsonb
-- );


-- =====================================================================
-- 2. FACULTY METADATA TABLE
-- =====================================================================
-- Extended information for faculty members
CREATE TABLE IF NOT EXISTS public.faculty_metadata (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  subject text NOT NULL,
  department text,
  is_verified boolean DEFAULT false,
  phone text,
  office_location text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_faculty_metadata_user_id ON public.faculty_metadata(user_id);


-- =====================================================================
-- 3. ASSIGNMENTS TABLE
-- =====================================================================
-- Stores generated assignment metadata and storage references
CREATE TABLE IF NOT EXISTS public.assignments (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  faculty_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  assignment_no text NOT NULL,
  subject text NOT NULL,
  branch text NOT NULL,
  semester text NOT NULL,
  difficulty text NOT NULL,  -- 'easy', 'medium', 'hard'
  given_date date NOT NULL,
  submission_date date NOT NULL,
  
  -- Questions and content
  questions jsonb NOT NULL,  -- Stores generated questions as JSON
  
  -- Storage references
  pdf_storage_path text NOT NULL,  -- Path in 'assignments' bucket
  pdf_url text NOT NULL,  -- Public URL to PDF
  teacher_notes_urls jsonb,  -- URLs to teacher notes in 'teacher-notes' bucket
  
  -- Metadata
  created_by text,
  status text DEFAULT 'active'::text,  -- 'active', 'archived', 'draft'
  total_questions integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  
  CONSTRAINT valid_difficulty CHECK (difficulty IN ('easy', 'medium', 'hard')),
  CONSTRAINT valid_status CHECK (status IN ('active', 'archived', 'draft'))
);

CREATE INDEX IF NOT EXISTS idx_assignments_faculty_id ON public.assignments(faculty_id);
CREATE INDEX IF NOT EXISTS idx_assignments_subject ON public.assignments(subject);
CREATE INDEX IF NOT EXISTS idx_assignments_semester ON public.assignments(semester);
CREATE INDEX IF NOT EXISTS idx_assignments_created_at ON public.assignments(created_at DESC);


-- =====================================================================
-- 4. STUDENT SUBMISSIONS TABLE
-- =====================================================================
-- Tracks student assignment submissions
CREATE TABLE IF NOT EXISTS public.submissions (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  assignment_id uuid NOT NULL REFERENCES public.assignments(id) ON DELETE CASCADE,
  student_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Submission details
  submitted_file_path text,  -- Path in 'submissions' bucket (if file uploaded)
  submitted_file_url text,
  submission_text text,
  submitted_at timestamp with time zone,
  is_late boolean DEFAULT false,
  days_late integer DEFAULT 0,
  
  -- Status tracking
  status text DEFAULT 'pending'::text,  -- 'pending', 'submitted', 'late', 'graded'
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  
  CONSTRAINT valid_submission_status CHECK (status IN ('pending', 'submitted', 'late', 'graded')),
  UNIQUE(assignment_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_submissions_assignment_id ON public.submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student_id ON public.submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON public.submissions(status);


-- =====================================================================
-- 5. EVALUATIONS TABLE
-- =====================================================================
-- Stores evaluation results for each submission
CREATE TABLE IF NOT EXISTS public.evaluations (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id uuid NOT NULL REFERENCES public.submissions(id) ON DELETE CASCADE,
  assignment_id uuid NOT NULL REFERENCES public.assignments(id) ON DELETE CASCADE,
  faculty_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE SET NULL,
  
  -- Scoring
  total_marks integer,
  marks_obtained integer,
  percentage real,
  grade text,
  
  -- Evaluation details
  feedback text,  -- Faculty feedback
  strengths text,
  areas_for_improvement text,
  model_evaluation text,  -- From LLM evaluation
  
  -- Metadata
  evaluated_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evaluations_submission_id ON public.evaluations(submission_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_assignment_id ON public.evaluations(assignment_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_faculty_id ON public.evaluations(faculty_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON public.evaluations(created_at DESC);


-- =====================================================================
-- 6. ANSWER COMPARISONS TABLE
-- =====================================================================
-- For similarity checking between student answers
CREATE TABLE IF NOT EXISTS public.answer_comparisons (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  assignment_id uuid NOT NULL REFERENCES public.assignments(id) ON DELETE CASCADE,
  student1_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  student2_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Similarity metrics
  similarity_score real,  -- 0-100
  duplicate_detection boolean DEFAULT false,
  flagged_for_review boolean DEFAULT false,
  match_details jsonb,  -- Detailed comparison data
  
  created_at timestamp with time zone DEFAULT now(),
  
  CHECK (student1_id < student2_id)  -- Avoid duplicate pairs
);

CREATE INDEX IF NOT EXISTS idx_answer_comparisons_assignment_id ON public.answer_comparisons(assignment_id);
CREATE INDEX IF NOT EXISTS idx_answer_comparisons_flagged ON public.answer_comparisons(flagged_for_review);


-- =====================================================================
-- 7. AUDIT LOG TABLE
-- =====================================================================
-- Track all important actions in the system
CREATE TABLE IF NOT EXISTS public.audit_log (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id),
  action text NOT NULL,  -- 'create_assignment', 'upload_notes', 'submit', 'evaluate', etc.
  entity_type text,  -- 'assignment', 'submission', 'evaluation'
  entity_id uuid,
  details jsonb,
  ip_address text,
  created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON public.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON public.audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON public.audit_log(created_at DESC);


-- =====================================================================
-- 8. NOTIFICATION PREFERENCES TABLE
-- =====================================================================
-- User preferences for notifications
CREATE TABLE IF NOT EXISTS public.notification_preferences (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Email notifications
  email_on_submission boolean DEFAULT true,
  email_on_grade boolean DEFAULT true,
  email_digest_frequency text DEFAULT 'daily'::text,  -- 'off', 'daily', 'weekly'
  
  -- In-app notifications
  in_app_notifications_enabled boolean DEFAULT true,
  
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON public.notification_preferences(user_id);


-- =====================================================================
-- 9. SYSTEM CONFIGURATION TABLE
-- =====================================================================
-- Store system-wide settings
CREATE TABLE IF NOT EXISTS public.system_config (
  id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
  config_key text NOT NULL UNIQUE,
  config_value text,
  data_type text,  -- 'string', 'integer', 'boolean', 'json'
  description text,
  updated_by uuid REFERENCES auth.users(id),
  updated_at timestamp with time zone DEFAULT now()
);

INSERT INTO public.system_config (config_key, config_value, data_type, description) VALUES
  ('max_file_upload_size_mb', '50', 'integer', 'Maximum file upload size in MB'),
  ('supported_file_types', '["pdf","doc","docx","txt"]', 'json', 'Supported file types for upload'),
  ('enable_plagiarism_detection', 'true', 'boolean', 'Enable similarity checking'),
  ('plagiarism_threshold', '70', 'integer', 'Similarity percentage to flag as potential plagiarism'),
  ('enable_auto_evaluation', 'true', 'boolean', 'Enable automatic LLM-based evaluation')
ON CONFLICT (config_key) DO NOTHING;


-- =====================================================================
-- STORAGE BUCKETS (To be created via Supabase console or SDK)
-- =====================================================================
-- 1. teacher-notes
--    - Path: {user_id}/{subject}/assignment-{assignment_no}/{filename}
--    - Public: false
--    - Purpose: Store teacher reference notes/materials

-- 2. assignments
--    - Path: {user_id}/{subject}/semester-{semester}/assignment-{assignment_no}/{filename}
--    - Public: false
--    - Purpose: Store generated assignment PDFs

-- 3. submissions (recommended)
--    - Path: {assignment_id}/{student_id}/{filename}
--    - Public: false
--    - Purpose: Store student submission files


-- =====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================================

-- Enable RLS on all tables
ALTER TABLE public.faculty_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.answer_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- Faculty can see their own metadata
CREATE POLICY "Faculty view own metadata" ON public.faculty_metadata
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Faculty update own metadata" ON public.faculty_metadata
  FOR UPDATE USING (user_id = auth.uid());

-- Faculty can see their own assignments
CREATE POLICY "Faculty view own assignments" ON public.assignments
  FOR SELECT USING (faculty_id = auth.uid());

CREATE POLICY "Faculty create assignments" ON public.assignments
  FOR INSERT WITH CHECK (faculty_id = auth.uid());

CREATE POLICY "Faculty update own assignments" ON public.assignments
  FOR UPDATE USING (faculty_id = auth.uid());

-- Students can see their own submissions
CREATE POLICY "Students view own submissions" ON public.submissions
  FOR SELECT USING (student_id = auth.uid());

CREATE POLICY "Faculty view assignment submissions" ON public.submissions
  FOR SELECT USING (
    assignment_id IN (
      SELECT id FROM public.assignments WHERE faculty_id = auth.uid()
    )
  );

-- Students can see their own evaluations
CREATE POLICY "Students view own evaluations" ON public.evaluations
  FOR SELECT USING (
    submission_id IN (
      SELECT id FROM public.submissions WHERE student_id = auth.uid()
    )
  );

-- Faculty can see evaluations for their assignments
CREATE POLICY "Faculty view evaluation" ON public.evaluations
  FOR SELECT USING (
    submission_id IN (
      SELECT s.id FROM public.submissions s
      JOIN public.assignments a ON s.assignment_id = a.id
      WHERE a.faculty_id = auth.uid()
    )
  );


-- =====================================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================================

-- View: Assignment Summary with submission stats
CREATE OR REPLACE VIEW assignment_stats AS
SELECT
  a.id,
  a.assignment_no,
  a.subject,
  a.semester,
  a.faculty_id,
  COUNT(DISTINCT s.id) as total_submissions,
  COUNT(DISTINCT CASE WHEN s.status = 'submitted' THEN s.id END) as submitted_count,
  COUNT(DISTINCT CASE WHEN s.status = 'pending' THEN s.id END) as pending_count,
  COUNT(DISTINCT CASE WHEN s.is_late = true THEN s.id END) as late_submissions,
  ROUND(AVG(e.percentage)::numeric, 2) as avg_percentage,
  ROUND(AVG(e.marks_obtained)::numeric, 2) as avg_marks,
  a.created_at
FROM public.assignments a
LEFT JOIN public.submissions s ON a.id = s.assignment_id
LEFT JOIN public.evaluations e ON s.id = e.submission_id
GROUP BY a.id, a.assignment_no, a.subject, a.semester, a.faculty_id, a.created_at;

-- View: Student Performance Summary
CREATE OR REPLACE VIEW student_performance AS
SELECT
  s.student_id,
  COUNT(DISTINCT s.assignment_id) as total_assignments,
  COUNT(DISTINCT CASE WHEN s.status = 'graded' THEN s.assignment_id END) as graded_assignments,
  ROUND(AVG(e.percentage)::numeric, 2) as avg_percentage,
  ROUND(AVG(e.marks_obtained)::numeric, 2) as avg_marks,
  MAX(e.percentage) as highest_percentage,
  MIN(e.percentage) as lowest_percentage
FROM public.submissions s
LEFT JOIN public.evaluations e ON s.id = e.submission_id
GROUP BY s.student_id;


-- =====================================================================
-- INITIAL DATA / HELPER SQL
-- =====================================================================

-- Function to auto-grade based on percentage
CREATE OR REPLACE FUNCTION calculate_grade(percentage real)
RETURNS text AS $$
BEGIN
  RETURN CASE
    WHEN percentage >= 90 THEN 'A'
    WHEN percentage >= 80 THEN 'B'
    WHEN percentage >= 70 THEN 'C'
    WHEN percentage >= 60 THEN 'D'
    ELSE 'F'
  END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to check if submission is late
CREATE OR REPLACE FUNCTION check_if_late()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.submitted_at > (SELECT submission_date FROM public.assignments WHERE id = NEW.assignment_id) THEN
    NEW.is_late := true;
    NEW.days_late := (NEW.submitted_at::date) - (SELECT submission_date FROM public.assignments WHERE id = NEW.assignment_id);
    NEW.status := 'late';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-check late submissions
CREATE TRIGGER trigger_check_late
BEFORE INSERT OR UPDATE ON public.submissions
FOR EACH ROW
EXECUTE FUNCTION check_if_late();

-- =====================================================================
-- MIGRATION NOTES
-- =====================================================================
/*
Steps to deploy this schema:

1. Connect to your Supabase project
2. Go to SQL Editor
3. Run this entire script
4. Create storage buckets:
   - teacher-notes (private)
   - assignments (private)
   - submissions (private) [recommended]

5. Verify all tables and indexes are created
6. Create RLS policies in dashboard if needed

For first-time setup with existing users from backend:
- User profiles are already in auth.users
- user_profiles table syncs from backend
- No migration needed, just schema extension
*/

-- =====================================================================
-- END OF SCHEMA
-- =====================================================================
