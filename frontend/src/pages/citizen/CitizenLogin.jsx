import { Link, useNavigate, useLocation } from 'react-router-dom'
import AuthShell from '../../components/auth/AuthShell.jsx'
import Field from '../../components/ui/Field.jsx'
import PasswordField from '../../components/ui/PasswordField.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import useForm, { loginRules } from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { ACCOUNT_TYPES, ROUTES } from '../../config/constants.js'

export const CITIZEN_POINTS = [
  'Post civic problems with photos, location and category',
  'Follow what’s happening in your locality',
  'Join volunteer drives and community events',
]

export default function CitizenLogin() {
  const { signIn } = useAuth()
  const nav = useNavigate()
  const from = useLocation().state?.from?.pathname
  const f = useForm({ email: '', password: '' }, loginRules)
  return (
    <AuthShell variant="citizen" title="Welcome back" subtitle="Log in to your citizen account." points={CITIZEN_POINTS}
      footer={<>
        <p>New here? <Link className="font-medium text-brand hover:underline" to={ROUTES.citizenRegister}>Create a citizen account</Link></p>
        <p>Representing an organization? <Link className="font-medium text-info hover:underline" to={ROUTES.orgLogin}>Organization login</Link></p>
      </>}>
      <form onSubmit={f.submit(async (v) => { await signIn(ACCOUNT_TYPES.CITIZEN, v.email.trim(), v.password); nav(from?.startsWith('/app') ? from : ROUTES.citizenHome, { replace: true }) })} className="space-y-4" noValidate>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <Field label="Email" type="email" autoComplete="email" value={f.values.email} onChange={f.set('email')} error={f.errors.email} />
        <PasswordField autoComplete="current-password" value={f.values.password} onChange={f.set('password')} error={f.errors.password} />
        <Button type="submit" loading={f.submitting} className="w-full">Log in</Button>
      </form>
    </AuthShell>
  )
}
