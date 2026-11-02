import { Link } from 'react-router-dom'
import { Users, Building2, ArrowRight } from 'lucide-react'
import Logo from '../../components/ui/Logo.jsx'
import Button from '../../components/ui/Button.jsx'
import { BRAND, ROUTES } from '../../config/constants.js'

function Path({ icon: Icon, title, text, login, register, tone }) {
  return (
    <div className="flex flex-col rounded-card bg-white p-6 shadow-card">
      <span className={`mb-4 grid h-11 w-11 place-items-center rounded-xl ${tone}`}><Icon className="h-5 w-5" /></span>
      <h2 className="text-xl">{title}</h2>
      <p className="mt-1.5 flex-1 text-sm text-ink/65">{text}</p>
      <div className="mt-5 flex gap-2">
        <Button as={Link} to={register} className="flex-1">Create account <ArrowRight className="h-4 w-4" /></Button>
        <Button as={Link} to={login} variant="secondary">Log in</Button>
      </div>
    </div>
  )
}

export default function Landing() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-5 py-5"><Logo /></header>
      <main className="mx-auto max-w-5xl px-5 pb-16 pt-8 text-center">
        <span className="rounded-full bg-gold px-3 py-1 text-xs font-semibold text-ink">Madurai</span>
        <h1 className="mt-4 text-4xl text-ink sm:text-5xl">{BRAND.tagline}.</h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/70">
          Report civic problems in your neighbourhood, see what your community is raising, and join volunteers and organizations turning reports into action.
        </p>
        <div className="mt-10 grid gap-5 text-left sm:grid-cols-2">
          <Path icon={Users} tone="bg-leaf/20 text-brand" title="I’m a citizen"
            text="Post issues, follow your locality’s feed, and join volunteer drives."
            login={ROUTES.citizenLogin} register={ROUTES.citizenRegister} />
          <Path icon={Building2} tone="bg-info/10 text-info" title="I represent an organization"
            text="Run volunteer groups and events. Management tools unlock after verification."
            login={ROUTES.orgLogin} register={ROUTES.orgRegister} />
        </div>
      </main>
    </div>
  )
}
