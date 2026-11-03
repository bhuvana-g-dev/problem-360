import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import EventCard from '../components/feed/EventCard.jsx'

const base = { id: 'e1', orgName: 'Green Trust', title: 'Park clean-up', description: 'Bring gloves', locality: 'Anna Nagar', locationText: '', startsAt: '2030-01-01T04:00:00Z',
  capacity: 2, registrationCount: 1, spotsLeft: 1, registeredByMe: false, safetyNotes: 'Wear gloves and closed shoes.' }

test('shows safety notes and spots left, and registers', async () => {
  const onRegister = vi.fn().mockResolvedValue({ registeredByMe: true })
  render(<EventCard event={base} onRegister={onRegister} onUnregister={vi.fn()} />)
  expect(screen.getByText(/wear gloves and closed shoes/i)).toBeInTheDocument()
  expect(screen.getByText('1 of 2 spots left')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Register' }))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Cancel registration' })).toBeInTheDocument())
  expect(screen.getByText('0 of 2 spots left')).toBeInTheDocument()
  expect(onRegister).toHaveBeenCalledWith('e1')
})

test('a full event cannot be joined', () => {
  render(<EventCard event={{ ...base, spotsLeft: 0, registrationCount: 2 }} onRegister={vi.fn()} onUnregister={vi.fn()} />)
  expect(screen.getByRole('button', { name: 'Full' })).toBeDisabled()
})

test('server errors are shown, not swallowed', async () => {
  const onRegister = vi.fn().mockRejectedValue(new Error('This event is full.'))
  render(<EventCard event={base} onRegister={onRegister} onUnregister={vi.fn()} />)
  await userEvent.click(screen.getByRole('button', { name: 'Register' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('This event is full.')
})
