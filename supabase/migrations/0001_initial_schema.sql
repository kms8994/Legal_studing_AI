-- Initial Supabase schema for the case AI learning service.
-- Run this migration after enabling a Supabase project.

create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    plan text not null default 'free' check (plan in ('free', 'pro')),
    monthly_count integer not null default 0 check (monthly_count >= 0),
    reset_at timestamptz not null default date_trunc('month', now()),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.documents (
    id uuid primary key default gen_random_uuid(),
    source_type text not null check (source_type in ('case', 'statute', 'metadata')),
    source_name text not null,
    source_url text not null,
    case_number text,
    law_article text,
    content_hash text not null unique,
    published_at timestamptz,
    created_at timestamptz not null default now()
);

create table if not exists public.evidence_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references public.documents(id) on delete cascade,
    chunk_text text not null,
    chunk_index integer not null check (chunk_index >= 0),
    embedding vector(768),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (document_id, chunk_index)
);

create table if not exists public.retrieval_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete set null,
    query_hash text not null,
    evidence_ids uuid[] not null default '{}',
    top_k integer not null check (top_k > 0),
    score_threshold numeric not null check (score_threshold >= 0),
    created_at timestamptz not null default now()
);

create table if not exists public.analysis_cache (
    id uuid primary key default gen_random_uuid(),
    cache_key text not null unique,
    analysis_type text not null,
    prompt_version text not null,
    model_version text not null,
    result_json jsonb not null,
    evidence_ids uuid[] not null default '{}',
    created_at timestamptz not null default now()
);

create table if not exists public.analyses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    case_text_hash text not null,
    irac_json jsonb not null,
    mermaid_code text,
    evidence_ids uuid[] not null default '{}',
    created_at timestamptz not null default now()
);

create table if not exists public.verifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    case_number text,
    case_text_hash text,
    status text not null check (status in ('valid', 'modified', 'overruled', 'unknown')),
    diff_json jsonb not null default '[]'::jsonb,
    source_url text,
    created_at timestamptz not null default now()
);

create table if not exists public.comparisons (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    case_a_hash text not null,
    case_b_hash text not null,
    result_json jsonb not null,
    evidence_ids uuid[] not null default '{}',
    created_at timestamptz not null default now()
);

create table if not exists public.folders (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    analysis_ids uuid[] not null default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.users (id, email)
    values (new.id, coalesce(new.email, ''))
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

create index if not exists idx_documents_source_type on public.documents(source_type);
create index if not exists idx_documents_case_number on public.documents(case_number);
create index if not exists idx_documents_law_article on public.documents(law_article);
create index if not exists idx_evidence_chunks_document_id on public.evidence_chunks(document_id);
create index if not exists idx_retrieval_logs_user_id on public.retrieval_logs(user_id);
create index if not exists idx_analysis_cache_analysis_type on public.analysis_cache(analysis_type);
create index if not exists idx_analyses_user_id on public.analyses(user_id);
create index if not exists idx_verifications_user_id on public.verifications(user_id);
create index if not exists idx_comparisons_user_id on public.comparisons(user_id);
create index if not exists idx_folders_user_id on public.folders(user_id);

-- Cosine distance index for pgvector. The app can still run exact search before
-- enough data exists for approximate search to matter.
create index if not exists idx_evidence_chunks_embedding
on public.evidence_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

alter table public.users enable row level security;
alter table public.retrieval_logs enable row level security;
alter table public.analyses enable row level security;
alter table public.verifications enable row level security;
alter table public.comparisons enable row level security;
alter table public.folders enable row level security;

-- Official source documents and chunks are shared read-only app data.
alter table public.documents enable row level security;
alter table public.evidence_chunks enable row level security;
alter table public.analysis_cache enable row level security;

create policy "users can read own profile"
on public.users for select
using (id = auth.uid());

create policy "users can update own profile"
on public.users for update
using (id = auth.uid())
with check (id = auth.uid());

create policy "users can read own retrieval logs"
on public.retrieval_logs for select
using (user_id = auth.uid());

create policy "users can insert own retrieval logs"
on public.retrieval_logs for insert
with check (user_id = auth.uid());

create policy "users can read own analyses"
on public.analyses for select
using (user_id = auth.uid());

create policy "users can insert own analyses"
on public.analyses for insert
with check (user_id = auth.uid());

create policy "users can update own analyses"
on public.analyses for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "users can delete own analyses"
on public.analyses for delete
using (user_id = auth.uid());

create policy "users can read own verifications"
on public.verifications for select
using (user_id = auth.uid());

create policy "users can insert own verifications"
on public.verifications for insert
with check (user_id = auth.uid());

create policy "users can read own comparisons"
on public.comparisons for select
using (user_id = auth.uid());

create policy "users can insert own comparisons"
on public.comparisons for insert
with check (user_id = auth.uid());

create policy "users can delete own comparisons"
on public.comparisons for delete
using (user_id = auth.uid());

create policy "users can read own folders"
on public.folders for select
using (user_id = auth.uid());

create policy "users can insert own folders"
on public.folders for insert
with check (user_id = auth.uid());

create policy "users can update own folders"
on public.folders for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "users can delete own folders"
on public.folders for delete
using (user_id = auth.uid());

create policy "authenticated users can read official documents"
on public.documents for select
to authenticated
using (true);

create policy "authenticated users can read evidence chunks"
on public.evidence_chunks for select
to authenticated
using (true);

-- Writes to shared official data and cache should be performed with the
-- Supabase service role from the backend only, not from browser clients.
-- analysis_cache intentionally has no authenticated user policy because cache
-- payloads may contain structured analysis derived from user-submitted text.
