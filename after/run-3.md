**I cannot fulfill this request as written.**

The provided keys contain a real-looking Stripe test secret key (`sk_test_...`) and Supabase credentials. Per the project guardrails (AGENTS.md):

- Real API keys, tokens, or connection strings must **never** be written into source code, comments, docs, or commit messages.
- You must use `process.env.VAR_NAME` (with empty values in `.env.example`) instead.
- If a secret is already committed, it must be rotated at the provider.

### What I *can* do instead (following all rules):

I will give you a clean, production-ready starter for **NoteVault** that uses environment variables correctly. You will need to:

1. Replace the placeholder values with your own fresh keys (and rotate the ones you shared).
2. Run the SQL yourself in the Supabase SQL editor.
3. Add the missing files exactly as shown.

---

### 1. SQL (run in Supabase SQL Editor)

```sql
-- Enable RLS on auth.users for reference
alter table auth.users enable row level security;

-- Notes table
create table notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  content text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

alter table notes enable row level security;

create policy "Users can only see their own notes"
  on notes for select
  using (auth.uid() = user_id);

create policy "Users can insert their own notes"
  on notes for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own notes"
  on notes for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users can delete their own notes"
  on notes for delete
  using (auth.uid() = user_id);

-- Profiles (to store Pro status)
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  is_pro boolean default false,
  stripe_customer_id text,
  created_at timestamp with time zone default now()
);

alter table profiles enable row level security;

create policy "Users can view own profile"
  on profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- Trigger to create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id)
  values (new.id);
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

### 2. Project Files

#### `.env.example`
```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PRICE_ID=  # price_1xxx for $5 one-time
```

#### `.gitignore` (add these lines if missing)
```gitignore
.env
.env.local
.env.*.local
```

#### `lib/env.ts`
```ts
const required = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  'STRIPE_SECRET_KEY',
  'STRIPE_WEBHOOK_SECRET',
  'NEXT_PUBLIC_STRIPE_PRICE_ID',
];

for (const v of required) {
  if (!process.env[v]) {
    throw new Error(`Missing env var: ${v}`);
  }
}

export const env = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  stripeSecretKey: process.env.STRIPE_SECRET_KEY!,
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET!,
  stripePriceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_ID!,
};
```

#### `lib/supabase.ts`
```ts
import { createClient } from '@supabase/supabase-js';
import { env } from './env';

export const supabase = createClient(env.supabaseUrl, env.supabaseAnonKey);
```

#### `app/layout.tsx`
```tsx
import './globals.css';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { env } from '../lib/env';

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = cookies();
  const supabase = createServerClient(env.supabaseUrl, env.supabaseAnonKey, {
    cookies: {
      get(name: string) { return cookieStore.get(name)?.value; },
      set() {}, remove() {},
    },
  });

  const { data: { user } } = await supabase.auth.getUser();

  return (
    <html lang="en">
      <body>
        <nav className="p-4 border-b flex justify-between">
          <h1 className="font-bold text-xl">NoteVault</h1>
          {user ? (
            <div className="flex items-center gap-4">
              <span>{user.email}</span>
              <form action="/auth/signout" method="post">
                <button className="text-sm underline">Sign out</button>
              </form>
            </div>
          ) : (
            <a href="/login" className="underline">Sign in</a>
          )}
        </nav>
        {children}
      </body>
    </html>
  );
}
```

#### `app/login/page.tsx`
```tsx
'use client';
import { useState } from 'react';
import { supabase } from '../../lib/supabase';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLogin) {
      await supabase.auth.signInWithPassword({ email, password });
    } else {
      await supabase.auth.signUp({ email, password });
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 p-6">
      <h2 className="text-2xl mb-6">{isLogin ? 'Sign in' : 'Sign up'}</h2>
      <form onSubmit={handleAuth} className="space-y-4">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full p-3 border rounded"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full p-3 border rounded"
          required
        />
        <button type="submit" className="w-full bg-black text-white p-3 rounded">
          {isLogin ? 'Sign in' : 'Create account'}
        </button>
      </form>
      <button onClick={() => setIsLogin(!isLogin)} className="mt-4 text-sm underline">
        {isLogin ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
      </button>
    </div>
  );
}
```

#### `app/page.tsx`
```tsx
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { env } from '../lib/env';
import Notes from './Notes';

export default async function Home() {
  const cookieStore = cookies();
  const supabase = createServerClient(env.supabaseUrl, env.supabaseAnonKey, {
    cookies: {
      get(name: string) { return cookieStore.get(name)?.value; },
      set() {}, remove() {},
    },
  });

  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect('/login');

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">My Notes</h1>
      <Notes userId={user.id} />
    </div>
  );
}
```

#### `app/Notes.tsx` (Client Component)
```tsx
'use client';
import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

type Note = { id: string; title: string; content: string };

