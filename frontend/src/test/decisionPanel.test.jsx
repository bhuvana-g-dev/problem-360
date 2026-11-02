import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import DecisionPanel from '../components/feed/DecisionPanel.jsx'

const base = { summary: 'Reviewed.', humanReviewRequired: false, urgency: { urgent: false }, department: null, duplicate: null, communityAction: null, questions: [] }

test('pending shows the agent is working', () => {
  render(<DecisionPanel state="pending" decision={null} />)
  expect(screen.getByRole('status')).toHaveTextContent('Strands Decider is reviewing')
})

test('no decision renders nothing (e.g. demo posts never show an AI decision)', () => {
  const { container } = render(<DecisionPanel state="completed" decision={null} />)
  expect(container).toBeEmptyDOMElement()
})

test('department routing says it is a recommendation and nobody was contacted', () => {
  render(<DecisionPanel state="completed" decision={{ ...base, action: 'ROUTE_TO_DEPARTMENT', department: { name: 'Roads & Engineering' } }} />)
  expect(screen.getByText('Roads & Engineering')).toBeInTheDocument()
  expect(screen.getByText(/no department has been contacted/i)).toBeInTheDocument()
})

test('urgent shows the emergency number and human review', () => {
  render(<DecisionPanel state="completed" decision={{ ...base, action: 'FLAG_URGENT', urgency: { urgent: true }, humanReviewRequired: true }} />)
  expect(screen.getByText(/call 112/i)).toBeInTheDocument()
  expect(screen.getByText(/marked for human review/i)).toBeInTheDocument()
})

test('failed review is shown honestly and offers retry', () => {
  const retry = vi.fn()
  render(<DecisionPanel state="failed" decision={{ summary: 'The automatic review could not run.', action: 'ESCALATE_FOR_HUMAN_REVIEW' }} onRetry={retry} />)
  expect(screen.getByRole('status')).toHaveTextContent('could not run')
  screen.getByText(/try the review again/i).click()
  expect(retry).toHaveBeenCalled()
})
