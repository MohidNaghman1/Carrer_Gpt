// frontend/src/app/chat/page.tsx
'use client';

export default function ChatPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-gray-50">
      <div className="max-w-xl">
        <div className="w-14 h-14 mx-auto rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white text-xl font-bold">
          CG
        </div>
        <h1 className="mt-4 text-2xl sm:text-3xl font-bold text-gray-900">
          Welcome to CareerGPT
        </h1>
        <p className="mt-2 text-gray-600">
          Select a conversation from the sidebar or start a new one to begin
          chatting.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <a
            href="/chat/new"
            className="inline-flex items-center justify-center px-4 py-2 rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            + New Chat
          </a>
        </div>
      </div>
    </div>
  );
}
