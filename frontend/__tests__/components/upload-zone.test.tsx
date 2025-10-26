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
    expect(screen.getByText('Supports bank CSV exports up to 10MB')).toBeInTheDocument()
  })

  it('handles file selection via input', async () => {
    const user = userEvent.setup()
    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    expect(screen.getByText('test.csv')).toBeInTheDocument()
    expect(screen.getByText(/KB/)).toBeInTheDocument()
  })

  it('shows error for non-CSV files', async () => {
    const user = userEvent.setup()
    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    expect(screen.getByText('Please upload a valid CSV file')).toBeInTheDocument()
  })

  it('handles drag and drop events', () => {
    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const dropZone = screen.getByText('Drop your CSV file here').closest('div')!
    
    // Test drag over
    fireEvent.dragOver(dropZone, {
      dataTransfer: {
        files: [new File(['test'], 'test.csv', { type: 'text/csv' })]
      }
    })
    
    // Test drag leave
    fireEvent.dragLeave(dropZone)
    
    // Test drop
    const csvFile = new File(['test content'], 'test.csv', { type: 'text/csv' })
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [csvFile]
      }
    })
    
    expect(screen.getByText('test.csv')).toBeInTheDocument()
  })

  it('shows upload button when file is selected', async () => {
    const user = userEvent.setup()
    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    expect(screen.getByText('Upload & Analyze')).toBeInTheDocument()
  })

  it('handles successful upload', async () => {
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

  it('handles upload error', async () => {
    const user = userEvent.setup()
    
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ message: 'Invalid file format' })
    })

    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByText('Upload & Analyze')
    await user.click(uploadButton)
    
    await waitFor(() => {
      expect(screen.getByText('Upload failed: 400')).toBeInTheDocument()
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

  it('shows loading state during upload', async () => {
    const user = userEvent.setup()
    
    // Mock a delayed response
    mockFetch.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ success: true, transactions: [], summary: {} })
      }), 100))
    )

    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    const uploadButton = screen.getByText('Upload & Analyze')
    await user.click(uploadButton)
    
    expect(screen.getByText('Uploading...')).toBeInTheDocument()
    expect(uploadButton).toBeDisabled()
  })

  it('allows file removal', async () => {
    const user = userEvent.setup()
    render(<UploadZone onUploadSuccess={mockOnUploadSuccess} />)
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    
    await user.upload(input, file)
    
    expect(screen.getByText('test.csv')).toBeInTheDocument()
    
    const removeButton = screen.getByRole('button', { name: '' }) // X button
    await user.click(removeButton)
    
    expect(screen.queryByText('test.csv')).not.toBeInTheDocument()
    expect(screen.getByText('Drop your CSV file here')).toBeInTheDocument()
  })
})