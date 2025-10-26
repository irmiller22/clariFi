export interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  category?: string
  type: 'debit' | 'credit'
}

export interface AnalyticsSummary {
  totalSpent: number
  totalIncome: number
  netAmount: number
  transactionCount: number
  avgTransactionAmount: number
}

export interface CategorySpending {
  category: string
  amount: number
  count: number
  percentage: number
}

export interface TimelineData {
  date: string
  amount: number
  cumulative: number
}

export interface UploadResponse {
  success: boolean
  message: string
  transactions?: Transaction[]
  summary?: AnalyticsSummary
}