// Get API base URL from environment, or construct from backend URL
const VITE_API_URL = import.meta.env.VITE_API_URL;
const BASE = VITE_API_URL 
  ? (VITE_API_URL.endsWith('/api') ? VITE_API_URL : `${VITE_API_URL}/api`)
  : '/api';

console.log('[API] Using BASE URL:', BASE);

function getToken() {
  return localStorage.getItem('access_token');
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const url = `${BASE}${path}`;
  console.log('[API Request]', options.method || 'GET', url);
  
  const res = await fetch(url, { ...options, headers });

  // Only redirect on 401 if we actually had a token (genuine session expiry)
  if (res.status === 401 && token) {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
    return;
  }

  let data = {};
  try {
    data = await res.json();
  } catch (e) {
    // Response is not JSON (e.g., 404 HTML)
    data = { detail: `HTTP ${res.status}: ${res.statusText}` };
  }

  if (!res.ok) {
    console.error('[API Error]', res.status, data);
    const err = new Error(data.detail || data.error || `Request failed (${res.status})`);
    err.data = data;
    err.status = res.status;
    throw err;
  }

  return data;
}

export const api = {
  login: (username, password) =>
    request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  me: () => request('/me/'),

  stats: () => request('/dashboard/stats/'),

  sources: () => request('/sources/'),

  uploadCsv: (file, sourceType) => {
    const form = new FormData();
    form.append('file', file);
    form.append('source_type', sourceType);
    return request('/upload/', { method: 'POST', body: form });
  },

  records: async (params = {}) => {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    );
    const qs = new URLSearchParams(clean).toString();
    const data = await request(`/records/${qs ? '?' + qs : ''}`);
    // Handle both paginated { results: [] } and plain array responses
    return Array.isArray(data) ? data : (data.results ?? []);
  },

  record: (id) => request(`/records/${id}/`),

  updateRecord: (id, body) =>
    request(`/records/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  reviewRecord: (id, action, note = '', edits = {}) =>
    request(`/records/${id}/review/`, {
      method: 'POST',
      body: JSON.stringify({ action, analyst_note: note, ...edits }),
    }),

  auditLog: (id) => request(`/records/${id}/audit/`),
};