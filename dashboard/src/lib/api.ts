import axios from 'axios';

// Lógica de detecção dinâmica inteligente para a URL do Bot Backend
export function getApiBaseUrl(): string {
  let rawBaseURL = process.env.NEXT_PUBLIC_API_URL;

  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

    // Se a variável não for definida ou se apontar para um host antigo do Easypanel, usa a detecção dinâmica por hostname
    if (!rawBaseURL || rawBaseURL.includes('easypanel.host')) {
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        rawBaseURL = 'http://localhost:8000';
      } else if (hostname.includes('-dashboard-')) {
        const isAgente = hostname.includes('sites-academia') || hostname.includes('agente');
        rawBaseURL = `${protocol}//${hostname.replace('-dashboard-', isAgente ? '-agente-' : '-bot-')}`;
      } else if (hostname.startsWith('app.')) {
        rawBaseURL = `${protocol}//api.${hostname.substring(4)}`;
      } else if (hostname.startsWith('dashboard.')) {
        rawBaseURL = `${protocol}//api.${hostname.substring(10)}`;
      } else {
        // Para domínios como agentego.com.br ou www.agentego.com.br -> https://api.agentego.com.br
        const cleanHost = hostname.replace(/^www\./, '');
        rawBaseURL = `${protocol}//api.${cleanHost}`;
      }
    }
  }

  if (!rawBaseURL) {
    rawBaseURL = 'http://localhost:8000';
  }

  return rawBaseURL.endsWith('/') ? rawBaseURL.slice(0, -1) : rawBaseURL;
}

const api = axios.create({
  baseURL: getApiBaseUrl() + '/api',
});

// Interceptor para atualizar dinamicamente a baseURL no client-side e adicionar token
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    config.baseURL = getApiBaseUrl() + '/api';
    const token = localStorage.getItem('agentego_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export default api;
