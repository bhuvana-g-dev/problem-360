import { Megaphone } from 'lucide-react'
import PageHeader from '../../components/org/PageHeader.jsx'
import Async from '../../components/org/Async.jsx'
import useRole from '../../components/org/useRole.js'
import Field from '../../components/ui/Field.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import Card from '../../components/ui/Card.jsx'
import useForm from '../../components/auth/useForm.js'
import useLoad from '../../hooks/useLoad.js'
import { orgUpdates, publishUpdate } from '../../services/org.js'
import { timeAgo } from '../../lib/format.js'

const rules = (v) => ({ ...(v.title.trim().length >= 3 ? {} : { title: 'Enter a title.' }), ...(v.body.trim().length >= 10 ? {} : { body: 'Write at least 10 characters.' }) })

export default function OrgUpdates() {
  const { canManage } = useRole()
  const load = useLoad(orgUpdates)
  const f = useForm({ title: '', body: '' }, rules)
  return (
    <div className="max-w-3xl">
      <PageHeader title="Organization updates" subtitle="Published updates are visible to citizens under Groups & events." />
      {canManage && (
        <Card className="mb-6">
          <form noValidate className="space-y-4" onSubmit={f.submit(async (v) => { await publishUpdate(v); f.reset(); load.reload() })}>
            {f.formError && <Alert tone="error">{f.formError}</Alert>}
            <Field label="Title" value={f.values.title} onChange={f.set('title')} error={f.errors.title} />
            <Field as="textarea" rows={3} label="Update" value={f.values.body} onChange={f.set('body')} error={f.errors.body} />
            <Button type="submit" variant="info" loading={f.submitting}>Publish update</Button>
          </form>
        </Card>
      )}
      <Async load={load} icon={Megaphone} emptyTitle="No updates yet" empty="Share news about your drives and results.">
        {(items) => <div className="space-y-3">{items.map((u) => <Card key={u.id}><h3 className="text-base">{u.title}</h3><p className="text-xs text-ink/50">{timeAgo(u.createdAt)}</p><p className="mt-2 whitespace-pre-line text-sm text-ink/80">{u.body}</p></Card>)}</div>}
      </Async>
    </div>
  )
}
