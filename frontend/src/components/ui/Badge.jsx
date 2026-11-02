import { BadgeCheck, Clock, XCircle } from 'lucide-react'
import { VERIFICATION } from '../../config/constants.js'

const statusStyles = {
  Submitted: 'bg-ink/10 text-ink',
  'Under Review': 'bg-info/10 text-info',
  Assigned: 'bg-info/10 text-info',
  'In Progress': 'bg-gold/20 text-ink',
  Resolved: 'bg-leaf/20 text-brand',
  Verified: 'bg-brand text-white',
  Reopened: 'bg-red-100 text-red-700',
}

/** Issue lifecycle badge (Submitted → Under Review → Assigned → In Progress → Resolved → Verified, or Reopened). */
export function StatusBadge({ status }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyles[status] || statusStyles.Submitted}`}>{status}</span>
}

const verification = {
  [VERIFICATION.PENDING]: ['Pending verification', 'bg-gold/20 text-ink', Clock],
  [VERIFICATION.VERIFIED]: ['Verified', 'bg-leaf/20 text-brand', BadgeCheck],
  [VERIFICATION.REJECTED]: ['Rejected', 'bg-red-100 text-red-700', XCircle],
}

export function VerificationBadge({ status }) {
  const [label, cls, Icon] = verification[status] || verification[VERIFICATION.PENDING]
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />{label}
    </span>
  )
}
