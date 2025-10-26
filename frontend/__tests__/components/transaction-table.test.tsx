import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TransactionTable } from '@/components/transaction-table'
import type { Transaction } from '@/lib/types'

const mockTransactions: Transaction[] = [
  {
    id: '1',
    date: '2024-01-15',
    description: 'Grocery Store',
    amount: -85.50,
    category: 'Food',
    type: 'debit'
  },
  {
    id: '2',
    date: '2024-01-14',
    description: 'Salary Deposit',
    amount: 2500.00,
    category: 'Income',
    type: 'credit'
  },
  {
    id: '3',
    date: '2024-01-13',
    description: 'Gas Station',
    amount: -45.25,
    category: 'Transportation',
    type: 'debit'
  },
  {
    id: '4',
    date: '2024-01-12',
    description: 'Coffee Shop',
    amount: -5.75,
    category: 'Food',
    type: 'debit'
  }
]

describe('TransactionTable', () => {
  it('renders transaction table with data', () => {
    render(<TransactionTable transactions={mockTransactions} />)
    
    // Check headers
    expect(screen.getByText('Date')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByText('Category')).toBeInTheDocument()
    expect(screen.getByText('Amount')).toBeInTheDocument()
    
    // Check transaction data
    expect(screen.getByText('Grocery Store')).toBeInTheDocument()
    expect(screen.getByText('Salary Deposit')).toBeInTheDocument()
    expect(screen.getByText('Gas Station')).toBeInTheDocument()
    expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
  })

  it('displays correct number of transactions', () => {
    render(<TransactionTable transactions={mockTransactions} />)
    
    expect(screen.getByText('Showing 4 of 4 transactions')).toBeInTheDocument()
  })

  it('filters transactions by search term', async () => {
    const user = userEvent.setup()
    render(<TransactionTable transactions={mockTransactions} />)
    
    const searchInput = screen.getByPlaceholderText('Search transactions...')
    await user.type(searchInput, 'grocery')
    
    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
      expect(screen.queryByText('Gas Station')).not.toBeInTheDocument()
      expect(screen.getByText('Showing 1 of 1 transactions')).toBeInTheDocument()
    })
  })

  it('filters transactions by category', async () => {
    const user = userEvent.setup()
    render(<TransactionTable transactions={mockTransactions} />)
    
    const categoryFilter = screen.getByDisplayValue('All Categories')
    await user.selectOptions(categoryFilter, 'Food')
    
    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument()
      expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
      expect(screen.queryByText('Gas Station')).not.toBeInTheDocument()
      expect(screen.getByText('Showing 2 of 2 transactions')).toBeInTheDocument()
    })
  })

  it('filters transactions by type', async () => {
    const user = userEvent.setup()
    render(<TransactionTable transactions={mockTransactions} />)
    
    const typeFilter = screen.getByDisplayValue('All Types')
    await user.selectOptions(typeFilter, 'credit')
    
    await waitFor(() => {
      expect(screen.getByText('Salary Deposit')).toBeInTheDocument()
      expect(screen.queryByText('Grocery Store')).not.toBeInTheDocument()
      expect(screen.getByText('Showing 1 of 1 transactions')).toBeInTheDocument()
    })
  })

  it('sorts transactions by date', async () => {
    const user = userEvent.setup()
    render(<TransactionTable transactions={mockTransactions} />)
    
    const dateHeader = screen.getByText('Date')
    await user.click(dateHeader)
    
    // Check if transactions are sorted (ascending order)
    const rows = screen.getAllByRole('row')
    // First row is header, so start from index 1
    expect(rows[1]).toHaveTextContent('Coffee Shop') // 2024-01-12
    expect(rows[2]).toHaveTextContent('Gas Station') // 2024-01-13
  })

  it('sorts transactions by amount', async () => {
    const user = userEvent.setup()
    render(<TransactionTable transactions={mockTransactions} />)
    
    const amountHeader = screen.getByText('Amount')
    await user.click(amountHeader)
    
    // Should sort by absolute amount (ascending)
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('Coffee Shop') // $5.75
  })

  it('shows correct amount formatting and colors', () => {
    render(<TransactionTable transactions={mockTransactions} />)
    
    // Check debit (negative) amounts
    const debitAmounts = screen.getAllByText(/-\$\d+\.\d{2}/)
    expect(debitAmounts.length).toBeGreaterThan(0)
    
    // Check credit (positive) amounts
    const creditAmounts = screen.getAllByText(/\+\$\d+\.\d{2}/)
    expect(creditAmounts.length).toBeGreaterThan(0)
  })

  it('displays category badges', () => {
    render(<TransactionTable transactions={mockTransactions} />)
    
    expect(screen.getByText('Food')).toBeInTheDocument()
    expect(screen.getByText('Income')).toBeInTheDocument()
    expect(screen.getByText('Transportation')).toBeInTheDocument()
  })

  it('handles empty transactions list', () => {
    render(<TransactionTable transactions={[]} />)
    
    expect(screen.getByText('Showing 0 of 0 transactions')).toBeInTheDocument()
    // Should still show headers
    expect(screen.getByText('Date')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
  })

  it('handles pagination for large datasets', () => {
    // Create 60 transactions to test pagination
    const manyTransactions = Array.from({ length: 60 }, (_, i) => ({
      id: `${i + 1}`,
      date: `2024-01-${String(i + 1).padStart(2, '0')}`,
      description: `Transaction ${i + 1}`,
      amount: -(i + 1) * 10,
      category: 'Test',
      type: 'debit' as const
    }))

    render(<TransactionTable transactions={manyTransactions} />)
    
    // Should show first page (50 items)
    expect(screen.getByText('Showing 50 of 60 transactions')).toBeInTheDocument()
    expect(screen.getByText('Page 1 of 2')).toBeInTheDocument()
    expect(screen.getByText('Next')).toBeInTheDocument()
  })

  it('navigates to next page', async () => {
    const user = userEvent.setup()
    
    // Create 60 transactions to test pagination
    const manyTransactions = Array.from({ length: 60 }, (_, i) => ({
      id: `${i + 1}`,
      date: `2024-01-${String(i + 1).padStart(2, '0')}`,
      description: `Transaction ${i + 1}`,
      amount: -(i + 1) * 10,
      category: 'Test',
      type: 'debit' as const
    }))

    render(<TransactionTable transactions={manyTransactions} />)
    
    const nextButton = screen.getByText('Next')
    await user.click(nextButton)
    
    await waitFor(() => {
      expect(screen.getByText('Showing 10 of 60 transactions')).toBeInTheDocument()
      expect(screen.getByText('Page 2 of 2')).toBeInTheDocument()
    })
  })

  it('combines multiple filters correctly', async () => {
    const user = userEvent.setup()
    render(<TransactionTable transactions={mockTransactions} />)
    
    // Filter by category
    const categoryFilter = screen.getByDisplayValue('All Categories')
    await user.selectOptions(categoryFilter, 'Food')
    
    // Then search within that category
    const searchInput = screen.getByPlaceholderText('Search transactions...')
    await user.type(searchInput, 'coffee')
    
    await waitFor(() => {
      expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
      expect(screen.queryByText('Grocery Store')).not.toBeInTheDocument()
      expect(screen.getByText('Showing 1 of 1 transactions')).toBeInTheDocument()
    })
  })

  it('shows trending indicators for amounts', () => {
    render(<TransactionTable transactions={mockTransactions} />)
    
    // Should show down arrows for debits and up arrows for credits
    const trendingDownIcons = screen.getAllByTestId('trending-down-icon') || 
      document.querySelectorAll('[data-lucide="trending-down"]')
    const trendingUpIcons = screen.getAllByTestId('trending-up-icon') || 
      document.querySelectorAll('[data-lucide="trending-up"]')
    
    expect(trendingDownIcons.length + trendingUpIcons.length).toBeGreaterThan(0)
  })
})