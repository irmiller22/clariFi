import { render, screen, waitFor } from '@testing-library/react'
import { CashflowPanel } from '../../components/cashflow-panel'
import { api } from '../../lib/api'
import type { Cashflow } from '../../lib/types'

// Mocked via a relative path: the `@/` alias is applied to `import` but not to
// jest.mock()'s module resolution in this next/jest setup.
jest.mock('../../lib/api', () => ({
  api: {
    getCashflow: jest.fn(),
  },
  ApiError: class ApiError extends Error {},
}))

const cashflow: Cashflow[] = [
  { month: '2026-04', income: 5000, spend: 3200, net: 1800 },
  { month: '2026-05', income: 5000, spend: 4100, net: 900 },
]

beforeEach(() => {
  jest.clearAllMocks()
})

describe('CashflowPanel', () => {
  it('shows a loading state then renders the cashflow chart', async () => {
    ;(api.getCashflow as jest.Mock).mockResolvedValue(cashflow)

    render(<CashflowPanel />)

    expect(screen.getByRole('status')).toHaveTextContent(/loading/i)

    // recharts doesn't paint its chart/legend at 0 width in jsdom, so assert the
    // panel rendered (heading present) rather than chart-internal labels.
    await waitFor(() => expect(screen.getByText('Cashflow')).toBeInTheDocument())
  })

  it('shows an empty state when there is no cashflow', async () => {
    ;(api.getCashflow as jest.Mock).mockResolvedValue([])

    render(<CashflowPanel />)

    await waitFor(() =>
      expect(screen.getByText(/no cashflow to analyze yet/i)).toBeInTheDocument()
    )
  })

  it('shows an error state when the request fails', async () => {
    ;(api.getCashflow as jest.Mock).mockRejectedValue(new Error('network down'))

    render(<CashflowPanel />)

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
