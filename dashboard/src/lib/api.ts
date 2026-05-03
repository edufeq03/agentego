import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
});

// Interceptor para adicionar o token de autenticação
api.interceptors.request.use((config) => {
  const token = process.env.NEXT_PUBLIC_TOKEN || 'primefit-token-123';
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
