// frontend/src/types/index.ts

export interface ChatSession {
    id: number;
    title: string;
    user_id: number;
    created_at: string;
    messages?: ChatMessage[];
}

// ADD THIS NEW TYPE
export interface ChatMessage {
    id: number;
    role: 'human' | 'ai';
    content: string;
    session_id: number;
    timestamp: string;
}