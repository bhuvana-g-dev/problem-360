import { useState } from 'react'
import { AlertTriangle, ClipboardCheck, Copy, HelpCircle } from 'lucide-react'
import PageHeader from '../../components/org/PageHeader.jsx'
import Async from '../../components/org/Async.jsx'
import Alert from '../../components/ui/Alert.jsx'
import Button from '../../components/ui/Button.jsx'
import Card from '../../components/ui/Card.jsx'
import Field from '../../components/ui/Field.jsx'
import { StatusBadge } from '../../components/ui/Badge.jsx'
import LocationPreview from '../../components/feed/LocationPreview.jsx'
import useLoad from '../../hooks/useLoad.js'
import { decideReview, reviewQueue, reviewStats, setReportStatus } from '../../services/admin.js'
import { timeAgo } from '../../lib/format.js'

const mins = (m) => (m == null ? '–' : m < 60 ? `${Math.round(m)} min` : m < 1440 ? `${(m / 60).toFixed(1)} h` : `${(m / 1440).toFixed(1)} d`)

function Why({ r }) {
  if (r.urgent) return <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-semibold text-red-700"><AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />Possible danger</span>
  if (r.failedClosed) return <span className="inline-flex items-center gap-1 rounded-full bg-gold/25 px-2.5 py-1 text-xs font-semibold text-ink"><HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />Agent could not review</span>
  if (r.action === 'CHECK_DUPLICATE') return <span className="inline-flex items-center gap-1 rounded-full bg-info/10 px-2.5 py-1 text-xs font-semibold text-info"><Copy className="h-3.5 w-3.5" aria-hidden="true" />Possible duplicate{r.duplicateOf ? ` of ${r.duplicateOf}` : ''}</span>
  return <span className="inline-flex rounded-full bg-ink/10 px-2.5 py-1 text-xs font-semibold">Needs a person</span>
}

function Stat({ label, value, tone = '' }) {
  return <div className={`rounded-xl border border-ink/10 bg-white p-3 ${tone}`}><p className="text-xs text-ink/60">{label}</p><p className="mt-0.5 text-xl font-semibold">{value}</p></div>
}

function ReviewCard({ r, onDone }) {
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const act = (key, fn) => async () => {
    setBusy(key); setError('')
    try { await fn(); onDone() } catch (e) { setError(e.message) } finally { setBusy('') }
  }
  const pending = r.review.state === 'pending'
  return (
    <Card>
      <div className="flex flex-wrap items-center gap-2">
        <Why r={r} /><StatusBadge status={r.status} />
        <span className="text-xs text-ink/55">{r.referenceId} · {r.category} · {r.locality}{r.locationText ? `, ${r.locationText}` : ''} · reported {timeAgo(r.createdAt)}</span>
      </div>
      <p className="mt-2 text-sm">{r.description}</p>
      {r.coordinates && <div className="mt-1"><LocationPreview coords={r.coordinates} /></div>}
      {r.keywordHits.length > 0 && <p className="mt-1 text-xs text-red-700">Danger words found by code: {r.keywordHits.join(', ')}</p>}
      {r.summary && <p className="mt-2 rounded-lg bg-ink/5 p-2 text-xs text-ink/75"><b>Citizen was told:</b> {r.summary}</p>}
      {!pending && (
        <p className="mt-2 text-xs text-ink/65">
          {r.review.state === 'approved' ? 'Approved' : 'Closed'} by {r.review.byName || 'a reviewer'} {mins(r.review.minutesToReview)} after it was reported
          {r.review.note ? ` · “${r.review.note}”` : ''}
        </p>
      )}
      {error && <div className="mt-2"><Alert tone="error">{error}</Alert></div>}
      {pending && (
        <div className="mt-3 space-y-2">
          <Field label="Note to the citizen (required to close)" as="textarea" rows={2} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)}
            hint="Sent with the notification. Do not say a department was contacted unless you contacted them yourself." />
          <div className="flex flex-wrap gap-2">
            <Button loading={busy === 'approve'} onClick={act('approve', () => decideReview(r.id, 'approve', note))}>Approve: acknowledged</Button>
            <Button variant="secondary" loading={busy === 'reject'} disabled={note.trim().length < 3}
              onClick={act('reject', () => decideReview(r.id, 'reject', note))}>Close: not actionable</Button>
          </div>
        </div>
      )}
      {r.review.state === 'approved' && (
        <div className="mt-3 flex flex-wrap gap-2">
          {r.status !== 'Resolved'
            ? <Button variant="info" loading={busy === 'resolve'} onClick={act('resolve', () => setReportStatus(r.id, 'Resolved'))}>Mark resolved</Button>
            : <Button variant="ghost" loading={busy === 'reopen'} onClick={act('reopen', () => setReportStatus(r.id, 'Acknowledged', 'Reopened for follow-up'))}>Reopen</Button>}
        </div>
      )}
    </Card>
  )
}

/** The human review queue: closes the loop on every report the agent marked for a person. */
export default function AdminReviews() {
  const [tab, setTab] = useState('pending')
  const load = useLoad(() => reviewQueue(tab), [tab])
  const stats = useLoad(reviewStats)
  const refresh = () => { load.reload(); stats.reload() }
  const s = stats.data
  return (
    <div className="max-w-4xl">
      <PageHeader title="Review queue" subtitle="Danger reports first, then reports the agent could not review, then the oldest. Each one needs a person." />
      {s && (
        <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Waiting for review" value={s.pending} tone={s.pending ? 'border-gold/60' : ''} />
          <Stat label="Danger reports waiting" value={s.urgentPending} tone={s.urgentPending ? 'border-red-300 bg-red-50' : ''} />
          <Stat label="Median time to a person" value={mins(s.medianMinutesToReview)} />
          <Stat label="…for danger reports" value={mins(s.medianMinutesToReviewUrgent)} />
        </div>
      )}
      <div role="tablist" className="mb-4 flex gap-2">
        {[['pending', 'Waiting'], ['done', 'Reviewed']].map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium ${tab === k ? 'bg-ink text-white' : 'bg-ink/5 text-ink/70 hover:bg-ink/10'}`}>{label}</button>
        ))}
      </div>
      <Async load={load} icon={ClipboardCheck} emptyTitle={tab === 'pending' ? 'Nothing is waiting' : 'Nothing reviewed yet'}
        empty={tab === 'pending' ? 'Every flagged report has been reviewed.' : 'Reviewed reports appear here.'}>
        {(rows) => <div className="space-y-3">{rows.map((r) => <ReviewCard key={r.id + r.review.state + r.status} r={r} onDone={refresh} />)}</div>}
      </Async>
    </div>
  )
}
