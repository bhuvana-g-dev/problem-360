export default function PageHeader({ title, subtitle, action }) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div><h1 className="text-2xl">{title}</h1>{subtitle && <p className="mt-0.5 text-sm text-ink/60">{subtitle}</p>}</div>
      {action}
    </div>
  )
}
