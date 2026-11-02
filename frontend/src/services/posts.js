import { apiFetch } from './api.js'

/** Real data comes from the FastAPI backend. VITE_DEMO_DATA=true swaps in clearly-labelled placeholder posts
 *  (src/demo/*) that live only in browser memory and are never sent to the backend. */
export const DEMO = import.meta.env.VITE_DEMO_DATA === 'true'
const demo = () => import('../demo/postsDemo.js')
const qs = (o) => { const p = new URLSearchParams(Object.entries(o).filter(([, v]) => v)); return p.toString() ? `?${p}` : '' }

export async function listPosts({ locality, category, q, mine } = {}) {
  if (DEMO) return (await demo()).listPosts({ locality, category, q, mine })
  return apiFetch(`/api/posts${qs({ locality, category, q, mine: mine ? '1' : '' })}`)
}

export async function getPost(id) {
  return DEMO ? (await demo()).getPost(id) : apiFetch(`/api/posts/${id}`)
}

/** Uploads one photo/video to private Firebase Storage through the backend. Returns { mediaPath, mediaType }. */
export async function uploadMedia(file) {
  if (DEMO) return (await demo()).uploadMedia(file)
  const form = new FormData()
  form.append('file', file)
  return apiFetch('/api/media', { method: 'POST', form })
}

/** Creates the report. The Strands agent then runs on the server; poll getPost until decisionState != 'pending'. */
export async function createPost(payload, account) {
  return DEMO ? (await demo()).createPost(payload, account) : apiFetch('/api/posts', { method: 'POST', body: payload })
}

export async function toggleLike(id) {
  return DEMO ? (await demo()).toggleLike(id) : apiFetch(`/api/posts/${id}/like`, { method: 'POST' })
}
export async function listComments(id) {
  return DEMO ? (await demo()).listComments(id) : apiFetch(`/api/posts/${id}/comments`)
}
export async function addComment(id, text, account) {
  return DEMO ? (await demo()).addComment(id, text, account) : apiFetch(`/api/posts/${id}/comments`, { method: 'POST', body: { text } })
}
export async function listNotifications() {
  return DEMO ? [] : apiFetch('/api/notifications')
}
/** Full decision record incl. tool runs and audit trail (author only). */
export async function getDecisionTrace(id) {
  if (DEMO) throw new Error('Demo posts have no Strands decision.')
  return apiFetch(`/api/posts/${id}/decision`)
}
export async function retryDecision(id) {
  return apiFetch(`/api/posts/${id}/decision/retry`, { method: 'POST' })
}
