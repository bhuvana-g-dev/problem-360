import { Users, CalendarDays, Megaphone, ClipboardList } from 'lucide-react'
import { useAuth } from '../../context/AuthContext.jsx'
import Card from '../../components/ui/Card.jsx'
import Alert from '../../components/ui/Alert.jsx'
import { VERIFICATION } from '../../config/constants.js'

const unlocks = [
  [Users, 'Volunteer groups'], [CalendarDays, 'Community events'], [Megaphone, 'Organization updates'], [ClipboardList, 'Coordinated civic activity'],
]

export default function OrgDashboard() {
  const { account } = useAuth()
  const org = account.organization
  const status = org.verificationStatus
  return (
    <div className="max-w-4xl space-y-5">
      <h1 className="text-2xl">{org.name}</h1>
      {status === VERIFICATION.PENDING && <Alert tone="warning" title="Verification pending">Your organization is awaiting review. You can edit your profile now; management features unlock once you’re verified.</Alert>}
      {status === VERIFICATION.REJECTED && <Alert tone="error" title="Verification rejected">Management features are unavailable for this organization.</Alert>}
      {status === VERIFICATION.VERIFIED && <Alert tone="success" title="Verified organization">All management tools are available as they are built.</Alert>}
      <div className="grid gap-4 sm:grid-cols-2">
        {unlocks.map(([Icon, label]) => (
          <Card key={label} className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-info/10 text-info"><Icon className="h-5 w-5" /></span>
            <div><p className="font-medium">{label}</p><p className="text-xs text-ink/55">{status === VERIFICATION.VERIFIED ? 'Built in Phase 5' : 'Requires verification'}</p></div>
          </Card>
        ))}
      </div>
    </div>
  )
}
