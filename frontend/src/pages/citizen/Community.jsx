import { useState } from 'react'
import { CalendarDays, Megaphone, Users } from 'lucide-react'
import Async from '../../components/org/Async.jsx'
import EventCard from '../../components/feed/EventCard.jsx'
import Button from '../../components/ui/Button.jsx'
import useLoad from '../../hooks/useLoad.js'
import { joinGroup, leaveGroup, listEvents, listGroups, listUpdates, registerEvent, unregisterEvent } from '../../services/community.js'
import { MADURAI_LOCALITIES } from '../../config/constants.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { timeAgo } from '../../lib/format.js'

function GroupCard({ group }) {
  const [g, setG] = useState(group)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const toggle = async () => {
    setBusy(true); setErr('')
    try { const r = g.joinedByMe ? await leaveGroup(g.id) : await joinGroup(g.id); setG((x) => ({ ...x, joinedByMe: r.joinedByMe, memberCount: x.memberCount + (r.joinedByMe ? 1 : -1) })) }
    catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  return (
    <article className="rounded-card bg-white p-5 shadow-card">
      <p className="text-xs font-semibold text-info">{g.orgName}</p>
      <h3 className="text-lg">{g.name}</h3>
      <p className="text-xs text-ink/55">{g.locality}{g.focus ? ` · ${g.focus}` : ''}</p>
      <p className="mt-2 text-sm text-ink/80">{g.description}</p>
      <div className="mt-4 flex items-center justify-between"><span className="text-xs text-ink/60">{g.memberCount} members</span>
        <Button onClick={toggle} loading={busy} variant={g.joinedByMe ? 'secondary' : 'primary'}>{g.joinedByMe ? 'Leave group' : 'Join group'}</Button></div>
      {err && <p role="alert" className="mt-2 text-xs text-red-600">{err}</p>}
    </article>
  )
}

const tabs = [['events', 'Events', CalendarDays], ['groups', 'Groups', Users], ['updates', 'Updates', Megaphone]]

export default function Community() {
  const { account } = useAuth()
  const [tab, setTab] = useState('events')
  const [locality, setLocality] = useState(account.locality || '')
  const events = useLoad(() => listEvents(locality), [locality])
  const groups = useLoad(() => listGroups(locality), [locality])
  const updates = useLoad(listUpdates)
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl">Volunteer groups & events</h1>
        <select aria-label="Locality" value={locality} onChange={(e) => setLocality(e.target.value)} className="rounded-xl border border-ink/15 bg-white px-3 py-2 text-sm">
          <option value="">All localities</option>{MADURAI_LOCALITIES.map((l) => <option key={l}>{l}</option>)}
        </select>
      </div>
      <div role="tablist" className="flex gap-1 rounded-xl bg-white p-1 shadow-card">
        {tabs.map(([id, label, Icon]) => (
          <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-medium ${tab === id ? 'bg-brand text-white' : 'text-ink/65 hover:bg-ink/5'}`}><Icon className="h-4 w-4" />{label}</button>))}
      </div>
      {tab === 'events' && <Async load={events} icon={CalendarDays} emptyTitle="No upcoming events" empty="Verified organizations will post volunteer drives here.">
        {(items) => <div className="space-y-4">{items.map((e) => <EventCard key={e.id} event={e} onRegister={registerEvent} onUnregister={unregisterEvent} />)}</div>}</Async>}
      {tab === 'groups' && <Async load={groups} icon={Users} emptyTitle="No groups yet" empty="Volunteer groups created by verified organizations appear here.">
        {(items) => <div className="space-y-4">{items.map((g) => <GroupCard key={g.id} group={g} />)}</div>}</Async>}
      {tab === 'updates' && <Async load={updates} icon={Megaphone} emptyTitle="No updates yet" empty="Organization news appears here.">
        {(items) => <div className="space-y-3">{items.map((u) => <article key={u.id} className="rounded-card bg-white p-5 shadow-card"><p className="text-xs font-semibold text-info">{u.orgName} · {timeAgo(u.createdAt)}</p><h3 className="text-base">{u.title}</h3><p className="mt-1 whitespace-pre-line text-sm text-ink/80">{u.body}</p></article>)}</div>}</Async>}
    </div>
  )
}
