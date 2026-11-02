import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../../components/auth/AuthShell.jsx'
import Field from '../../components/ui/Field.jsx'
import PasswordField from '../../components/ui/PasswordField.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import useForm, { loginRules } from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { ACCOUNT_TYPES, ROUTES } from '../../config/constants.js'

export const ORG_POINTS = [
  'Create and manage volunteer groups',
  'Organize community events and registrations',
  'Publish updates and coordinate civic activity',
  'Management tools unlock after verification',
]

export default function OrgLogin() {
  const { signIn } = useAuth()
  const nav = useNavigate()
  const f = useForm({ email: '', password: '' }, loginRules)
  return (
    <AuthShell variant="organization" title="Organization login" subtitle="Access your organization workspace." points={ORG_POINTS}
      footer={<>
        <p>No account yet? <Link className="font-medium text-info hover:underline" to={ROUTES.orgRegister}>Register your organization</Link></p>
        <p>Looking for the citizen app? <Link className="font-medium text-brand hover:underline" to={ROUTES.citizenLogin}>Citizen login</Link></p>
      </>}>
      <form onSubmit={f.submit(async (v) => { await signIn(ACCOUNT_TYPES.ORGANIZATION, v.email.trim(), v.password); nav(ROUTES.orgHome, { replace: true }) })} className="space-y-4" noValidate>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <Field label="Work email" type="email" autoComplete="email" value={f.values.email} onChange={f.set('email')} error={f.errors.email} />
        <PasswordField autoComplete="current-password" value={f.values.password} onChange={f.set('password')} error={f.errors.password} />
        <Button type="submit" variant="info" loading={f.submitting} className="w-full">Log in</Button>
      </form>
    </AuthShell>
  )
}
