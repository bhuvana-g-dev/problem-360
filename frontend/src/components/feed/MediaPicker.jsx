import { useEffect, useRef, useState } from 'react'
import { ImagePlus, X } from 'lucide-react'

const MAX_MB = 25

/** Photo/video chooser with local preview. Calls onChange(file|null). */
export default function MediaPicker({ onChange }) {
  const [file, setFile] = useState(null)
  const [url, setUrl] = useState('')
  const [err, setErr] = useState('')
  const input = useRef()
  useEffect(() => () => url && URL.revokeObjectURL(url), [url])

  const pick = (e) => {
    const f = e.target.files[0]
    if (!f) return
    if (!/^(image|video)\//.test(f.type)) return setErr('Choose a photo or a video.')
    if (f.size > MAX_MB * 1048576) return setErr(`File is larger than ${MAX_MB} MB.`)
    setErr(''); setFile(f); setUrl(URL.createObjectURL(f)); onChange(f)
  }
  const clear = () => { setFile(null); setUrl(''); onChange(null); if (input.current) input.current.value = '' }

  return (
    <div>
      <span className="mb-1.5 block text-sm font-medium">Photo or video</span>
      {file ? (
        <div className="relative overflow-hidden rounded-xl bg-ink">
          {file.type.startsWith('video/') ? <video src={url} controls className="max-h-72 w-full" /> : <img src={url} alt="Selected upload preview" className="max-h-72 w-full object-cover" />}
          <button type="button" onClick={clear} aria-label="Remove file" className="absolute right-2 top-2 rounded-full bg-white/90 p-1.5"><X className="h-4 w-4" /></button>
        </div>
      ) : (
        <button type="button" onClick={() => input.current.click()} className="flex w-full flex-col items-center gap-1 rounded-xl border-2 border-dashed border-brand/30 bg-surface py-8 text-sm text-brand hover:bg-brand/5">
          <ImagePlus className="h-6 w-6" />Add a photo or video
        </button>
      )}
      <input ref={input} type="file" accept="image/*,video/*" onChange={pick} className="sr-only" aria-label="Choose photo or video" />
      {err && <p role="alert" className="mt-1 text-xs text-red-600">{err}</p>}
    </div>
  )
}
