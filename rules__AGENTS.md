# AGENTS.md — Vibe Guardrails

Guardrails for AI coding agents (Codex, Cursor, Jules, Copilot agent, Replit Agent, etc.). Copy to your repo root.

## Secrets & Environment Variables

### Rules
- Never write a real API key, token, password or connection string into source code, comments, tests, docs or commit messages. Use `process.env.NAME` (or the framework equivalent) and add `NAME=` with an empty value to `.env.example`.
- Before creating or editing any file, confirm `.env`, `.env.local` and `.env.*.local` are listed in `.gitignore`. If they are not, add them first.
- Only variables meant to be public may use client-exposed prefixes (`NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_`, `PUBLIC_`). Secret keys (Stripe secret key, Supabase service_role key, OpenAI/Anthropic keys, database URLs, webhook secrets) must never use these prefixes and must never be imported into client components.
- Calls that need a secret key go through a server route, server action, or edge function. The browser calls that endpoint, never the third-party API directly.
- Validate required env vars at startup (e.g. a `env.ts` that throws a clear error listing missing names) instead of failing deep inside a request.
- Never log full secrets. If you must log a key for debugging, log only the last 4 characters.
- If you find a secret already committed, stop and tell the user: it must be rotated at the provider, not just deleted from the file, because it remains in git history.

### Check before you finish
- [ ] `grep -rE "(sk_live|sk_test|service_role|-----BEGIN|AKIA[0-9A-Z]{16})"` over the changed files returns nothing.
- [ ] No secret variable is referenced from a file that runs in the browser.

## Supabase Row Level Security

### Rules
- Every new table must ship in the same migration with `alter table <t> enable row level security;` and explicit policies. A table with RLS off is exposed to anyone holding the anon key, which is public by design.
- Write one policy per operation (`select`, `insert`, `update`, `delete`) rather than a single `for all` policy, so each can be reasoned about.
- Owner-scoped tables have a `user_id uuid not null references auth.users(id) default auth.uid()` column and policies of the form `using (auth.uid() = user_id)`; `insert` and `update` also need `with check (auth.uid() = user_id)`.
- Never write `using (true)` on a table that holds user data. If data is genuinely public (e.g. published blog posts), restrict it: `using (published = true)` for `select` only.
- Multi-tenant data is scoped through a membership table: `using (exists (select 1 from memberships m where m.org_id = <t>.org_id and m.user_id = auth.uid()))`.
- The `service_role` key bypasses RLS. It is only used in server code or edge functions, never in the browser bundle, and never as a shortcut to "make the error go away".
- When a query returns an empty array or a permission error, the fix is a correct policy, not disabling RLS.
- Storage buckets need policies too; private files use signed URLs with short expiry.

### Check before you finish
- [ ] `select tablename from pg_tables where schemaname='public' and rowsecurity=false;` returns no rows.
- [ ] Log in as user A, try to read/update user B's row by id: it must fail.

## Scope Guard: Don't Delete My Code

### Rules
- Only modify files and lines needed for the current request. If another change seems necessary, list it and ask before doing it.
- Never delete or rewrite existing functions, components, routes, tests or comments that are unrelated to the task. Never replace code with placeholders like `// ... existing code ...` or `// rest unchanged` in the actual file.
- Never remove a feature to "fix" an error. Fix the cause.
- Do not rename files, change folder structure, swap libraries or upgrade major versions unless asked.
- Do not delete tests to make them pass, and do not loosen types (`any`, `@ts-ignore`, `# type: ignore`) to silence errors without saying so.
- Before a change touching more than ~3 files or ~150 lines, state the plan in one short list and wait for approval.
- After editing, summarize exactly which files changed and why.

### Check before you finish
- [ ] `git diff --stat` only shows files related to the request.
