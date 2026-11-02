import { useEffect, useState } from 'react'
import { Bell } from 'lucide-react'
import { EmptyState } from '../../components/ui/States.jsx'
import Alert from '../../components/ui/Alert.jsx'
import { listNotifications } from '../../services/posts.js'
import { timeAgo } from '../../lib/format.js'

export default function Notifications() {
  const [s, setS] = useState({ status: 'loading', items: [], error: '' })
  useEffect(() => { listNotifications().then((items) => setS({ status: 'ok', items, error: '' })).catch((e) => setS({ status: 'error', items: [], error: e.message })) }, [])
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl">Notifications</h1>
      {s.status === 'loading' && <p role="status" className="text-sm text-ink/60">Loading…</p>}
      {s.status === 'error' && <Alert tone="error">{s.error}</Alert>}
      {s.status === 'ok' && !s.items.length && <EmptyState icon={Bell} title="You’re all caught up">Updates on your reports will show up here.</EmptyState>}
      {s.items.map((n) => <div key={n.id} className="rounded-card bg-white p-4 text-sm shadow-card">{n.text} <span className="text-xs text-ink/45">{timeAgo(n.createdAt)}</span></div>)}
    </div>
  )
}
