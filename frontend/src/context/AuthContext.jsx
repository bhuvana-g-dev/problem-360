import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import {
  createUserWithEmailAndPassword, onAuthStateChanged, sendPasswordResetEmail,
  signInWithEmailAndPassword, signOut as fbSignOut,
} from 'firebase/auth'
import { auth, isFirebaseConfigured } from '../config/firebase.js'
import { apiFetch, ApiError } from '../services/api.js'
import { ACCOUNT_TYPES } from '../config/constants.js'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

const friendly = (e) => {
  const code = e?.code || ''
  if (['auth/invalid-credential', 'auth/wrong-password', 'auth/user-not-found', 'auth/invalid-email'].includes(code)) return 'Email or password is incorrect.'
  if (code === 'auth/email-already-in-use') return 'An account with this email already exists. Try logging in instead.'
  if (code === 'auth/weak-password') return 'Choose a stronger password (at least 8 characters).'
  if (code === 'auth/too-many-requests') return 'Too many attempts. Please wait a moment and try again.'
  if (code === 'auth/network-request-failed') return 'Network error. Check your connection.'
  return e?.message || 'Something went wrong.'
}

/**
 * status: loading | signedOut | ready | error | misconfigured
 * account (from backend GET /api/auth/me): { uid, email, displayName, accountType, locality, organization? }
 * The backend is the source of truth for accountType; the UI never decides it.
 */
export function AuthProvider({ children }) {
  const [state, setState] = useState({ status: isFirebaseConfigured ? 'loading' : 'misconfigured', account: null, error: null })
  const busy = useRef(false) // suppress auth-state loading while login/register flows drive it

  const loadAccount = useCallback(async () => {
    try {
      const account = await apiFetch('/api/auth/me')
      setState({ status: 'ready', account, error: null })
      return account
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) { // Firebase user exists but has no Problem 360 account
        await fbSignOut(auth)
        setState({ status: 'signedOut', account: null, error: null })
        return null
      }
      setState({ status: 'error', account: null, error: e.message })
      throw e
    }
  }, [])

  useEffect(() => {
    if (!isFirebaseConfigured) return
    return onAuthStateChanged(auth, async (user) => {
      if (busy.current) return
      if (!user) return setState({ status: 'signedOut', account: null, error: null })
      setState((s) => ({ ...s, status: 'loading' }))
      loadAccount().catch(() => {})
    })
  }, [loadAccount])

  /** Login for one account type; rejects if the account belongs to the other type. */
  const signIn = useCallback(async (expectedType, email, password) => {
    busy.current = true
    try {
      await signInWithEmailAndPassword(auth, email, password)
      const account = await loadAccount()
      if (!account) throw new Error('No Problem 360 account found for this login. Please register first.')
      if (account.accountType !== expectedType) {
        await fbSignOut(auth)
        setState({ status: 'signedOut', account: null, error: null })
        throw new Error(expectedType === ACCOUNT_TYPES.CITIZEN
          ? 'This is an organization account. Please use the Organization login.'
          : 'This is a citizen account. Please use the Citizen login.')
      }
      return account
    } catch (e) { throw new Error(friendly(e)) } finally { busy.current = false }
  }, [loadAccount])

  /** Creates the Firebase user, then asks the backend to create the typed account. Rolls back on failure. */
  const register = useCallback(async (path, email, password, body) => {
    busy.current = true
    let fbUser
    try {
      fbUser = (await createUserWithEmailAndPassword(auth, email, password)).user
      await apiFetch(path, { method: 'POST', body, token: await fbUser.getIdToken() })
      await fbUser.getIdToken(true) // pick up the new accountType claim
      return await loadAccount()
    } catch (e) {
      if (fbUser) await fbUser.delete().catch(() => {}) // don't leave a half-created login behind
      setState({ status: 'signedOut', account: null, error: null })
      throw new Error(friendly(e))
    } finally { busy.current = false }
  }, [loadAccount])

  const value = useMemo(() => ({
    ...state,
    signIn,
    registerCitizen: ({ email, password, ...rest }) => register('/api/auth/register/citizen', email, password, rest),
    registerOrganization: ({ email, password, ...rest }) => register('/api/auth/register/organization', email, password, rest),
    joinOrganization: ({ email, password, ...rest }) => register('/api/auth/register/organization-member', email, password, rest),
    resetPassword: (email) => sendPasswordResetEmail(auth, email).catch((e) => { throw new Error(friendly(e)) }),
    signOut: () => fbSignOut(auth),
    retry: () => { setState((s) => ({ ...s, status: 'loading' })); loadAccount().catch(() => {}) },
  }), [state, signIn, register, loadAccount])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
