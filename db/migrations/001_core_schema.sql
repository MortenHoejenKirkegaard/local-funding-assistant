CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE companies (
  id text PRIMARY KEY,
  display_name text,
  short_description text,
  therapeutic_area text,
  technology_type text,
  product_stage text,
  trl integer CHECK (trl IS NULL OR (trl >= 1 AND trl <= 9)),
  regulatory_stage text,
  ip_status text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id text NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name text NOT NULL,
  objective text,
  stage text,
  funding_need_amount numeric,
  funding_need_currency text DEFAULT 'DKK',
  target_deadline date,
  milestones jsonb NOT NULL DEFAULT '[]'::jsonb,
  known_gaps jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id text REFERENCES companies(id) ON DELETE SET NULL,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  source_path text NOT NULL,
  sha256 text NOT NULL,
  document_type text NOT NULL,
  title text,
  language text,
  confidentiality text NOT NULL DEFAULT 'confidential'
    CHECK (confidentiality IN ('internal', 'confidential', 'highly_confidential')),
  indexed_at timestamptz,
  parser text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_path, sha256)
);

CREATE TABLE document_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  company_id text REFERENCES companies(id) ON DELETE SET NULL,
  chunk_index integer NOT NULL,
  text text NOT NULL,
  page_number integer,
  sheet_name text,
  section_heading text,
  token_count integer,
  embedding_id text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (document_id, chunk_index)
);

CREATE TABLE funders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  country text NOT NULL DEFAULT 'DK',
  website text,
  profile_type text CHECK (
    profile_type IS NULL OR profile_type IN (
      'impact',
      'research',
      'commercialization',
      'clinical',
      'mixed'
    )
  ),
  typical_grant_size_min numeric,
  typical_grant_size_max numeric,
  typical_requirements jsonb NOT NULL DEFAULT '{}'::jsonb,
  historical_notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name, country)
);

CREATE TABLE funding_calls (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  funder_id uuid REFERENCES funders(id) ON DELETE SET NULL,
  title text NOT NULL,
  status text NOT NULL DEFAULT 'unknown'
    CHECK (status IN ('active', 'upcoming', 'closed', 'unknown')),
  opens_at date,
  deadline_at timestamptz,
  decision_at date,
  grant_min numeric,
  grant_max numeric,
  currency text DEFAULT 'DKK',
  focus_areas jsonb NOT NULL DEFAULT '[]'::jsonb,
  eligibility_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
  documentation_requirements jsonb NOT NULL DEFAULT '[]'::jsonb,
  evaluation_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
  source_url text,
  source_snapshot_path text,
  last_checked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE applications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id text REFERENCES companies(id) ON DELETE SET NULL,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  funding_call_id uuid REFERENCES funding_calls(id) ON DELETE SET NULL,
  funder_id uuid REFERENCES funders(id) ON DELETE SET NULL,
  title text NOT NULL,
  status text NOT NULL CHECK (status IN ('approved', 'rejected', 'submitted', 'draft')),
  submitted_at date,
  decision_at date,
  requested_amount numeric,
  awarded_amount numeric,
  currency text DEFAULT 'DKK',
  score_or_feedback text,
  source_path text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE match_scores (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  funding_call_id uuid NOT NULL REFERENCES funding_calls(id) ON DELETE CASCADE,
  company_id text NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  overall_score numeric NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
  strategic_fit_score numeric CHECK (strategic_fit_score IS NULL OR (strategic_fit_score >= 0 AND strategic_fit_score <= 100)),
  eligibility_score numeric CHECK (eligibility_score IS NULL OR (eligibility_score >= 0 AND eligibility_score <= 100)),
  evidence_score numeric CHECK (evidence_score IS NULL OR (evidence_score >= 0 AND evidence_score <= 100)),
  ip_score numeric CHECK (ip_score IS NULL OR (ip_score >= 0 AND ip_score <= 100)),
  commercial_score numeric CHECK (commercial_score IS NULL OR (commercial_score >= 0 AND commercial_score <= 100)),
  effort_score numeric CHECK (effort_score IS NULL OR (effort_score >= 0 AND effort_score <= 100)),
  deadline_urgency_score numeric CHECK (deadline_urgency_score IS NULL OR (deadline_urgency_score >= 0 AND deadline_urgency_score <= 100)),
  rationale text,
  missing_requirements jsonb NOT NULL DEFAULT '[]'::jsonb,
  recommended_action text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (funding_call_id, company_id, project_id)
);

CREATE TABLE drafts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id uuid NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  version integer NOT NULL,
  section text NOT NULL,
  content text NOT NULL,
  assumptions jsonb NOT NULL DEFAULT '[]'::jsonb,
  source_references jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (application_id, version, section)
);