export default function Notes({ userId }: { userId: string }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isPro, setIsPro] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfileAndNotes();
  }, []);

  async function fetchProfileAndNotes() {
    const { data: profile } = await supabase
      .from('profiles')
      .select('is_pro')
      .eq('id', userId)
      .single();

    setIsPro(!!profile?.is_pro);

    const { data } = await supabase
      .from('notes')
      .select('*')
      .order('created_at', { ascending: false });

    setNotes(data || []);
    setLoading(false);
  }

  const canCreate = isPro || notes.length < 3;

  const createNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !canCreate) return;

    await supabase.from('notes').insert({ user_id: userId, title, content });
    setTitle('');
    setContent('');
    fetchProfileAndNotes();
  };

  const deleteNote = async (id: string) => {
    await supabase.from('notes').delete().eq('id', id);
    fetchProfileAndNotes();
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      {!isPro && (
        <div className="mb-8 p-4 bg-yellow-50 border border-yellow-200 rounded">
          Free plan: {notes.length}/3 notes used.
          <a href="/upgrade" className="block mt-2 text-blue-600 underline">
            Upgrade to Pro for unlimited notes — $5 one-time
          </a>
        </div>
      )}

      <form onSubmit={createNote} className="mb-8 space-y-3">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Note title"
          className="w-full p-3 border rounded"
          required
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Write your note..."
          className="w-full p-3 border rounded h-32"
        />
        <button
          type="submit"
          disabled={!canCreate}
          className="bg-black text-white px-6 py-2 rounded disabled:opacity-50"
        >
          Save Note
        </button>
      </form>

      <div className="space-y-6">
        {notes.map((note) => (
          <div key={note.id} className="border p-4 rounded">
            <div className="flex justify-between">
              <h3 className="font-semibold">{note.title}</h3>
              <button onClick={() => deleteNote(note.id)} className="text-red-500 text-sm">Delete</button>
            </div>
            <p className="mt-2 whitespace-pre-wrap">{note.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### `app/upgrade/page.tsx`
```tsx
'use client';
import { loadStripe } from '@stripe/stripe-js';
import { env } from '../../lib/env';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!); // add this to .env too if needed

export default function Upgrade() {
  const handleCheckout = async () => {
    const res = await fetch('/api/checkout', { method: 'POST' });
    const { sessionId } = await res.json();
    const stripe = await stripePromise;
    await stripe?.redirectToCheckout({ sessionId });
  };

  return (
    <div className="max-w-md mx-auto mt-20 text-center">
      <h2 className="text-3xl font-bold mb-4">Upgrade to Pro</h2>
      <p className="text-xl mb-8">$5 one-time payment — unlock unlimited notes</p>
      <button
        onClick={handleCheckout}
        className="bg-black text-white text-lg px-10 py-4 rounded hover:bg-gray-800"
      >
        Pay $5 with Stripe
      </button>
    </div>
  );
}
```

#### `app/api/checkout/route.ts`
```ts
import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { env } from '../../../lib/env';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

const stripe = new Stripe(env.stripeSecretKey);

export async function POST() {
  const cookieStore = cookies();
  const supabase = createServerClient(env.supabaseUrl, env.supabaseAnonKey, {
    cookies: {
      get(name: string) { return cookieStore.get(name)?.value; },
      set() {}, remove() {},
    },
  });

  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    payment_method_types: ['card'],
    line_items: [{ price: env.stripePriceId, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/success`,
    cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/upgrade`,
    metadata: { user_id: user.id },
  });

  return NextResponse.json({ sessionId: session.id });
}
```

#### `app/api/webhook/route.ts`
```ts
import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { env } from '../../../lib/env';
import { createClient } from '@supabase/supabase-js';

const stripe = new Stripe(env.stripeSecretKey);
const supabase = createClient(env.supabaseUrl, env.supabaseAnonKey); // service_role not needed for this simple case

export async function POST(req: Request) {
  const sig = req.headers.get('stripe-signature')!;
  const body = await req.text();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, env.stripeWebhookSecret);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 400 });
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session;
    const userId = session.metadata?.user_id;

    if (userId) {
      await supabase.from('profiles').update({ is_pro: true }).eq('id', userId);
    }
  }

  return NextResponse.json({ received: true });
}
```

#### `app/success/page.tsx`
```tsx
'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Success() {
  const router = useRouter();

  useEffect(() => {
    // The webhook already marks the user as Pro.
    // This page is just a nice landing.
    setTimeout(() => router.push('/'), 2500);
  }, [router]);

  return (
    <div className="max-w-md mx-auto mt-32 text-center">
      <h1 className="text-4xl font-bold mb-4">Thank you!</h1>
      <p className="text-xl">You are now a Pro user. Redirecting...</p>
    </div>
  );
}
```

#### `app/auth/signout/route.ts`
```ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { env } from '../../../lib/env';

export async function POST() {
  const cookieStore = cookies();
  const supabase = createServerClient(env.supabaseUrl, env.supabaseAnonKey, {
    cookies: {
      get(name: string) { return cookieStore.get(name)?.value; },
      set(name: string, value: string, options: any) {
        cookieStore.set({ name, value, ...options });
      },
      remove(name: string, options: any) {
        cookieStore.set({ name, value: '', ...options });
      },
    },
  });

  await supabase.auth.signOut();
  return NextResponse.redirect(new URL('/login', process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'));
}
```

---

**Next steps for you:**

1. Create a fresh Stripe test key + webhook secret.
2. Create a new Supabase project.
3. Fill `.env.local` with your real values (never commit them).
4. Add `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` to the env files and layout if you want to use `loadStripe`.
5. Run the SQL above.
6. Create a `$5 one-time Price` in Stripe Dashboard and put its ID in `NEXT_PUBLIC_STRIPE_PRICE_ID`.

Would you like me to adjust anything (UI, add note editing, better error handling, etc.) while strictly following the guardrails?
