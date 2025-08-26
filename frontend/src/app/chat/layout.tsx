// frontend/src/app/chat/layout.tsx
"use client";

import { useEffect, useState,useCallback  } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import apiClient from "../../services/api"; // Use relative path for safety
import { ChatSession } from "../../types";
import { useAuth } from "../../context/AuthContext";

// --- Sidebar Component ---
const Sidebar = ({
  sessions,
  onRename,
  onDelete,
  onLogout,
}: {
  sessions: ChatSession[];
  onRename: (id: number, title: string) => void;
  onDelete: (id: number) => void;
  onLogout: () => void;
}) => {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 bg-gray-800 text-white">
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-xl font-bold">Chat History</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        <nav className="p-2 space-y-1">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group flex items-center justify-between px-2 py-2 rounded-md text-sm transition-colors ${
                pathname === `/chat/${session.id}`
                  ? "bg-indigo-600"
                  : "hover:bg-gray-700"
              }`}
            >
              <Link
                href={`/chat/${session.id}`}
                className="flex-1 truncate pr-2 font-medium"
              >
                {session.title}
              </Link>
              <button
                className="opacity-75 hover:opacity-100 mr-1"
                title="Rename"
                onClick={async () => {
                  const next = prompt("Rename chat:", session.title);
                  if (next && next.trim() && next !== session.title) {
                    onRename(session.id, next.trim());
                  }
                }}
              >
                ✏️
              </button>
              <button
                className="opacity-75 hover:opacity-100"
                title="Delete"
                onClick={() => {
                  if (confirm("Are you sure you want to delete this chat?")) {
                    onDelete(session.id);
                  }
                }}
              >
                🗑️
              </button>
            </div>
          ))}
        </nav>
      </div>
      <div className="p-4 border-t border-gray-700">
        <Link
          href="/chat/new"
          className="w-full text-center block bg-indigo-600 hover:bg-indigo-700 rounded-md py-2 text-sm font-medium"
        >
          + New Chat
        </Link>
        <button
          onClick={onLogout}
          className="w-full mt-2 text-center bg-red-600 hover:bg-red-700 rounded-md py-2 text-sm font-medium"
        >
          Logout
        </button>
      </div>
    </div>
  );
};

// --- Main ChatLayout Component ---
export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  // Get the reliable state from our global AuthContext
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  // Memoize the refresh function so it doesn't get redefined on every render
  const refreshSessions = useCallback(async () => {
    // Only fetch if we are authenticated
    if (isAuthenticated) {
      try {
        const response = await apiClient.get<ChatSession[]>("/chat/");
        setSessions(response.data);
      } catch (error) {
        console.error("Failed to refresh sessions:", error);
      }
    }
  }, [isAuthenticated]);

  // This effect is now ONLY responsible for fetching data when things change.
  useEffect(() => {
    refreshSessions();
  }, [pathname, refreshSessions]); // refreshSessions is stable due to useCallback

  // This effect handles the initial authentication guard.
  useEffect(() => {
    // When the initial auth check is done...
    if (!isLoading && !isAuthenticated) {
      // ...and the user is NOT authenticated, redirect to login.
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  const handleLogout = () => {
    setSessions([]); // Clear local state first
    logout(); // Call the centralized logout function from context
  };

  const handleRename = async (id: number, title: string) => {
    try {
      await apiClient.put(`/chat/${id}`, { title });
      await refreshSessions(); // Use the memoized refresh function
    } catch (e) {
      console.error("Failed to rename session", e);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiClient.delete(`/chat/${id}`);
      await refreshSessions(); // Use the memoized refresh function
      if (pathname === `/chat/${id}`) {
        router.push("/chat/new");
      }
    } catch (e) {
      console.error("Failed to delete session", e);
    }
  };
  
  // --- This is the new, more robust loading and guarding logic ---
  
  // While the AuthContext is doing its initial check, show a loading screen.
  // This is what fixes the "stuck" screen. `isLoading` is guaranteed to become `false`.
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div>Loading Application...</div>
      </div>
    );
  }

  // If the check is done and the user is not authenticated, render nothing.
  // The useEffect above will handle the redirect to the login page.
  if (!isAuthenticated) {
    return null;
  }

  // If we get here, the user is authenticated and we can render the app.
  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar
        sessions={sessions}
        onRename={handleRename}
        onDelete={handleDelete}
        onLogout={handleLogout}
      />
      <main className="flex-1 flex flex-col">{children}</main>
    </div>
  );
}
