
import axios from 'axios';
import toast from 'react-hot-toast';


const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Create an axios instance with a base URL for our backend
const apiClient = axios.create({
    baseURL: apiBaseUrl, // The URL of our FastAPI backend
    headers: {
        'Content-Type': 'application/json',
    },
});

// We can add an interceptor to automatically add the auth token to every request
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default apiClient;

// Global 401 handler: if token is invalid/expired, clear and redirect to login
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error?.response?.status;
        if (status === 401) {
            try { localStorage.removeItem('accessToken'); } catch {}
            toast.error('Session expired. Please log in again.');
            if (typeof window !== 'undefined') {
                window.location.href = '/login';
            }
        } else if (status) {
            const detail = error?.response?.data?.detail || error?.message || 'An error occurred';
            toast.error(`Request failed (${status}): ${detail}`);
        } else if (error?.message) {
            toast.error(error.message);
        }
        return Promise.reject(error);
    }
);

console.log(`API Client initialized with baseURL: ${apiBaseUrl}`);
