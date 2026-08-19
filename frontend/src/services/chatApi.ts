// frontend/src/services/chatApi.ts
// Comprehensive API service for chat functionality matching backend endpoints

import apiClient from './api';
import { ChatSession, ChatMessage } from '@/types';

export interface ChatSessionCreate {
    title?: string;
    first_message?: string;
}

export interface ChatSessionUpdate {
    title: string;
}

export interface MessageCreate {
    content: string;
}

/**
 * Chat API Service
 * All endpoints match the backend structure in app/api/routes/chat.py
 */
export const chatApi = {
    /**
     * GET /chat/
     * Retrieves all chat sessions for the current logged-in user
     */
    getAllSessions: async (): Promise<ChatSession[]> => {
        const response = await apiClient.get('/chat/');
        return response.data;
    },

    /**
     * GET /chat/{session_id}
     * Retrieves details for a specific chat session
     */
    getSession: async (sessionId: number): Promise<ChatSession> => {
        const response = await apiClient.get(`/chat/${sessionId}`);
        return response.data;
    },

    /**
     * POST /chat/
     * Creates a new chat session (optionally with first message)
     */
    createSession: async (data: ChatSessionCreate): Promise<ChatSession> => {
        const response = await apiClient.post('/chat/', data);
        return response.data;
    },

    /**
     * POST /chat/stream
     * Creates a new chat session with streaming first message
     * Returns a ReadableStream for SSE
     */
    createSessionWithStream: (data: ChatSessionCreate): Promise<Response> => {
        const token = localStorage.getItem('accessToken');
        return fetch(`${apiClient.defaults.baseURL}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'text/event-stream',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify(data),
        });
    },

    /**
     * PUT /chat/{session_id}
     * Updates a chat session (currently only title)
     */
    updateSession: async (
        sessionId: number,
        data: ChatSessionUpdate
    ): Promise<ChatSession> => {
        const response = await apiClient.put(`/chat/${sessionId}`, data);
        return response.data;
    },

    /**
     * DELETE /chat/{session_id}
     * Deletes a chat session and all its messages
     */
    deleteSession: async (sessionId: number): Promise<void> => {
        await apiClient.delete(`/chat/${sessionId}`);
    },

    /**
     * POST /chat/{session_id}/messages/stream
     * Posts a new message to an existing session with streaming response
     * Returns a ReadableStream for SSE
     */
    sendMessageStream: (
        sessionId: number,
        message: MessageCreate
    ): Promise<Response> => {
        const token = localStorage.getItem('accessToken');
        return fetch(
            `${apiClient.defaults.baseURL}/chat/${sessionId}/messages/stream`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'text/event-stream',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify(message),
            }
        );
    },

    /**
     * POST /chat/resume-analysis
     * Creates a new session with resume upload and analysis
     */
    createSessionWithResume: async (file: File): Promise<ChatSession> => {
        const formData = new FormData();
        formData.append('resume', file);
        const response = await apiClient.post('/chat/resume-analysis', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    /**
     * POST /chat/{session_id}/resume-analysis
     * Adds resume analysis to an existing session
     */
    addResumeToSession: async (
        sessionId: number,
        file: File
    ): Promise<ChatSession> => {
        const formData = new FormData();
        formData.append('resume', file);
        const response = await apiClient.post(
            `/chat/${sessionId}/resume-analysis`,
            formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' },
            }
        );
        return response.data;
    },
};

/**
 * Authentication API Service
 * All endpoints match the backend structure in app/api/routes/auth.py
 */
export const authApi = {
    /**
     * POST /auth/register
     * Registers a new user
     */
    register: async (email: string, password: string) => {
        const response = await apiClient.post('/auth/register', {
            email,
            password,
        });
        return response.data;
    },

    /**
     * POST /auth/token
     * Login endpoint - uses OAuth2PasswordRequestForm format (form-data)
     */
    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append('username', email); // OAuth2 uses "username" field
        formData.append('password', password);

        const response = await apiClient.post('/auth/token', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return response.data;
    },
};

/**
 * Helper function to process SSE stream
 * Used for both new session streaming and existing session message streaming
 */
export async function processSSEStream(
    response: Response,
    onToken: (token: string) => void,
    onSession?: (session: ChatSession) => void,
    onError?: (error: string) => void,
    onDone?: () => void
): Promise<void> {
    if (!response.ok || !response.body) {
        throw new Error('Stream request failed.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete events
            let eventEnd;
            while ((eventEnd = buffer.indexOf('\n\n')) !== -1) {
                const event = buffer.slice(0, eventEnd).trim();
                buffer = buffer.slice(eventEnd + 2);

                if (event.startsWith('data: ')) {
                    const dataStr = event.slice(6);

                    // Check for stream end
                    if (dataStr.trim() === '[DONE]') {
                        if (onDone) onDone();
                        return;
                    }

                    try {
                        const data = JSON.parse(dataStr);

                        // Handle different data types
                        if (data.token && data.token.trim()) {
                            onToken(data.token);
                        }
                        if (data.session && onSession) {
                            onSession(data.session);
                        }
                        if (data.error && onError) {
                            onError(data.error);
                        }
                    } catch (parseError) {
                        console.error('Failed to parse stream data:', dataStr);
                    }
                }
            }
        }
    } catch (streamError) {
        console.error('Streaming error:', streamError);
        if (onError) {
            onError('Sorry, there was an error processing your request. Please try again.');
        }
    }
}
