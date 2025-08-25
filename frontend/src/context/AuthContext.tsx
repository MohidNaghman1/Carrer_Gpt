// frontend/src/context/AuthContext.tsx
'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface AuthContextType {
    isAuthenticated: boolean;
    login: (token: string) => void;
    logout: () => void;
    isLoading: boolean;
    hasHydrated: boolean; // To prevent initial render flicker
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [hasHydrated, setHasHydrated] = useState(false); // Tracks if we've checked localStorage yet
    const router = useRouter();

    useEffect(() => {
        // This effect runs only once on initial client load
        try {
            const token = localStorage.getItem('accessToken');
            if (token) {
                setIsAuthenticated(true);
            }
        } catch (error) {
            console.error('Could not access localStorage:', error);
        } finally {
            setIsLoading(false);
            setHasHydrated(true); // Mark that we have checked
        }
    }, []);

    const login = (token: string) => {
        localStorage.setItem('accessToken', token);
        setIsAuthenticated(true);
        router.push('/chat'); // Centralized redirect
    };

    const logout = () => {
        localStorage.removeItem('accessToken');
        setIsAuthenticated(false);
        router.push('/login'); // Centralized redirect
    };

    const value = { isAuthenticated, login, logout, isLoading, hasHydrated };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};