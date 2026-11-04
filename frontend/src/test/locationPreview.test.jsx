import { render, screen } from '@testing-library/react'
import LocationPreview, { mapLink } from '../components/feed/LocationPreview.jsx'

const here = { lat: 9.92518, lng: 78.11987 }

test('shows the coordinates and a link that opens that exact spot', () => {
  render(<LocationPreview coords={here} />)
  expect(screen.getByText(/9\.92518, 78\.11987/)).toBeInTheDocument()
  const link = screen.getByRole('link', { name: /open on map/i })
  expect(link).toHaveAttribute('href', mapLink(here))
  expect(link.getAttribute('href')).toContain('mlat=9.92518&mlon=78.11987')
  expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  expect(screen.queryByTitle(/map showing/i)).toBeNull()   // no third-party request unless a map is asked for
})

test('the embedded map centres on the point and says where it is loaded from', () => {
  render(<LocationPreview coords={here} map />)
  const frame = screen.getByTitle(/map showing the reported location/i)
  expect(frame.getAttribute('src')).toMatch(/^https:\/\/www\.openstreetmap\.org\/export\/embed\.html\?bbox=/)
  expect(frame.getAttribute('src')).toContain('marker=9.92518%2C78.11987')
  expect(screen.getByText(/loaded from openstreetmap/i)).toBeInTheDocument()
})

test('a weak fix is called out, a good one is not, and no coordinates renders nothing', () => {
  const { rerender, container } = render(<LocationPreview coords={here} accuracy={1800} />)
  expect(screen.getByText(/accurate to about 1800 m/i)).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent(/only approximate/i)
  rerender(<LocationPreview coords={here} accuracy={15} />)
  expect(screen.queryByRole('status')).toBeNull()
  rerender(<LocationPreview coords={null} />)
  expect(container).toBeEmptyDOMElement()
})
