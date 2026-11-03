import { vi } from 'vitest'

afterEach(() => { vi.resetModules(); vi.doUnmock('../services/api.js') })

test('org and community services call the right backend endpoints', async () => {
  const apiFetch = vi.fn().mockResolvedValue({})
  vi.doMock('../services/api.js', () => ({ apiFetch }))
  const org = await import('../services/org.js')
  const community = await import('../services/community.js')
  await org.createEvent({ title: 'x' }); await org.cancelEvent('e1'); await org.setMemberRole('u1', 'admin'); await org.removeMember('u1')
  await community.registerEvent('e1'); await community.listEvents('Anna Nagar'); await community.trending('Anna Nagar')
  expect(apiFetch.mock.calls).toEqual([
    ['/api/org/events', { method: 'POST', body: { title: 'x' } }], ['/api/org/events/e1/cancel', { method: 'POST', body: undefined }],
    ['/api/org/members/u1', { method: 'PATCH', body: { role: 'admin' } }], ['/api/org/members/u1', { method: 'DELETE' }],
    ['/api/events/e1/register', { method: 'POST' }], ['/api/events?locality=Anna%20Nagar'], ['/api/trending?locality=Anna%20Nagar'],
  ])
})
