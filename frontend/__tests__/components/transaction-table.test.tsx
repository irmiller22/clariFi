import { useState } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TransactionTable } from '@/components/transaction-table'
import { DEFAULT_CATEGORIES } from '@/lib/categories'
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

// Render the table with the categorization props the page supplies. Categories
// default to the built-ins plus whatever the supplied transactions already use,
// so per-row `<select>` values always map to a valid option.
function renderTable(transactions: Transaction[]) {
  const present = transactions
    .map(t => t.category)
    .filter((c): c is string => Boolean(c))
  const available = [...new Set([...DEFAULT_CATEGORIES, ...present])]
  return render(
    <TransactionTable
      transactions={transactions}
      availableCategories={available}
      onCategorize={() => {}}
      onAddCategory={() => {}}
    />
  )
}

// A stateful wrapper used to assert that categorization edits flow through and
// re-render — mirrors the lifting done in `app/page.tsx`.
function StatefulTable({ initial }: { initial: Transaction[] }) {
  const [transactions, setTransactions] = useState(initial)
  const [custom, setCustom] = useState<string[]>([])
  return (
    <TransactionTable
      transactions={transactions}
      availableCategories={[...DEFAULT_CATEGORIES, ...custom]}
      onCategorize={(ids, category) =>
        setTransactions(prev =>
          prev.map(t => (ids.includes(t.id) ? { ...t, category } : t))
        )
      }
      onAddCategory={category => setCustom(prev => [...prev, category])}
    />
  )
}

