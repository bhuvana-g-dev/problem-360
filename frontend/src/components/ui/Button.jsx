import { Loader2 } from 'lucide-react'

const variants = {
  primary: 'bg-brand text-white hover:bg-brand/90',
  secondary: 'border border-brand/30 bg-white text-brand hover:bg-brand/5',
  accent: 'bg-gold text-ink hover:bg-gold/90',
  info: 'bg-info text-white hover:bg-info/90',
  ghost: 'text-ink/70 hover:bg-ink/5',
}

export default function Button({ variant = 'primary', loading = false, className = '', children, disabled, as: Tag = 'button', ...rest }) {
  return (
    <Tag
      disabled={Tag === 'button' ? disabled || loading : undefined}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...rest}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {children}
    </Tag>
  )
}
