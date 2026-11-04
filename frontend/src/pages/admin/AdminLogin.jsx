import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../../components/auth/AuthShell.jsx'
import Field from '../../components/ui/Field.jsx'
import PasswordField from '../../components/ui/PasswordField.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import useForm, { loginRules } from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { ACCOUNT_TYPES, ROUTES } from '../../config/constants.js'

const POINTS = [
  'Review every report the agent flagged: danger, possible duplicates and reports it could not decide',
  'Approve or close each one, then mark it resolved',
  'The citizen is notified at every step',
]

/** Reviewer (admin) login. Admin accounts are never self-registered: see backend/scripts/make_admin.py. */
export default function AdminLogin() {
  const { signIn } = useAuth()
  const nav = useNavigate()
  const f = useForm({ email: '', password: '' }, loginRules)
  return (
    <AuthShell variant="organization" title="Reviewer login" subtitle="For Problem 360 reviewers (admins) only." points={POINTS}
      footer={<p>Not a reviewer? <Link className="font-medium text-brand hover:underline" to={ROUTES.citizenLogin}>Citizen login</Link></p>}>
      <form onSubmit={f.submit(async (v) => { await signIn(ACCOUNT_TYPES.ADMIN, v.email.trim(), v.password); nav(ROUTES.adminHome, { replace: true }) })} className="space-y-4" noValidate>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <Field label="Email" type="email" autoComplete="email" value={f.values.email} onChange={f.set('email')} error={f.errors.email} />
        <PasswordField autoComplete="current-password" value={f.values.password} onChange={f.set('password')} error={f.errors.password} />
        <Button type="submit" loading={f.submitting} className="w-full">Log in</Button>
      </form>
    </AuthShell>
  )
}
