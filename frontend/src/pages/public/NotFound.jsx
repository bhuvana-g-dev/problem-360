import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/ui/States.jsx'
import Button from '../../components/ui/Button.jsx'

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="w-full max-w-lg">
        <EmptyState title="Page not found" action={<Button as={Link} to="/">Go to home</Button>}>That page doesn’t exist.</EmptyState>
      </div>
    </div>
  )
}
