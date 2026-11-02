import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Users, CalendarDays, Megaphone, UserCog, Settings, LogOut, Lock } from 'lucide-react'
import Logo from '../ui/Logo.jsx'
import { VerificationBadge } from '../ui/Badge.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import { VERIFICATION } from '../../config/constants.js'

const nav = [
  { to: '/org/dashboard', label: 'Overview', icon: LayoutDashboard, open: true },
  { to: '/org/groups', label: 'Volunteer groups', icon: Users },
  { to: '/org/events', label: 'Events', icon: CalendarDays },
  { to: '/org/updates', label: 'Updates', icon: Megaphone },
  { to: '/org/members', label: 'Members', icon: UserCog },
  { to: '/org/settings', label: 'Organization profile', icon: Settings, open: true },
]

/** Management workspace: sidebar + header. Deliberately unlike the citizen feed. */
export default function OrganizationLayout() {
  const { account, signOut } = useAuth()
  const org = account.organization
  const verified = org?.verificationStatus === VERIFICATION.VERIFIED
  return (
    <div className="min-h-screen md:grid md:grid-cols-[17rem_1fr]">
      <aside className="border-b border-white/10 bg-ink p-4 text-white md:min-h-screen md:border-b-0">
        <Logo to="/org/dashboard" light />
        <div className="mt-5 rounded-xl bg-white/5 p-3">
          <p className="truncate text-sm font-semibold">{org?.name}</p>
          <p className="truncate text-xs text-white/60">{org?.category}</p>
          <div className="mt-2"><VerificationBadge status={org?.verificationStatus} /></div>
        </div>
        <nav aria-label="Organization" className="mt-5 flex gap-1 overflow-x-auto md:flex-col">
          {nav.map(({ to, label, icon: Icon, open }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) => `flex items-center gap-2.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm transition ${isActive ? 'bg-info text-white' : 'text-white/75 hover:bg-white/10'}`}>
              <Icon className="h-4 w-4" />{label}
              {!open && !verified && <Lock className="ml-auto h-3.5 w-3.5 text-white/40" aria-label="Requires verification" />}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div>
        <header className="flex items-center justify-between border-b border-ink/10 bg-white px-6 py-3">
          <p className="text-sm text-ink/65">Signed in as <span className="font-medium text-ink">{account.displayName}</span></p>
          <button onClick={signOut} className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-ink/70 hover:bg-ink/5"><LogOut className="h-4 w-4" />Log out</button>
        </header>
        <main className="p-6"><Outlet /></main>
      </div>
    </div>
  )
}
