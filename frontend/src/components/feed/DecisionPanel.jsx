import { Loader2, Cpu, ShieldAlert, Building2, Copy, HelpCircle, Users, UserCheck } from 'lucide-react'
import Alert from '../ui/Alert.jsx'
import { useT } from '../../i18n/LangContext.jsx'
import { ACTION_LABELS_I18N } from '../../i18n/strings.js'

export const ACTION_LABELS = ACTION_LABELS_I18N.en

const Row = ({ icon: Icon, children }) => (
  <p className="flex gap-2 text-xs"><Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" /><span>{children}</span></p>
)

/** Shows the REAL decision stored by the backend. Renders nothing when there is none (e.g. demo posts). */
export default function DecisionPanel({ state, decision, onRetry }) {
  const { t, action, lang } = useT()
  if (state === 'pending') {
    return (
      <div role="status" className="flex items-center gap-2 rounded-xl bg-info/5 p-3 text-xs text-info">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />{t('dp.reviewing')}
      </div>
    )
  }
  if (!decision) return null
  if (state === 'failed') {
    return (
      <Alert tone="warning" title={t('dp.failedTitle')}>
        <p>{decision.summary}</p>
        {onRetry && <button onClick={onRetry} className="mt-2 font-semibold underline">{t('dp.retry')}</button>}
      </Alert>
    )
  }
  const urgent = decision.urgency?.urgent
  return (
    <div className={`space-y-2 rounded-xl p-3 ${urgent ? 'bg-red-50 text-red-900' : 'bg-info/5 text-info'}`}>
      <p className="flex items-center gap-2 text-xs font-semibold">
        <Cpu className="h-4 w-4" aria-hidden="true" />Strands Decider: {action(decision.action)}
      </p>
      <p className="text-sm text-ink">{decision.summary}</p>
      <div className="space-y-1 text-ink/80">
        {urgent && <Row icon={ShieldAlert}>{t('dp.urgent')}</Row>}
        {decision.duplicate && <Row icon={Copy}>{t('dp.similar')} <b>{decision.duplicate.referenceId}</b>.</Row>}
        {decision.department && decision.action === 'ROUTE_TO_DEPARTMENT' && (
          <Row icon={Building2}>{t('dp.dept')} <b>{decision.department.name}</b>. {t('dp.deptNote')}</Row>
        )}
        {decision.communityAction?.suggestion && <Row icon={Users}>{(lang === 'ta' && decision.communityAction.suggestion_ta) || decision.communityAction.suggestion}</Row>}
        {decision.communityAction?.matches?.length > 0 && (
          <Row icon={Users}>{t('dp.events')} {decision.communityAction.matches.map((m) => `${m.title} (${m.orgName})`).join('; ')}.</Row>
        )}
        {decision.questions?.length > 0 && <Row icon={HelpCircle}>{decision.questions.join(' ')}</Row>}
        {decision.humanReviewRequired && <Row icon={UserCheck}>{t('dp.human')}</Row>}
      </div>
    </div>
  )
}
