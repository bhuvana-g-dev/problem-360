import { Link } from 'react-router-dom'
import { Users, CalendarDays, Megaphone, ClipboardList, UserCog, HeartHandshake } from 'lucide-react'
import { useAuth } from '../../context/AuthContext.jsx'
import Card from '../../components/ui/Card.jsx'
import Alert from '../../components/ui/Alert.jsx'
import useLoad from '../../hooks/useLoad.js'
import { orgOverview } from '../../services/org.js'
import { VERIFICATION } from '../../config/constants.js'

const locked = [[Users, 'Volunteer groups'], [CalendarDays, 'Community events'], [Megaphone, 'Organization updates'], [ClipboardList, 'Coordinated civic activity']]

function Stat({ icon: Icon, label, value, to }) {
  return (
    <Card as={Link} to={to} className="flex items-center gap-3 transition hover:shadow-md">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-info/10 text-info"><Icon className="h-5 w-5" /></span>
      <div><p className="font-heading text-2xl font-semibold leading-none">{value}</p><p className="mt-1 text-xs text-ink/60">{label}</p></div>
    </Card>
  )
}

function Overview() {
  const { loading, data, error, reload } = useLoad(orgOverview)
  if (loading) return <p role="status" className="text-sm text-ink/60">Loading overview…</p>
  if (error) return <Alert tone="error">{error} <button onClick={reload} className="underline">Retry</button></Alert>
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Stat icon={HeartHandshake} label="Open civic opportunities" value={data.openOpportunities} to="/org/civic" />
      <Stat icon={Users} label={`Volunteer groups · ${data.groupMembers} members`} value={data.groups} to="/org/groups" />
      <Stat icon={CalendarDays} label={`Upcoming events · ${data.registrations} registrations`} value={data.upcomingEvents} to="/org/events" />
      <Stat icon={ClipboardList} label="Coordinated civic activities" value={data.coordinatedActivities} to="/org/civic" />
      <Stat icon={Megaphone} label="Published updates" value={data.updates} to="/org/updates" />
      <Stat icon={UserCog} label="Team members" value={data.members} to="/org/members" />
    </div>
  )
}

export default function OrgDashboard() {
  const { account } = useAuth()
  const org = account.organization
  const status = org.verificationStatus
  return (
    <div className="max-w-4xl space-y-5">
      <h1 className="text-2xl">{org.name}</h1>
      {status === VERIFICATION.PENDING && <Alert tone="warning" title="Verification pending">Your organization is awaiting review by a Problem 360 administrator. You can edit your profile now; management features unlock once you’re verified.</Alert>}
      {status === VERIFICATION.REJECTED && <Alert tone="error" title="Verification rejected">Management features are unavailable for this organization.</Alert>}
      {status === VERIFICATION.VERIFIED ? <Overview /> : (
        <div className="grid gap-4 sm:grid-cols-2">
          {locked.map(([Icon, label]) => (
            <Card key={label} className="flex items-center gap-3 opacity-70">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-info/10 text-info"><Icon className="h-5 w-5" /></span>
              <div><p className="font-medium">{label}</p><p className="text-xs text-ink/55">Requires verification</p></div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
