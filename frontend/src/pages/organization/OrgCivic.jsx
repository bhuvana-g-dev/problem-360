import { Link } from 'react-router-dom'
import { HeartHandshake } from 'lucide-react'
import PageHeader from '../../components/org/PageHeader.jsx'
import Async from '../../components/org/Async.jsx'
import useRole from '../../components/org/useRole.js'
import Button from '../../components/ui/Button.jsx'
import Card from '../../components/ui/Card.jsx'
import useLoad from '../../hooks/useLoad.js'
import { orgOpportunities } from '../../services/org.js'
import { timeAgo } from '../../lib/format.js'

/** Reports the Strands Decider judged safe for community action: the bridge from a citizen report to a volunteer drive. */
export default function OrgCivic() {
  const { canManage } = useRole()
  const load = useLoad(orgOpportunities)
  return (
    <div className="max-w-3xl">
      <PageHeader title="Civic activity" subtitle="Citizen reports where the Strands Decider found neighbours can safely help. Urgent or hazardous reports never appear here." />
      <Async load={load} icon={HeartHandshake} emptyTitle="No community-action reports yet" empty="They appear here when a report is judged safe for volunteers.">
        {(items) => <div className="space-y-3">{items.map((o) => (
          <Card key={o.postId}>
            <p className="text-xs text-ink/55">{o.referenceId} · {o.category} · {o.locality}{o.locationText ? `, ${o.locationText}` : ''} · {timeAgo(o.createdAt)}</p>
            <p className="mt-1 text-sm">{o.description}</p>
            {o.suggestion && <p className="mt-2 rounded-lg bg-leaf/10 p-2 text-xs text-brand">{o.suggestion}</p>}
            {canManage && <div className="mt-3"><Button as={Link} to={`/org/events?post=${o.postId}`} variant="info">Organise an event for this</Button></div>}
          </Card>))}</div>}
      </Async>
    </div>
  )
}
