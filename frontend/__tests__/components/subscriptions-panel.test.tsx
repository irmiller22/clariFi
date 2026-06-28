import { render, screen, waitFor } from '@testing-library/react'
import { SubscriptionsPanel } from '../../components/subscriptions-panel'
import { api } from '../../lib/api'
import type { RecurringCharge } from '../../lib/types'

// Mocked via a relative path: the `@/` alias is applied to `import` but not to
// jest.mock()'s module resolution in this next/jest setup.
jest.mock('../../lib/api', () => ({
  api: {
    getRecurring: jest.fn(),
  },
  ApiError: class ApiError extends Error {},
}))

const charges: RecurringCharge[] = [
  {
    merchant: 'Netflix',
    cadence: 'monthly',
    typicalAmount: 15.99,
    occurrences: 6,
    lastDate: '2026-05-01',
    nextExpectedDate: '2026-06-01',
  },
  {
    merchant: 'Gym',
    cadence: 'weekly',
    typicalAmount: 20,
    occurrences: 12,
    lastDate: '2026-06-01',
    nextExpectedDate: '2026-06-08',
  },
]

beforeEach(() => {
  jest.clearAllMocks()
})

describe('SubscriptionsPanel', () => {
  it('shows a loading state then renders the subscription list', async () => {
    ;(api.getRecurring as jest.Mock).mockResolvedValue(charges)

    render(<SubscriptionsPanel />)

    expect(screen.getByRole('status')).toHaveTextContent(/loading/i)

    await waitFor(() => expect(screen.getByText('Netflix')).toBeInTheDocument())
    expect(screen.getByText('Gym')).toBeInTheDocument()
    // Headline: monthly equivalent total = 15.99 + (20 * 52/12 = 86.67) = 102.66
    expect(screen.getByText(/across 2 subscriptions/i)).toBeInTheDocument()
    expect(screen.getByText(/\$102\.66\/mo/)).toBeInTheDocument()
  })

  it('sorts by monthly-equivalent cost descending', async () => {
    ;(api.getRecurring as jest.Mock).mockResolvedValue(charges)

    render(<SubscriptionsPanel />)

    await waitFor(() => expect(screen.getByText('Netflix')).toBeInTheDocument())

    const rows = screen.getAllByRole('row')
    // rows[0] is the header; the weekly Gym ($86.67/mo) outranks Netflix.
    expect(rows[1]).toHaveTextContent('Gym')
    expect(rows[2]).toHaveTextContent('Netflix')
  })

  it('shows an empty state when there are no subscriptions', async () => {
    ;(api.getRecurring as jest.Mock).mockResolvedValue([])

    render(<SubscriptionsPanel />)

    await waitFor(() =>
      expect(screen.getByText(/no recurring subscriptions detected yet/i)).toBeInTheDocument()
    )
  })

  it('shows an error state when the request fails', async () => {
    ;(api.getRecurring as jest.Mock).mockRejectedValue(new Error('network down'))

    render(<SubscriptionsPanel />)

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
