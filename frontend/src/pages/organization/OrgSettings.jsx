import { useAuth } from '../../context/AuthContext.jsx'
import Card from '../../components/ui/Card.jsx'
import { VerificationBadge } from '../../components/ui/Badge.jsx'

export default function OrgSettings() {
  const { account } = useAuth()
  const o = account.organization
  const rows = [['Name', o.name], ['Category', o.category], ['Locality', o.locality], ['Your role', o.memberRole], ['Contact', account.email]]
  return (
    <Card className="max-w-xl">
      <div className="mb-4 flex items-center justify-between"><h1 className="text-xl">Organization profile</h1><VerificationBadge status={o.verificationStatus} /></div>
      <dl className="divide-y divide-ink/10 text-sm">
        {rows.map(([k, v]) => <div key={k} className="flex justify-between py-2.5"><dt className="text-ink/60">{k}</dt><dd className="font-medium">{v}</dd></div>)}
      </dl>
      <p className="mt-4 text-xs text-ink/55">Editing the profile and uploading a logo arrive in Phase 5 (logo needs Firebase Storage).</p>
    </Card>
  )
}
