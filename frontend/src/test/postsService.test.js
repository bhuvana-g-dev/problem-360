import { vi } from 'vitest'

afterEach(() => { vi.resetModules(); vi.unstubAllEnvs(); vi.doUnmock('../demo/postsDemo.js'); vi.doUnmock('../services/api.js') })

test('by default posts come from the backend API, never from demo data', async () => {
  vi.stubEnv('VITE_DEMO_DATA', 'false')
  const apiFetch = vi.fn().mockResolvedValue([{ id: 'real-1' }])
  vi.doMock('../services/api.js', () => ({ apiFetch }))
  const demoSpy = vi.fn()
  vi.doMock('../demo/postsDemo.js', () => { demoSpy(); return {} })
  const posts = await import('../services/posts.js')
  expect(await posts.listPosts({ locality: 'Anna Nagar', q: 'pothole' })).toEqual([{ id: 'real-1' }])
  expect(apiFetch).toHaveBeenCalledWith('/api/posts?locality=Anna+Nagar&q=pothole')
  expect(demoSpy).not.toHaveBeenCalled()
})

test('demo mode never calls the backend', async () => {
  vi.stubEnv('VITE_DEMO_DATA', 'true')
  const apiFetch = vi.fn()
  vi.doMock('../services/api.js', () => ({ apiFetch }))
  const posts = await import('../services/posts.js')
  const list = await posts.listPosts({})
  expect(list.length).toBeGreaterThan(0)
  expect(list.every((p) => p.decision === null)).toBe(true)
  expect(apiFetch).not.toHaveBeenCalled()
})

test('real report creation posts to the API', async () => {
  vi.stubEnv('VITE_DEMO_DATA', 'false')
  const apiFetch = vi.fn().mockResolvedValue({ id: 'p1' })
  vi.doMock('../services/api.js', () => ({ apiFetch }))
  const posts = await import('../services/posts.js')
  await posts.createPost({ description: 'x' }, {})
  expect(apiFetch).toHaveBeenCalledWith('/api/posts', { method: 'POST', body: { description: 'x' } })
})
