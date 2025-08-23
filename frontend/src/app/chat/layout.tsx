// frontend/src/app/chat/layout.tsx
"use client";

import { useEffect, useState } from "react";
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
  const { isAuthenticated, isLoading, hasHydrated, logout } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  const refreshSessions = async () => {
    const response = await apiClient.get<ChatSession[]>("/chat/");
    setSessions(response.data);
  };

  const handleLogout = () => {
    setSessions([]);
    logout();
  };

  const handleRename = async (id: number, title: string) => {
    try {
      await apiClient.put(`/chat/${id}`, { title });
      await refreshSessions();
    } catch (e) {
      console.error("Failed to rename session", e);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiClient.delete(`/chat/${id}`);
      await refreshSessions();
      if (pathname === `/chat/${id}`) {
        router.push("/chat/new");
      }
    } catch (e) {
      console.error("Failed to delete session", e);
    }
  };

  useEffect(() => {
    if (!hasHydrated) return;
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    const fetchSessions = async () => {
      try {
        const response = await apiClient.get<ChatSession[]>("/chat/");
        setSessions(response.data);
      } catch (error) {
        console.error("Failed to fetch sessions:", error);
        if ((error as any).response?.status === 401) {
          router.push("/login");
        }
      }
    };

    fetchSessions();
  }, [router, pathname, isAuthenticated, hasHydrated]); // Re-fetch when pathname changes to update sidebar

  if (!hasHydrated || !isAuthenticated || isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div>Loading...</div>
      </div>
    );
  }

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
