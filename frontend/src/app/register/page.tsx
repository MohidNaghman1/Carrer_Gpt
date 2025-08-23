// frontend/src/app/register/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import apiClient from "../../services/api"; // Using relative path

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
      // Call the /auth/register endpoint, which expects JSON
      await apiClient.post("/auth/register", { email, password });

      // On successful registration, redirect to the login page with a success message (optional)
      alert("Registration successful! Please sign in.");
      router.push("/login");
    } catch (err: any) {
      // Check the browser console (F12) for detailed CORS or network errors
      if (err.response && err.response.data.detail) {
        setError(err.response.data.detail); // Show error from backend (e.g., "Email already registered")
      } else {
        setError("An unexpected error occurred during registration.");
        console.error("Registration failed:", err); // Log the full error
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="w-full max-w-md p-8 space-y-8 bg-white/90 rounded-2xl shadow-xl border border-gray-100">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">
            Create an Account
          </h1>
          <p className="mt-2 text-gray-600">
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
                className="relative block w-full px-4 py-3 text-gray-900 placeholder-gray-400 border border-gray-300 rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-500 focus:z-10 sm:text-base transition-all shadow-sm"
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
                className={`relative block w-full px-4 py-3 text-gray-900 placeholder-gray-400 border rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-500 focus:z-10 sm:text-base transition-all shadow-sm ${
                  passwordTouched && password.length < minPasswordLength
                    ? "border-red-400"
                    : "border-gray-300"
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
              className="relative flex justify-center w-full px-4 py-3 text-base font-semibold text-white bg-indigo-600 border border-transparent rounded-lg group hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-400 disabled:bg-indigo-300 disabled:cursor-not-allowed shadow-md transition-all"
            >
              {loading ? "Creating Account..." : "Create Account"}
            </button>
          </div>
        </form>
        <p className="mt-4 text-sm text-center text-gray-600">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-semibold text-indigo-600 hover:text-indigo-500 transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
