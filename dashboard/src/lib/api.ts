import axios from 'axios';

// Lógica de detecção dinâmica inteligente para a URL do Bot Backend
let rawBaseURL = process.env.NEXT_PUBLIC_API_URL;

if (!rawBaseURL && typeof window !== 'undefined') {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;

  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    rawBaseURL = 'http://localhost:8000';
  } else if (hostname.includes('-dashboard-')) {
    // Para padrões de subdomínio do Easypanel (ex: agentego-dashboard-homolog -> agentego-bot-homolog)
    // Se o hostname contiver "sites-academia" ou "agente", substitui por "-agente-" em vez de "-bot-"
    const isAgente = hostname.includes('sites-academia') || hostname.includes('agente');
    rawBaseURL = `${protocol}//${hostname.replace('-dashboard-', isAgente ? '-agente-' : '-bot-')}`;
  } else if (hostname.startsWith('dashboard.')) {
    // Se usar subdomínio padrão 'dashboard.dominio.com' -> 'api.dominio.com'
    rawBaseURL = `${protocol}//api.${hostname.substring(10)}`;
  } else {
    // Se for o domínio raiz (ex: agentego.com.br) -> 'api.agentego.com.br'
    rawBaseURL = `${protocol}//api.${hostname}`;
  }
}

// Fallback final caso tudo falhe ou esteja rodando no server-side sem variável
if (!rawBaseURL) {
  rawBaseURL = 'http://localhost:8000';
}

const baseURL = rawBaseURL.endsWith('/') ? rawBaseURL.slice(0, -1) : rawBaseURL;

const api = axios.create({
  baseURL: baseURL + '/api',
});

// Interceptor para adicionar o token de autenticação
api.interceptors.request.use((config) => {
  // Apenas roda no client-side
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('agentego_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export default api;
