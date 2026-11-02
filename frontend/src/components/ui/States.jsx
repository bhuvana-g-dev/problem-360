import { Loader2 } from 'lucide-react'
import Alert from './Alert.jsx'
import Button from './Button.jsx'

export function FullPageLoader({ label = 'Loading…' }) {
  return (
    <div className="grid min-h-screen place-items-center bg-surface" role="status">
      <div className="flex items-center gap-3 text-brand"><Loader2 className="h-6 w-6 animate-spin" /><span className="font-medium">{label}</span></div>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="rounded-card border border-dashed border-brand/25 bg-white/60 p-10 text-center">
      {Icon && <Icon className="mx-auto mb-3 h-9 w-9 text-brand/60" aria-hidden="true" />}
      <h2 className="text-lg text-ink">{title}</h2>
      <p className="mx-auto mt-1 max-w-md text-sm text-ink/65">{children}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function ErrorScreen({ message, onRetry }) {
  return (
    <div className="grid min-h-screen place-items-center bg-surface p-6">
      <div className="w-full max-w-md space-y-4">
        <Alert tone="error" title="We couldn’t load your account">{message}</Alert>
        {onRetry && <Button onClick={onRetry} className="w-full">Try again</Button>}
      </div>
    </div>
  )
}
