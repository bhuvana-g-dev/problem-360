import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { FullPageLoader, ErrorScreen, EmptyState } from '../components/ui/States.jsx'
import { homeFor, loginFor, ACCOUNT_TYPES, VERIFICATION } from '../config/constants.js'
import Alert from '../components/ui/Alert.jsx'

/** Route guard: signed in AND the right account type. UI convenience only — the backend enforces the real permission. */
export function RequireAccount({ type }) {
  const { status, account, error, retry } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <FullPageLoader />
  if (status === 'error') return <ErrorScreen message={error} onRetry={retry} />
  if (status !== 'ready') return <Navigate to={loginFor(type)} state={{ from: location }} replace />
  if (account.accountType !== type) return <Navigate to={homeFor(account.accountType)} replace />
  return <Outlet />
}

/** Wraps org management routes: renders a locked state until the organization is Verified. */
export function RequireVerifiedOrg() {
  const { account } = useAuth()
  const status = account.organization?.verificationStatus
  if (status === VERIFICATION.VERIFIED) return <Outlet />
  return (
    <EmptyState icon={ShieldAlert} title="Verification required">
      {status === VERIFICATION.REJECTED
        ? 'Your organization’s verification was rejected, so management features are unavailable.'
        : 'This area unlocks once Problem 360 verifies your organization. You’ll see the status on your overview.'}
    </EmptyState>
  )
}

/** Redirect already-signed-in visitors away from login/register pages. */
export function PublicOnly() {
  const { status, account } = useAuth()
  if (status === 'loading') return <FullPageLoader />
  if (status === 'ready' && account.accountType !== ACCOUNT_TYPES.ADMIN) return <Navigate to={homeFor(account.accountType)} replace />
  return <Outlet />
}

export function ConfigGate({ children }) {
  const { status } = useAuth()
  if (status !== 'misconfigured') return children
  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="max-w-lg"><Alert tone="warning" title="Firebase isn’t configured">
        Copy <code>frontend/.env.example</code> to <code>frontend/.env</code> and fill in your Firebase web app values, then restart <code>npm run dev</code>.
      </Alert></div>
    </div>
  )
}
