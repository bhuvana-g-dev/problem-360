import { useAuth } from '../../context/AuthContext.jsx'

/** UI hint only; the backend enforces the real role matrix. */
export default function useRole() {
  const role = useAuth().account.organization?.memberRole
  return { role, canManage: role === 'owner' || role === 'admin', isOwner: role === 'owner' }
}
