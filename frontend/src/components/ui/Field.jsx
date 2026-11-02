import { useId } from 'react'

const base = 'w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-ink placeholder:text-ink/40 transition focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20'

/** Labelled form control. as: 'input' | 'select' | 'textarea'. Errors are announced to screen readers. */
export default function Field({ label, error, hint, as: Tag = 'input', children, className = '', ...rest }) {
  const id = useId()
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-ink">{label}</label>
      <Tag id={id} aria-invalid={!!error} aria-describedby={error ? `${id}-e` : hint ? `${id}-h` : undefined}
        className={`${base} ${error ? 'border-red-500' : 'border-ink/15'}`} {...rest}>
        {children}
      </Tag>
      {error ? <p id={`${id}-e`} role="alert" className="mt-1 text-xs text-red-600">{error}</p>
        : hint ? <p id={`${id}-h`} className="mt-1 text-xs text-ink/55">{hint}</p> : null}
    </div>
  )
}
