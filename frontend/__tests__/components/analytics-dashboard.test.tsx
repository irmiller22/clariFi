import { render, screen, waitFor } from '@testing-library/react'
import { AnalyticsDashboard } from '../../components/analytics-dashboard'
import { api } from '../../lib/api'
import type { AnalyticsSummary } from '../../lib/types'

// Mocked via a relative path: the `@/` alias is applied to `import` but not to
// jest.mock()'s module resolution in this next/jest setup.
jest.mock('../../lib/api', () => ({
  api: {
    getCategoryAnalytics: jest.fn(),
    getTimelineAnalytics: jest.fn(),
    getTrends: jest.fn(),
  },
  ApiError: class ApiError extends Error {},
}))

const summary: AnalyticsSummary = {
  totalSpent: 50,
  totalIncome: 0,
  netAmount: -50,
  transactionCount: 1,
  avgTransactionAmount: 50,
}

function mockAnalytics(options: {
  categories?: unknown[]
  timeline?: unknown[]
  trends?: unknown
} = {}) {
  ;(api.getCategoryAnalytics as jest.Mock).mockResolvedValue(options.categories ?? [])
  ;(api.getTimelineAnalytics as jest.Mock).mockResolvedValue(options.timeline ?? [])
  ;(api.getTrends as jest.Mock).mockResolvedValue(options.trends ?? { overall: [], byCategory: [] })
}

beforeEach(() => {
  jest.clearAllMocks()
})

describe('AnalyticsDashboard', () => {
  it('shows a loading state then renders the category breakdown', async () => {
    mockAnalytics({
      categories: [{ category: 'Food', amount: 50, count: 1, percentage: 100 }],
    })

    render(<AnalyticsDashboard summary={summary} />)

    expect(screen.getByRole('status')).toHaveTextContent(/loading/i)

    await waitFor(() => expect(screen.getByText('Food')).toBeInTheDocument())
    expect(screen.getByText('Total Spent')).toBeInTheDocument()
    expect(screen.getByText('Spending by Category')).toBeInTheDocument()
  })

  it('shows an empty state when there is no spend', async () => {
    mockAnalytics()

    render(<AnalyticsDashboard summary={summary} />)

    await waitFor(() =>
      expect(screen.getByText(/no spending to analyze yet/i)).toBeInTheDocument()
    )
    // Summary cards still render even with no spend breakdown.
    expect(screen.getByText('Total Spent')).toBeInTheDocument()
  })

  it('shows an error state when a request fails', async () => {
    ;(api.getCategoryAnalytics as jest.Mock).mockRejectedValue(new Error('network down'))
    ;(api.getTimelineAnalytics as jest.Mock).mockResolvedValue([])
    ;(api.getTrends as jest.Mock).mockResolvedValue({ overall: [], byCategory: [] })

    render(<AnalyticsDashboard summary={summary} />)

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
