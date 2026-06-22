import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home page', () => {
  it('renders the upload view by default', () => {
    render(<Home />)
    expect(
      screen.getByRole('heading', { name: /analyze your spending/i })
    ).toBeInTheDocument()
    expect(screen.getByText('clariFi')).toBeInTheDocument()
  })

  it('disables the transactions and analytics tabs until data is loaded', () => {
    render(<Home />)
    expect(screen.getByRole('button', { name: 'Transactions' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Analytics' })).toBeDisabled()
  })
})
