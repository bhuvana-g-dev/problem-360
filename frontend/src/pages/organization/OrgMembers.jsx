import { useState } from 'react'
import { UserCog } from 'lucide-react'
import PageHeader from '../../components/org/PageHeader.jsx'
import Async from '../../components/org/Async.jsx'
import useRole from '../../components/org/useRole.js'
import Field from '../../components/ui/Field.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import Card from '../../components/ui/Card.jsx'
import useForm, { isEmail } from '../../components/auth/useForm.js'
import useLoad from '../../hooks/useLoad.js'
import { inviteMember, orgInvites, orgMembers, removeMember, revokeInvite, setMemberRole } from '../../services/org.js'

export default function OrgMembers() {
  const { canManage, isOwner } = useRole()
  const members = useLoad(orgMembers)
  const invites = useLoad(() => (canManage ? orgInvites() : Promise.resolve([])), [canManage])
  const [fresh, setFresh] = useState(null)
  const [err, setErr] = useState('')
  const f = useForm({ email: '', role: 'member' }, (v) => (isEmail(v.email) ? {} : { email: 'Enter a valid email.' }))
  const act = (fn) => async () => { setErr(''); try { await fn(); members.reload(); invites.reload() } catch (e) { setErr(e.message) } }
  const joinUrl = (code) => `${location.origin}/org/join?code=${code}`

  return (
    <div className="max-w-3xl">
      <PageHeader title="Members" subtitle="Authorized people who can work in this organization’s workspace." />
      {canManage && (
        <Card className="mb-6">
          <form noValidate className="grid gap-4 sm:grid-cols-[1fr_9rem_auto]" onSubmit={f.submit(async (v) => { setFresh(await inviteMember(v)); f.reset(); invites.reload() })}>
            {f.formError && <div className="sm:col-span-3"><Alert tone="error">{f.formError}</Alert></div>}
            <Field label="Invite by email" type="email" value={f.values.email} onChange={f.set('email')} error={f.errors.email} />
            <Field as="select" label="Role" value={f.values.role} onChange={f.set('role')}><option value="member">Member (view only)</option><option value="admin">Admin (manage)</option></Field>
            <div className="flex items-end"><Button type="submit" variant="info" loading={f.submitting}>Create invite</Button></div>
          </form>
          {fresh && (
            <div className="mt-4"><Alert tone="success" title="Invite created">
              Send this link to <b>{fresh.email}</b> (valid {fresh.expiresInDays} days, single use, only works for that email). No email is sent automatically.
              <input readOnly aria-label="Invite link" value={joinUrl(fresh.code)} onFocus={(e) => e.target.select()} className="mt-2 w-full rounded-lg border border-ink/15 bg-white px-2 py-1.5 text-xs" />
            </Alert></div>
          )}
        </Card>
      )}
      {err && <div className="mb-3"><Alert tone="error">{err}</Alert></div>}
      <Async load={members} icon={UserCog} emptyTitle="No members" empty="">
        {(rows) => <Card className="divide-y divide-ink/10 p-0">{rows.map((m) => (
          <div key={m.uid} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 text-sm">
            <div><p className="font-medium">{m.name}</p><p className="text-xs text-ink/55">{m.email}</p></div>
            <div className="flex items-center gap-2">
              {isOwner && m.role !== 'owner' ? (
                <select aria-label={`Role for ${m.name}`} value={m.role} onChange={(e) => act(() => setMemberRole(m.uid, e.target.value))()} className="rounded-lg border border-ink/15 px-2 py-1 text-xs">
                  <option value="member">member</option><option value="admin">admin</option></select>
              ) : <span className="rounded-full bg-info/10 px-2.5 py-1 text-xs font-semibold text-info">{m.role}</span>}
              {isOwner && m.role !== 'owner' && <button className="text-xs text-red-600 underline" onClick={act(() => removeMember(m.uid))}>Remove</button>}
            </div>
          </div>))}</Card>}
      </Async>
      {canManage && (invites.data?.length > 0) && (
        <>
          <h2 className="mb-2 mt-6 text-lg">Pending invites</h2>
          <Card className="divide-y divide-ink/10 p-0">{invites.data.map((i) => (
            <div key={i.code} className="flex items-center justify-between px-4 py-3 text-sm"><span>{i.email} · {i.role}</span>
              <button className="text-xs text-red-600 underline" onClick={act(() => revokeInvite(i.code))}>Revoke</button></div>))}</Card>
        </>
      )}
    </div>
  )
}
