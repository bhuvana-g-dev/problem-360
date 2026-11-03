import { Users } from 'lucide-react'
import PageHeader from '../../components/org/PageHeader.jsx'
import Async from '../../components/org/Async.jsx'
import useRole from '../../components/org/useRole.js'
import Field from '../../components/ui/Field.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import Card from '../../components/ui/Card.jsx'
import useForm from '../../components/auth/useForm.js'
import useLoad from '../../hooks/useLoad.js'
import { createGroup, orgGroups } from '../../services/org.js'
import { ISSUE_CATEGORIES, MADURAI_LOCALITIES } from '../../config/constants.js'
import { useAuth } from '../../context/AuthContext.jsx'

const rules = (v) => ({
  ...(v.name.trim().length >= 3 ? {} : { name: 'Enter a group name.' }),
  ...(v.description.trim().length >= 10 ? {} : { description: 'Describe the group in at least 10 characters.' }),
  ...(v.locality ? {} : { locality: 'Choose a locality.' }),
})

export default function OrgGroups() {
  const { canManage } = useRole()
  const { account } = useAuth()
  const load = useLoad(orgGroups)
  const f = useForm({ name: '', description: '', locality: account.organization.locality || '', focus: '' }, rules)
  const t = (n) => ({ value: f.values[n], onChange: f.set(n), error: f.errors[n] })
  return (
    <div className="max-w-4xl">
      <PageHeader title="Volunteer groups" subtitle="Citizens in your locality can discover and join these groups." />
      {canManage && (
        <Card className="mb-6">
          <form noValidate className="grid gap-4 sm:grid-cols-2" onSubmit={f.submit(async (v) => { await createGroup({ ...v, focus: v.focus || null }); f.reset?.(); load.reload() })}>
            <h2 className="text-lg sm:col-span-2">Create a group</h2>
            {f.formError && <div className="sm:col-span-2"><Alert tone="error">{f.formError}</Alert></div>}
            <Field label="Group name" {...t('name')} />
            <Field as="select" label="Locality" {...t('locality')}><option value="">Select</option>{MADURAI_LOCALITIES.map((l) => <option key={l}>{l}</option>)}</Field>
            <Field as="textarea" rows={2} label="What does the group do?" className="sm:col-span-2" {...t('description')} />
            <Field as="select" label="Focus (optional)" {...t('focus')}><option value="">Any</option>{ISSUE_CATEGORIES.map((c) => <option key={c}>{c}</option>)}</Field>
            <div className="flex items-end"><Button type="submit" variant="info" loading={f.submitting}>Create group</Button></div>
          </form>
        </Card>
      )}
      <Async load={load} icon={Users} emptyTitle="No groups yet" empty="Create your first volunteer group.">
        {(groups) => <div className="grid gap-4 sm:grid-cols-2">{groups.map((g) => (
          <Card key={g.id}><h3 className="text-base">{g.name}</h3><p className="text-xs text-ink/55">{g.locality}{g.focus ? ` · ${g.focus}` : ''}</p>
            <p className="mt-2 text-sm text-ink/75">{g.description}</p><p className="mt-3 text-sm font-semibold text-info">{g.memberCount} members</p></Card>))}</div>}
      </Async>
    </div>
  )
}
