import { useEffect, useRef, useState } from 'react'
import { Mic, MicOff } from 'lucide-react'
import { useT } from '../../i18n/LangContext.jsx'

const Recognition = () => (typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)) || null

/** Speak a report instead of typing (low-literacy users). Uses the browser's Web Speech API (Chrome / Edge;
 *  ta-IN and en-IN). Hidden where unsupported. The text lands in the textarea, so the person can check and fix it. */
export default function VoiceInput({ onText }) {
  const { lang, t } = useT()
  const [on, setOn] = useState(false)
  const [msg, setMsg] = useState('')
  const rec = useRef(null)
  useEffect(() => () => rec.current?.abort(), [])
  const SR = Recognition()
  if (!SR) return null

  const start = () => {
    const r = new SR()
    r.lang = lang === 'ta' ? 'ta-IN' : 'en-IN'
    r.interimResults = false
    r.continuous = false
    r.onresult = (e) => onText(Array.from(e.results).map((x) => x[0].transcript).join(' ').trim())
    r.onerror = () => setMsg(t('voice.error'))
    r.onend = () => setOn(false)
    rec.current = r
    setMsg(t('voice.listening')); setOn(true)
    r.start()
  }
  const stop = () => { rec.current?.stop(); setOn(false); setMsg('') }

  return (
    <div>
      <button type="button" onClick={on ? stop : start} aria-pressed={on}
        className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium ${on ? 'border-red-300 bg-red-50 text-red-700' : 'border-brand/30 text-brand hover:bg-brand/5'}`}>
        {on ? <MicOff className="h-4 w-4" aria-hidden="true" /> : <Mic className="h-4 w-4" aria-hidden="true" />}
        {on ? t('voice.stop') : t('voice.start')}
      </button>
      <p role="status" className="mt-1 text-xs text-ink/55">{msg || t('voice.privacy')}</p>
    </div>
  )
}
