// DEMO DATA — placeholder posts for previewing the UI only (VITE_DEMO_DATA=true).
// These are NOT real reports and contain no Strands decisions.
const h = (n) => new Date(Date.now() - n * 3600e3).toISOString()
export const demoPosts = [
  { id: 'demo-1', author: { uid: 'd1', name: 'Demo User A', locality: 'Anna Nagar' }, description: 'Demo: large pothole near the bus stop.', category: 'Roads & potholes', locality: 'Anna Nagar', locationText: 'Main road bus stop', createdAt: h(2), status: 'Submitted', referenceId: null, likeCount: 4, commentCount: 1, likedByMe: false },
  { id: 'demo-2', author: { uid: 'd2', name: 'Demo User B', locality: 'KK Nagar' }, description: 'Demo: garbage not collected for three days.', category: 'Waste & sanitation', locality: 'KK Nagar', locationText: '5th street', createdAt: h(30), status: 'Under Review', referenceId: null, likeCount: 9, commentCount: 0, likedByMe: true },
  { id: 'demo-3', author: { uid: 'd3', name: 'Demo User C', locality: 'Simmakkal' }, description: 'Demo: waterlogging after rain near the market.', category: 'Drainage & flooding', locality: 'Simmakkal', locationText: 'Market entrance', createdAt: h(70), status: 'In Progress', referenceId: null, likeCount: 12, commentCount: 2, likedByMe: false },
]
export const demoComments = { 'demo-1': [{ id: 'c1', author: { name: 'Demo User B' }, text: 'Demo comment.', createdAt: h(1) }] }
