"use client";

import React from "react";
import { useEffect, useState, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { useParams, useRouter } from "next/navigation";
import apiClient from "../../../services/api";
import { ChatMessage, ChatSession } from "../../../types";

// --- Enhanced UI Components ---

const MessageBubble = React.memo(
  ({
    message,
    isTyping = false,
    streaming = false,
    isLatest = false,
  }: {
    message: ChatMessage;
    isTyping?: boolean;
    streaming?: boolean;
    isLatest?: boolean;
  }) => {
    const isAi = message.role === "ai";
    
    return (
      <div
        className={`flex w-full mb-6 animate-fadeIn ${
          isAi ? "justify-start" : "justify-end"
        }`}
      >
        <div
          className={`flex max-w-4xl ${isAi ? "flex-row" : "flex-row-reverse"}`}
        >
          {/* Avatar */}
          <div className={`flex-shrink-0 ${isAi ? "mr-3" : "ml-3"}`}>
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                isAi
                  ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg"
                  : "bg-gradient-to-r from-gray-700 to-gray-800 text-white shadow-md"
              } ${streaming ? "animate-pulse" : ""}`}
            >
              {isAi ? "🤖" : "👤"}
            </div>
          </div>

          {/* Message Bubble */}
          <div
            className={`relative px-4 py-3 rounded-2xl shadow-sm transition-all transform ${
              isAi
                ? "bg-white text-gray-800 border border-gray-200 hover:shadow-md"
                : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg hover:shadow-xl"
            } ${isLatest ? "animate-slideUp" : ""}`}
          >
            {/* Speech bubble tail */}
            <div
              className={`absolute top-3 w-3 h-3 transform rotate-45 ${
                isAi
                  ? "bg-white border-l border-t border-gray-200 -left-1.5"
                  : "bg-indigo-600 -right-1.5"
              }`}
            />

            {/* Message Content */}
            <div className="relative z-10">
              {isTyping ? (
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    />
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                  </div>
                  <span className="text-gray-500 text-sm">Thinking...</span>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none">
                  {streaming ? (
                    <div className="relative">
                      {message.content}
                      <span className="inline-block w-2 h-5 bg-indigo-500 animate-pulse ml-1" />
                    </div>
                  ) : (
                    <ReactMarkdown
                      components={{
                        // Custom styling for markdown elements
                        h1: ({ children }) => (
                          <h1 className="text-xl font-bold mb-2 text-gray-900">
                            {children}
                          </h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="text-lg font-semibold mb-2 text-gray-800">
                            {children}
                          </h2>
                        ),
                        p: ({ children }) => (
                          <p className="mb-2 text-gray-700 leading-relaxed">
                            {children}
                          </p>
                        ),
                        code: ({ children, className }) => {
                          const isBlock = className?.includes("language-");
                          if (isBlock) {
                            return (
                              <pre className="bg-gray-100 rounded-lg p-3 overflow-x-auto my-2">
                                <code className="text-sm text-gray-800">
                                  {children}
                                </code>
                              </pre>
                            );
                          }
                          return (
                            <code className="bg-gray-100 px-1 py-0.5 rounded text-sm text-gray-800">
                              {children}
                            </code>
                          );
                        },
                        ul: ({ children }) => (
                          <ul className="list-disc list-inside mb-2 space-y-1 text-gray-700">
                            {children}
                          </ul>
                        ),
                        ol: ({ children }) => (
                          <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-700">
                            {children}
                          </ol>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  )}
                </div>
              )}
            </div>

            {/* Timestamp */}
            <div
              className={`text-xs mt-2 ${
                isAi ? "text-gray-400" : "text-indigo-200"
              }`}
            >
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          </div>
        </div>
      </div>
    );
  }
);

const EnhancedMessageInput = ({
  onSendMessage,
  onFileUpload,
  isLoading,
}: {
  onSendMessage: (input: string) => void;
  onFileUpload: (file: File) => void;
  isLoading: boolean;
}) => {
  const [userInput, setUserInput] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [userInput]);

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
    if (file && (file.type === "application/pdf" || file.name.endsWith(".pdf"))) {
      onFileUpload(file);
    } else if (file) {
      alert("Please select a PDF file for resume analysis.");
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === "application/pdf" || file.name.endsWith(".pdf"))) {
      onFileUpload(file);
    } else {
      alert("Please drop a PDF file for resume analysis.");
    }
  };

  return (
    <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div
            className={`flex items-end space-x-3 transition-all ${
              isDragging ? "opacity-50" : ""
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about your career..."
                className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all max-h-32 overflow-y-auto"
                disabled={isLoading}
                rows={1}
                style={{ minHeight: "48px" }}
              />
              {userInput.length > 0 && (
                <button
                  type="button"
                  onClick={() => setUserInput("")}
                  className="absolute right-3 top-3 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  ✕
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="h-12 px-3 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-all disabled:opacity-50 text-xs sm:text-sm font-medium shadow-sm hover:shadow-md"
                disabled={isLoading}
                title="Upload Resume (PDF)"
              >
                📄 PDF
              </button>
              <button
                type="submit"
                className={`h-12 px-6 rounded-lg font-medium transition-all shadow-sm ${
                  isLoading || !userInput.trim()
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-md transform hover:scale-105"
                }`}
                disabled={isLoading || !userInput.trim()}
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Sending...</span>
                  </div>
                ) : (
                  "Send"
                )}
              </button>
            </div>
          </div>
        </form>
        
        {isDragging && (
          <div className="absolute inset-0 bg-indigo-50 border-2 border-dashed border-indigo-300 rounded-xl flex items-center justify-center z-10">
            <div className="text-center">
              <div className="text-2xl mb-2">📄</div>
              <p className="text-indigo-600 font-medium">Drop your PDF resume here</p>
            </div>
          </div>
        )}
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>
    </div>
  );
};

const EnhancedWelcomeScreen = ({
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
    "Help me write a compelling cover letter",
    "What skills should I learn for software engineering?",
    "How can I negotiate a better salary?",
  ];

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && (file.type === "application/pdf" || file.name.endsWith(".pdf"))) {
      onFileUpload(file);
    } else if (file) {
      alert("Please select a PDF file for resume analysis.");
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 bg-gradient-to-br from-gray-50 to-indigo-50">
      <div className="max-w-4xl w-full text-center">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white text-2xl font-bold shadow-xl animate-bounce">
          🤖
        </div>
        <h2 className="mt-6 text-3xl sm:text-4xl font-bold text-gray-900 animate-fadeIn">
          Start a new conversation
        </h2>
        <p className="mt-3 text-gray-600 text-lg animate-fadeIn">
          Ask anything about your career, or upload a resume for instant analysis.
        </p>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 animate-fadeIn">
          {samplePrompts.map((prompt, index) => (
            <button
              key={prompt}
              onClick={() => onSendMessage(prompt)}
              disabled={isLoading}
              className="text-sm px-4 py-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 disabled:opacity-50 transition-all hover:shadow-md hover:border-indigo-200 hover:text-indigo-700 text-left"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="font-medium line-clamp-2">{prompt}</div>
            </button>
          ))}
        </div>

        <div className="mt-10 animate-fadeIn">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="inline-flex items-center justify-center px-6 py-3 rounded-xl border-2 border-dashed border-indigo-300 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 font-medium transition-all hover:border-indigo-400 hover:shadow-lg"
          >
            <span className="mr-2 text-xl">📄</span>
            Upload Resume for Analysis
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      </div>
    </div>
  );
};

// --- Main Enhanced Chat Component ---
export default function EnhancedChatSessionPage() {
  const params = useParams();
  const router = useRouter();
  const { session_id } = params;
  const isNewChat = session_id === "new";

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Enhanced scroll to bottom with smooth behavior
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ 
      behavior: "smooth",
      block: "end"
    });
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timeoutId);
  }, [messages, isLoading, scrollToBottom]);

  // Enhanced error handling with retry logic
  const handleError = useCallback((error: any, context: string) => {
    console.error(`Error in ${context}:`, error);
    const errorMessage = error?.response?.data?.detail || error?.message || "An unexpected error occurred";
    setError(errorMessage);
    
    // Auto-clear error after 5 seconds
    setTimeout(() => setError(null), 5000);
  }, []);

  // Enhanced streaming with better error handling and reconnection
  const handleSendMessage = async (userMessageContent: string) => {
    setIsLoading(true);
    setError(null);

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const optimisticUserMessage: ChatMessage = {
      id: Date.now(),
      role: "human",
      content: userMessageContent,
      session_id: 0,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMessage]);

    try {
      let currentSessionId = isNewChat ? null : (session_id as string);

      if (isNewChat) {
        // Create new session with first message
        const response = await apiClient.post("/chat/", {
          first_message: userMessageContent,
        });
        const newSession: ChatSession = response.data;
        currentSessionId = newSession.id.toString();

        router.replace(`/chat/${currentSessionId}`, { scroll: false });
        setSession(newSession);
        setMessages(newSession.messages || []);
        setIsLoading(false);
        return;
      }

      if (currentSessionId) {
        // Enhanced streaming for existing chats
        abortControllerRef.current = new AbortController();
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
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok || !response.body) {
          throw new Error(`Stream request failed: ${response.status}`);
        }

        const aiMessageId = Date.now() + 1;
        const aiPlaceholder: ChatMessage = {
          id: aiMessageId,
          role: "ai",
          content: "",
          session_id: Number(currentSessionId),
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiPlaceholder]);
        setStreamingMessageId(aiMessageId);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.slice(6).trim();
              if (dataStr === "[DONE]") {
                setStreamingMessageId(null);
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
                if (data.event === 'done') {
                  setStreamingMessageId(null);
                }
              } catch (parseError) {
                console.warn("Failed to parse stream data:", dataStr);
              }
            }
          }
        }
        
        setStreamingMessageId(null);
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted');
        return;
      }

      handleError(error, "handleSendMessage");
      
      // Remove optimistic message and add error message
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "ai",
        content: "Sorry, I encountered an error while processing your message. Please try again.",
        session_id: isNewChat ? 0 : Number(session_id),
        timestamp: new Date().toISOString(),
      };
      
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticUserMessage.id),
        errorMessage,
      ]);
      
      setStreamingMessageId(null);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Enhanced file upload with progress indication
  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    
    const optimisticUploadMessage: ChatMessage = {
      id: Date.now(),
      role: "human",
      content: `📄 Analyzing uploaded resume: ${file.name}...`,
      session_id: 0,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUploadMessage]);

    const formData = new FormData();
    formData.append("resume", file);

    try {
      let currentSessionId = isNewChat ? null : (session_id as string);

      if (isNewChat) {
        const response = await apiClient.post("/chat/resume-analysis", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        const newSession: ChatSession = response.data;
        currentSessionId = newSession.id.toString();

        router.replace(`/chat/${currentSessionId}`);
        setSession(newSession);
        setMessages(newSession.messages || []);
        return;
      }
      
      if (currentSessionId) {
        await apiClient.post(`/chat/${currentSessionId}/resume-analysis`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        const updatedSessionResponse = await apiClient.get(`/chat/${currentSessionId}`);
        setSession(updatedSessionResponse.data);
        setMessages(updatedSessionResponse.data.messages || []);
      }
    } catch (error) {
      handleError(error, "handleFileUpload");
      
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUploadMessage.id));
      const errorMessage: ChatMessage = {
        id: Date.now(),
        role: "ai",
        content: "Sorry, I encountered an error processing your resume. Please try again with a different PDF file.",
        session_id: 0,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Load session data
  useEffect(() => {
    if (!isNewChat && session_id && typeof session_id === "string") {
      const fetchMessages = async () => {
        setIsLoading(true);
        try {
          const response = await apiClient.get(`/chat/${session_id}`);
          setSession(response.data);
          setMessages(response.data.messages || []);
        } catch (error) {
          handleError(error, "fetchMessages");
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
  }, [session_id, isNewChat, router, handleError]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Welcome screen for new chats
  if (isNewChat && messages.length === 0) {
    return (
      <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 to-indigo-50">
        <EnhancedWelcomeScreen
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
        <EnhancedMessageInput
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Enhanced Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm flex-shrink-0">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-800 truncate">
            {session?.title || "Chat"}
          </h1>
          <div className="flex items-center space-x-2">
            {streamingMessageId && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span>AI is responding...</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Error Banner */}
        {error && (
          <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="text-red-400 hover:text-red-600 ml-2"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto">
          {messages.map((msg, index) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isTyping={isLoading && streamingMessageId === msg.id}
              streaming={streamingMessageId === msg.id}
              isLatest={index === messages.length - 1}
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
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Enhanced Input */}
      <div className="flex-shrink-0">
        <EnhancedMessageInput
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}