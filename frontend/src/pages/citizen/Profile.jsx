import { useState } from 'react'
import Card from '../../components/ui/Card.jsx'
import FeedList from '../../components/feed/FeedList.jsx'
import DemoBanner from '../../components/feed/DemoBanner.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import { initials } from '../../lib/format.js'

export default function Profile() {
  const { account } = useAuth()
  const [filters] = useState({ mine: true })
  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <Card className="flex items-center gap-4">
        <span className="grid h-16 w-16 place-items-center rounded-full bg-brand font-heading text-xl font-semibold text-white" aria-hidden="true">{initials(account.displayName)}</span>
        <div><h1 className="text-xl">{account.displayName}</h1><p className="text-sm text-ink/60">{account.locality} · {account.email}</p></div>
      </Card>
      <DemoBanner />
      <h2 className="text-lg">My reports</h2>
      <FeedList filters={filters} emptyText="You haven’t posted anything yet." />
    </div>
  )
}
