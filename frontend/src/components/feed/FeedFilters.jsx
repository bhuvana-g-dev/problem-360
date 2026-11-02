import { Search } from 'lucide-react'
import { ISSUE_CATEGORIES, MADURAI_LOCALITIES } from '../../config/constants.js'

const sel = 'rounded-xl border border-ink/15 bg-white px-3 py-2 text-sm focus:border-brand focus:outline-none'

export default function FeedFilters({ value, onChange }) {
  const set = (k) => (e) => onChange({ ...value, [k]: e.target.value })
  return (
    <div className="flex flex-wrap gap-2" role="search">
      <div className="relative min-w-[10rem] flex-1">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-ink/40" aria-hidden="true" />
        <input aria-label="Search posts" value={value.q} onChange={set('q')} placeholder="Search issues" className={`${sel} w-full pl-9`} />
      </div>
      <select aria-label="Filter by locality" value={value.locality} onChange={set('locality')} className={sel}>
        <option value="">All localities</option>{MADURAI_LOCALITIES.map((l) => <option key={l}>{l}</option>)}
      </select>
      <select aria-label="Filter by category" value={value.category} onChange={set('category')} className={sel}>
        <option value="">All categories</option>{ISSUE_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
      </select>
    </div>
  )
}
