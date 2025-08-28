// frontend/src/app/chat/page.tsx
"use client";

export default function DefaultChatPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center bg-slate-900">
      <div className="w-16 h-16 bg-gradient-to-br from-blue-700 to-blue-900 rounded-2xl flex items-center justify-center mb-6 shadow-xl">
        <span className="text-3xl">🚀</span>
      </div>
      <h1 className="text-3xl font-bold text-white">Welcome to CareerGPT</h1>
      <p className="mt-2 text-blue-100 max-w-md">
        Please select a conversation from the sidebar on the left, or click "+
        New Chat" to begin a new conversation.
      </p>
    </div>
  );
}
