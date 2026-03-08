-- Run this in your Supabase SQL Editor
-- Go to: Project → SQL Editor → New Query → Paste and run

-- Questions table: records every question a user asks
CREATE TABLE IF NOT EXISTS questions (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     text NOT NULL,
  question    text NOT NULL,
  skill_level text NOT NULL DEFAULT 'beginner',
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- Quiz scores table: records quiz results
CREATE TABLE IF NOT EXISTS quiz_scores (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    text NOT NULL,
  topic      text NOT NULL,
  score      integer NOT NULL,
  total      integer NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes for fast per-user queries
CREATE INDEX IF NOT EXISTS idx_questions_user_id  ON questions(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_scores_user_id ON quiz_scores(user_id);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE questions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_scores ENABLE ROW LEVEL SECURITY;

-- Allow anon key full access (MVP — lock down in production)
CREATE POLICY "allow_all_questions"   ON questions   FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_quiz_scores" ON quiz_scores FOR ALL USING (true) WITH CHECK (true);
