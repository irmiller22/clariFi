import type {
  UploadResponse,
  Transaction,
  AnalyticsSummary,
  CategorySpending,
  TimelineData,
  SpendingTrends,
  MerchantSpending,
  RecurringCharge,
  Anomaly,
  RollingAverage,
  Cashflow,
} from "./types"

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
  async uploadTransactions(files: File | File[]): Promise<UploadResponse> {
    const formData = new FormData()
    const list = Array.isArray(files) ? files : [files]
    list.forEach((file) => formData.append("files", file))

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
    account?: string
    search?: string
  }): Promise<{ transactions: Transaction[], total: number }> {
    const queryParams = new URLSearchParams()

    if (params?.limit !== undefined) queryParams.set("limit", params.limit.toString())
    if (params?.offset !== undefined) queryParams.set("offset", params.offset.toString())
    if (params?.category) queryParams.set("category", params.category)
    if (params?.type) queryParams.set("type", params.type)
    if (params?.account) queryParams.set("account", params.account)
    if (params?.search) queryParams.set("search", params.search)

    const url = `${API_BASE_URL}/api/transactions?${queryParams.toString()}`
    const response = await fetch(url)

    return handleResponse<{ transactions: Transaction[], total: number }>(response)
  },

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/summary`)
    return handleResponse<AnalyticsSummary>(response)
  },

  async getCategoryAnalytics(): Promise<CategorySpending[]> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/by-category`)
    return handleResponse<CategorySpending[]>(response)
  },

  async getTimelineAnalytics(
    granularity: "day" | "week" | "month" = "month"
  ): Promise<TimelineData[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/analytics/timeline?granularity=${granularity}`
    )
    return handleResponse<TimelineData[]>(response)
  },

  async getTrends(params?: { category?: string; months?: number }): Promise<SpendingTrends> {
    const query = new URLSearchParams()
    if (params?.category) query.set("category", params.category)
    if (params?.months !== undefined) query.set("months", params.months.toString())
    const response = await fetch(`${API_BASE_URL}/api/analytics/trends?${query.toString()}`)
    return handleResponse<SpendingTrends>(response)
  },

  async getTopMerchants(params?: {
    limit?: number
    by?: "spend" | "count"
  }): Promise<MerchantSpending[]> {
    const query = new URLSearchParams()
    if (params?.limit !== undefined) query.set("limit", params.limit.toString())
    if (params?.by) query.set("by", params.by)
    const response = await fetch(`${API_BASE_URL}/api/analytics/top-merchants?${query.toString()}`)
    return handleResponse<MerchantSpending[]>(response)
  },

  async getRecurring(): Promise<RecurringCharge[]> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/recurring`)
    return handleResponse<RecurringCharge[]>(response)
  },

  async getAnomalies(): Promise<Anomaly[]> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/anomalies`)
    return handleResponse<Anomaly[]>(response)
  },

  async getRollingAverage(window = 3): Promise<RollingAverage[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/analytics/rolling-average?window=${window}`
    )
    return handleResponse<RollingAverage[]>(response)
  },

  async getCashflow(): Promise<Cashflow[]> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/cashflow`)
    return handleResponse<Cashflow[]>(response)
  }
}

export { ApiError }