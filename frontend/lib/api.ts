import type { UploadResponse, Transaction, AnalyticsSummary } from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`
    try {
      const errorData = await response.json()
      errorMessage = errorData.message || errorData.detail || errorMessage
    } catch {
      // If we can't parse the error, use the status text
      errorMessage = response.statusText || errorMessage
    }
    throw new ApiError(response.status, errorMessage)
  }

  const contentType = response.headers.get("content-type")
  if (contentType && contentType.includes("application/json")) {
    return response.json()
  }
  
  return response.text() as unknown as T
}

export const api = {
  async uploadTransactions(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append("file", file)

    const response = await fetch(`${API_BASE_URL}/api/transactions/upload`, {
      method: "POST",
      body: formData,
    })

    return handleResponse<UploadResponse>(response)
  },

  async getTransactions(params?: {
    limit?: number
    offset?: number
    category?: string
    type?: "debit" | "credit"
    search?: string
  }): Promise<{ transactions: Transaction[], total: number }> {
    const queryParams = new URLSearchParams()
    
    if (params?.limit !== undefined) queryParams.set("limit", params.limit.toString())
    if (params?.offset !== undefined) queryParams.set("offset", params.offset.toString())
    if (params?.category) queryParams.set("category", params.category)
    if (params?.type) queryParams.set("type", params.type)
    if (params?.search) queryParams.set("search", params.search)

    const url = `${API_BASE_URL}/api/transactions?${queryParams.toString()}`
    const response = await fetch(url)

    return handleResponse<{ transactions: Transaction[], total: number }>(response)
  },

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/summary`)
    return handleResponse<AnalyticsSummary>(response)
  },

  async getCategoryAnalytics(): Promise<Array<{
    category: string
    amount: number
    count: number
    percentage: number
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/by-category`)
    return handleResponse<Array<{
      category: string
      amount: number
      count: number
      percentage: number
    }>>(response)
  },

  async getTimelineAnalytics(): Promise<Array<{
    date: string
    amount: number
    cumulative: number
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/timeline`)
    return handleResponse<Array<{
      date: string
      amount: number
      cumulative: number
    }>>(response)
  }
}

export { ApiError }