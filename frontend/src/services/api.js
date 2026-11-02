import { auth } from '../config/firebase.js'

const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status }
}

/** Calls the FastAPI backend with the current user's Firebase ID token. Pass `form` (FormData) for uploads. */
export async function apiFetch(path, { method = 'GET', body, form, token } = {}) {
  const idToken = token ?? (auth?.currentUser ? await auth.currentUser.getIdToken() : null)
  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers: { ...(form ? {} : { 'Content-Type': 'application/json' }), ...(idToken ? { Authorization: `Bearer ${idToken}` } : {}) },
      body: form ?? (body ? JSON.stringify(body) : undefined),
    })
  } catch {
    throw new ApiError('Cannot reach the Problem 360 server. Check that the backend is running.', 0)
  }
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data?.detail
    const msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d) => d.msg).join('; ') : 'Something went wrong.'
    throw new ApiError(msg, res.status)
  }
  return data
}
