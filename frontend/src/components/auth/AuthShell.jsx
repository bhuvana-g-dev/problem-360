import { Link } from 'react-router-dom'
import Logo from '../ui/Logo.jsx'
import { BRAND } from '../../config/constants.js'

/**
 * Split-screen auth layout. `variant` gives citizen and organization flows visibly different identities:
 * citizen = bright green community feel, organization = dark management workspace with info-blue accent.
 */
export default function AuthShell({ variant = 'citizen', title, subtitle, points, children, footer }) {
  const org = variant === 'organization'
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <aside className={`relative hidden flex-col justify-between overflow-hidden p-10 text-white lg:flex ${org ? 'bg-ink' : 'bg-brand'}`}>
        <div aria-hidden="true" className={`absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-30 blur-3xl ${org ? 'bg-info' : 'bg-leaf'}`} />
        <div aria-hidden="true" className="absolute -bottom-24 -left-16 h-64 w-64 rounded-full bg-gold/25 blur-3xl" />
        <Logo light showTagline />
        <div className="relative">
          <span className={`mb-4 inline-block rounded-full px-3 py-1 text-xs font-semibold ${org ? 'bg-info text-white' : 'bg-gold text-ink'}`}>
            {org ? 'Organization workspace' : 'Citizen community'}
          </span>
          <h2 className="font-heading text-3xl font-semibold leading-snug">{BRAND.tagline}.</h2>
          <ul className="mt-6 space-y-3 text-white/85">
            {points.map((p) => (
              <li key={p} className="flex gap-3 text-sm"><span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${org ? 'bg-info' : 'bg-leaf'}`} />{p}</li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-white/60">Problem 360 · Madurai</p>
      </aside>

      <main className="flex items-center justify-center px-5 py-10">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden"><Logo showTagline /></div>
          <h1 className="text-2xl text-ink">{title}</h1>
          <p className="mt-1 text-sm text-ink/65">{subtitle}</p>
          <div className="mt-6">{children}</div>
          <div className="mt-6 space-y-2 text-center text-sm text-ink/65">
            {footer}
            <p><Link to="/" className="text-brand hover:underline">← Back to home</Link></p>
          </div>
        </div>
      </main>
    </div>
  )
}
