import { AlertCircle, CheckCircle2, Info } from 'lucide-react'

const tones = {
  error: ['border-red-200 bg-red-50 text-red-800', AlertCircle],
  success: ['border-leaf/40 bg-leaf/10 text-brand', CheckCircle2],
  info: ['border-info/25 bg-info/5 text-info', Info],
  warning: ['border-gold/50 bg-gold/10 text-ink', AlertCircle],
}

export default function Alert({ tone = 'info', title, children }) {
  const [cls, Icon] = tones[tone]
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`flex gap-3 rounded-xl border p-3.5 text-sm ${cls}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div>{title && <p className="font-semibold">{title}</p>}<div>{children}</div></div>
    </div>
  )
}
