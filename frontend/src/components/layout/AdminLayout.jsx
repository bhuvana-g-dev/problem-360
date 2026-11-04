import { NavLink, Outlet } from 'react-router-dom'
import { ClipboardCheck, Building2, LogOut } from 'lucide-react'
import Logo from '../ui/Logo.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

const nav = [
  { to: '/admin/reviews', label: 'Review queue', icon: ClipboardCheck },
  { to: '/admin/organizations', label: 'Organizations', icon: Building2 },
]

/** Reviewer workspace. Every action is enforced by the backend (admin role); this is only the screen. */
export default function AdminLayout() {
  const { account, signOut } = useAuth()
  return (
    <div className="min-h-screen md:grid md:grid-cols-[15rem_1fr]">
      <aside className="border-b border-white/10 bg-ink p-4 text-white md:min-h-screen md:border-b-0">
        <Logo to="/admin/reviews" light />
        <p className="mt-4 rounded-lg bg-white/5 px-3 py-2 text-xs text-white/70">Reviewer workspace</p>
        <nav aria-label="Reviewer" className="mt-4 flex gap-1 overflow-x-auto md:flex-col">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) => `flex items-center gap-2.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm transition ${isActive ? 'bg-info text-white' : 'text-white/75 hover:bg-white/10'}`}>
              <Icon className="h-4 w-4" aria-hidden="true" />{label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div>
        <header className="flex items-center justify-between border-b border-ink/10 bg-white px-6 py-3">
          <p className="text-sm text-ink/65">Signed in as <span className="font-medium text-ink">{account.displayName}</span> (reviewer)</p>
          <button onClick={signOut} className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-ink/70 hover:bg-ink/5"><LogOut className="h-4 w-4" aria-hidden="true" />Log out</button>
        </header>
        <main className="p-6"><Outlet /></main>
      </div>
    </div>
  )
}
