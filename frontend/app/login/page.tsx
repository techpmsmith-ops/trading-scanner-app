"use client";

import { useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { Disclaimer } from "@/components/Disclaimer";
import { api } from "@/lib/api";

type LoginResponse = {
  access_token: string;
  token_type: string;
  user: {
    email: string;
  };
};

export default function LoginPage() {
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      const secureCookie = window.location.protocol === "https:" || process.env.NEXT_PUBLIC_APP_ENV === "production";
      document.cookie = `scanner_token=${encodeURIComponent(response.access_token)}; path=/; max-age=43200; SameSite=Lax${secureCookie ? "; Secure" : ""}`;
      window.location.href = searchParams.get("next") || "/";
    } catch {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-6 py-12">
      <Disclaimer />
      <div>
        <h1 className="text-2xl font-semibold">Private Login</h1>
        <p className="mt-2 text-sm text-muted">Sign in to access the scanner, journal, and performance pages.</p>
      </div>
      <form onSubmit={submit} className="space-y-4 rounded-md border border-border bg-panel p-5">
        <label className="grid gap-1 text-sm text-muted">
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required className="px-3 py-2" />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Password
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required className="px-3 py-2" />
        </label>
        {error ? <p className="text-sm text-danger">{error}</p> : null}
        <button disabled={loading} className="w-full bg-positive px-4 py-2 text-sm font-semibold text-[#07130d] disabled:opacity-60">
          {loading ? "Signing in" : "Sign In"}
        </button>
      </form>
    </div>
  );
}
