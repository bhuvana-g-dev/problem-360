import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import PostCard from '../../components/feed/PostCard.jsx'
import Alert from '../../components/ui/Alert.jsx'
import Card from '../../components/ui/Card.jsx'
import { getDecisionTrace, getPost } from '../../services/posts.js'

const pretty = (o) => JSON.stringify(o, null, 1).replace(/[{}"]/g, '').replace(/,\n/g, '\n').trim()

/** Report detail: the post with its live Strands decision, plus the recorded tool runs and audit trail. */
export default function PostResult() {
  const { id } = useParams()
  const [post, setPost] = useState(null)
  const [error, setError] = useState('')
  const [trace, setTrace] = useState(null)
  const [traceError, setTraceError] = useState('')

  useEffect(() => { getPost(id).then(setPost).catch((e) => setError(e.message)) }, [id])

  // Load the trace once the review is no longer pending (poll the post until then)
  useEffect(() => {
    if (!post) return
    if (post.decisionState === 'pending') {
      const t = setTimeout(() => getPost(id).then(setPost).catch(() => {}), 3000)
      return () => clearTimeout(t)
    }
    getDecisionTrace(id).then(setTrace).catch((e) => setTraceError(e.message))
  }, [post, id])

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <Link to="/app" className="inline-flex items-center gap-1 text-sm text-brand hover:underline"><ArrowLeft className="h-4 w-4" />Back to feed</Link>
      {error && <Alert tone="error" title="Couldn’t load this report">{error}</Alert>}
      {!post && !error && <p role="status" className="text-sm text-ink/60">Loading…</p>}
      {post && <PostCard key={post.id + post.decisionState} post={post} />}
      {traceError && <Alert tone="info">{traceError}</Alert>}
      {trace && (
        <Card>
          <h2 className="text-lg">How this was decided</h2>
          <p className="mt-1 text-xs text-ink/60">
            Source: {trace.source === 'strands_agent' ? `Strands agent (${trace.model}) with the Strands Decider` : 'safety fallback (the agent did not run)'}.
            {' '}No department has been contacted{trace.incident ? `; incident ${trace.incident} was recorded for human approval` : ''}.
          </p>
          {trace.error && <p className="mt-2 rounded-lg bg-gold/15 p-2 text-xs"><b>Why it failed:</b> {trace.error}</p>}
          {trace.overrides?.length > 0 && (
            <ul className="mt-3 space-y-1 text-xs text-ink/80">
              {trace.overrides.map((o, i) => <li key={i}>Safety rule changed <b>{o.from}</b> to <b>{o.to}</b>: {o.reason}</li>)}
            </ul>
          )}
          <h3 className="mt-4 text-sm">Tool results</h3>
          {trace.toolRuns.length === 0 ? <p className="text-xs text-ink/55">No tools ran.</p> : (
            <div className="mt-1 space-y-2">
              {trace.toolRuns.map((r, i) => (
                <details key={i} className="rounded-lg border border-ink/10 p-2 text-xs">
                  <summary className="cursor-pointer font-medium">{r.tool} <span className="font-normal text-ink/50">· {r.invokedBy} · {r.ms} ms</span></summary>
                  <pre className="mt-2 whitespace-pre-wrap break-words text-ink/70">{pretty(r.output)}</pre>
                </details>
              ))}
            </div>
          )}
          <h3 className="mt-4 text-sm">Audit trail</h3>
          <ol className="mt-1 space-y-0.5 text-xs text-ink/70">{trace.audit.map((a, i) => <li key={i}>{new Date(a.at).toLocaleTimeString()} · {a.type.replaceAll('_', ' ')}</li>)}</ol>
        </Card>
      )}
    </div>
  )
}
