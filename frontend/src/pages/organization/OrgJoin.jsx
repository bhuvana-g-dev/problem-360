import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import AuthShell from '../../components/auth/AuthShell.jsx'
import Field from '../../components/ui/Field.jsx'
import PasswordField from '../../components/ui/PasswordField.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import useForm, { isEmail } from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { ROUTES } from '../../config/constants.js'
import { ORG_POINTS } from './OrgLogin.jsx'

const rules = (v) => ({
  ...(v.contactName.trim().length >= 2 ? {} : { contactName: 'Enter your name.' }),
  ...(isEmail(v.email) ? {} : { email: 'Enter the email the invite was sent to.' }),
  ...(v.password.length >= 8 ? {} : { password: 'Use at least 8 characters.' }),
  ...(v.inviteCode.trim().length >= 10 ? {} : { inviteCode: 'Paste your invite code.' }),
})

/** Join an EXISTING organization with a single-use invite. This never creates a new organization. */
export default function OrgJoin() {
  const { joinOrganization } = useAuth()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const f = useForm({ contactName: '', email: '', password: '', inviteCode: params.get('code') || '' }, rules)
  const t = (n) => ({ value: f.values[n], onChange: f.set(n), error: f.errors[n] })
  return (
    <AuthShell variant="organization" title="Join your organization" subtitle="Use the invite link an organization owner or admin sent you." points={ORG_POINTS}
      footer={<p>Already joined? <Link className="font-medium text-info hover:underline" to={ROUTES.orgLogin}>Log in</Link></p>}>
      <form noValidate className="space-y-4" onSubmit={f.submit(async (v) => {
        await joinOrganization({ contactName: v.contactName.trim(), inviteCode: v.inviteCode.trim(), email: v.email.trim(), password: v.password }); nav(ROUTES.orgHome, { replace: true })
      })}>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <Field label="Your name" autoComplete="name" {...t('contactName')} />
        <Field label="Email (the one invited)" type="email" autoComplete="email" {...t('email')} />
        <PasswordField autoComplete="new-password" hint="At least 8 characters." {...t('password')} />
        <Field label="Invite code" {...t('inviteCode')} />
        <Button type="submit" variant="info" loading={f.submitting} className="w-full">Join organization</Button>
      </form>
    </AuthShell>
  )
}
