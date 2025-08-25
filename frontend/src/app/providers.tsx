'use client';
import { AuthProvider } from '../context/AuthContext'; // Adjusted path

export function Providers({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}