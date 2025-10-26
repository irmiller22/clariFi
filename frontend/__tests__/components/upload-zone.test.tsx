import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UploadZone } from '@/components/upload-zone'

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

const mockOnUploadSuccess = jest.fn()

describe('UploadZone', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockClear()
  })

  it('renders upload zone with correct initial state', () => {
    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    expect(screen.getByText('Drop your CSV file here')).toBeInTheDocument()
    expect(screen.getByText('or click to browse files')).toBeInTheDocument()
  })

  it('handles file selection and shows upload button', async () => {
    const user = userEvent.setup()
    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    expect(screen.getByText('test.csv')).toBeInTheDocument()
    expect(screen.getByText('Upload & Analyze')).toBeInTheDocument()
  })

  it('handles successful upload and calls onUploadSuccess', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      success: true,
      transactions: [
        {
          id: '1',
          date: '2024-01-01',
          description: 'Test Transaction',
          amount: -100,
          category: 'Food',
          type: 'debit'
        }
      ],
      summary: {
        totalSpent: 100,
        totalIncome: 0,
        netAmount: -100,
        transactionCount: 1,
        avgTransactionAmount: 100
      }
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByText('Upload & Analyze')
    await user.click(uploadButton)
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/transactions/upload', {
        method: 'POST',
        body: expect.any(FormData)
      })
      expect(mockOnUploadSuccess).toHaveBeenCalledWith(mockResponse)
    })
  })

  it('handles upload error and displays error message', async () => {
    const user = userEvent.setup()
    
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Invalid file format' })
    })

    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByText('Upload & Analyze')
    await user.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid file format')).toBeInTheDocument()
    })
  })

  it('handles network error', async () => {
    const user = userEvent.setup()
    
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByText('Upload & Analyze')
    await user.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })
})