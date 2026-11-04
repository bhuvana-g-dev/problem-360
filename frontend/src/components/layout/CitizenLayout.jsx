import { NavLink, Outlet, Link } from 'react-router-dom'
import { Home, Compass, PlusCircle, Bell, User, LogOut, Users } from 'lucide-react'
import Logo from '../ui/Logo.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import { LangToggle } from '../../i18n/LangContext.jsx'

const nav = [
  { to: '/app', label: 'Home', icon: Home, end: true },
  { to: '/app/explore', label: 'Nearby', icon: Compass },
  { to: '/app/report/new', label: 'Report', icon: PlusCircle },
  { to: '/app/groups', label: 'Groups', icon: Users },
  { to: '/app/notifications', label: 'Alerts', icon: Bell },
  { to: '/app/profile', label: 'Profile', icon: User },
]

const link = ({ isActive }) =>
  `flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-brand/10 text-brand' : 'text-ink/65 hover:bg-ink/5'}`

/** Social-feed shell: top bar on desktop, bottom tab bar on mobile. */
export default function CitizenLayout() {
  const { account, signOut } = useAuth()
  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <header className="sticky top-0 z-30 border-b border-ink/10 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-2.5">
          <Logo to="/app" />
          <nav aria-label="Main" className="ml-auto hidden items-center gap-1 md:flex">
            {nav.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className={link}><Icon className="h-4 w-4" />{label}</NavLink>
            ))}
          </nav>
          <LangToggle className="ml-auto md:ml-0" />
          <button onClick={signOut} className="rounded-xl p-2 text-ink/60 hover:bg-ink/5" aria-label="Log out" title={account?.displayName}>
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6"><Outlet /></main>
      <nav aria-label="Main mobile" className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-6 border-t border-ink/10 bg-white md:hidden">
        {nav.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => `flex flex-col items-center gap-0.5 py-2 text-[11px] ${isActive ? 'text-brand' : 'text-ink/55'}`}>
            <Icon className="h-5 w-5" />{label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
