import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Crosshair } from 'lucide-react'
import Field from '../../components/ui/Field.jsx'
import Button from '../../components/ui/Button.jsx'
import Alert from '../../components/ui/Alert.jsx'
import MediaPicker from '../../components/feed/MediaPicker.jsx'
import DemoBanner from '../../components/feed/DemoBanner.jsx'
import useForm from '../../components/auth/useForm.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { createPost, uploadMedia } from '../../services/posts.js'
import { ISSUE_CATEGORIES, MADURAI_LOCALITIES } from '../../config/constants.js'

const rules = (v) => ({
  ...(v.description.trim().length >= 15 ? {} : { description: 'Describe the problem in at least 15 characters.' }),
  ...(v.category ? {} : { category: 'Choose a category.' }),
  ...(v.locality ? {} : { locality: 'Choose a locality.' }),
})

export default function ReportNew() {
  const { account } = useAuth()
  const nav = useNavigate()
  const [file, setFile] = useState(null)
  const [coords, setCoords] = useState(null)
  const [geoMsg, setGeoMsg] = useState('')
  const f = useForm({ description: '', category: '', locality: account.locality || '', locationText: '' }, rules)
  const t = (n) => ({ value: f.values[n], onChange: f.set(n), error: f.errors[n] })

  const locate = () => {
    if (!navigator.geolocation) return setGeoMsg('Location isn’t available on this device.')
    setGeoMsg('Finding your location…')
    navigator.geolocation.getCurrentPosition(
      (p) => { setCoords({ lat: +p.coords.latitude.toFixed(5), lng: +p.coords.longitude.toFixed(5) }); setGeoMsg('Location added.') },
      () => setGeoMsg('Couldn’t get your location. You can still describe it in words.'),
      { timeout: 10000 })
  }

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <h1 className="text-2xl">Report a problem</h1>
      <DemoBanner />
      <form noValidate className="space-y-4 rounded-card bg-white p-5 shadow-card"
        onSubmit={f.submit(async (v) => {
          const media = file ? await uploadMedia(file) : null   // private Firebase Storage via the backend
          const post = await createPost({ description: v.description.trim(), category: v.category, locality: v.locality, locationText: v.locationText.trim(),
            coordinates: coords, mediaPath: media?.mediaPath ?? null,
            ...(media?._url ? { mediaUrl: media._url, mediaType: media.mediaType } : {}) }, account)   // _url exists only in demo mode
          nav(`/app/post/${post.id}`, { replace: true })          // result page shows the Strands decision as it arrives
        })}>
        {f.formError && <Alert tone="error">{f.formError}</Alert>}
        <MediaPicker onChange={setFile} />
        <Field as="textarea" rows={4} label="What’s the problem?" placeholder="What is wrong, and how long has it been like this?" maxLength={1000} {...t('description')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field as="select" label="Category" {...t('category')}><option value="">Select</option>{ISSUE_CATEGORIES.map((c) => <option key={c}>{c}</option>)}</Field>
          <Field as="select" label="Locality" {...t('locality')}><option value="">Select</option>{MADURAI_LOCALITIES.map((c) => <option key={c}>{c}</option>)}</Field>
        </div>
        <Field label="Landmark / street (optional)" placeholder="e.g. opposite the bus stop" {...t('locationText')} />
        <div>
          <Button type="button" variant="secondary" onClick={locate}><Crosshair className="h-4 w-4" />Use my current location</Button>
          {geoMsg && <p role="status" className="mt-1.5 text-xs text-ink/60">{geoMsg}</p>}
        </div>
        <Button type="submit" loading={f.submitting} className="w-full">Post</Button>
      </form>
    </div>
  )
}
