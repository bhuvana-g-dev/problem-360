import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, MessageCircle, Share2, MapPin, Hash, Navigation } from 'lucide-react'
import DecisionPanel from './DecisionPanel.jsx'
import { mapLink } from './LocationPreview.jsx'
import { useT } from '../../i18n/LangContext.jsx'
import { StatusBadge } from '../ui/Badge.jsx'
import { timeAgo, initials } from '../../lib/format.js'
import { addComment, getPost, listComments, retryDecision, toggleLike } from '../../services/posts.js'
import { useAuth } from '../../context/AuthContext.jsx'

export default function PostCard({ post }) {
  const { account } = useAuth()
  const { t } = useT()
  const [p, setP] = useState(post)
  const [open, setOpen] = useState(false)
  const [comments, setComments] = useState(null)
  const [text, setText] = useState('')
  const [note, setNote] = useState('')

  // While the Strands agent is working, poll the backend (every 3 s, up to about 2 minutes)
  useEffect(() => {
    if (p.decisionState !== 'pending') return
    let tries = 0
    const t = setInterval(async () => {
      tries += 1
      try { const fresh = await getPost(p.id); if (fresh.decisionState !== 'pending') setP((x) => ({ ...x, decisionState: fresh.decisionState, decision: fresh.decision })) } catch { /* keep trying */ }
      if (tries >= 40) clearInterval(t)
    }, 3000)
    return () => clearInterval(t)
  }, [p.id, p.decisionState])
  const retry = async () => { try { await retryDecision(p.id); setP((x) => ({ ...x, decisionState: 'pending', decision: null })) } catch (e) { setNote(e.message) } }

  const like = async () => {
    const prev = p
    setP({ ...p, likedByMe: !p.likedByMe, likeCount: p.likeCount + (p.likedByMe ? -1 : 1) }) // optimistic
    try { const r = await toggleLike(p.id); setP((x) => ({ ...x, ...r })) } catch { setP(prev); setNote('Couldn’t update like.') }
  }
  const toggleComments = async () => {
    setOpen((o) => !o)
    if (comments === null) try { setComments(await listComments(p.id)) } catch { setComments([]); setNote('Couldn’t load comments.') }
  }
  const send = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    try { const c = await addComment(p.id, text.trim(), account); setComments((l) => [...(l || []), c]); setP((x) => ({ ...x, commentCount: x.commentCount + 1 })); setText('') }
    catch (err) { setNote(err.message) }
  }
  const share = async () => {
    const url = `${location.origin}/app/post/${p.id}`
    try {
      if (navigator.share) await navigator.share({ title: 'Problem 360', text: p.description, url })
      else { await navigator.clipboard.writeText(url); setNote('Link copied.') }
    } catch { /* user cancelled */ }
  }

  return (
    <article className="overflow-hidden rounded-card bg-white shadow-card">
      <header className="flex items-center gap-3 p-4">
        <span className="grid h-10 w-10 place-items-center rounded-full bg-brand text-sm font-semibold text-white" aria-hidden="true">{initials(p.author.name)}</span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{p.author.name}</p>
          <p className="truncate text-xs text-ink/55">{p.author.locality} · {timeAgo(p.createdAt)}</p>
        </div>
        <StatusBadge status={p.status} />
      </header>

      {p.mediaUrl && (p.mediaType === 'video'
        ? <video src={p.mediaUrl} controls className="max-h-[28rem] w-full bg-ink object-cover" />
        : <img src={p.mediaUrl} alt={`Photo for: ${p.description.slice(0, 60)}`} className="max-h-[28rem] w-full object-cover" loading="lazy" />)}

      <div className="space-y-2.5 p-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full bg-gold/20 px-2.5 py-1 font-semibold">{p.category}</span>
          <span className="flex items-center gap-1 text-ink/60"><MapPin className="h-3.5 w-3.5" />{[p.locationText, p.locality].filter(Boolean).join(', ')}</span>
          {p.referenceId && <span className="flex items-center gap-1 text-ink/60"><Hash className="h-3.5 w-3.5" />{p.referenceId}</span>}
          {p.coordinates && (
            <a href={mapLink(p.coordinates)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 font-medium text-brand hover:underline">
              <Navigation className="h-3.5 w-3.5" aria-hidden="true" />{t('geo.openMap')}</a>
          )}
        </div>
        <p className="text-sm leading-relaxed">{p.description}</p>
        <DecisionPanel state={p.decisionState} decision={p.decision} onRetry={p.author.uid === account.uid ? retry : undefined} />
        <Link to={`/app/post/${p.id}`} className="text-xs font-medium text-brand hover:underline">Open report details</Link>
      </div>

      <footer className="border-t border-ink/10 px-2 py-1.5">
        <div className="flex">
          <button onClick={like} aria-pressed={p.likedByMe} className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg py-2 text-sm hover:bg-ink/5 ${p.likedByMe ? 'font-semibold text-red-600' : 'text-ink/65'}`}>
            <Heart className={`h-4 w-4 ${p.likedByMe ? 'fill-current' : ''}`} />{p.likeCount}<span className="sr-only"> likes</span>
          </button>
          <button onClick={toggleComments} aria-expanded={open} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg py-2 text-sm text-ink/65 hover:bg-ink/5">
            <MessageCircle className="h-4 w-4" />{p.commentCount}<span className="sr-only"> comments</span>
          </button>
          <button onClick={share} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg py-2 text-sm text-ink/65 hover:bg-ink/5"><Share2 className="h-4 w-4" />Share</button>
        </div>
        {note && <p role="status" className="px-3 pb-1 text-xs text-ink/60">{note}</p>}
        {open && (
          <div className="space-y-3 border-t border-ink/10 p-3">
            {comments === null ? <p className="text-xs text-ink/55">Loading comments…</p>
              : comments.length === 0 ? <p className="text-xs text-ink/55">No comments yet.</p>
              : comments.map((c) => <p key={c.id} className="text-sm"><b>{c.author.name}</b> <span className="text-ink/80">{c.text}</span> <span className="text-xs text-ink/45">{timeAgo(c.createdAt)}</span></p>)}
            <form onSubmit={send} className="flex gap-2">
              <input value={text} onChange={(e) => setText(e.target.value)} maxLength={500} aria-label="Add a comment" placeholder="Add a comment…" className="flex-1 rounded-full border border-ink/15 px-3.5 py-2 text-sm focus:border-brand focus:outline-none" />
              <button className="rounded-full bg-brand px-4 text-sm font-semibold text-white">Post</button>
            </form>
          </div>
        )}
      </footer>
    </article>
  )
}
