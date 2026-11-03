import { useCallback, useEffect, useState } from 'react'

/** Loads async data with loading / error / reload. `fn` must be stable per `deps`. */
export default function useLoad(fn, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: '' })
  const [tick, setTick] = useState(0)
  useEffect(() => {
    let live = true
    setState((s) => ({ ...s, loading: true, error: '' }))
    fn().then((data) => live && setState({ loading: false, data, error: '' })).catch((e) => live && setState({ loading: false, data: null, error: e.message }))
    return () => { live = false }
  }, [...deps, tick]) // eslint-disable-line react-hooks/exhaustive-deps
  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { ...state, reload }
}
