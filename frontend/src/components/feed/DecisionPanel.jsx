import { Loader2, Cpu, ShieldAlert, Building2, Copy, HelpCircle, Users, UserCheck } from 'lucide-react'
import Alert from '../ui/Alert.jsx'

export const ACTION_LABELS = {
  CREATE_REPORT: 'Report recorded',
  CHECK_DUPLICATE: 'Possible duplicate',
  FLAG_URGENT: 'Flagged as urgent',
  REQUEST_MORE_INFORMATION: 'More information needed',
  ROUTE_TO_DEPARTMENT: 'Department recommended',
  SUGGEST_COMMUNITY_ACTION: 'Community action suggested',
  ESCALATE_FOR_HUMAN_REVIEW: 'Sent for human review',
}

const Row = ({ icon: Icon, children }) => (
  <p className="flex gap-2 text-xs"><Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" /><span>{children}</span></p>
)

/** Shows the REAL decision stored by the backend. Renders nothing when there is none (e.g. demo posts). */
export default function DecisionPanel({ state, decision, onRetry }) {
  if (state === 'pending') {
    return (
      <div role="status" className="flex items-center gap-2 rounded-xl bg-info/5 p-3 text-xs text-info">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />Strands Decider is reviewing this report…
      </div>
    )
  }
  if (!decision) return null
  if (state === 'failed') {
    return (
      <Alert tone="warning" title="Automatic review could not run">
        <p>{decision.summary}</p>
        {onRetry && <button onClick={onRetry} className="mt-2 font-semibold underline">Try the review again</button>}
      </Alert>
    )
  }
  const urgent = decision.urgency?.urgent
  return (
    <div className={`space-y-2 rounded-xl p-3 ${urgent ? 'bg-red-50 text-red-900' : 'bg-info/5 text-info'}`}>
      <p className="flex items-center gap-2 text-xs font-semibold">
        <Cpu className="h-4 w-4" aria-hidden="true" />Strands Decider: {ACTION_LABELS[decision.action] || decision.action}
      </p>
      <p className="text-sm text-ink">{decision.summary}</p>
      <div className="space-y-1 text-ink/80">
        {urgent && <Row icon={ShieldAlert}>Treated as urgent. In an emergency call 112.</Row>}
        {decision.duplicate && <Row icon={Copy}>Similar to report <b>{decision.duplicate.referenceId}</b>.</Row>}
        {decision.department && decision.action === 'ROUTE_TO_DEPARTMENT' && (
          <Row icon={Building2}>Recommended department: <b>{decision.department.name}</b>. This is a recommendation; no department has been contacted.</Row>
        )}
        {decision.communityAction?.suggestion && <Row icon={Users}>{decision.communityAction.suggestion}</Row>}
        {decision.communityAction?.matches?.length > 0 && (
          <Row icon={Users}>Upcoming volunteer events nearby: {decision.communityAction.matches.map((m) => `${m.title} (${m.orgName})`).join('; ')}.</Row>
        )}
        {decision.questions?.length > 0 && <Row icon={HelpCircle}>{decision.questions.join(' ')}</Row>}
        {decision.humanReviewRequired && <Row icon={UserCheck}>Marked for human review.</Row>}
      </div>
    </div>
  )
}
