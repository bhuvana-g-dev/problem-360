import { Hammer } from 'lucide-react'
import { EmptyState } from '../../components/ui/States.jsx'

/** Route placeholder for a later build phase. Shows no fake data. */
export default function ComingSoon({ title, phase }) {
  return (
    <EmptyState icon={Hammer} title={title}>This screen is planned for Phase {phase} of the build. Nothing is mocked here.</EmptyState>
  )
}
