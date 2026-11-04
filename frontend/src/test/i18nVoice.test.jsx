import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import DecisionPanel from '../components/feed/DecisionPanel.jsx'
import VoiceInput from '../components/feed/VoiceInput.jsx'
import { LangProvider, LangToggle } from '../i18n/LangContext.jsx'

const decision = { action: 'FLAG_URGENT', summary: 'அவசரம்: 112 அழையுங்கள்', urgency: { urgent: true }, humanReviewRequired: true, questions: [] }

afterEach(() => { localStorage.clear(); delete window.SpeechRecognition })

test('the toggle switches the decision panel to Tamil and remembers it', async () => {
  render(<LangProvider><LangToggle /><DecisionPanel state="completed" decision={decision} /></LangProvider>)
  expect(screen.getByText(/flagged as urgent/i)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: /switch to tamil/i }))
  expect(screen.getByText(/அவசரமாகக் குறிக்கப்பட்டது/)).toBeInTheDocument()
  expect(screen.getByText(/112 அழையுங்கள்\./)).toBeInTheDocument()
  expect(localStorage.getItem('p360.lang')).toBe('ta')
  expect(document.documentElement.lang).toBe('ta')
})

test('voice input is hidden where the browser has no speech recognition', () => {
  const { container } = render(<VoiceInput onText={vi.fn()} />)
  expect(container).toBeEmptyDOMElement()
})

test('voice input listens in Tamil when the UI is Tamil and hands the text over', async () => {
  const made = []
  window.SpeechRecognition = class {
    constructor() { made.push(this) }
    start() { this.onresult({ results: [[{ transcript: 'தெருவில் மின்கம்பி அறுந்து கிடக்கிறது' }]] }); this.onend() }
    stop() {}
    abort() {}
  }
  localStorage.setItem('p360.lang', 'ta')
  const onText = vi.fn()
  render(<LangProvider><VoiceInput onText={onText} /></LangProvider>)
  await userEvent.click(screen.getByRole('button', { name: /பேசுங்கள்/ }))
  expect(made[0].lang).toBe('ta-IN')
  expect(onText).toHaveBeenCalledWith('தெருவில் மின்கம்பி அறுந்து கிடக்கிறது')
})
