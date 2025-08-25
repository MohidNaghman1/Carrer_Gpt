"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
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
        className={`flex w-full mb-6 animate-fadeIn ${
          isAi ? "justify-start" : "justify-end"
        }`}
      >
        <div
          className={`flex max-w-4xl ${isAi ? "flex-row" : "flex-row-reverse"}`}
        >
          <div className={`flex-shrink-0 ${isAi ? "mr-3" : "ml-3"}`}>
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                isAi
                  ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white"
                  : "bg-gray-700 text-white"
              }`}
            >
              {isAi ? "🤖" : "👤"}
            </div>
          </div>
          <div
            className={`relative px-4 py-3 rounded-2xl shadow-sm ${
              isAi
                ? "bg-white text-gray-800 border border-gray-200"
                : "bg-gradient-to-r from-indigo-600 to-purple-600 text-white"
            }`}
          >
            <div
              className={`absolute top-3 w-3 h-3 transform rotate-45 ${
                isAi
                  ? "bg-white border-l border-t border-gray-200 -left-1.5"
                  : "bg-indigo-600 -right-1.5"
              }`}
            ></div>
            <div className="relative z-10">
              {isTyping ? (
                <div className="flex items-center space-x-1">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                  <span className="text-gray-500 text-sm ml-2">
                    Thinking...
                  </span>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none">
                  {streaming ? (
                    <div className="relative">
                      {message.content}
                      <span className="inline-block w-2 h-4 bg-indigo-500 animate-pulse ml-1 align-middle" />
                    </div>
                  ) : (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
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
MessageBubble.displayName = 'MessageBubble';

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
    if (file && (file.type === "application/pdf" || file.name.endsWith(".pdf"))) {
      onFileUpload(file);
    } else if (file) {
      alert("Please select a valid PDF file.");
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-end space-x-3">
            <textarea value={userInput} onChange={(e) => setUserInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Ask me anything about your career..." className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-24 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all max-h-32 overflow-y-auto" disabled={isLoading} rows={1} />
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => fileInputRef.current?.click()} className="h-12 px-3 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-all disabled:opacity-50 text-xs sm:text-sm font-medium" disabled={isLoading} title="Upload Resume (PDF)">📄 PDF</button>
              <button type="submit" className={`h-12 px-6 rounded-lg font-medium transition-all ${isLoading || !userInput.trim() ? "bg-gray-200 text-gray-400 cursor-not-allowed" : "bg-indigo-600 text-white hover:bg-indigo-700"}`} disabled={isLoading || !userInput.trim()}>Send</button>
            </div>
          </div>
        </form>
        <input ref={fileInputRef} type="file" accept=".pdf,application/pdf" onChange={handleFileSelect} className="hidden" />
      </div>
    </div>
  );
};

const EnhancedWelcomeScreen = ({ onSendMessage, onFileUpload }: { onSendMessage: (input: string) => void; onFileUpload: (file: File) => void; }) => {
  // Your beautiful welcome screen component JSX
  return <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">...</div>;
};

// --- NEW PERFORMANCE-OPTIMIZED STREAMING COMPONENT ---
const StreamingBubble = ({ reader, onStreamEnd }: { reader: ReadableStreamDefaultReader<Uint8Array>, onStreamEnd: (fullContent: string) => void }) => {
    const [content, setContent] = useState("");
    const isStreaming = useRef(true);

    useEffect(() => {
        const stream = async () => {
            const decoder = new TextDecoder();
            let fullResponse = "";
            while (isStreaming.current) {
                try {
                    const { value, done } = await reader.read();
                    if (done) {
                        isStreaming.current = false;
                        onStreamEnd(fullResponse);
                        break;
                    }
                    
                    const decodedChunk = decoder.decode(value);
                    const events = decodedChunk.split('\n\n');

                    for (const event of events) {
                        if (event.startsWith('data: ')) {
                            const dataStr = event.slice(6);
                            if (dataStr.trim() === "[DONE]") {
                               isStreaming.current = false;
                               onStreamEnd(fullResponse);
                               break;
                            }
                            try {
                                const data = JSON.parse(dataStr);
                                if (data.token) {
                                    fullResponse += data.token;
                                    setContent(fullResponse);
                                }
                                if (data.error) { throw new Error(data.error); }
                                if (data.event === 'done') { isStreaming.current = false; onStreamEnd(fullResponse); break; }
                            } catch (e) { console.warn("Failed to parse stream data:", dataStr); }
                        }
                    }
                } catch (error) {
                    console.error("Stream read error:", error);
                    isStreaming.current = false;
                    onStreamEnd(fullResponse + "\n\n[Error: Connection lost during stream]");
                    break;
                }
            }
        };
        stream();
    }, [reader, onStreamEnd]);

    const streamingMessage: ChatMessage = { id: Date.now(), role: 'ai', content, session_id: 0, timestamp: new Date().toISOString() };
    return <MessageBubble message={streamingMessage} streaming={isStreaming.current} />;
};
StreamingBubble.displayName = 'StreamingBubble';


// --- Main Page Component ---
export default function EnhancedChatSessionPage() {
    const params = useParams();
    const router = useRouter();
    const { session_id } = params;
    const isNewChat = session_id === "new";

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [session, setSession] = useState<ChatSession | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [streamReader, setStreamReader] = useState<ReadableStreamDefaultReader<Uint8Array> | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }, []);
    useEffect(scrollToBottom, [messages, isLoading, streamReader]);

    useEffect(() => {
        if (!isNewChat && session_id && typeof session_id === "string") {
            setIsLoading(true);
            apiClient.get(`/chat/${session_id}`).then(response => {
                setSession(response.data);
                setMessages(response.data.messages || []);
            }).catch(error => {
                console.error("Failed to fetch chat session:", error);
                router.push("/chat/new");
            }).finally(() => setIsLoading(false));
        } else {
            setMessages([]);
            setSession(null);
        }
    }, [session_id, isNewChat, router]);

    const handleFileUpload = async (file: File) => {
        setIsLoading(true);
        const optimisticMsg: ChatMessage = { id: Date.now(), role: "human", content: `📄 Analyzing uploaded resume: ${file.name}...`, session_id: 0, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, optimisticMsg]);
        const formData = new FormData();
        formData.append("resume", file);
        try {
            const endpoint = isNewChat ? "/chat/resume-analysis" : `/chat/${session_id}/resume-analysis`;
            const response = await apiClient.post(endpoint, formData, { headers: { "Content-Type": "multipart/form-data" } });
            const newSession: ChatSession = response.data;
            if (isNewChat) router.replace(`/chat/${newSession.id}`);
            setSession(newSession);
            setMessages(newSession.messages || []);
        } catch (error) {
            console.error("Failed to upload resume:", error);
            setMessages(prev => prev.filter(m => m.id !== optimisticMsg.id));
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async (userMessageContent: string) => {
        setIsLoading(true);
        setStreamReader(null);
        const optimisticUserMessage: ChatMessage = { id: Date.now(), role: "human", content: userMessageContent, session_id: 0, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, optimisticUserMessage]);

        try {
            if (isNewChat) {
                const response = await apiClient.post("/chat/", { first_message: userMessageContent });
                const newSession: ChatSession = response.data;
                router.replace(`/chat/${newSession.id}`);
                setSession(newSession);
                setMessages(newSession.messages || []);
                setIsLoading(false);
                return;
            }

            const token = localStorage.getItem("accessToken");
            const url = `${apiClient.defaults.baseURL}/chat/${session_id}/messages/stream`;
            const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", ...(token && { Authorization: `Bearer ${token}` }) }, body: JSON.stringify({ content: userMessageContent }) });
            if (!response.ok || !response.body) { throw new Error(`Stream request failed: ${response.status}`); }
            
            setStreamReader(response.body.getReader());
        } catch (error) {
            console.error("Failed to send message:", error);
            setMessages(prev => prev.filter(m => m.id !== optimisticUserMessage.id));
            setIsLoading(false);
        }
    };

    const handleStreamEnd = (fullContent: string) => {
        const finalAiMessage: ChatMessage = { id: Date.now(), role: 'ai', content: fullContent, session_id: Number(session_id), timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, finalAiMessage]);
        setStreamReader(null);
        setIsLoading(false);
    };

    // --- JSX Rendering Logic ---
    if (isNewChat) {
        return (
            <div className="h-full flex flex-col bg-gray-50">
                <EnhancedWelcomeScreen onSendMessage={handleSendMessage} onFileUpload={handleFileUpload} />
                <EnhancedMessageInput onSendMessage={handleSendMessage} onFileUpload={handleFileUpload} isLoading={isLoading} />
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-gray-50">
            <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm flex-shrink-0">
                <h1 className="text-lg font-semibold text-gray-800 truncate">{session?.title || "Chat"}</h1>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-4">
                <div className="max-w-4xl mx-auto">
                    {messages.map((msg) => (<MessageBubble key={msg.id} message={msg} />))}
                    {streamReader && <StreamingBubble reader={streamReader} onStreamEnd={handleStreamEnd} />}
                    <div ref={messagesEndRef} className="h-4" />
                </div>
            </div>
            <div className="flex-shrink-0">
                <EnhancedMessageInput onSendMessage={handleSendMessage} onFileUpload={handleFileUpload} isLoading={isLoading} />
            </div>
        </div>
    );}