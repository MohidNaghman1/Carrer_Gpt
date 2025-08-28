// frontend/src/app/register/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import apiClient from "@/services/api"; // Using clean path alias

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const minPasswordLength = 8;
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setPasswordTouched(true);
    if (password.length < minPasswordLength) {
      setError(`Password must be at least ${minPasswordLength} characters.`);
      return;
    }
    setLoading(true);

    try {
      await apiClient.post("/auth/register", { email, password });
      alert("Registration successful! Please sign in.");
      router.push("/login");
    } catch (err: any) {
      if (err.response && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("An unexpected error occurred during registration.");
        console.error("Registration failed:", err);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900">
      <div className="w-full max-w-md p-8 space-y-8 bg-slate-900/95 rounded-2xl shadow-2xl border border-blue-900/60">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-white drop-shadow">
            Create an Account
          </h1>
          <p className="mt-2 text-blue-100">
            Get started with your AI-powered career assistant.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4 rounded-md">
            <div>
              <label htmlFor="email-address" className="sr-only">
                Email address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="relative block w-full px-4 py-3 text-white placeholder-blue-200 bg-slate-800 border border-blue-900 rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-500 focus:z-10 sm:text-base transition-all shadow-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                className={`relative block w-full px-4 py-3 text-white placeholder-blue-200 bg-slate-800 border rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-500 focus:z-10 sm:text-base transition-all shadow-sm ${
                  passwordTouched && password.length < minPasswordLength
                    ? "border-red-400"
                    : "border-blue-900"
                }`}
                placeholder="Password (min 8 characters)"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setPasswordTouched(true);
                }}
                minLength={minPasswordLength}
              />
              {passwordTouched &&
                password.length > 0 &&
                password.length < minPasswordLength && (
                  <p className="mt-1 text-xs text-red-500">
                    Password too short (min {minPasswordLength} characters)
                  </p>
                )}
            </div>
          </div>

          {error && (
            <p className="text-sm text-center text-red-600 font-medium">
              {error}
            </p>
          )}

          <div>
            <button
              type="submit"
              disabled={loading || password.length < minPasswordLength}
              className="relative flex justify-center w-full px-4 py-3 text-base font-semibold text-white bg-blue-700 border border-blue-800 rounded-lg group hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400 disabled:bg-blue-300 disabled:cursor-not-allowed shadow-lg transition-all"
            >
              {loading ? "Creating Account..." : "Create Account"}
            </button>
          </div>
        </form>
        <p className="mt-4 text-sm text-center text-blue-100">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-semibold text-blue-400 hover:text-white transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
