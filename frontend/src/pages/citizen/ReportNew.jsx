import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Crosshair } from 'lucide-react'
import Field from '../../components/ui/Field.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import MediaPicker from '../../components/feed/MediaPicker.jsx'
import DemoBanner from '../../components/feed/DemoBanner.jsx'
import VoiceInput from '../../components/feed/VoiceInput.jsx'
import LocationPreview from '../../components/feed/LocationPreview.jsx'
import useForm from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useT } from '../../i18n/LangContext.jsx'
import { createPost, uploadMedia } from '../../services/posts.js'
import { ISSUE_CATEGORIES, MADURAI_LOCALITIES } from '../../config/constants.js'

export default function ReportNew() {
  const { account } = useAuth()
  const { t, category } = useT()
  const nav = useNavigate()
  const [file, setFile] = useState(null)
  const [coords, setCoords] = useState(null)
  const [accuracy, setAccuracy] = useState(null)
  const [geoMsg, setGeoMsg] = useState('')
  const rules = (v) => ({
    ...(v.description.trim().length >= 15 ? {} : { description: t('err.description') }),
    ...(v.category ? {} : { category: t('err.category') }),
    ...(v.locality ? {} : { locality: t('err.locality') }),
  })
  const f = useForm({ description: '', category: '', locality: account.locality || '', locationText: '' }, rules)
  const field = (n) => ({ value: f.values[n], onChange: f.set(n), error: f.errors[n] })
  const addSpoken = (text) => text && f.set('description')({ target: { value: `${f.values.description ? f.values.description.trim() + ' ' : ''}${text}`.slice(0, 1000) } })

  const locate = () => {
    if (!navigator.geolocation) return setGeoMsg(t('geo.unavailable'))
    setGeoMsg(t('geo.finding'))
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setCoords({ lat: +p.coords.latitude.toFixed(5), lng: +p.coords.longitude.toFixed(5) })
        setAccuracy(Number.isFinite(p.coords.accuracy) ? Math.round(p.coords.accuracy) : null)
        setGeoMsg(t('geo.added'))
      },
      () => setGeoMsg(t('geo.fail')),
      { timeout: 10000 })
  }

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <h1 className="text-2xl">{t('report.title')}</h1>
      <DemoBanner />
      <form noValidate className="space-y-4 rounded-card bg-white p-5 shadow-card"
        onSubmit={f.submit(async (v) => {
          const media = file ? await uploadMedia(file) : null   // private media storage via the backend
          const post = await createPost({ description: v.description.trim(), category: v.category, locality: v.locality, locationText: v.locationText.trim(),
            coordinates: coords, mediaPath: media?.mediaPath ?? null,
            ...(media?._url ? { mediaUrl: media._url, mediaType: media.mediaType } : {}) }, account)   // _url exists only in demo mode
          nav(`/app/post/${post.id}`, { replace: true })          // result page shows the Strands decision as it arrives
        })}>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <MediaPicker onChange={setFile} />
        <Field as="textarea" rows={4} label={t('report.what')} placeholder={t('report.placeholder')} maxLength={1000} {...field('description')} />
        <VoiceInput onText={addSpoken} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field as="select" label={t('report.category')} {...field('category')}>
            <option value="">{t('report.select')}</option>{ISSUE_CATEGORIES.map((c) => <option key={c} value={c}>{category(c)}</option>)}
          </Field>
          <Field as="select" label={t('report.locality')} {...field('locality')}>
            <option value="">{t('report.select')}</option>{MADURAI_LOCALITIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </Field>
        </div>
        <Field label={t('report.landmark')} placeholder={t('report.landmarkPh')} {...field('locationText')} />
        <div>
          <Button type="button" variant="secondary" onClick={locate}><Crosshair className="h-4 w-4" aria-hidden="true" />{t('report.locate')}</Button>
          {geoMsg && <p role="status" className="mt-1.5 text-xs text-ink/60">{geoMsg}</p>}
        </div>
        {coords && (
          <div className="space-y-2 rounded-xl border border-ink/10 p-3">
            <LocationPreview coords={coords} accuracy={accuracy} map />
            <button type="button" onClick={() => { setCoords(null); setAccuracy(null); setGeoMsg('') }}
              className="text-xs font-medium text-red-600 hover:underline">{t('geo.remove')}</button>
          </div>
        )}
        <Button type="submit" loading={f.submitting} className="w-full">{t('report.post')}</Button>
      </form>
    </div>
  )
}
