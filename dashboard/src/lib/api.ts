import axios from 'axios';

const rawBaseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const baseURL = rawBaseURL.endsWith('/') ? rawBaseURL.slice(0, -1) : rawBaseURL;

const api = axios.create({
  baseURL: baseURL + '/api',
});

// Interceptor para adicionar o token de autenticação
api.interceptors.request.use((config) => {
  // Apenas roda no client-side
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('atendia_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export default api;
