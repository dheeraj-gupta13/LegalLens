// All HTTP lives here. Components never call fetch directly.
const BASE = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
const TOKEN_KEY = "legallens_token";

let token = localStorage.getItem(TOKEN_KEY);
let onUnauthorized = null;

export const setToken = (t) => {
  token = t;
  t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);
};
export const hasToken = () => Boolean(token);
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status; this.code = code; this.details = details;
  }
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) payload = form;
  else if (body !== undefined) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }

  let res;
  try { res = await fetch(BASE + path, { method, headers, body: payload }); }
  catch { throw new ApiError(0, "NETWORK_ERROR", "Can't reach the server. Check your connection."); }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const e = data.error || {};
    if (res.status === 401 && token && onUnauthorized) onUnauthorized();
    throw new ApiError(res.status, e.code || "ERROR", e.message || "Something went wrong.", e.details);
  }
  return data;
}

export const api = {
  register: (email, password) => request("/auth/register", { method: "POST", body: { email, password } }),
  login: (email, password) => request("/auth/login", { method: "POST", body: { email, password } }),
  me: () => request("/auth/me"),
  listDocuments: () => request("/documents?per_page=50"),
  uploadDocument: (file) => { const form = new FormData(); form.append("file", file); return request("/documents", { method: "POST", form }); },
  deleteDocument: (id) => request(`/documents/${id}`, { method: "DELETE" }),
  listMessages: (id) => request(`/documents/${id}/messages`),
  ask: (id, question) => request(`/documents/${id}/messages`, { method: "POST", body: { question } }),
  getAnalysis: (id) => request(`/documents/${id}/analysis`),
  compare: (a, b) => request("/comparisons", { method: "POST", body: { document_ids: [a, b] } }),
};
