# Supabase Setup

This folder contains database migrations for the RAG-based case AI learning service.

## Phase 2 Scope

The initial migration prepares:

- user plan and usage tracking
- official source document metadata
- RAG evidence chunks with `pgvector`
- retrieval logs
- Gemini analysis cache
- saved analyses
- verification results
- comparison results
- user folders
- RLS policies for user-owned data

## Apply Order

1. Create a Supabase project.
2. Enable the `vector` extension or run the migration as a privileged database role.
3. Apply `migrations/0001_initial_schema.sql`.
4. Confirm RLS is enabled on all user-owned tables.
5. Confirm the vector index exists on `public.evidence_chunks.embedding`.

## Data Retention Notes

- User-submitted case text should be stored as hashes unless the user explicitly saves an analysis.
- Official source documents can be stored because they come from public legal data sources.
- Analysis cache stores structured AI output, evidence IDs, prompt version, and model version.
- Browser clients must not read or write shared official documents, evidence chunks, or analysis cache directly unless a RLS policy explicitly allows it.
- Service-role writes should stay in the backend only.

## Live Verification Checklist

- Run a Supabase connection test from the backend.
- Insert a test user and confirm `users.id = auth.uid()` RLS behavior.
- Insert an evidence chunk and confirm vector search works.
- Confirm a different user cannot read another user's `analyses`, `comparisons`, or `folders`.
