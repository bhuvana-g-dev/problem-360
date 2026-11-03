import Alert from '../ui/Alert.jsx'
import Button from '../ui/Button.jsx'
import { EmptyState } from '../ui/States.jsx'

/** Standard loading / error / empty wrapper for a useLoad() result. */
export default function Async({ load, empty, emptyTitle = 'Nothing here yet', icon, children }) {
  if (load.loading) return <p role="status" className="text-sm text-ink/60">Loading…</p>
  if (load.error) return <div className="space-y-3"><Alert tone="error">{load.error}</Alert><Button variant="secondary" onClick={load.reload}>Try again</Button></div>
  if (!load.data?.length) return <EmptyState icon={icon} title={emptyTitle}>{empty}</EmptyState>
  return children(load.data)
}
