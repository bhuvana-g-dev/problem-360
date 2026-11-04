import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { ACTION_LABELS_I18N, CATEGORY_TA, STRINGS } from './strings.js'

const KEY = 'p360.lang'
const make = (lang, setLang = () => {}) => ({
  lang, setLang,
  t: (k) => STRINGS[lang]?.[k] ?? STRINGS.en[k] ?? k,
  action: (a) => ACTION_LABELS_I18N[lang]?.[a] ?? ACTION_LABELS_I18N.en[a] ?? a,
  category: (c) => (lang === 'ta' ? CATEGORY_TA[c] || c : c),
})

// Without a provider (e.g. in a component test) everything is English.
const LangContext = createContext(make('en'))
export const useT = () => useContext(LangContext)

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => {
    try { return localStorage.getItem(KEY) === 'ta' ? 'ta' : 'en' } catch { return 'en' }
  })
  useEffect(() => {
    document.documentElement.lang = lang
    try { localStorage.setItem(KEY, lang) } catch { /* private mode: language just won't persist */ }
  }, [lang])
  const value = useMemo(() => make(lang, setLang), [lang])
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}

/** English / தமிழ் toggle. */
export function LangToggle({ className = '' }) {
  const { lang, setLang, t } = useT()
  return (
    <button type="button" onClick={() => setLang(lang === 'ta' ? 'en' : 'ta')} aria-label={t('lang.switchLabel')}
      className={`rounded-xl border border-ink/15 px-3 py-1.5 text-sm font-medium text-ink/75 hover:bg-ink/5 ${className}`}>
      {t('lang.switch')}
    </button>
  )
}
