import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

// Public web config only. No secrets live in the frontend; the backend uses the Admin SDK.
const cfg = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

export const isFirebaseConfigured = Object.values(cfg).every(Boolean)
export const auth = isFirebaseConfigured ? getAuth(initializeApp(cfg)) : null
