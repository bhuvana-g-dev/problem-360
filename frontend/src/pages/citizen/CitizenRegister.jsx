import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../../components/auth/AuthShell.jsx'
import Field from '../../components/ui/Field.jsx'
import PasswordField from '../../components/ui/PasswordField.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import useForm, { isEmail } from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { MADURAI_LOCALITIES, ROUTES } from '../../config/constants.js'
import { CITIZEN_POINTS } from './CitizenLogin.jsx'

const rules = (v) => ({
  ...(v.displayName.trim().length >= 2 ? {} : { displayName: 'Enter your name.' }),
  ...(isEmail(v.email) ? {} : { email: 'Enter a valid email.' }),
  ...(v.password.length >= 8 ? {} : { password: 'Use at least 8 characters.' }),
  ...(v.locality ? {} : { locality: 'Choose your locality.' }),
})

export default function CitizenRegister() {
  const { registerCitizen } = useAuth()
  const nav = useNavigate()
  const f = useForm({ displayName: '', email: '', password: '', locality: '' }, rules)
  return (
    <AuthShell variant="citizen" title="Create your citizen account" subtitle="Join your neighbours in making Madurai better." points={CITIZEN_POINTS}
      footer={<p>Already registered? <Link className="font-medium text-brand hover:underline" to={ROUTES.citizenLogin}>Log in</Link></p>}>
      <form onSubmit={f.submit(async (v) => { await registerCitizen({ ...v, displayName: v.displayName.trim(), email: v.email.trim() }); nav(ROUTES.citizenHome, { replace: true }) })} className="space-y-4" noValidate>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <Field label="Full name" autoComplete="name" value={f.values.displayName} onChange={f.set('displayName')} error={f.errors.displayName} />
        <Field label="Email" type="email" autoComplete="email" value={f.values.email} onChange={f.set('email')} error={f.errors.email} />
        <PasswordField autoComplete="new-password" value={f.values.password} onChange={f.set('password')} error={f.errors.password} hint="At least 8 characters." />
        <Field as="select" label="Your locality" value={f.values.locality} onChange={f.set('locality')} error={f.errors.locality}>
          <option value="">Select locality</option>
          {MADURAI_LOCALITIES.map((l) => <option key={l}>{l}</option>)}
        </Field>
        <Button type="submit" loading={f.submitting} className="w-full">Create account</Button>
      </form>
    </AuthShell>
  )
}
