import { useState } from 'react'
import { MapPin } from 'lucide-react'
import FeedFilters from '../../components/feed/FeedFilters.jsx'
import FeedList from '../../components/feed/FeedList.jsx'
import DemoBanner from '../../components/feed/DemoBanner.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

export default function Explore() {
  const { account } = useAuth()
  const [filters, setFilters] = useState({ q: '', locality: account.locality || '', category: '' })
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div><h1 className="flex items-center gap-2 text-2xl"><MapPin className="h-6 w-6 text-brand" />Nearby issues</h1>
        <p className="text-sm text-ink/60">Starts with your locality. Trending topics will use real post activity once the API is live.</p></div>
      <DemoBanner />
      <FeedFilters value={filters} onChange={setFilters} />
      <FeedList filters={filters} emptyText="No issues reported in this locality yet." />
    </div>
  )
}
