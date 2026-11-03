import { useState } from 'react'
import { MapPin } from 'lucide-react'
import { TrendingUp } from 'lucide-react'
import useLoad from '../../hooks/useLoad.js'
import { trending } from '../../services/community.js'
import { DEMO } from '../../services/posts.js'
import FeedFilters from '../../components/feed/FeedFilters.jsx'
import FeedList from '../../components/feed/FeedList.jsx'
import DemoBanner from '../../components/feed/DemoBanner.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

export default function Explore() {
  const { account } = useAuth()
  const [filters, setFilters] = useState({ q: '', locality: account.locality || '', category: '' })
  const hot = useLoad(() => (DEMO ? Promise.resolve([]) : trending(filters.locality)), [filters.locality])
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div><h1 className="flex items-center gap-2 text-2xl"><MapPin className="h-6 w-6 text-brand" />Nearby issues</h1>
        <p className="text-sm text-ink/60">Starts with your locality. Trending is computed from real reports and likes in the last 7 days.</p></div>
      {hot.data?.length > 0 && (
        <div className="rounded-card bg-white p-4 shadow-card"><p className="mb-2 flex items-center gap-1.5 text-sm font-semibold"><TrendingUp className="h-4 w-4 text-brand" />Trending in {filters.locality || 'Madurai'}</p>
          <div className="flex flex-wrap gap-2">{hot.data.map((t) => (
            <button key={t.category} onClick={() => setFilters({ ...filters, category: t.category })} className="rounded-full bg-gold/20 px-3 py-1 text-xs font-semibold hover:bg-gold/30">{t.category} · {t.reports} reports</button>))}</div></div>
      )}
      <DemoBanner />
      <FeedFilters value={filters} onChange={setFilters} />
      <FeedList filters={filters} emptyText="No issues reported in this locality yet." />
    </div>
  )
}
