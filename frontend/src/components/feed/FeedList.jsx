import { useEffect, useState } from 'react'
import { Newspaper } from 'lucide-react'
import PostCard from './PostCard.jsx'
import Alert from '../ui/Alert.jsx'
import Button from '../ui/Button.jsx'
import { EmptyState } from '../ui/States.jsx'
import { listPosts } from '../../services/posts.js'

/** Loads and renders posts for the given filters with loading / error / empty states. */
export default function FeedList({ filters, emptyText = 'No posts match these filters yet.' }) {
  const [state, setState] = useState({ status: 'loading', posts: [], error: '' })
  const [tick, setTick] = useState(0)
  const key = JSON.stringify(filters)

  useEffect(() => {
    let live = true
    setState((s) => ({ ...s, status: 'loading' }))
    const t = setTimeout(() => listPosts(filters)
      .then((posts) => live && setState({ status: 'ok', posts, error: '' }))
      .catch((e) => live && setState({ status: 'error', posts: [], error: e.message })), 200) // debounce typing
    return () => { live = false; clearTimeout(t) }
  }, [key, tick]) // eslint-disable-line react-hooks/exhaustive-deps

  if (state.status === 'loading') return <div className="space-y-4" role="status" aria-label="Loading posts">{[0, 1].map((i) => <div key={i} className="h-56 animate-pulse rounded-card bg-white shadow-card" />)}</div>
  if (state.status === 'error') return <div className="space-y-3"><Alert tone="error" title="Couldn’t load posts">{state.error}</Alert><Button variant="secondary" onClick={() => setTick((t) => t + 1)}>Try again</Button></div>
  if (!state.posts.length) return <EmptyState icon={Newspaper} title="Nothing here yet">{emptyText}</EmptyState>
  return <div className="space-y-4">{state.posts.map((p) => <PostCard key={p.id} post={p} />)}</div>
}
