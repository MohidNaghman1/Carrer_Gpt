"use client";

import React from "react";
import { useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { useParams, useRouter } from "next/navigation";
import apiClient from "../../../services/api";
import { ChatMessage, ChatSession } from "../../../types";

// --- UI Sub-components ---

const MessageBubble = React.memo(
  ({
    message,
    isTyping = false,
    streaming = false,
  }: {
    message: ChatMessage;
    isTyping?: boolean;
    streaming?: boolean;
  }) => {
    const isAi = message.role === "ai";
    return (
      <div
        className={`flex w-full mb-6 ${isAi ? "justify-start" : "justify-end"}`}
      >
        <div
          className={`flex max-w-4xl ${isAi ? "flex-row" : "flex-row-reverse"}`}
        >
          <div className={`flex-shrink-0 ${isAi ? "mr-3" : "ml-3"}`}>
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                isAi
                  ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white"
                  : "bg-slate-600 text-white"
              }`}
            >
              {isAi ? "🤖" : "👤"}
            </div>
          </div>
          <div
            className={`relative px-4 py-3 rounded-2xl shadow-sm ${
              isAi
                ? "bg-slate-50 text-slate-800 border border-slate-200"
                : "bg-gradient-to-r from-emerald-600 to-teal-600 text-white"
            }`}
          >
            <div
              className={`absolute top-3 w-3 h-3 transform rotate-45 ${
                isAi
                  ? "bg-slate-50 border-l border-t border-slate-200 -left-1.5"
                  : "bg-emerald-600 -right-1.5"
              }`}
            ></div>
            <div className="relative z-10">
              {isTyping ? (
                <div className="flex items-center space-x-1">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                  <span className="text-slate-500 text-sm ml-2">
                    Thinking...
                  </span>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none prose-slate">
                  {streaming ? (
                    message.content // plain text while streaming
                  ) : (
                    <ReactMarkdown>{message.content}</ReactMarkdown> // markdown when done
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
);

const MessageInput = ({
  onSendMessage,
  onFileUpload,
  isLoading,
}: {
  onSendMessage: (input: string) => void;
  onFileUpload: (file: File) => void;
  isLoading: boolean;
}) => {
  const [userInput, setUserInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading) return;
    onSendMessage(userInput);
    setUserInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const allowedExts = [".pdf", ".doc", ".docx"];
    if (
      file &&
      (allowedTypes.includes(file.type) ||
        allowedExts.some((ext) => file.name.toLowerCase().endsWith(ext)))
    ) {
      onFileUpload(file);
    } else {
      alert(
        "Please select a PDF or Word file (.pdf, .doc, .docx) for resume analysis."
      );
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="bg-slate-50 border-t border-slate-200 p-4">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-end space-x-3">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about your career..."
              className="w-full resize-none rounded-xl border border-slate-300 bg-white px-4 py-3 text-black placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all max-h-32 overflow-y-auto"
              disabled={isLoading}
              rows={1}
            />
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="h-10 px-3 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-all disabled:opacity-50 text-xs sm:text-sm"
                disabled={isLoading}
                title="Upload Resume (PDF)"
              >
                Upload PDF
              </button>
              <button
                type="submit"
                className={`h-10 px-4 rounded-lg transition-all ${
                  isLoading || !userInput.trim()
                    ? "bg-slate-300 text-slate-500 cursor-not-allowed"
                    : "bg-emerald-600 text-white hover:bg-emerald-700"
                }`}
                disabled={isLoading || !userInput.trim()}
              >
                Send
              </button>
            </div>
          </div>
        </form>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>
    </div>
  );
};

const WelcomeScreen = ({
  onSendMessage,
  onFileUpload,
  isLoading,
}: {
  onSendMessage: (input: string) => void;
  onFileUpload: (file: File) => void;
  isLoading: boolean;
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const samplePrompts = [
    "List the top 10 most commonly asked interview questions",
    "Generate a step-by-step roadmap to become a Data Scientist in 2025",
    "What are the latest AI job opportunities in Pakistan?",
  ];

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const allowedExts = [".pdf", ".doc", ".docx"];
    if (
      file &&
      (allowedTypes.includes(file.type) ||
        allowedExts.some((ext) => file.name.toLowerCase().endsWith(ext)))
    ) {
      onFileUpload(file);
    } else if (file) {
      alert(
        "Please select a PDF or Word file (.pdf, .doc, .docx) for resume analysis."
      );
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-100">
      <div className="max-w-3xl w-full text-center">
        <div className="w-14 h-14 mx-auto rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 flex items-center justify-center text-white text-xl font-bold">
          🤖
        </div>
        <h2 className="mt-4 text-2xl sm:text-3xl font-bold text-slate-900">
          Start a new chat
        </h2>
        <p className="mt-2 text-slate-600">
          Ask anything about your career, or upload a resume for instant
          analysis.
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {samplePrompts.map((p) => (
            <button
              key={p}
              onClick={() => onSendMessage(p)}
              disabled={isLoading}
              className="text-xs sm:text-sm px-3 py-2 rounded-full border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-50"
            >
              {p}
            </button>
          ))}
        </div>

        <div className="mt-8">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="inline-flex items-center justify-center px-4 py-2 rounded-md border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 disabled:opacity-50 text-xs sm:text-sm"
          >
            Upload Resume (PDF)
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      </div>
    </div>
  );
};

// --- Main Page Component ---
export default function ChatSessionPage() {
  const params = useParams();
  const router = useRouter();
  const { session_id } = params;
  const isNewChat = session_id === "new";

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<number | null>(
    null
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(scrollToBottom, [messages, isLoading]);

  const streamInMessageContent = (messageId: number, fullContent: string) => {
    setStreamingMessageId(messageId);
    const tokens = Array.from(fullContent);
    let index = 0;
    const chunkSize = 3;
    const interval = setInterval(() => {
      index += chunkSize;
      const next = fullContent.slice(0, index);
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, content: next } : m))
      );
      if (index >= tokens.length) {
        clearInterval(interval);
        setStreamingMessageId(null);
      }
    }, 25);
  };

  useEffect(() => {
    if (!isNewChat && session_id && typeof session_id === "string") {
      const fetchMessages = async () => {
        setIsLoading(true);
        try {
          const response = await apiClient.get(`/chat/${session_id}`);
          setSession(response.data);
          setMessages(response.data.messages || []);
        } catch (error) {
          console.error("Failed to fetch chat session:", error);
          router.push("/chat/new");
        } finally {
          setIsLoading(false);
        }
      };
      fetchMessages();
    } else {
      setMessages([]);
      setSession(null);
    }
  }, [session_id, isNewChat, router]);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    const optimisticMsg = {
      id: Date.now(),
      role: "human" as const,
      content: `📄 Analyzing uploaded resume: ${file.name}...`,
      session_id: 0,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);

    const formData = new FormData();
    formData.append("resume", file);

    try {
      const endpoint = isNewChat
        ? "/chat/resume-analysis"
        : `/chat/${session_id}/resume-analysis`;
      // This single API call does everything: creates the session (if new),
      // analyzes the resume, saves the messages, and returns the complete, updated session.
      const response = await apiClient.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const sessionData = response.data;

      // If it was a new chat, we need to navigate to the new URL
      if (isNewChat) {
        router.replace(`/chat/${sessionData.id}`);
      }

      // The response contains the full, updated truth. We just need to display it.
      setSession(sessionData);
      setMessages(sessionData.messages || []);
    } catch (error) {
      console.error("Failed to upload resume:", error);
      setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
      // Add a proper error message bubble here
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (userMessageContent: string) => {
    setIsLoading(true);

    const optimisticUserMessage: ChatMessage = {
      id: Date.now(),
      role: "human",
      content: userMessageContent,
      session_id: 0, // Placeholder, will be updated
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMessage]);

    try {
      let currentSessionId = isNewChat ? null : (session_id as string);

      // --- Case 1: This is the VERY FIRST message of a NEW chat ---
      if (isNewChat) {
        // This endpoint creates the session, gets the first AI response, and returns the whole package.
        // It is NOT a streaming call.
        const response = await apiClient.post("/chat/", {
          first_message: userMessageContent,
        });
        const newSession: ChatSession = response.data;
        currentSessionId = newSession.id.toString();

        // Navigate to the new URL and display the complete first turn from the backend.
        router.replace(`/chat/${currentSessionId}`, { scroll: false });
        setSession(newSession);
        setMessages(newSession.messages || []); // This now includes the first user and AI messages.

        // The first-turn transaction is complete, so we can stop loading.
        setIsLoading(false);
        return; // Exit the function here.
      }

      // --- Case 2: This is a message in an EXISTING chat ---
      if (currentSessionId) {
        // For existing chats, we use the efficient streaming endpoint.
        const token = localStorage.getItem("accessToken");
        const url = `${apiClient.defaults.baseURL}/chat/${currentSessionId}/messages/stream`;

        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ content: userMessageContent }),
        });

        if (!response.ok || !response.body) {
          throw new Error("Stream request failed.");
        }

        // Create a correctly-typed placeholder for the AI's streaming response.
        const aiMessageId = Date.now() + 1; // Use a new unique ID
        const aiPlaceholder: ChatMessage = {
          id: aiMessageId,
          role: "ai",
          content: "", // Start with empty content
          session_id: Number(currentSessionId),
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiPlaceholder]);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const decodedChunk = decoder.decode(value);
          const events = decodedChunk.split("\n\n");
          for (const event of events) {
            if (event.startsWith("data: ")) {
              const dataStr = event.slice(6);
              if (dataStr.trim() === "[DONE]") {
                break;
              }
              try {
                const data = JSON.parse(dataStr);
                if (data.token) {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === aiMessageId
                        ? { ...m, content: m.content + data.token }
                        : m
                    )
                  );
                }
                if (data.error) {
                  throw new Error(data.error);
                }
              } catch (e) {
                console.error("Failed to parse stream data:", dataStr);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      // Add a clear error message to the chat UI
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "ai",
        content: "Sorry, an error occurred. Please try again.",
        session_id: isNewChat ? 0 : Number(session_id),
        timestamp: new Date().toISOString(),
      };
      // Remove the optimistic user message and add the error
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticUserMessage.id),
        errorMessage,
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  // --- JSX Rendering Logic ---
  if (isNewChat && messages.length === 0) {
    return (
      <div className="h-full flex flex-col bg-slate-100">
        <WelcomeScreen
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
        <MessageInput
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
      </div>
    );
  }

  // In your ChatSessionPage component's return statement for an existing chat:

  return (
    // Make this the main flex container for the chat view
    <div className="h-full flex flex-col bg-slate-100">
      {/* Header: This has a fixed height */}

      <div className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm flex-shrink-0 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800 truncate">
          {session?.title || "Chat"}
        </h1>
        <div className="flex items-center gap-2">
          <a
            href="https://carrer-gpt.vercel.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-2 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 hover:bg-emerald-100 transition-all text-xs sm:text-sm font-medium"
          >
            Go Back to Dashboard
          </a>
          {/* Add your New Chat and Logout buttons here if not already present */}
        </div>
      </div>

      {/* Messages area: This is the key change. */}
      {/* We use flex-1 and overflow-y-auto HERE to make THIS the scrollable container. */}
      {/* The inner div will grow, but the container's boundaries are fixed. */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isTyping={isLoading && streamingMessageId === msg.id}
              streaming={streamingMessageId === msg.id}
            />
          ))}
          {isLoading && !streamingMessageId && (
            <MessageBubble
              message={{
                id: 0,
                role: "ai",
                content: "",
                session_id: 0,
                timestamp: "",
              }}
              isTyping={true}
            />
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="flex-shrink-0">
        <MessageInput
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
