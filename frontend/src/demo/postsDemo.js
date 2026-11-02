// DEMO MODE ONLY (VITE_DEMO_DATA=true). In-memory placeholders; nothing here touches the backend or Firestore.
import { demoPosts, demoComments } from './demoData.js'

const state = { posts: demoPosts.map((p) => ({ ...p, decisionState: 'completed', decision: null })), comments: { ...demoComments } }
const wait = (v) => new Promise((r) => setTimeout(() => r(v), 150))

export async function listPosts({ locality, category, q, mine }) {
  const s = (q || '').toLowerCase()
  return wait(state.posts.filter((p) => (!locality || p.locality === locality) && (!category || p.category === category)
    && (!s || p.description.toLowerCase().includes(s)) && (!mine || p.author.uid === 'me')))
}
export const getPost = async (id) => wait(state.posts.find((p) => p.id === id))
export const uploadMedia = async (file) => ({ mediaPath: 'demo', mediaType: file.type.startsWith('video/') ? 'video' : 'image', _url: URL.createObjectURL(file) })
export async function createPost(payload, account) {
  const post = { id: `demo-${Date.now()}`, author: { uid: 'me', name: account.displayName, locality: account.locality }, ...payload,
    createdAt: new Date().toISOString(), status: 'Submitted', referenceId: 'DEMO', likeCount: 0, commentCount: 0, likedByMe: false, decisionState: 'completed', decision: null }
  state.posts.unshift(post)
  return wait(post)
}
export async function toggleLike(id) {
  const p = state.posts.find((x) => x.id === id)
  p.likedByMe = !p.likedByMe; p.likeCount += p.likedByMe ? 1 : -1
  return wait({ likedByMe: p.likedByMe, likeCount: p.likeCount })
}
export const listComments = async (id) => wait(state.comments[id] || [])
export async function addComment(id, text, account) {
  const c = { id: `c-${Date.now()}`, author: { name: account.displayName }, text, createdAt: new Date().toISOString() }
  state.comments[id] = [...(state.comments[id] || []), c]
  state.posts.find((x) => x.id === id).commentCount += 1
  return wait(c)
}
