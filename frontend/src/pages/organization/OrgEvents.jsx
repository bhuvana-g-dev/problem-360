import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CalendarDays } from 'lucide-react'
import PageHeader from '../../components/org/PageHeader.jsx'
import Async from '../../components/org/Async.jsx'
import useRole from '../../components/org/useRole.js'
import Field from '../../components/ui/Field.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import Card from '../../components/ui/Card.jsx'
import useForm from '../../components/auth/useForm.js'
import useLoad from '../../hooks/useLoad.js'
import { cancelEvent, createEvent, eventRegistrations, orgEvents, orgGroups, orgOpportunities } from '../../services/org.js'
import { MADURAI_LOCALITIES } from '../../config/constants.js'
import { fmtDateTime, toIso } from '../../lib/format.js'
import { useAuth } from '../../context/AuthContext.jsx'

const rules = (v) => ({
  ...(v.title.trim().length >= 3 ? {} : { title: 'Enter a title.' }),
  ...(v.description.trim().length >= 10 ? {} : { description: 'Describe the event (10+ characters).' }),
  ...(v.locality ? {} : { locality: 'Choose a locality.' }),
  ...(v.startsAt && new Date(v.startsAt) > new Date() ? {} : { startsAt: 'Choose a start time in the future.' }),
  ...(!v.endsAt || new Date(v.endsAt) > new Date(v.startsAt) ? {} : { endsAt: 'End must be after start.' }),
  ...(!v.capacity || Number(v.capacity) >= 1 ? {} : { capacity: 'Capacity must be at least 1.' }),
  ...(v.safetyNotes.trim().length >= 10 ? {} : { safetyNotes: 'Say how participants stay safe (10+ characters).' }),
})

function Registrations({ id }) {
  const load = useLoad(() => eventRegistrations(id), [id])
  if (load.loading) return <p className="text-xs text-ink/55">Loading…</p>
  if (load.error) return <p className="text-xs text-red-600">{load.error}</p>
  return load.data.length ? <ul className="mt-2 text-xs text-ink/75">{load.data.map((r) => <li key={r.uid}>{r.name}</li>)}</ul> : <p className="mt-2 text-xs text-ink/55">No registrations yet.</p>
}

export default function OrgEvents() {
  const { canManage } = useRole()
  const { account } = useAuth()
  const [params] = useSearchParams()
  const load = useLoad(orgEvents)
  const groups = useLoad(orgGroups)
  const opps = useLoad(orgOpportunities)
  const [open, setOpen] = useState(null)
  const [actionError, setActionError] = useState('')
  const f = useForm({ title: '', description: '', locality: account.organization.locality || '', locationText: '', startsAt: '', endsAt: '', capacity: '',
    groupId: '', relatedPostId: params.get('post') || '', safetyNotes: '' }, rules)
  const t = (n) => ({ value: f.values[n], onChange: f.set(n), error: f.errors[n] })

  const cancel = async (id) => { setActionError(''); try { await cancelEvent(id); load.reload() } catch (e) { setActionError(e.message) } }
  return (
    <div className="max-w-4xl">
      <PageHeader title="Events & volunteer drives" subtitle="Registrations are capacity-checked. Every event needs safety notes." />
      {canManage && (
        <Card className="mb-6">
          <form noValidate className="grid gap-4 sm:grid-cols-2" onSubmit={f.submit(async (v) => {
            await createEvent({ title: v.title, description: v.description, locality: v.locality, locationText: v.locationText, startsAt: toIso(v.startsAt), endsAt: toIso(v.endsAt),
              capacity: v.capacity ? Number(v.capacity) : null, groupId: v.groupId || null, relatedPostId: v.relatedPostId || null, safetyNotes: v.safetyNotes })
            f.reset(); load.reload()
          })}>
            <h2 className="text-lg sm:col-span-2">Create a volunteer drive or event</h2>
            {f.formError && <div className="sm:col-span-2"><Alert tone="error">{f.formError}</Alert></div>}
            <Field label="Title" className="sm:col-span-2" {...t('title')} />
            <Field as="textarea" rows={2} label="Details" className="sm:col-span-2" {...t('description')} />
            <Field as="select" label="Locality" {...t('locality')}><option value="">Select</option>{MADURAI_LOCALITIES.map((l) => <option key={l}>{l}</option>)}</Field>
            <Field label="Meeting point (optional)" {...t('locationText')} />
            <Field label="Starts" type="datetime-local" {...t('startsAt')} />
            <Field label="Ends (optional)" type="datetime-local" {...t('endsAt')} />
            <Field label="Capacity (optional)" type="number" min="1" {...t('capacity')} />
            <Field as="select" label="Group (optional)" {...t('groupId')}><option value="">None</option>{(groups.data || []).map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</Field>
            <Field as="select" label="Linked civic report (optional)" className="sm:col-span-2" hint="Only reports the Strands Decider marked safe for community action can be linked."
              {...t('relatedPostId')}><option value="">None</option>{(opps.data || []).map((o) => <option key={o.postId} value={o.postId}>{o.referenceId} · {o.category} · {o.description.slice(0, 50)}</option>)}</Field>
            <Field as="textarea" rows={2} label="Safety notes (required)" className="sm:col-span-2" placeholder="Gloves, closed shoes, adult supervision, what NOT to touch…" {...t('safetyNotes')} />
            <div><Button type="submit" variant="info" loading={f.submitting}>Create event</Button></div>
          </form>
        </Card>
      )}
      {actionError && <div className="mb-3"><Alert tone="error">{actionError}</Alert></div>}
      <Async load={load} icon={CalendarDays} emptyTitle="No events yet" empty="Create a volunteer drive to start collecting registrations.">
        {(events) => <div className="space-y-3">{events.map((e) => (
          <Card key={e.id}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div><h3 className="text-base">{e.title}</h3><p className="text-xs text-ink/55">{fmtDateTime(e.startsAt)} · {e.locality}{e.locationText ? `, ${e.locationText}` : ''}</p></div>
              <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${e.status === 'scheduled' ? 'bg-leaf/20 text-brand' : 'bg-ink/10 text-ink/60'}`}>{e.status}</span>
            </div>
            <p className="mt-2 text-sm text-ink/75">{e.description}</p>
            <p className="mt-1 text-xs text-ink/60"><b>Safety:</b> {e.safetyNotes}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
              <span className="font-semibold text-info">{e.registrationCount}{e.capacity ? ` / ${e.capacity}` : ''} registered</span>
              <button className="text-brand underline" onClick={() => setOpen(open === e.id ? null : e.id)}>{open === e.id ? 'Hide' : 'View'} registrations</button>
              {canManage && e.status === 'scheduled' && <button className="text-red-600 underline" onClick={() => cancel(e.id)}>Cancel event</button>}
            </div>
            {open === e.id && <Registrations id={e.id} />}
          </Card>))}</div>}
      </Async>
    </div>
  )
}
