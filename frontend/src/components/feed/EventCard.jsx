import { useState } from 'react'
import { CalendarDays, MapPin, ShieldCheck } from 'lucide-react'
import Button from '../ui/Button.jsx'
import { fmtDateTime } from '../../lib/format.js'

/** Citizen-facing event with capacity-aware register / cancel. `onRegister` / `onUnregister` return the new registeredByMe. */
export default function EventCard({ event, onRegister, onUnregister }) {
  const [e, setE] = useState(event)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const full = e.spotsLeft === 0 && !e.registeredByMe

  const toggle = async () => {
    setBusy(true); setError('')
    try {
      const r = e.registeredByMe ? await onUnregister(e.id) : await onRegister(e.id)
      setE((x) => ({ ...x, registeredByMe: r.registeredByMe, registrationCount: x.registrationCount + (r.registeredByMe === x.registeredByMe ? 0 : r.registeredByMe ? 1 : -1),
        spotsLeft: x.spotsLeft === null ? null : x.spotsLeft + (r.registeredByMe === x.registeredByMe ? 0 : r.registeredByMe ? -1 : 1) }))
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <article className="rounded-card bg-white p-5 shadow-card">
      <p className="text-xs font-semibold text-info">{e.orgName}</p>
      <h3 className="text-lg">{e.title}</h3>
      <p className="mt-1 flex items-center gap-1.5 text-xs text-ink/60"><CalendarDays className="h-3.5 w-3.5" />{fmtDateTime(e.startsAt)}</p>
      <p className="flex items-center gap-1.5 text-xs text-ink/60"><MapPin className="h-3.5 w-3.5" />{[e.locationText, e.locality].filter(Boolean).join(', ')}</p>
      <p className="mt-2 text-sm text-ink/80">{e.description}</p>
      <p className="mt-2 flex gap-1.5 text-xs text-ink/70"><ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" /><span><b>Safety:</b> {e.safetyNotes}</span></p>
      <div className="mt-4 flex items-center justify-between gap-3">
        <span className="text-xs text-ink/60">{e.capacity ? `${e.spotsLeft} of ${e.capacity} spots left` : `${e.registrationCount} registered`}</span>
        <Button onClick={toggle} loading={busy} disabled={full} variant={e.registeredByMe ? 'secondary' : 'primary'}>
          {e.registeredByMe ? 'Cancel registration' : full ? 'Full' : 'Register'}
        </Button>
      </div>
      {error && <p role="alert" className="mt-2 text-xs text-red-600">{error}</p>}
    </article>
  )
}
