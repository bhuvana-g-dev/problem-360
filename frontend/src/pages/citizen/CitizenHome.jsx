import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PlusCircle } from 'lucide-react'
import FeedFilters from '../../components/feed/FeedFilters.jsx'
import FeedList from '../../components/feed/FeedList.jsx'
import DemoBanner from '../../components/feed/DemoBanner.jsx'
import Button from '../../components/ui/Button.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

export default function CitizenHome() {
  const { account } = useAuth()
  const [filters, setFilters] = useState({ q: '', locality: '', category: '' })
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl">Hello, {account.displayName.split(' ')[0]}</h1>
        <Button as={Link} to="/app/report/new" variant="accent"><PlusCircle className="h-4 w-4" />Create post</Button>
      </div>
      <DemoBanner />
      <FeedFilters value={filters} onChange={setFilters} />
      <FeedList filters={filters} emptyText="No civic posts yet. Be the first to report a problem in your area." />
    </div>
  )
}
