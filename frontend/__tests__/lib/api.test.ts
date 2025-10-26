import { api, ApiError } from '@/lib/api'

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockClear()
  })

  describe('uploadTransactions', () => {
    it('successfully uploads a file', async () => {
      const mockResponse = {
        success: true,
        message: 'Upload successful',
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
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => mockResponse
      })

      const file = new File(['test content'], 'test.csv', { type: 'text/csv' })
      const result = await api.uploadTransactions(file)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/transactions/upload',
        {
          method: 'POST',
          body: expect.any(FormData)
        }
      )
      expect(result).toEqual(mockResponse)
    })

    it('throws ApiError on HTTP error', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => ({ message: 'Invalid file format' })
      }
      
      mockFetch.mockResolvedValue(mockResponse)

      const file = new File(['test content'], 'test.csv', { type: 'text/csv' })

      await expect(api.uploadTransactions(file)).rejects.toThrow(ApiError)
      await expect(api.uploadTransactions(file)).rejects.toThrow('Invalid file format')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const file = new File(['test content'], 'test.csv', { type: 'text/csv' })

      await expect(api.uploadTransactions(file)).rejects.toThrow('Network error')
    })
  })

  describe('getTransactions', () => {
    it('fetches transactions without parameters', async () => {
      const mockResponse = {
        transactions: [
          {
            id: '1',
            date: '2024-01-01',
            description: 'Test',
            amount: -100,
            category: 'Food',
            type: 'debit'
          }
        ],
        total: 1
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => mockResponse
      })

      const result = await api.getTransactions()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/transactions?')
      expect(result).toEqual(mockResponse)
    })

    it('fetches transactions with parameters', async () => {
      const mockResponse = { transactions: [], total: 0 }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => mockResponse
      })

      await api.getTransactions({
        limit: 10,
        offset: 20,
        category: 'Food',
        type: 'debit',
        search: 'grocery'
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/transactions?limit=10&offset=20&category=Food&type=debit&search=grocery'
      )
    })
  })

  describe('getAnalyticsSummary', () => {
    it('fetches analytics summary', async () => {
      const mockResponse = {
        totalSpent: 1000,
        totalIncome: 2000,
        netAmount: 1000,
        transactionCount: 50,
        avgTransactionAmount: 20
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => mockResponse
      })

      const result = await api.getAnalyticsSummary()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/analytics/summary')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getCategoryAnalytics', () => {
    it('fetches category analytics', async () => {
      const mockResponse = [
        {
          category: 'Food',
          amount: 500,
          count: 10,
          percentage: 50
        },
        {
          category: 'Transportation',
          amount: 300,
          count: 5,
          percentage: 30
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => mockResponse
      })

      const result = await api.getCategoryAnalytics()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/analytics/by-category')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getTimelineAnalytics', () => {
    it('fetches timeline analytics', async () => {
      const mockResponse = [
        {
          date: '2024-01',
          amount: -500,
          cumulative: -500
        },
        {
          date: '2024-02',
          amount: -300,
          cumulative: -800
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => mockResponse
      })

      const result = await api.getTimelineAnalytics()

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/analytics/timeline')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Error handling', () => {
    it('handles non-JSON error responses', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => { throw new Error('Not JSON') }
      }
      
      mockFetch.mockResolvedValue(mockResponse)

      const file = new File(['test'], 'test.csv')

      await expect(api.uploadTransactions(file)).rejects.toThrow(ApiError)
      await expect(api.uploadTransactions(file)).rejects.toThrow('Internal Server Error')
    })

    it('creates ApiError with correct status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: {
          get: (name: string) => name === 'content-type' ? 'application/json' : null
        },
        json: async () => ({ detail: 'Resource not found' })
      })

      try {
        await api.getAnalyticsSummary()
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect((error as ApiError).status).toBe(404)
        expect((error as ApiError).message).toBe('Resource not found')
      }
    })

    it('handles text responses for non-JSON endpoints', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: (name: string) => name === 'content-type' ? 'text/plain' : null
        },
        text: async () => 'Success'
      })

      // This would be for a hypothetical text endpoint
      const result = await api.getAnalyticsSummary()
      expect(result).toBe('Success')
    })
  })
})