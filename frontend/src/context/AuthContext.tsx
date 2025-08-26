// frontend/src/context/AuthContext.tsx
'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface AuthContextType {
    isAuthenticated: boolean;
    login: (token: string) => void;
    logout: () => void;
    isLoading: boolean; // This will represent the initial auth check
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true); // START in loading state
    const router = useRouter();

    useEffect(() => {
        // This runs ONLY ONCE when the app first loads in the browser
        try {
            const token = localStorage.getItem('accessToken');
            if (token) {
                setIsAuthenticated(true);
            }
        } catch (error) {
            console.error('Could not access localStorage:', error);
        } finally {
            // CRITICAL: Set loading to false after we've checked the token
            setIsLoading(false); 
        }
    }, []);

    const login = (token: string) => {
        localStorage.setItem('accessToken', token);
        setIsAuthenticated(true);
        router.push('/chat');
    };

    const logout = () => {
        localStorage.removeItem('accessToken');
        setIsAuthenticated(false);
        router.push('/login');
    };

    const value = { isAuthenticated, login, logout, isLoading };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};