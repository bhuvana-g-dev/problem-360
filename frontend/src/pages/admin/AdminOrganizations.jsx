import { useState } from 'react'
import { Building2 } from 'lucide-react'
import PageHeader from '../../components/org/PageHeader.jsx'
import Async from '../../components/org/Async.jsx'
import Alert from '../../components/ui/Alert.jsx'
import Button from '../../components/ui/Button.jsx'
import Card from '../../components/ui/Card.jsx'
import Field from '../../components/ui/Field.jsx'
import { VerificationBadge } from '../../components/ui/Badge.jsx'
import useLoad from '../../hooks/useLoad.js'
import { adminOrganizations, setVerification } from '../../services/admin.js'
import { timeAgo } from '../../lib/format.js'

function OrgCard({ o, onDone }) {
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const set = (st) => async () => {
    setBusy(st); setError('')
    try { await setVerification(o.id, st, note); onDone() } catch (e) { setError(e.message) } finally { setBusy('') }
  }
  return (
    <Card>
      <div className="flex flex-wrap items-center gap-2"><h2 className="text-base">{o.name}</h2><VerificationBadge status={o.verificationStatus} /></div>
      <p className="text-xs text-ink/55">{o.category} · {o.locality} · registered {timeAgo(o.createdAt)}{o.website ? ` · ${o.website}` : ''}</p>
      <p className="mt-2 text-sm">{o.description}</p>
      {error && <div className="mt-2"><Alert tone="error">{error}</Alert></div>}
      <Field className="mt-3" label="Note (what you checked)" value={note} maxLength={300} onChange={(e) => setNote(e.target.value)} />
      <div className="mt-2 flex flex-wrap gap-2">
        {o.verificationStatus !== 'verified' && <Button loading={busy === 'verified'} onClick={set('verified')}>Verify</Button>}
        {o.verificationStatus !== 'rejected' && <Button variant="secondary" loading={busy === 'rejected'} onClick={set('rejected')}>Reject</Button>}
      </div>
    </Card>
  )
}

/** Organization verification (backend: /api/admin/organizations). Verify only after checking real documents. */
export default function AdminOrganizations() {
  const [tab, setTab] = useState('pending')
  const load = useLoad(() => adminOrganizations(tab === 'all' ? undefined : tab), [tab])
  return (
    <div className="max-w-3xl">
      <PageHeader title="Organizations" subtitle="Verify an organization only after checking its registration documents. The backend trusts this decision." />
      <div role="tablist" className="mb-4 flex gap-2">
        {[['pending', 'Pending'], ['verified', 'Verified'], ['rejected', 'Rejected'], ['all', 'All']].map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium ${tab === k ? 'bg-ink text-white' : 'bg-ink/5 text-ink/70 hover:bg-ink/10'}`}>{label}</button>
        ))}
      </div>
      <Async load={load} icon={Building2} emptyTitle="No organizations here" empty="New registrations appear under Pending.">
        {(rows) => <div className="space-y-3">{rows.map((o) => <OrgCard key={o.id + o.verificationStatus} o={o} onDone={load.reload} />)}</div>}
      </Async>
    </div>
  )
}
