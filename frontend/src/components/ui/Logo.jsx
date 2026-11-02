import { Link } from 'react-router-dom'
import { BRAND } from '../../config/constants.js'

export function LogoMark({ className = 'h-9 w-9' }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <circle cx="20" cy="20" r="18" fill="#0F6B4E" />
      <path d="M20 6a14 14 0 1 1-9.9 4.1" fill="none" stroke="#22C55E" strokeWidth="3.5" strokeLinecap="round" />
      <path d="M8.5 6.5l1.6 4.6 4.6-1.5" fill="none" stroke="#F59E0B" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="20" cy="20" r="4.5" fill="#fff" />
    </svg>
  )
}

export default function Logo({ to = '/', light = false, showTagline = false }) {
  return (
    <Link to={to} className="inline-flex items-center gap-2.5" aria-label={`${BRAND.name} home`}>
      <LogoMark />
      <span className="leading-tight">
        <span className={`block font-heading text-lg font-semibold ${light ? 'text-white' : 'text-brand'}`}>{BRAND.name}</span>
        {showTagline && <span className={`block text-xs ${light ? 'text-white/70' : 'text-ink/60'}`}>{BRAND.tagline}</span>}
      </span>
    </Link>
  )
}
