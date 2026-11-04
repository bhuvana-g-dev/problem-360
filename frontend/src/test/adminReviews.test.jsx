import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

vi.mock('../services/admin.js', () => ({
  reviewQueue: vi.fn(),
  reviewStats: vi.fn(),
  decideReview: vi.fn(),
  setReportStatus: vi.fn(),
}))

import * as admin from '../services/admin.js'
import AdminReviews from '../pages/admin/AdminReviews.jsx'

const urgent = {
  id: 'p1', referenceId: 'P360-1', description: 'Live wire hanging near the bus stop', category: 'Electricity', locality: 'Anna Nagar',
  locationText: '', createdAt: new Date().toISOString(), ageMinutes: 3, status: 'Submitted', action: 'FLAG_URGENT', source: 'red_flag_hook',
  summary: 'URGENT: call 112 now', urgent: true, keywordHits: ['live wire'], duplicateOf: null, failedClosed: false,
  review: { state: 'pending', byName: null, at: null, note: null, minutesToReview: null },
}

beforeEach(() => {
  vi.clearAllMocks()
  admin.reviewQueue.mockResolvedValue([urgent])
  admin.reviewStats.mockResolvedValue({ pending: 1, urgentPending: 1, medianMinutesToReview: null, medianMinutesToReviewUrgent: null })
  admin.decideReview.mockResolvedValue({ id: 'p1', status: 'Acknowledged' })
})

test('danger reports show why they are queued and can be approved', async () => {
  render(<AdminReviews />)
  expect(await screen.findByText('Possible danger')).toBeInTheDocument()
  expect(screen.getByText(/danger words found by code: live wire/i)).toBeInTheDocument()
  expect(screen.getByText('Danger reports waiting').nextSibling).toHaveTextContent('1')
  await userEvent.click(screen.getByRole('button', { name: /approve/i }))
  await waitFor(() => expect(admin.decideReview).toHaveBeenCalledWith('p1', 'approve', ''))
  expect(admin.reviewQueue).toHaveBeenCalledTimes(2)   // the queue reloads after a decision
})

test('closing a report needs a note for the citizen', async () => {
  render(<AdminReviews />)
  const close = await screen.findByRole('button', { name: /close/i })
  expect(close).toBeDisabled()
  await userEvent.type(screen.getByLabelText(/note to the citizen/i), 'Already fixed')
  expect(close).toBeEnabled()
  await userEvent.click(close)
  await waitFor(() => expect(admin.decideReview).toHaveBeenCalledWith('p1', 'reject', 'Already fixed'))
})

test('server errors are shown, not swallowed', async () => {
  admin.decideReview.mockRejectedValue(new Error('This report has already been reviewed.'))
  render(<AdminReviews />)
  await userEvent.click(await screen.findByRole('button', { name: /approve/i }))
  expect(await screen.findByText('This report has already been reviewed.')).toBeInTheDocument()
})
