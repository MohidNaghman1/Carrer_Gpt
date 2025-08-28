// frontend/src/app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import apiClient from "@/services/api"; // Using clean path alias
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const auth = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await apiClient.post("/auth/token", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const { access_token } = response.data;
      auth.login(access_token);
    } catch (err: any) {
      if (err.response && err.response.status === 401) {
        setError("Incorrect email or password. Please try again.");
      } else {
        setError("An unexpected error occurred. Please try again later.");
        console.error("Login failed:", err);
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
            Welcome Back
          </h1>
          <p className="mt-2 text-blue-100">
            Sign in to access your CareerGPT dashboard.
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
                autoComplete="current-password"
                required
                className="relative block w-full px-4 py-3 text-white placeholder-blue-200 bg-slate-800 border border-blue-900 rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-500 focus:z-10 sm:text-base transition-all shadow-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
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
              disabled={loading}
              className="relative flex justify-center w-full px-4 py-3 text-base font-semibold text-white bg-blue-700 border border-blue-800 rounded-lg group hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400 disabled:bg-blue-300 disabled:cursor-not-allowed shadow-lg transition-all"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </div>
        </form>
        <p className="mt-4 text-sm text-center text-blue-100">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-semibold text-blue-400 hover:text-white transition-colors"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
