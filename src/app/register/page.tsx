"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password);
      router.push("/");
      router.refresh();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-2xl border bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h1 className="text-xl font-semibold">Create account</h1>
        <p className="mt-1 text-sm text-slate-500">Your content is private to this account.</p>
        {error && <div className="mt-4 rounded bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-950/40">{error}</div>}
        <label className="mt-4 block text-sm font-medium">Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required className="mt-1 w-full rounded-lg border px-3 py-2 text-sm dark:bg-slate-800" />
        <label className="mt-3 block text-sm font-medium">Password (min 8)</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required minLength={8} className="mt-1 w-full rounded-lg border px-3 py-2 text-sm dark:bg-slate-800" />
        <button disabled={loading} type="submit" className="mt-6 w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-white dark:text-slate-900">
          {loading ? "Creating…" : "Create account"}
        </button>
        <p className="mt-4 text-center text-sm text-slate-500">
          Have an account? <a href="/login" className="font-medium text-slate-900 underline dark:text-white">Sign in</a>
        </p>
      </form>
    </div>
  );
}