CREATE TABLE notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel text NOT NULL CHECK (channel IN ('dashboard', 'slack', 'email')),
  recipient text,
  trigger_type text NOT NULL CHECK (trigger_type IN ('deadline', 'high_match', 'missing_requirement')),
  funding_call_id uuid REFERENCES funding_calls(id) ON DELETE SET NULL,
  company_id text REFERENCES companies(id) ON DELETE SET NULL,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  subject text NOT NULL,
  body text NOT NULL,
  contains_confidential_content boolean NOT NULL DEFAULT false,
  sent_at timestamptz,
  status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'failed')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor text NOT NULL,
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id text,
  company_id text REFERENCES companies(id) ON DELETE SET NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE api_usage_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  model text NOT NULL,
  task_type text NOT NULL,
  company_id text REFERENCES companies(id) ON DELETE SET NULL,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  input_tokens integer NOT NULL DEFAULT 0,
  cached_input_tokens integer NOT NULL DEFAULT 0,
  output_tokens integer NOT NULL DEFAULT 0,
  web_search_calls integer NOT NULL DEFAULT 0,
  estimated_cost_usd numeric NOT NULL DEFAULT 0,
  actual_cost_usd numeric,
  status text NOT NULL DEFAULT 'completed'
    CHECK (status IN ('estimated', 'approved', 'completed', 'failed', 'cancelled')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ingestion_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status text NOT NULL DEFAULT 'pending_user_selection'
    CHECK (status IN (
      'pending_user_selection',
      'approved',
      'moving',
      'parsing',
      'indexing',
      'indexed',
      'failed',
      'cancelled'
    )),
  original_filename text NOT NULL,
  original_path text,
  dropzone_path text NOT NULL,
  destination_path text,
  sha256 text,
  file_size_bytes bigint,
  file_extension text,
  mime_type text,
  suggested_company_id text REFERENCES companies(id) ON DELETE SET NULL,
  selected_company_id text REFERENCES companies(id) ON DELETE SET NULL,
  suggested_project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  selected_project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  suggested_document_type text,
  selected_document_type text,
  confidentiality text NOT NULL DEFAULT 'confidential'
    CHECK (confidentiality IN ('internal', 'confidential', 'highly_confidential')),
  user_approved_at timestamptz,
  indexed_document_id uuid REFERENCES documents(id) ON DELETE SET NULL,
  error_message text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ingestion_job_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingestion_job_id uuid NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
  event_type text NOT NULL,
  message text,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE action_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor text NOT NULL,
  action_type text NOT NULL CHECK (action_type IN (
    'local_read',
    'local_write',
    'api_analysis',
    'slack_output',
    'external_submission',
    'purchase',
    'agreement',
    'account_creation',
    'email_send'
  )),
  target text,
  company_id text REFERENCES companies(id) ON DELETE SET NULL,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  decision text NOT NULL DEFAULT 'blocked' CHECK (decision IN (
    'allowed',
    'requires_approval',
    'blocked'
  )),
  reason text NOT NULL,
  estimated_cost_usd numeric,
  user_approved_at timestamptz,
  executed_at timestamptz,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_projects_company_id ON projects(company_id);
CREATE INDEX idx_documents_company_id ON documents(company_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_company_id ON document_chunks(company_id);
CREATE INDEX idx_funding_calls_status_deadline ON funding_calls(status, deadline_at);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_company_id ON applications(company_id);
CREATE INDEX idx_match_scores_company_score ON match_scores(company_id, overall_score DESC);
CREATE INDEX idx_match_scores_call_score ON match_scores(funding_call_id, overall_score DESC);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_audit_events_company_time ON audit_events(company_id, created_at DESC);
CREATE INDEX idx_api_usage_events_company_time ON api_usage_events(company_id, created_at DESC);
CREATE INDEX idx_api_usage_events_task_time ON api_usage_events(task_type, created_at DESC);
CREATE INDEX idx_ingestion_jobs_status_time ON ingestion_jobs(status, created_at DESC);
CREATE INDEX idx_ingestion_jobs_selected_company ON ingestion_jobs(selected_company_id, created_at DESC);
CREATE INDEX idx_ingestion_job_events_job_time ON ingestion_job_events(ingestion_job_id, created_at DESC);
CREATE INDEX idx_action_requests_decision_time ON action_requests(decision, created_at DESC);
CREATE INDEX idx_action_requests_type_time ON action_requests(action_type, created_at DESC);
