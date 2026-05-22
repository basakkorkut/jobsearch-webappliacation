import { supabase } from './supabase'

const BASE = import.meta.env.VITE_API_GATEWAY_URL

async function apiFetch(path, options = {}) {
  let token = null
  try {
    const { data } = await supabase.auth.getSession()
    token = data?.session?.access_token ?? null
  } catch {
    // proceed without auth token
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (res.status === 204) return null

  const json = await res.json()
  if (!res.ok) throw new Error(json.detail || `HTTP ${res.status}`)
  return json
}

export const api = {
  get:    (path)        => apiFetch(path),
  post:   (path, body)  => apiFetch(path, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (path, body)  => apiFetch(path, { method: 'PUT',    body: JSON.stringify(body) }),
  patch:  (path, body)  => apiFetch(path, { method: 'PATCH',  body: JSON.stringify(body) }),
  delete: (path)        => apiFetch(path, { method: 'DELETE' }),
}