describe('TransactionTable', () => {
  it('renders transaction table with data', () => {
    renderTable(mockTransactions)

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
    renderTable(mockTransactions)

    expect(screen.getByText('Showing 4 of 4 transactions')).toBeInTheDocument()
  })

  it('filters transactions by search term', async () => {
    const user = userEvent.setup()
    renderTable(mockTransactions)

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
    renderTable(mockTransactions)

    const categoryFilter = screen.getByLabelText('Filter by category')
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
    renderTable(mockTransactions)

    const typeFilter = screen.getByLabelText('Filter by type')
    await user.selectOptions(typeFilter, 'credit')

    await waitFor(() => {
      expect(screen.getByText('Salary Deposit')).toBeInTheDocument()
      expect(screen.queryByText('Grocery Store')).not.toBeInTheDocument()
      expect(screen.getByText('Showing 1 of 1 transactions')).toBeInTheDocument()
    })
  })

  it('filters to only uncategorized transactions', async () => {
    const user = userEvent.setup()
    renderTable([
      ...mockTransactions,
      { id: '5', date: '2024-01-11', description: 'Mystery Charge', amount: -12.0, type: 'debit' },
    ])

    const categoryFilter = screen.getByLabelText('Filter by category')
    await user.selectOptions(categoryFilter, 'Uncategorized')

    await waitFor(() => {
      expect(screen.getByText('Mystery Charge')).toBeInTheDocument()
      expect(screen.queryByText('Grocery Store')).not.toBeInTheDocument()
      expect(screen.getByText('Showing 1 of 1 transactions')).toBeInTheDocument()
    })
  })

  it('sorts transactions by date', async () => {
    const user = userEvent.setup()
    renderTable(mockTransactions)

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
    renderTable(mockTransactions)

    const amountHeader = screen.getByText('Amount')
    await user.click(amountHeader)

    // Should sort by absolute amount (ascending)
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('Coffee Shop') // $5.75
  })

  it('shows correct amount formatting and colors', () => {
    renderTable(mockTransactions)

    const tableBody = document.querySelector('tbody')
    expect(tableBody).toBeInTheDocument()

    // Verify that amounts are formatted (contains $ symbol)
    expect(tableBody?.textContent).toContain('$85.50')
    expect(tableBody?.textContent).toContain('$5.75')
    expect(tableBody?.textContent).toContain('$45.25')
    expect(tableBody?.textContent).toContain('$2,500.00')

    // Check that signs are displayed for debits and credits
    expect(tableBody?.textContent).toContain('-') // Debit transactions
    expect(tableBody?.textContent).toContain('+') // Credit transactions
  })

  it('handles empty transactions list', () => {
    renderTable([])

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

    renderTable(manyTransactions)

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

    renderTable(manyTransactions)

    const nextButton = screen.getByText('Next')
    await user.click(nextButton)

    await waitFor(() => {
      expect(screen.getByText('Showing 10 of 60 transactions')).toBeInTheDocument()
      expect(screen.getByText('Page 2 of 2')).toBeInTheDocument()
    })
  })

  it('combines multiple filters correctly', async () => {
    const user = userEvent.setup()
    renderTable(mockTransactions)

    // Filter by category
    const categoryFilter = screen.getByLabelText('Filter by category')
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
    renderTable(mockTransactions)

    // Check that trending icons are present using class selectors
    const trendingIcons = document.querySelectorAll('.lucide-trending-down, .lucide-trending-up')
    expect(trendingIcons.length).toBe(4) // Should have an icon for each transaction
  })

  describe('categorization', () => {
    it('lets the user change a transaction category from the row editor', async () => {
      const user = userEvent.setup()
      render(<StatefulTable initial={mockTransactions} />)

      const editor = screen.getByLabelText('Category for Gas Station')
      expect(editor).toHaveValue('Transportation')

      await user.selectOptions(editor, 'Travel')

      await waitFor(() =>
        expect(screen.getByLabelText('Category for Gas Station')).toHaveValue('Travel')
      )
    })

    it('suggests a category for an uncategorized transaction and applies it on accept', async () => {
      const user = userEvent.setup()
      render(
        <StatefulTable
          initial={[
            { id: '1', date: '2024-02-01', description: 'STARBUCKS STORE 123', amount: -6.5, type: 'debit' },
          ]}
        />
      )

      const editor = screen.getByLabelText('Category for STARBUCKS STORE 123')
      expect(editor).toHaveValue('')

      const suggest = screen.getByRole('button', { name: /suggest: dining/i })
      await user.click(suggest)

      await waitFor(() =>
        expect(screen.getByLabelText('Category for STARBUCKS STORE 123')).toHaveValue('Dining')
      )
    })

    it('applies a category to every transaction from the same merchant', async () => {
      const user = userEvent.setup()
      render(
        <StatefulTable
          initial={[
            { id: '1', date: '2024-03-01', description: 'AMAZON #1', merchant: 'Amazon', amount: -20, type: 'debit' },
            { id: '2', date: '2024-03-02', description: 'AMAZON #2', merchant: 'Amazon', amount: -35, type: 'debit' },
          ]}
        />
      )

      // Tag the first Amazon row, then propagate to the merchant.
      await user.selectOptions(screen.getByLabelText('Category for AMAZON #1'), 'Shopping')
      const applyAll = await screen.findByRole('button', { name: /apply to all 2 from this merchant/i })
      await user.click(applyAll)

      await waitFor(() => {
        expect(screen.getByLabelText('Category for AMAZON #1')).toHaveValue('Shopping')
        expect(screen.getByLabelText('Category for AMAZON #2')).toHaveValue('Shopping')
      })
    })

    it('adds a custom category and makes it selectable', async () => {
      const user = userEvent.setup()
      render(
        <StatefulTable
          initial={[
            { id: '1', date: '2024-04-01', description: 'Mystery Charge', amount: -12, type: 'debit' },
          ]}
        />
      )

      await user.type(screen.getByLabelText('New category name'), 'Vacation Fund')
      await user.click(screen.getByRole('button', { name: 'Add' }))

      const editor = screen.getByLabelText('Category for Mystery Charge')
      await waitFor(() =>
        expect(screen.getByRole('option', { name: 'Vacation Fund' })).toBeInTheDocument()
      )
      await user.selectOptions(editor, 'Vacation Fund')
      expect(screen.getByLabelText('Category for Mystery Charge')).toHaveValue('Vacation Fund')
    })

    it('bulk auto-categorizes every matchable uncategorized transaction', async () => {
      const user = userEvent.setup()
      render(
        <StatefulTable
          initial={[
            { id: '1', date: '2024-05-01', description: 'NETFLIX.COM', amount: -15.99, type: 'debit' },
            { id: '2', date: '2024-05-02', description: 'WHOLE FOODS MKT', amount: -54.2, type: 'debit' },
            { id: '3', date: '2024-05-03', description: 'UNKNOWN VENDOR', amount: -9.0, type: 'debit' },
          ]}
        />
      )

      await user.click(screen.getByRole('button', { name: /auto-categorize/i }))

      await waitFor(() => {
        expect(screen.getByLabelText('Category for NETFLIX.COM')).toHaveValue('Subscriptions')
        expect(screen.getByLabelText('Category for WHOLE FOODS MKT')).toHaveValue('Groceries')
        // No rule matches — left uncategorized for the user (or AI, later).
        expect(screen.getByLabelText('Category for UNKNOWN VENDOR')).toHaveValue('')
      })
    })
  })
})
