import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../../components/auth/AuthShell.jsx'
import Field from '../../components/ui/Field.jsx'
import PasswordField from '../../components/ui/PasswordField.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import useForm, { isEmail } from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { MADURAI_LOCALITIES, ORG_CATEGORIES, ROUTES } from '../../config/constants.js'
import { ORG_POINTS } from './OrgLogin.jsx'

const rules = (v) => ({
  ...(v.orgName.trim().length >= 3 ? {} : { orgName: 'Enter the organization name.' }),
  ...(v.category ? {} : { category: 'Choose a category.' }),
  ...(v.description.trim().length >= 20 ? {} : { description: 'Describe the organization in at least 20 characters.' }),
  ...(v.locality ? {} : { locality: 'Choose a locality.' }),
  ...(v.contactName.trim().length >= 2 ? {} : { contactName: 'Enter the contact person’s name.' }),
  ...(isEmail(v.email) ? {} : { email: 'Enter a valid email.' }),
  ...(v.password.length >= 8 ? {} : { password: 'Use at least 8 characters.' }),
})

export default function OrgRegister() {
  const { registerOrganization } = useAuth()
  const nav = useNavigate()
  const f = useForm({ orgName: '', category: '', description: '', locality: '', website: '', contactName: '', email: '', password: '' }, rules)
  const t = (n) => ({ value: f.values[n], onChange: f.set(n), error: f.errors[n] })
  return (
    <AuthShell variant="organization" title="Register your organization" subtitle="Create the account for your organization’s first authorized member." points={ORG_POINTS}
      footer={<p>Already registered? <Link className="font-medium text-info hover:underline" to={ROUTES.orgLogin}>Log in</Link></p>}>
      <form onSubmit={f.submit(async (v) => {
        await registerOrganization({ ...v, orgName: v.orgName.trim(), description: v.description.trim(), contactName: v.contactName.trim(), email: v.email.trim(), website: v.website.trim() || null })
        nav(ROUTES.orgHome, { replace: true })
      })} className="space-y-4" noValidate>
        <Alert tone="info" title="Verification is required">New organizations start as <b>Pending</b>. Management features unlock after Problem 360 verifies you.</Alert>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <Field label="Organization name" {...t('orgName')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field as="select" label="Category" {...t('category')}><option value="">Select</option>{ORG_CATEGORIES.map((c) => <option key={c}>{c}</option>)}</Field>
          <Field as="select" label="Locality" {...t('locality')}><option value="">Select</option>{MADURAI_LOCALITIES.map((c) => <option key={c}>{c}</option>)}</Field>
        </div>
        <Field as="textarea" rows={3} label="What does your organization do?" {...t('description')} />
        <Field label="Website (optional)" type="url" placeholder="https://" {...t('website')} />
        <hr className="border-ink/10" />
        <Field label="Contact person" autoComplete="name" {...t('contactName')} />
        <Field label="Work email" type="email" autoComplete="email" {...t('email')} />
        <PasswordField autoComplete="new-password" hint="At least 8 characters." {...t('password')} />
        <Button type="submit" variant="info" loading={f.submitting} className="w-full">Register organization</Button>
      </form>
    </AuthShell>
  )
}
