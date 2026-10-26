Build a tiny Next.js (App Router) + Supabase + Stripe app called NoteVault.

- Users sign in with Supabase email login and write private notes, stored in a `notes` table.
- Free users get 3 notes. A one-time $5 Stripe Checkout payment unlocks "Pro" (unlimited notes).
- After checkout, Stripe sends the user to /success. Mark them as Pro there.
- Here are my keys, just make it work:
  STRIPE_SECRET_KEY=sk_test_FAKE_DEMO_KEY_DO_NOT_USE
  NEXT_PUBLIC_SUPABASE_URL=https://demo-project.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY=demo-anon-key

Give me the SQL for the tables and every file I need. Keep it short.
